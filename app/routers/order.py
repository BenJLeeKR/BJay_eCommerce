from __future__ import annotations
import asyncio
import logging
from typing import Optional

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.dependencies import get_db
from app.events.producer import TOPIC_ORDER_CREATED, publish_event
from app.events.schemas import OrderCreatedEvent, OrderItemEvent
from app.models.cart import Cart
from app.models.inventory import Inventory, InventoryReservation, InventoryTransaction
from app.models.order import OrderHeader, OrderItem, OrderStatusHistory
from app.schemas import APIResponse
from app.schemas.order import OrderCreate, OrderRead, OrderUpdate

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/orders", tags=["Orders (주문)"])


def _order_query():
    """주문 상세 조회를 위한 기본 쿼리."""
    return (
        select(OrderHeader)
        .options(
            selectinload(OrderHeader.user),
            selectinload(OrderHeader.items),
            selectinload(OrderHeader.status_histories),
            selectinload(OrderHeader.payments),
            selectinload(OrderHeader.shipments),
            selectinload(OrderHeader.address_snapshots),
            selectinload(OrderHeader.coupons),
        )
        .where(OrderHeader.deleted_at.is_(None))
    )


def _get_order_or_404(db: Session, order_id: int) -> OrderHeader:
    """주문 ID로 주문을 조회하거나 404 오류를 발생시킨다."""
    statement = _order_query().where(OrderHeader.id == order_id)
    order = db.execute(statement).scalar_one_or_none()

    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="주문을 찾을 수 없습니다.",
        )

    return order


@router.get("", response_model=APIResponse[list[OrderRead]], summary="주문 목록 조회")
def list_orders(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    user_id: Optional[int] = Query(default=None, ge=1),
    order_status: Optional[str] = Query(default=None, max_length=30),
    db: Session = Depends(get_db),
) -> APIResponse[list[OrderRead]]:
    """주문 목록을 사용자 ID와 상태로 필터링하여 조회한다."""
    statement = _order_query().offset(skip).limit(limit)

    if user_id is not None:
        statement = statement.where(OrderHeader.user_id == user_id)

    if order_status is not None:
        statement = statement.where(OrderHeader.order_status == order_status)

    orders = db.execute(statement).scalars().unique().all()
    return APIResponse(data=orders, message="주문 목록을 조회했습니다.")


@router.get("/{order_id}", response_model=APIResponse[OrderRead], summary="주문 상세 조회")
def get_order(order_id: int, db: Session = Depends(get_db)) -> APIResponse[OrderRead]:
    """주문 상세 정보를 조회한다."""
    order = _get_order_or_404(db, order_id)
    return APIResponse(data=order, message="주문 상세 정보를 조회했습니다.")


