from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable, Optional

from aiokafka import AIOKafkaConsumer

from app.core.config import settings
from app.core.enums import OrderStatus, PaymentStatus, ShipmentStatus
from app.database import SessionLocal
from app.events.producer import (
    TOPIC_INVENTORY_UPDATED,
    TOPIC_ORDER_CREATED,
    TOPIC_PAYMENT_COMPLETED,
    TOPIC_PRODUCT_INDEX_UPDATED,
    TOPIC_SHIPMENT_CREATED,
    publish_event,
)
from app.events.retry import is_duplicate, publish_to_dlq
from app.events.schemas import (
    InventoryUpdatedEvent,
    OrderCreatedEvent,
    PaymentCompletedEvent,
    ProductIndexUpdatedEvent,
    ShipmentCreatedEvent,
)
# 모든 모델을 임포트하여 SQLAlchemy 매퍼가 모든 관계를 올바르게
# 해석할 수 있도록 한다 (string-based forward reference 해결).
# IMPORTANT: UserAccount는 Cart에서 string reference로 참조되므로
# Cart보다 먼저 import되어야 한다.
from app.models.user import UserAccount  # noqa: F401 -- 반드시 Cart보다 먼저!
from app.models.admin import AdminAccount  # noqa: F401
from app.models.cart import Cart, CartCoupon, CartItem, CartItemOptionSnapshot  # noqa: F401
from app.models.inventory import (  # noqa: F401
    Inventory,
    InventoryAdjustment,
    InventoryReservation,
    InventoryTransaction,
    WarehouseStock,
)
from app.models.order import (  # noqa: F401
    OrderAddressSnapshot,
    OrderCoupon,
    OrderHeader,
    OrderItem,
    OrderPayment,
    OrderShipment,
    OrderStatusHistory,
)
from app.models.payment import Payment, PaymentLog, PaymentMethod, PaymentRefund, PaymentTransaction  # noqa: F401
from app.models.product import (  # noqa: F401
    Brand,
    Category,
    Product,
    ProductCategoryMap,
    ProductImage,
    ProductOption,
    ProductOptionValue,
    SKU,
    SKUOptionValueMap,
)
from app.models.promotion import Coupon, CouponIssue, CouponUsage, Promotion, PromotionCondition, PromotionTarget  # noqa: F401
from app.models.review import (  # noqa: F401
    ProductReviewSummary,
    Review,
    ReviewComment,
    ReviewImage,
    ReviewLike,
    ReviewRating,
    ReviewReport,
)
from app.models.search import SearchAutocomplete, SearchKeyword, SearchProductIndex, SearchSynonym  # noqa: F401
from app.models.shipment import (  # noqa: F401
    Shipment,
    ShipmentItem,
    ShipmentPackage,
    ShipmentStatusHistory,
    ShipmentTracking,
    Warehouse,
)

# 개별 모델 재임포트 (실제 사용을 위해)
from app.models.inventory import Inventory, InventoryReservation, InventoryTransaction
from app.models.order import OrderHeader, OrderStatusHistory
from app.models.payment import Payment, PaymentTransaction
from app.models.shipment import Shipment, ShipmentItem, ShipmentStatusHistory, Warehouse
from app.models.user import UserAccount

logger = logging.getLogger(__name__)


# ============================================================
# Phase 1: 공통 상태 변경 유틸리티
# ============================================================


