from __future__ import annotations
import logging
from typing import Optional

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.enums import OrderStatus, ShipmentStatus

logger = logging.getLogger(__name__)
from app.dependencies import get_db
from app.models.inventory import WarehouseStock
from app.models.order import OrderHeader, OrderStatusHistory
from app.models.product import SKU
from app.models.shipment import Shipment, ShipmentItem, ShipmentTracking, ShipmentStatusHistory, Warehouse, ShipmentPackage
from app.schemas import APIResponse
from app.schemas.inventory import WarehouseStockCreate, WarehouseStockRead
from app.schemas.shipment import (
    ShipmentCreate,
    ShipmentRead,
    ShipmentUpdate,
    ShipmentItemCreate,
    ShipmentItemRead,
    ShipmentItemUpdate,
    ShipmentTrackingCreate,
    ShipmentTrackingRead,
    ShipmentTrackingUpdate,
    ShipmentStatusHistoryCreate,
    ShipmentStatusHistoryRead,
    ShipmentStatusHistoryUpdate,
    WarehouseCreate,
    WarehouseRead,
    WarehouseUpdate,
    ShipmentPackageCreate,
    ShipmentPackageRead,
    ShipmentPackageUpdate,
)

router = APIRouter(tags=["Shipments (배송)"])


def _shipment_query():
    """배송 기본 쿼리 (관계 로딩 포함)."""
    return (
        select(Shipment)
        .options(
            selectinload(Shipment.order),
            selectinload(Shipment.warehouse),
            selectinload(Shipment.items),
            selectinload(Shipment.tracking),
            selectinload(Shipment.status_history),
            selectinload(Shipment.packages),
        )
        .where(Shipment.deleted_at.is_(None))
    )


def _get_shipment_or_404(db: Session, shipment_id: int) -> Shipment:
    """배송을 조회하거나 404 예외를 발생시킨다."""
    statement = _shipment_query().where(Shipment.id == shipment_id)
    shipment = db.execute(statement).scalar_one_or_none()

    if shipment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="배송을 찾을 수 없습니다.",
        )

    return shipment


@router.get("/shipments", response_model=APIResponse[list[ShipmentRead]], summary="배송 목록 조회")
def list_shipments(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    shipment_status: Optional[str] = Query(default=None, max_length=30),
    order_id: Optional[int] = Query(default=None),
    db: Session = Depends(get_db),
) -> APIResponse[list[ShipmentRead]]:
    """배송 목록을 상태, 주문 ID, 페이징 조건으로 조회한다."""
    statement = _shipment_query().offset(skip).limit(limit)

    if shipment_status is not None:
        statement = statement.where(Shipment.shipment_status == shipment_status)
    if order_id is not None:
        statement = statement.where(Shipment.order_id == order_id)

    shipments = db.execute(statement).scalars().unique().all()
    return APIResponse(data=shipments, message="배송 목록을 조회했습니다.")


@router.get("/shipments/{shipment_id}", response_model=APIResponse[ShipmentRead], summary="배송 상세 조회")
def get_shipment(shipment_id: int, db: Session = Depends(get_db)) -> APIResponse[ShipmentRead]:
    """배송 상세 정보를 조회한다."""
    shipment = _get_shipment_or_404(db, shipment_id)
    return APIResponse(data=shipment, message="배송 상세 정보를 조회했습니다.")


@router.post(
    "/shipments",
    response_model=APIResponse[ShipmentRead],
    status_code=status.HTTP_201_CREATED,
    summary="배송 생성",
)
def create_shipment(payload: ShipmentCreate, db: Session = Depends(get_db)) -> APIResponse[ShipmentRead]:
    """배송 정보를 생성한다."""
    shipment = Shipment(
        order_id=payload.order_id,
        shipment_status=payload.shipment_status,
        shipment_type=payload.shipment_type,
        total_shipping_amount=payload.total_shipping_amount,
        shipped_at=payload.shipped_at,
        delivered_at=payload.delivered_at,
        warehouse_id=payload.warehouse_id,
        created_by=payload.created_by,
    )
    db.add(shipment)
    db.commit()
    db.refresh(shipment)

    created_shipment = _get_shipment_or_404(db, shipment.id)
    return APIResponse(data=created_shipment, message="배송을 생성했습니다.")