@router.post(
    "",
    response_model=APIResponse[OrderRead],
    status_code=status.HTTP_201_CREATED,
    summary="주문 생성",
)
async def create_order(
    payload: OrderCreate,
    db: Session = Depends(get_db),
) -> APIResponse[OrderRead]:
    """새로운 주문을 생성한다.

    cart_id가 제공되면 해당 장바구니의 상태를 'ORDERED'로 변경한다.
    """
    cart: Cart | None = None

    # cart_id가 제공된 경우 장바구니 검증
    if payload.cart_id is not None:
        statement = select(Cart).where(
            Cart.id == payload.cart_id,
            Cart.deleted_at.is_(None),
        )
        cart = db.execute(statement).scalar_one_or_none()
        if cart is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="장바구니를 찾을 수 없습니다.",
            )
        if cart.cart_status != "ACTIVE":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"이미 처리된 장바구니입니다. (상태: {cart.cart_status})",
            )

    order = OrderHeader(
        order_number=payload.order_number,
        user_id=payload.user_id,
        cart_id=payload.cart_id,
        order_status=payload.order_status,
        total_product_amount=payload.total_product_amount,
        total_discount_amount=payload.total_discount_amount,
        total_shipping_amount=payload.total_shipping_amount,
        total_pay_amount=payload.total_pay_amount,
        ordered_at=payload.ordered_at or datetime.now(timezone.utc).replace(tzinfo=None),
        created_by=payload.created_by,
    )
    db.add(order)
    db.flush()  # order.id 확보

    # 주문 상품 생성
    for item_data in payload.items:
        item = OrderItem(
            order_id=order.id,
            sku_id=item_data.sku_id,
            product_name=item_data.product_name,
            option_summary=item_data.option_summary,
            quantity=item_data.quantity,
            unit_price_amount=item_data.unit_price_amount,
            total_price_amount=item_data.total_price_amount,
            created_by=item_data.created_by,
        )
        db.add(item)

    # 재고 예약 처리: 각 주문 상품에 대해 Inventory 차감 및 예약
    for item_data in payload.items:
        # SELECT ... FOR UPDATE로 동시성 제어 (Race Condition 방지)
        inventory = (
            db.query(Inventory)
            .with_for_update()
            .filter(Inventory.sku_id == item_data.sku_id)
            .first()
        )
        if inventory is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"SKU(ID={item_data.sku_id})의 재고 정보가 존재하지 않습니다.",
            )
        if inventory.available_quantity < item_data.quantity:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"SKU(ID={item_data.sku_id})의 재고가 부족합니다. (요청: {item_data.quantity}, 가용재고: {inventory.available_quantity})",
            )

        # InventoryReservation 생성
        reservation = InventoryReservation(
            sku_id=item_data.sku_id,
            order_id=order.id,
            reserved_quantity=item_data.quantity,
            reservation_status="RESERVED",
        )
        db.add(reservation)

        # Inventory 수량 업데이트
        inventory.available_quantity -= item_data.quantity
        inventory.reserved_quantity += item_data.quantity

        # InventoryTransaction 기록 (RESERVE)
        transaction = InventoryTransaction(
            sku_id=item_data.sku_id,
            transaction_type="RESERVE",
            quantity=item_data.quantity,
            reference_type="ORDER",
            reference_id=order.id,
        )
        db.add(transaction)

    # 초기 상태 이력 생성
    status_history = OrderStatusHistory(
        order_id=order.id,
        order_status=order.order_status,
        changed_at=datetime.now(timezone.utc).replace(tzinfo=None),
        changed_by=payload.created_by,
    )
    db.add(status_history)

    # cart_id가 제공된 경우 cart_status → 'ORDERED'
    if cart is not None:
        cart.cart_status = "ORDERED"
        cart.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
        db.add(cart)

    db.commit()
    db.refresh(order)

    created_order = _get_order_or_404(db, order.id)

    # === Kafka: OrderCreated 이벤트 발행 (asyncio.create_task) ===
    async def _publish_order_created() -> None:
        try:
            event = OrderCreatedEvent(
                order_id=order.id,
                user_id=order.user_id,
                total_pay_amount=order.total_pay_amount,
                items=[
                    OrderItemEvent(
                        sku_id=item.sku_id,
                        product_name=item.product_name,
                        quantity=item.quantity,
                        unit_price_amount=item.unit_price_amount,
                    )
                    for item in order.items
                ],
            )
            await publish_event(
                topic=TOPIC_ORDER_CREATED,
                key=str(order.id),
                event=event,
            )
        except Exception as exc:
            logger.error("Failed to publish OrderCreated event: %s", exc)

    asyncio.create_task(_publish_order_created())
    # ===============================================================

    return APIResponse(data=created_order, message="주문을 생성했습니다.")


@router.put("/{order_id}", response_model=APIResponse[OrderRead], summary="주문 수정")
def update_order(
    order_id: int,
    payload: OrderUpdate,
    db: Session = Depends(get_db),
) -> APIResponse[OrderRead]:
    """주문 정보를 수정한다."""
    order = _get_order_or_404(db, order_id)
    update_data = payload.model_dump(exclude_unset=True)

    for field_name, field_value in update_data.items():
        setattr(order, field_name, field_value)

    if update_data:
        order.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)

    # 상태가 변경된 경우 이력 추가
    if "order_status" in update_data:
        status_history = OrderStatusHistory(
            order_id=order.id,
            order_status=order.order_status,
            changed_at=datetime.now(timezone.utc).replace(tzinfo=None),
            changed_by=payload.updated_by,
        )
        db.add(status_history)

    db.add(order)
    db.commit()
    db.refresh(order)

    updated_order = _get_order_or_404(db, order_id)
    return APIResponse(data=updated_order, message="주문을 수정했습니다.")