def _update_order_status(
    db: SessionLocal,
    order_id: int,
    new_status: str,
    changed_by: int | None = None,
    change_reason: str | None = None,
) -> OrderHeader:
    """주문 상태를 변경하고 이력을 추가한다."""
    order = db.query(OrderHeader).filter(OrderHeader.id == order_id).first()
    if order is None:
        raise ValueError(f"Order {order_id} not found")

    if not OrderStatus.is_valid_transition(order.order_status, new_status):
        logger.warning(
            "Invalid status transition: %s -> %s for order %s",
            order.order_status,
            new_status,
            order_id,
        )
        return order

    old_status = order.order_status
    order.order_status = new_status
    order.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)

    history = OrderStatusHistory(
        order_id=order.id,
        order_status=new_status,
        changed_at=datetime.now(timezone.utc).replace(tzinfo=None),
        changed_by=changed_by,
        change_reason=change_reason,
    )
    db.add(history)
    db.add(order)
    db.commit()
    logger.info("Order %s status changed: %s -> %s", order_id, old_status, new_status)
    return order


def _rollback_inventory(
    db: SessionLocal,
    order_id: int,
) -> None:
    """주문의 재고 예약을 롤백한다. (CANCELLED 시)"""
    reservations = (
        db.query(InventoryReservation)
        .filter(InventoryReservation.order_id == order_id)
        .all()
    )
    for res in reservations:
        inventory = (
            db.query(Inventory)
            .filter(Inventory.sku_id == res.sku_id)
            .first()
        )
        if inventory:
            inventory.available_quantity += res.reserved_quantity
            inventory.reserved_quantity -= res.reserved_quantity

        res.reservation_status = "CANCELLED"
        db.add(res)

        txn = InventoryTransaction(
            sku_id=res.sku_id,
            transaction_type="ROLLBACK",
            quantity=res.reserved_quantity,
            reference_type="ORDER",
            reference_id=order_id,
        )
        db.add(txn)

    db.commit()
    logger.info("Inventory rollback complete for order %s", order_id)


# ============================================================
# Phase 2: handle_order_created 개선 (재고 부족 시 자동 취소)
# ============================================================


async def handle_order_created(message_value: dict[str, Any]) -> None:
    """OrderCreated 이벤트 처리 → DB 실제 재고 조회 후 InventoryUpdated 발행.

    설계 문서 §5 정상 흐름:
    1. Order 생성 (완료)
    2. Inventory reserve (Order 생성 시 이미 동기 처리됨)
    3. Payment 요청 (→ handle_inventory_updated)
    4. Payment 성공
    5. Shipment 생성

    재고 부족(오버부킹) 시:
    - Order를 CANCELLED로 변경
    - 재고 롤백
    - PaymentCompleted(FAIL) 발행 → 배송 생성 차단
    """
    event = OrderCreatedEvent(**message_value)
    logger.info("[Kafka] Received event: topic=%s key=%s", TOPIC_ORDER_CREATED, event.order_id)
    logger.info("[Kafka] Processing: handle_order_created - order_id=%s items_count=%d", event.order_id, len(event.items))

    event_id = f"{TOPIC_ORDER_CREATED}:{event.order_id}:{event.occurred_at}"
    if is_duplicate(event_id):
        logger.info("[Kafka] Skipped: order_id=%s reason=duplicate event", event.order_id)
        return

    db = SessionLocal()
    try:
        insufficient_items: list[str] = []

        # 각 SKU별로 DB에서 실제 재고 조회
        for item in event.items:
            inventory = (
                db.query(Inventory)
                .filter(Inventory.sku_id == item.sku_id)
                .first()
            )
            if inventory is None:
                logger.warning(
                    "[Kafka]   SKU %d: inventory not found (order_id=%s)",
                    item.sku_id, event.order_id,
                )
                insufficient_items.append(f"SKU(ID={item.sku_id}) 재고 정보 없음")
                continue

            available_qty = inventory.available_quantity
            logger.info(
                "[Kafka]   SKU %d: inventory_id=%s available_qty=%d requested=%s",
                item.sku_id, inventory.id, available_qty, item.quantity,
            )

            # 재고 부족 체크 (오버부킹 감지)
            if available_qty < item.quantity:
                logger.warning(
                    "[Kafka]   SKU %d: INSUFFICIENT stock (available=%d, requested=%d)",
                    item.sku_id, available_qty, item.quantity,
                )
                insufficient_items.append(
                    f"SKU(ID={item.sku_id}) 재고 부족 (available={available_qty}, requested={item.quantity})"
                )
                continue

            # 재고 정상 → InventoryUpdated 발행
            await publish_event(
                TOPIC_INVENTORY_UPDATED,
                str(item.sku_id),
                InventoryUpdatedEvent(
                    sku_id=item.sku_id,
                    available_quantity=available_qty,
                    reserved_quantity=item.quantity,
                    order_id=event.order_id,
                ),
            )
            logger.info(
                "[Kafka]   SKU %d: Published topic=%s available=%d reserved=%d",
                item.sku_id, TOPIC_INVENTORY_UPDATED, available_qty, item.quantity,
            )

        # 재고 부족 아이템이 있으면 Order 취소
        if insufficient_items:
            reason = "; ".join(insufficient_items)
            logger.warning(
                "[Kafka] Cancelled: order_id=%s reason=%s",
                event.order_id, reason,
            )
            _update_order_status(
                db,
                event.order_id,
                OrderStatus.CANCELLED,
                change_reason=f"재고 부족 자동 취소: {reason}",
            )
            _rollback_inventory(db, event.order_id)

            # PaymentCompleted FAIL 발행 → 배송 생성 차단
            await publish_event(
                TOPIC_PAYMENT_COMPLETED,
                str(event.order_id),
                PaymentCompletedEvent(
                    order_id=event.order_id,
                    payment_id=0,
                    status="FAIL",
                ),
            )
            logger.info(
                "[Kafka] Published: topic=%s key=%s status=FAIL (재고 부족 자동 취소)",
                TOPIC_PAYMENT_COMPLETED, event.order_id,
            )
            logger.info(
                "[Kafka] Completed: handle_order_created - CANCELLED (재고 부족)"
            )
        else:
            logger.info(
                "[Kafka] Completed: handle_order_created - OK (모든 SKU 재고 정상)"
            )
    except Exception as exc:
        logger.error(
            "[Kafka] Error: handle_order_created - order_id=%s error=%s",
            event.order_id, exc,
        )
    finally:
        db.close()