@router.put("/shipments/{shipment_id}", response_model=APIResponse[ShipmentRead], summary="배송 수정")
def update_shipment(
    shipment_id: int,
    payload: ShipmentUpdate,
    db: Session = Depends(get_db),
) -> APIResponse[ShipmentRead]:
    """배송 정보를 수정한다."""
    shipment = _get_shipment_or_404(db, shipment_id)
    update_data = payload.model_dump(exclude_unset=True)

    for field_name, field_value in update_data.items():
        setattr(shipment, field_name, field_value)

    if update_data:
        shipment.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)

    db.add(shipment)
    db.commit()
    db.refresh(shipment)

    updated_shipment = _get_shipment_or_404(db, shipment_id)
    return APIResponse(data=updated_shipment, message="배송을 수정했습니다.")


@router.delete(
    "/shipments/{shipment_id}",
    response_model=APIResponse[dict[str, int]],
    summary="배송 삭제",
)
def delete_shipment(shipment_id: int, db: Session = Depends(get_db)) -> APIResponse[dict[str, int]]:
    """배송을 소프트 삭제한다."""
    shipment = _get_shipment_or_404(db, shipment_id)
    shipment.deleted_at = datetime.now(timezone.utc).replace(tzinfo=None)
    db.add(shipment)
    db.commit()
    db.refresh(shipment)

    return APIResponse(data={"shipment_id": shipment_id}, message="배송을 삭제했습니다.")


# -------------------------------------------------------------------
# ShipmentItem 라우터 (하위 경로)
# -------------------------------------------------------------------
item_router = APIRouter(prefix="/shipments/{shipment_id}/items", tags=["Shipment Items (배송 상품)"])


def _get_shipment_item_or_404(db: Session, shipment_item_id: int) -> ShipmentItem:
    """배송 상품을 조회하거나 404 예외를 발생시킨다."""
    statement = (
        select(ShipmentItem)
        .options(
            selectinload(ShipmentItem.shipment),
            selectinload(ShipmentItem.order_item),
            selectinload(ShipmentItem.sku),
        )
        .where(ShipmentItem.id == shipment_item_id, ShipmentItem.deleted_at.is_(None))
    )
    item = db.execute(statement).scalar_one_or_none()
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="배송 상품을 찾을 수 없습니다.",
        )
    return item


@item_router.get("", response_model=APIResponse[list[ShipmentItemRead]], summary="배송 상품 목록 조회")
def list_shipment_items(
    shipment_id: int,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> APIResponse[list[ShipmentItemRead]]:
    """특정 배송의 상품 목록을 조회한다."""
    statement = (
        select(ShipmentItem)
        .options(
            selectinload(ShipmentItem.shipment),
            selectinload(ShipmentItem.order_item),
            selectinload(ShipmentItem.sku),
        )
        .where(ShipmentItem.shipment_id == shipment_id, ShipmentItem.deleted_at.is_(None))
        .offset(skip)
        .limit(limit)
    )
    items = db.execute(statement).scalars().unique().all()
    return APIResponse(data=items, message="배송 상품 목록을 조회했습니다.")


@item_router.get("/{item_id}", response_model=APIResponse[ShipmentItemRead], summary="배송 상품 상세 조회")
def get_shipment_item(
    shipment_id: int,
    item_id: int,
    db: Session = Depends(get_db),
) -> APIResponse[ShipmentItemRead]:
    """배송 상품 상세 정보를 조회한다."""
    item = _get_shipment_item_or_404(db, item_id)
    if item.shipment_id != shipment_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="해당 배송에 속한 상품이 아닙니다.",
        )
    return APIResponse(data=item, message="배송 상품 상세 정보를 조회했습니다.")


@item_router.post(
    "",
    response_model=APIResponse[ShipmentItemRead],
    status_code=status.HTTP_201_CREATED,
    summary="배송 상품 생성",
)
def create_shipment_item(
    shipment_id: int,
    payload: ShipmentItemCreate,
    db: Session = Depends(get_db),
) -> APIResponse[ShipmentItemRead]:
    """배송 상품을 생성한다."""
    # shipment 존재 확인
    shipment = _get_shipment_or_404(db, shipment_id)
    item = ShipmentItem(
        shipment_id=shipment_id,
        order_item_id=payload.order_item_id,
        sku_id=payload.sku_id,
        shipped_quantity=payload.shipped_quantity,
        delivered_quantity=payload.delivered_quantity,
        shipment_item_status=payload.shipment_item_status,
        created_by=payload.created_by,
    )
    db.add(item)
    db.commit()
    db.refresh(item)

    created_item = _get_shipment_item_or_404(db, item.id)
    return APIResponse(data=created_item, message="배송 상품을 생성했습니다.")