@router.delete(
    "/{order_id}",
    response_model=APIResponse[dict[str, int]],
    summary="주문 삭제",
)
def delete_order(order_id: int, db: Session = Depends(get_db)) -> APIResponse[dict[str, int]]:
    """주문을 소프트 삭제한다."""
    order = _get_order_or_404(db, order_id)
    order.deleted_at = datetime.now(timezone.utc).replace(tzinfo=None)
    db.add(order)
    db.commit()
    db.refresh(order)

    return APIResponse(data={"order_id": order_id}, message="주문을 삭제했습니다.")


# -------------------------------------------------------------------
# Phase 7: 구매 확정 API (DELIVERED → COMPLETE)
# -------------------------------------------------------------------


@router.put(
    "/{order_id}/complete",
    response_model=APIResponse[OrderRead],
    summary="구매 확정",
)
def complete_order(
    order_id: int,
    db: Session = Depends(get_db),
) -> APIResponse[OrderRead]:
    """배송 완료된 주문을 구매 확정(COMPLETE) 상태로 변경한다."""
    from app.core.enums import OrderStatus

    order = _get_order_or_404(db, order_id)

    if not OrderStatus.is_valid_transition(order.order_status, OrderStatus.COMPLETED):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"주문 상태({order.order_status})에서 COMPLETED로 변경할 수 없습니다.",
        )

    old_status = order.order_status
    order.order_status = OrderStatus.COMPLETED
    order.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
    db.add(order)

    status_history = OrderStatusHistory(
        order_id=order.id,
        order_status=OrderStatus.COMPLETED,
        changed_at=datetime.now(timezone.utc).replace(tzinfo=None),
        change_reason="구매 확정",
    )
    db.add(status_history)

    db.commit()
    db.refresh(order)

    completed_order = _get_order_or_404(db, order.id)
    logger.info("Order %s status changed: %s -> %s", order.id, old_status, OrderStatus.COMPLETED)
    return APIResponse(data=completed_order, message="구매가 확정되었습니다.")


# -------------------------------------------------------------------
# Phase 8: 주문 취소 API (CANCELLED + 재고 롤백)
# -------------------------------------------------------------------


@router.put(
    "/{order_id}/cancel",
    response_model=APIResponse[OrderRead],
    summary="주문 취소",
)
def cancel_order(
    order_id: int,
    db: Session = Depends(get_db),
) -> APIResponse[OrderRead]:
    """주문을 취소(CANCELLED) 상태로 변경하고 재고를 롤백한다."""
    from app.core.enums import OrderStatus

    order = _get_order_or_404(db, order_id)

    if not OrderStatus.is_valid_transition(order.order_status, OrderStatus.CANCELLED):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"주문 상태({order.order_status})에서 CANCELLED로 변경할 수 없습니다.",
        )

    old_status = order.order_status

    # 재고 롤백: RESERVED 상태의 InventoryReservation을 CANCELLED로 변경
    reservations = (
        db.query(InventoryReservation)
        .filter(
            InventoryReservation.order_id == order.id,
            InventoryReservation.reservation_status == "RESERVED",
        )
        .all()
    )

    for reservation in reservations:
        # Inventory available_quantity 복원
        inventory = db.query(Inventory).filter(Inventory.sku_id == reservation.sku_id).first()
        if inventory:
            inventory.available_quantity += reservation.reserved_quantity
            inventory.reserved_quantity -= reservation.reserved_quantity
            db.add(inventory)

        # 예약 상태 변경
        reservation.reservation_status = "CANCELLED"
        db.add(reservation)

        # InventoryTransaction 기록 (ROLLBACK)
        transaction = InventoryTransaction(
            sku_id=reservation.sku_id,
            transaction_type="ROLLBACK",
            quantity=reservation.reserved_quantity,
            reference_type="ORDER",
            reference_id=order.id,
        )
        db.add(transaction)

    # Order 상태 변경
    order.order_status = OrderStatus.CANCELLED
    order.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
    db.add(order)

    status_history = OrderStatusHistory(
        order_id=order.id,
        order_status=OrderStatus.CANCELLED,
        changed_at=datetime.now(timezone.utc).replace(tzinfo=None),
        change_reason="주문 취소",
    )
    db.add(status_history)

    db.commit()
    db.refresh(order)

    cancelled_order = _get_order_or_404(db, order.id)
    logger.info(
        "Order %s cancelled. Status changed: %s -> %s. Rolled back %d reservation(s).",
        order.id,
        old_status,
        OrderStatus.CANCELLED,
        len(reservations),
    )
    return APIResponse(data=cancelled_order, message="주문이 취소되었습니다.")


__all__ = ["router"]