# ============================================================
# Phase 3: handle_inventory_updated (PENDING → PAYMENT_PENDING → PAID)
# ============================================================


async def handle_inventory_updated(message_value: dict[str, Any]) -> None:
    """InventoryUpdated 이벤트 처리 → 결제 생성 및 Mock PG 결제.

    1. Order 상태 PAYMENT_PENDING으로 변경
    2. Payment 레코드 생성 (첫 번째 SKU만)
    3. Mock PG 결제 처리 (1초 지연)
    4. Order 상태 PAID로 변경
    5. PaymentCompleted 이벤트 발행

    재고 부족(available_quantity <= 0) 시:
    - 결제 중단
    - Order CANCELLED + 재고 롤백
    - PaymentCompleted(FAIL) 발행
    """
    event = InventoryUpdatedEvent(**message_value)
    logger.info(
        "[Kafka] Received event: topic=%s key=%s",
        TOPIC_INVENTORY_UPDATED, event.sku_id,
    )
    logger.info(
        "[Kafka] Processing: handle_inventory_updated - order_id=%s sku_id=%s available=%s reserved=%s",
        event.order_id, event.sku_id, event.available_quantity, event.reserved_quantity,
    )

    event_id = f"{TOPIC_INVENTORY_UPDATED}:{event.order_id}:{event.sku_id}:{event.occurred_at}"
    if is_duplicate(event_id):
        logger.info(
            "[Kafka] Skipped: order_id=%s sku_id=%s reason=duplicate event",
            event.order_id, event.sku_id,
        )
        return

    db = SessionLocal()
    try:
        # === 재고 부족 체크 ===
        if event.available_quantity < event.reserved_quantity:
            logger.warning(
                "[Kafka]   INSUFFICIENT stock: available=%d < reserved=%d (order_id=%s)",
                event.available_quantity, event.reserved_quantity, event.order_id,
            )
            # Order CANCELLED + 재고 롤백
            _update_order_status(
                db,
                event.order_id,
                OrderStatus.CANCELLED,
                change_reason=f"재고 부족 자동 취소 (available={event.available_quantity}, reserved={event.reserved_quantity})",
            )
            _rollback_inventory(db, event.order_id)
            await publish_event(
                TOPIC_PAYMENT_COMPLETED,
                str(event.order_id),
                PaymentCompletedEvent(
                    order_id=event.order_id,
                    payment_id=0,
                    status="FAIL",
                ),
            )
            logger.info(
                "[Kafka] Cancelled: order_id=%s reason=재고 부족 (available=%d < reserved=%d)",
                event.order_id, event.available_quantity, event.reserved_quantity,
            )
            logger.info(
                "[Kafka] Completed: handle_inventory_updated - CANCELLED (재고 부족)"
            )
            return

        # === 1. Order 상태를 PAYMENT_PENDING으로 변경 (첫 번째 SKU 처리 시에만) ===
        order = db.query(OrderHeader).filter(OrderHeader.id == event.order_id).first()
        if order and order.order_status == OrderStatus.CREATED:
            _update_order_status(
                db,
                event.order_id,
                OrderStatus.PAYMENT_PENDING,
                change_reason="재고 확인 완료, 결제 진행",
            )
            logger.info(
                "[Kafka]   Order %s status: CREATED → PAYMENT_PENDING",
                event.order_id,
            )

        # === 2. Payment 레코드 생성 (첫 번째 SKU 처리 시에만) ===
        existing_payments = (
            db.query(Payment)
            .filter(Payment.order_id == event.order_id)
            .count()
        )
        if existing_payments == 0:
            payment = Payment(
                order_id=event.order_id,
                payment_status=PaymentStatus.READY,
                payment_amount=order.total_pay_amount if order else 0,
                paid_amount=0,
                currency_code="KRW",
            )
            db.add(payment)
            db.commit()
            db.refresh(payment)
            payment_id = payment.id
            logger.info(
                "[Kafka]   Payment created: id=%s order_id=%s amount=%s",
                payment_id, event.order_id, payment.payment_amount,
            )

            # === 3. Mock PG 결제 처리 (1초 지연으로 PG사 호출 시뮬레이션) ===
            logger.info("[Kafka]   Mock PG: processing payment for order %s...", event.order_id)
            await asyncio.sleep(1)

            # Mock: 항상 성공
            payment.payment_status = PaymentStatus.SUCCESS
            payment.paid_amount = order.total_pay_amount if order else 0
            payment.approved_at = datetime.now(timezone.utc).replace(tzinfo=None)
            db.add(payment)

            # PaymentTransaction 기록
            txn = PaymentTransaction(
                payment_id=payment.id,
                transaction_type="PAYMENT",
                transaction_status="SUCCESS",
                transaction_amount=payment.payment_amount,
                pg_provider="MOCK_PG",
                pg_transaction_id=f"MOCK-TXN-{event.order_id}-{datetime.utcnow().timestamp()}",
                pg_response_raw={},
                responded_at=datetime.now(timezone.utc).replace(tzinfo=None),
            )
            db.add(txn)
            db.commit()
            logger.info("[Kafka]   Mock PG: payment SUCCESS for order %s", event.order_id)

            # === 4. Order 상태 PAID로 변경 ===
            _update_order_status(
                db,
                event.order_id,
                OrderStatus.PAID,
                change_reason=f"결제 성공 (payment_id={payment.id})",
            )
            logger.info(
                "[Kafka]   Order %s status: PAYMENT_PENDING → PAID",
                event.order_id,
            )

            # === 5. PaymentCompleted 이벤트 발행 ===
            await publish_event(
                TOPIC_PAYMENT_COMPLETED,
                str(event.order_id),
                PaymentCompletedEvent(
                    order_id=event.order_id,
                    payment_id=payment.id,
                    status="SUCCESS",
                ),
            )
            logger.info(
                "[Kafka] Published: topic=%s key=%s status=SUCCESS",
                TOPIC_PAYMENT_COMPLETED, event.order_id,
            )
            logger.info(
                "[Kafka] Completed: handle_inventory_updated - PAID (결제 성공)"
            )
        else:
            logger.info(
                "[Kafka]   Payment already exists for order %s, skipping",
                event.order_id,
            )
            logger.info(
                "[Kafka] Completed: handle_inventory_updated - SKIPPED (이미 결제 있음)"
            )
    except Exception as exc:
        logger.error(
            "[Kafka] Error: handle_inventory_updated - order_id=%s error=%s",
            event.order_id, exc,
        )
        db.rollback()
        # 실패 시 Order CANCELLED + 재고 롤백
        _update_order_status(
            db,
            event.order_id,
            OrderStatus.CANCELLED,
            change_reason=f"결제 실패: {exc}",
        )
        _rollback_inventory(db, event.order_id)
        # PaymentCompleted FAIL 발행
        await publish_event(
            TOPIC_PAYMENT_COMPLETED,
            str(event.order_id),
            PaymentCompletedEvent(
                order_id=event.order_id,
                payment_id=0,
                status="FAIL",
            ),
        )
        logger.info(
            "[Kafka] Cancelled: order_id=%s reason=결제 처리 예외: %s",
            event.order_id, exc,
        )
        logger.info(
            "[Kafka] Completed: handle_inventory_updated - CANCELLED (예외)"
        )
    finally:
        db.close()