@item_router.put("/{item_id}", response_model=APIResponse[ShipmentItemRead], summary="배송 상품 수정")
def update_shipment_item(
    shipment_id: int,
    item_id: int,
    payload: ShipmentItemUpdate,
    db: Session = Depends(get_db),
) -> APIResponse[ShipmentItemRead]:
    """배송 상품 정보를 수정한다."""
    item = _get_shipment_item_or_404(db, item_id)
    if item.shipment_id != shipment_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="해당 배송에 속한 상품이 아닙니다.",
        )
    update_data = payload.model_dump(exclude_unset=True)
    for field_name, field_value in update_data.items():
        setattr(item, field_name, field_value)

    if update_data:
        item.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)

    db.add(item)
    db.commit()
    db.refresh(item)

    updated_item = _get_shipment_item_or_404(db, item_id)
    return APIResponse(data=updated_item, message="배송 상품을 수정했습니다.")


@item_router.delete(
    "/{item_id}",
    response_model=APIResponse[dict[str, int]],
    summary="배송 상품 삭제",
)
def delete_shipment_item(
    shipment_id: int,
    item_id: int,
    db: Session = Depends(get_db),
) -> APIResponse[dict[str, int]]:
    """배송 상품을 소프트 삭제한다."""
    item = _get_shipment_item_or_404(db, item_id)
    if item.shipment_id != shipment_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="해당 배송에 속한 상품이 아닙니다.",
        )
    item.deleted_at = datetime.now(timezone.utc).replace(tzinfo=None)
    db.add(item)
    db.commit()
    db.refresh(item)

    return APIResponse(data={"item_id": item_id}, message="배송 상품을 삭제했습니다.")


# -------------------------------------------------------------------
# Warehouse 라우터 (별도 경로)
# -------------------------------------------------------------------
warehouse_router = APIRouter(prefix="/warehouses", tags=["Warehouses (창고)"])


def _warehouse_query():
    return select(Warehouse).where(Warehouse.id.is_not(None))


def _get_warehouse_or_404(db: Session, warehouse_id: int) -> Warehouse:
    statement = _warehouse_query().where(Warehouse.id == warehouse_id)
    warehouse = db.execute(statement).scalar_one_or_none()
    if warehouse is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="창고를 찾을 수 없습니다.",
        )
    return warehouse