# ============================================================
# Phase 4: handle_payment_completed 구현 (PAID → SHIPPING → SHIPPED)
# ============================================================


async def handle_payment_completed(message_value: dict[str, Any]) -> None:
    """PaymentCompleted 이벤트 처리 → 배송 생성.

    1. Order 상태 SHIPPING으로 변경
    2. Shipment 레코드 생성
    3. ShipmentItem 생성 (OrderItem 기준)
    4. Order 상태 SHIPPED로 변경
    5. ShipmentCreated 이벤트 발행
    """
    event = PaymentCompletedEvent(**message_value)
    logger.info(
        "[Kafka] Received event: topic=%s key=%s",
        TOPIC_PAYMENT_COMPLETED, event.order_id,
    )
    logger.info(
        "[Kafka] Processing: handle_payment_completed - order_id=%s status=%s",
        event.order_id, event.status,
    )

    event_id = f"{TOPIC_PAYMENT_COMPLETED}:{event.order_id}:{event.occurred_at}"
    if is_duplicate(event_id):
        logger.info(
            "[Kafka] Skipped: order_id=%s reason=duplicate event",
            event.order_id,
        )
        return

    if event.status != "SUCCESS":
        logger.warning(
            "[Kafka]   Payment FAIL for order %s, skipping shipment",
            event.order_id,
        )
        logger.info(
            "[Kafka] Completed: handle_payment_completed - SKIPPED (결제 실패)"
        )
        return

    db = SessionLocal()
    try:
        # === 1. Order 상태를 SHIPPING으로 변경 ===
        _update_order_status(
            db,
            event.order_id,
            OrderStatus.SHIPPING,
            change_reason="결제 완료, 배송 준비",
        )
        logger.info(
            "[Kafka]   Order %s status: PAID → SHIPPING",
            event.order_id,
        )

        # === 2. Shipment 레코드 생성 ===
        order = db.query(OrderHeader).filter(OrderHeader.id == event.order_id).first()
        if order is None:
            logger.error("[Kafka]   Order %s not found", event.order_id)
            return

        # 첫 번째 Warehouse 조회 (또는 기본값)
        warehouse = db.query(Warehouse).first()

        shipment = Shipment(
            order_id=event.order_id,
            shipment_status=ShipmentStatus.READY,
            total_shipping_amount=order.total_shipping_amount,
            warehouse_id=warehouse.id if warehouse else None,
        )
        db.add(shipment)
        db.flush()
        logger.info(
            "[Kafka]   Shipment created: id=%s order_id=%s warehouse_id=%s",
            shipment.id, event.order_id, shipment.warehouse_id,
        )

        # === 3. ShipmentItem 생성 (OrderItem 기준) ===
        for order_item in order.items:
            shipment_item = ShipmentItem(
                shipment_id=shipment.id,
                order_item_id=order_item.id,
                sku_id=order_item.sku_id,
                shipped_quantity=order_item.quantity,
                shipment_item_status="PENDING",
            )
            db.add(shipment_item)
        logger.info(
            "[Kafka]   ShipmentItems created: count=%d for shipment_id=%s",
            len(order.items), shipment.id,
        )

        # === 4. ShipmentStatusHistory 기록 ===
        status_history = ShipmentStatusHistory(
            shipment_id=shipment.id,
            shipment_status=ShipmentStatus.READY,
        )
        db.add(status_history)
        db.commit()
        db.refresh(shipment)

        # === 5. Order 상태 SHIPPED로 변경 ===
        _update_order_status(
            db,
            event.order_id,
            OrderStatus.SHIPPED,
            change_reason=f"배송 생성 (shipment_id={shipment.id})",
        )
        logger.info(
            "[Kafka]   Order %s status: SHIPPING → SHIPPED",
            event.order_id,
        )

        # === 6. ShipmentCreated 이벤트 발행 ===
        await publish_event(
            TOPIC_SHIPMENT_CREATED,
            str(event.order_id),
            ShipmentCreatedEvent(
                shipment_id=shipment.id,
                order_id=event.order_id,
                warehouse_id=shipment.warehouse_id or 0,
            ),
        )
        logger.info(
            "[Kafka] Published: topic=%s key=%s shipment_id=%s",
            TOPIC_SHIPMENT_CREATED, event.order_id, shipment.id,
        )
        logger.info(
            "[Kafka] Completed: handle_payment_completed - SHIPPED (배송 생성 완료)"
        )
    except Exception as exc:
        logger.error(
            "[Kafka] Error: handle_payment_completed - order_id=%s error=%s",
            event.order_id, exc,
        )
        db.rollback()
    finally:
        db.close()


# ============================================================
# Phase 5: handle_shipment_created 구현
# ============================================================


async def handle_shipment_created(message_value: dict[str, Any]) -> None:
    """ShipmentCreated 이벤트 처리 (알림/로깅)."""
    event = ShipmentCreatedEvent(**message_value)
    logger.info(
        "[Kafka] Received event: topic=%s key=%s",
        TOPIC_SHIPMENT_CREATED, event.order_id,
    )
    logger.info(
        "[Kafka] Processing: handle_shipment_created - shipment_id=%s order_id=%s warehouse_id=%s",
        event.shipment_id, event.order_id, event.warehouse_id,
    )

    event_id = f"{TOPIC_SHIPMENT_CREATED}:{event.shipment_id}:{event.occurred_at}"
    if is_duplicate(event_id):
        logger.info(
            "[Kafka] Skipped: shipment_id=%s reason=duplicate event",
            event.shipment_id,
        )
        return

    # TODO: 알림 서비스 호출
    # await notification_service.send_shipment_notification(
    #     order_id=event.order_id,
    #     shipment_id=event.shipment_id,
    # )
    logger.info(
        "[Kafka] Completed: handle_shipment_created - OK (배송 생성 알림)"
    )


# ============================================================
# ProductIndexUpdated 핸들러 (기존 유지)
# ============================================================