@warehouse_router.get("", response_model=APIResponse[list[WarehouseRead]], summary="창고 목록 조회")
def list_warehouses(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> APIResponse[list[WarehouseRead]]:
    """창고 목록을 조회한다."""
    statement = _warehouse_query().offset(skip).limit(limit)
    warehouses = db.execute(statement).scalars().unique().all()
    return APIResponse(data=warehouses, message="창고 목록을 조회했습니다.")


@warehouse_router.get("/{warehouse_id}", response_model=APIResponse[WarehouseRead], summary="창고 상세 조회")
def get_warehouse(warehouse_id: int, db: Session = Depends(get_db)) -> APIResponse[WarehouseRead]:
    """창고 상세 정보를 조회한다."""
    warehouse = _get_warehouse_or_404(db, warehouse_id)
    return APIResponse(data=warehouse, message="창고 상세 정보를 조회했습니다.")


@warehouse_router.post(
    "",
    response_model=APIResponse[WarehouseRead],
    status_code=status.HTTP_201_CREATED,
    summary="창고 생성",
)
def create_warehouse(payload: WarehouseCreate, db: Session = Depends(get_db)) -> APIResponse[WarehouseRead]:
    """창고 정보를 생성한다."""
    warehouse = Warehouse(
        warehouse_name=payload.warehouse_name,
        postal_code=payload.postal_code,
        address_line1=payload.address_line1,
        address_line2=payload.address_line2,
    )
    db.add(warehouse)
    db.commit()
    db.refresh(warehouse)

    created_warehouse = _get_warehouse_or_404(db, warehouse.id)
    return APIResponse(data=created_warehouse, message="창고를 생성했습니다.")


@warehouse_router.put("/{warehouse_id}", response_model=APIResponse[WarehouseRead], summary="창고 수정")
def update_warehouse(
    warehouse_id: int,
    payload: WarehouseUpdate,
    db: Session = Depends(get_db),
) -> APIResponse[WarehouseRead]:
    """창고 정보를 수정한다."""
    warehouse = _get_warehouse_or_404(db, warehouse_id)
    update_data = payload.model_dump(exclude_unset=True)
    for field_name, field_value in update_data.items():
        setattr(warehouse, field_name, field_value)

    db.add(warehouse)
    db.commit()
    db.refresh(warehouse)

    updated_warehouse = _get_warehouse_or_404(db, warehouse_id)
    return APIResponse(data=updated_warehouse, message="창고를 수정했습니다.")


@warehouse_router.delete(
    "/{warehouse_id}",
    response_model=APIResponse[dict[str, int]],
    summary="창고 삭제",
)
def delete_warehouse(warehouse_id: int, db: Session = Depends(get_db)) -> APIResponse[dict[str, int]]:
    """창고를 삭제한다."""
    warehouse = _get_warehouse_or_404(db, warehouse_id)
    db.delete(warehouse)
    db.commit()
    return APIResponse(data={"warehouse_id": warehouse_id}, message="창고를 삭제했습니다.")


# -------------------------------------------------------------------
# WarehouseStock 라우터 (창고 하위 재고)
# -------------------------------------------------------------------
warehouse_stock_router = APIRouter(
    prefix="/{warehouse_id}/stocks",
    tags=["Warehouse Stocks (창고 재고)"],
)


def _get_warehouse_stock_or_404(
    db: Session,
    warehouse_id: int,
    stock_id: int,
) -> WarehouseStock:
    """창고 재고를 조회하고 없으면 404를 반환한다."""
    statement = (
        select(WarehouseStock)
        .options(selectinload(WarehouseStock.inventory))
        .where(
            WarehouseStock.id == stock_id,
            WarehouseStock.warehouse_id == warehouse_id,
        )
    )
    stock = db.execute(statement).scalar_one_or_none()
    if stock is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="창고 재고를 찾을 수 없습니다.",
        )
    return stock


@warehouse_stock_router.get(
    "",
    response_model=APIResponse[list[WarehouseStockRead]],
    summary="창고 재고 목록 조회",
)
def list_warehouse_stocks(
    warehouse_id: int,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    sku_id: Optional[int] = Query(default=None, gt=0),
    db: Session = Depends(get_db),
) -> APIResponse[list[WarehouseStockRead]]:
    """특정 창고의 재고 목록을 조회한다."""
    _get_warehouse_or_404(db, warehouse_id)
    statement = (
        select(WarehouseStock)
        .options(selectinload(WarehouseStock.inventory))
        .where(WarehouseStock.warehouse_id == warehouse_id)
    )
    if sku_id is not None:
        statement = statement.where(WarehouseStock.sku_id == sku_id)
    statement = statement.offset(skip).limit(limit)
    stocks = db.execute(statement).scalars().unique().all()
    return APIResponse(data=stocks, message="창고 재고 목록을 조회했습니다.")


@warehouse_stock_router.get(
    "/{stock_id}",
    response_model=APIResponse[WarehouseStockRead],
    summary="창고 재고 상세 조회",
)
def get_warehouse_stock(
    warehouse_id: int,
    stock_id: int,
    db: Session = Depends(get_db),
) -> APIResponse[WarehouseStockRead]:
    """창고 재고 상세 정보를 조회한다."""
    stock = _get_warehouse_stock_or_404(db, warehouse_id, stock_id)
    return APIResponse(data=stock, message="창고 재고 상세 정보를 조회했습니다.")