async def handle_product_index_updated(message_value: dict[str, Any]) -> None:
    """ProductIndexUpdated 이벤트 처리 → Elasticsearch 인덱싱.

    설계 문서 §2.10 Search 특징:
    - DB → Kafka → Elasticsearch
    - Denormalization

    Product 생성/수정 시 발행된 이벤트를 수신하여
    SearchProductIndex를 업데이트하고 Elasticsearch에 동기화한다.
    """
    event = ProductIndexUpdatedEvent(**message_value)
    logger.info(
        "Handling ProductIndexUpdated: product_id=%s",
        event.product_id,
    )

    event_id = f"{TOPIC_PRODUCT_INDEX_UPDATED}:{event.product_id}:{event.occurred_at}"
    if is_duplicate(event_id):
        return

    # Phase 1: SearchProductIndex DB 업데이트 (partial update)
    from app.models.search import SearchProductIndex

    db = SessionLocal()
    try:
        index = db.query(SearchProductIndex).filter(
            SearchProductIndex.product_id == event.product_id
        ).first()
        if index is None:
            index = SearchProductIndex(product_id=event.product_id)
            db.add(index)
        if event.product_name is not None:
            index.product_name = event.product_name
        if event.product_description is not None:
            index.product_description = event.product_description
        if event.category_ids is not None:
            index.category_ids = event.category_ids
        if event.brand_name is not None:
            index.brand_name = event.brand_name
        if event.price_amount is not None:
            index.price_amount = event.price_amount
        if event.is_active is not None:
            index.is_active = event.is_active
        db.commit()
    finally:
        db.close()

    # Phase 2: Elasticsearch 인덱싱 (DB 전체 레코드 기반)
    from app.services.elasticsearch import index_product

    await index_product(event.product_id)


# 토픽별 핸들러 매핑
HANDLERS: dict[str, Callable[[dict[str, Any]], Awaitable[None]]] = {
    TOPIC_ORDER_CREATED: handle_order_created,
    TOPIC_INVENTORY_UPDATED: handle_inventory_updated,
    TOPIC_PAYMENT_COMPLETED: handle_payment_completed,
    TOPIC_SHIPMENT_CREATED: handle_shipment_created,
    TOPIC_PRODUCT_INDEX_UPDATED: handle_product_index_updated,
}


async def consume_loop() -> None:
    """Kafka Consumer 메인 루프.

    lifespan에서 asyncio.create_task()로 실행된다.
    Kafka를 사용할 수 없는 환경(테스트, 개발)에서는 자동으로 비활성화된다.

    Kafka 브로커가 아직 준비되지 않은 경우(타이밍 이슈)를 대비해,
    연결 실패 시 백그라운드에서 주기적으로 재연결을 시도한다.
    """
    # Kafka bootstrap 서버가 설정되지 않은 경우 건너뛴다
    if not settings.KAFKA_BOOTSTRAP_SERVERS:
        logger.info("KAFKA_BOOTSTRAP_SERVERS not set, Kafka consumer disabled")
        return

    # 초기 재시도 설정 (빠른 재시도)
    initial_retries = 5
    initial_delay = 3  # 초

    # 연결 성공 후 메시지 소비 루프
    consumer: Optional[AIOKafkaConsumer] = None
    # finally 블록에서 정리할 consumer 객체 참조 유지 (CancelledError로 인한 orphan 방지)
    _consumers_to_cleanup: list[AIOKafkaConsumer] = []

    try:
        while True:
            # Consumer가 없거나 중단된 경우 재연결 시도
            if consumer is None:
                for attempt in range(1, initial_retries + 1):
                    consumer = AIOKafkaConsumer(
                        *HANDLERS.keys(),
                        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                        group_id=settings.KAFKA_CONSUMER_GROUP_ID,
                        auto_offset_reset=settings.KAFKA_AUTO_OFFSET_RESET,
                        enable_auto_commit=settings.KAFKA_ENABLE_AUTO_COMMIT,
                        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
                        key_deserializer=lambda k: k.decode("utf-8") if k else None,
                        request_timeout_ms=10000,
                        session_timeout_ms=15000,
                    )
                    try:
                        await consumer.start()
                        logger.info(
                            "Kafka consumer started: topics=%s group=%s",
                            list(HANDLERS.keys()),
                            settings.KAFKA_CONSUMER_GROUP_ID,
                        )
                        break  # 연결 성공 → 루프 탈출
                    except asyncio.CancelledError:
                        logger.info("Kafka consumer cancelled during start")
                        # consumer.start()가 취소됨 → consumer 객체 정리
                        if consumer is not None:
                            _consumers_to_cleanup.append(consumer)
                            try:
                                await asyncio.shield(consumer.stop())
                            except Exception:
                                pass
                        consumer = None
                        raise  # 상위 try/finally로 전파
                    except Exception as exc:
                        logger.warning(
                            "Kafka consumer start failed (attempt %d/%d): %s",
                            attempt,
                            initial_retries,
                            exc,
                        )
                        if consumer is not None:
                            _consumers_to_cleanup.append(consumer)
                            await consumer.stop()
                        consumer = None
                        if attempt < initial_retries:
                            await asyncio.sleep(initial_delay)
                        else:
                            logger.error(
                                "Kafka consumer could not start after %d attempts, "
                                "will retry in 30 seconds",
                                initial_retries,
                            )
                            await asyncio.sleep(30)
                            # while 루프로 돌아가 재시도
                            continue

            # consumer가 None이면 재시도 실패 → while 처음으로
            if consumer is None:
                continue

            # 메시지 소비 루프
            try:
                async for msg in consumer:
                    handler = HANDLERS.get(msg.topic)
                    if handler is None:
                        logger.warning("No handler for topic: %s", msg.topic)
                        continue

                    try:
                        await handler(msg.value)
                        # 수동 commit (enable_auto_commit=False)
                        await consumer.commit()
                    except Exception as exc:
                        logger.error(
                            "Handler failed: topic=%s key=%s error=%s",
                            msg.topic,
                            msg.key,
                            exc,
                        )
                        # DLQ 발행
                        await publish_to_dlq(
                            topic=msg.topic,
                            message=msg.value,
                            error=str(exc),
                        )
            except asyncio.CancelledError:
                logger.info("Kafka consumer cancelled during message consumption")
                # CancelledError 발생 시 consumer 정리 후 break
                if consumer is not None:
                    _consumers_to_cleanup.append(consumer)
                    try:
                        await asyncio.shield(consumer.stop())
                    except Exception:
                        pass
                    consumer = None
                break
            except Exception as exc:
                logger.error(
                    "Kafka consumer error: %s, will reconnect in 10 seconds",
                    exc,
                )
                if consumer is not None:
                    _consumers_to_cleanup.append(consumer)
                    await consumer.stop()
                    consumer = None
                await asyncio.sleep(10)
                # while 루프로 돌아가 재연결 시도
                continue
    finally:
        # 최종 정리 (CancelledError 포함 모든 종료 경로에서 실행 보장)
        # 현재 consumer 변수 정리
        if consumer is not None:
            _consumers_to_cleanup.append(consumer)
            try:
                await asyncio.shield(consumer.stop())
            except Exception:
                pass
        # _consumers_to_cleanup에 저장된 모든 orphaned consumer 객체 정리
        # (consumer.stop()이 완료되기 전에 consumer=None으로 설정되어
        #  GC에 의해 Unclosed 경고가 발생하는 것을 방지)
        for c in _consumers_to_cleanup:
            if c is not consumer:
                try:
                    await asyncio.shield(c.stop())
                except Exception:
                    pass
        logger.info("Kafka consumer stopped")


__all__ = [
    "consume_loop",
    "HANDLERS",
]