@warehouse_stock_router.post(
    "",
    response_model=APIResponse[WarehouseStockRead],
    status_code=status.HTTP_201_CREATED,
    summary="창고 재고 생성",
)
def create_warehouse_stock(
    warehouse_id: int,
    payload: WarehouseStockCreate,
    db: Session = Depends(get_db),
) -> APIResponse[WarehouseStockRead]:
    """창고 재고를 생성한다."""
    _get_warehouse_or_404(db, warehouse_id)

    sku = db.execute(select(SKU).where(SKU.id == payload.sku_id)).scalar_one_or_none()
    if sku is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="해당 SKU를 찾을 수 없습니다.",
        )

    stock = WarehouseStock(
        warehouse_id=warehouse_id,
        sku_id=payload.sku_id,
        stock_quantity=payload.stock_quantity,
    )
    db.add(stock)
    db.commit()
    db.refresh(stock)

    created_stock = _get_warehouse_stock_or_404(db, warehouse_id, stock.id)
    return APIResponse(data=created_stock, message="창고 재고를 생성했습니다.")


@warehouse_stock_router.put(
    "/{stock_id}",
    response_model=APIResponse[WarehouseStockRead],
    summary="창고 재고 수정",
)
def update_warehouse_stock(
    warehouse_id: int,
    stock_id: int,
    payload: WarehouseStockCreate,
    db: Session = Depends(get_db),
) -> APIResponse[WarehouseStockRead]:
    """창고 재고 수량을 수정한다."""
    stock = _get_warehouse_stock_or_404(db, warehouse_id, stock_id)
    stock.sku_id = payload.sku_id
    stock.stock_quantity = payload.stock_quantity
    db.commit()
    db.refresh(stock)
    return APIResponse(data=stock, message="창고 재고를 수정했습니다.")


@warehouse_stock_router.delete(
    "/{stock_id}",
    response_model=APIResponse[dict[str, int]],
    summary="창고 재고 삭제",
)
def delete_warehouse_stock(
    warehouse_id: int,
    stock_id: int,
    db: Session = Depends(get_db),
) -> APIResponse[dict[str, int]]:
    """창고 재고를 삭제한다."""
    stock = _get_warehouse_stock_or_404(db, warehouse_id, stock_id)
    db.delete(stock)
    db.commit()
    return APIResponse(
        data={"stock_id": stock_id},
        message="창고 재고를 삭제했습니다.",
    )


# -------------------------------------------------------------------
# Phase 6: 배송 완료 API (SHIPPED → DELIVERED)
# -------------------------------------------------------------------


@router.put(
    "/shipments/{shipment_id}/deliver",
    response_model=APIResponse[ShipmentRead],
    summary="배송 완료 처리",
)
def deliver_shipment(
    shipment_id: int,
    db: Session = Depends(get_db),
) -> APIResponse[ShipmentRead]:
    """배송 완료 처리 → Order 상태 DELIVERED로 변경."""
    shipment = db.query(Shipment).filter(Shipment.id == shipment_id, Shipment.deleted_at.is_(None)).first()
    if shipment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="배송을 찾을 수 없습니다.",
        )

    # 배송 상태 변경
    shipment.shipment_status = ShipmentStatus.DELIVERED
    shipment.delivered_at = datetime.now(timezone.utc).replace(tzinfo=None)
    shipment.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
    db.add(shipment)

    # ShipmentStatusHistory 기록
    status_history = ShipmentStatusHistory(
        shipment_id=shipment.id,
        shipment_status=ShipmentStatus.DELIVERED,
        changed_at=datetime.now(timezone.utc).replace(tzinfo=None),
    )
    db.add(status_history)

    # Order 상태 DELIVERED로 변경
    order = db.query(OrderHeader).filter(OrderHeader.id == shipment.order_id).first()
    if order:
        old_status = order.order_status
        order.order_status = OrderStatus.DELIVERED
        order.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
        db.add(order)

        order_history = OrderStatusHistory(
            order_id=order.id,
            order_status=OrderStatus.DELIVERED,
            changed_at=datetime.now(timezone.utc).replace(tzinfo=None),
            change_reason=f"배송 완료 (shipment_id={shipment.id})",
        )
        db.add(order_history)
        logger.info("Order %s status changed: %s -> %s", order.id, old_status, OrderStatus.DELIVERED)

    db.commit()
    db.refresh(shipment)

    return APIResponse(data=shipment, message="배송 완료 처리했습니다.")


# -------------------------------------------------------------------
# 라우터 등록
# -------------------------------------------------------------------
router.include_router(item_router)
warehouse_router.include_router(warehouse_stock_router)
router.include_router(warehouse_router)

__all__ = ["router"]