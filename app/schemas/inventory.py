from __future__ import annotations
from typing import Optional

from datetime import datetime

from pydantic import Field

from app.schemas import ORMBaseSchema, TimestampSchema


class InventoryBase(ORMBaseSchema):
    """재고 공통 입력 스키마."""

    sku_id: int = Field(..., gt=0)
    total_quantity: int = Field(..., ge=0)
    available_quantity: int = Field(..., ge=0)
    reserved_quantity: int = Field(..., ge=0)
    safety_stock_quantity: int = Field(default=0, ge=0)


class InventoryCreate(InventoryBase):
    """재고 생성 요청 스키마."""

    created_by: Optional[int] = None


class InventoryUpdate(ORMBaseSchema):
    """재고 수정 요청 스키마."""

    total_quantity: Optional[int] = Field(default=None, ge=0)
    available_quantity: Optional[int] = Field(default=None, ge=0)
    reserved_quantity: Optional[int] = Field(default=None, ge=0)
    safety_stock_quantity: Optional[int] = Field(default=None, ge=0)
    updated_by: Optional[int] = None


class InventoryRead(InventoryBase, TimestampSchema):
    """재고 상세 응답 스키마."""

    id: int
    created_by: Optional[int] = None
    updated_at: Optional[datetime] = None
    # 관계 필드 (선택적)
    sku: "Optional[SKURead]" = None
    reservations: list["InventoryReservationRead"] = Field(default_factory=list)
    transactions: list["InventoryTransactionRead"] = Field(default_factory=list)


class InventoryReservationBase(ORMBaseSchema):
    """재고 예약 공통 입력 스키마."""

    sku_id: int = Field(..., gt=0)
    order_id: int = Field(..., gt=0)
    reserved_quantity: int = Field(..., gt=0)
    reservation_status: str = Field(..., max_length=30)
    expired_at: Optional[datetime] = None


class InventoryReservationCreate(InventoryReservationBase):
    """재고 예약 생성 요청 스키마."""

    pass


class InventoryReservationUpdate(ORMBaseSchema):
    """재고 예약 수정 요청 스키마."""

    reserved_quantity: Optional[int] = Field(default=None, gt=0)
    reservation_status: Optional[str] = Field(default=None, max_length=30)
    expired_at: Optional[datetime] = None


class InventoryReservationRead(InventoryReservationBase, TimestampSchema):
    """재고 예약 응답 스키마."""

    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    order: "Optional[OrderRead]" = None


class InventoryTransactionBase(ORMBaseSchema):
    """재고 변동 공통 입력 스키마."""

    sku_id: int = Field(..., gt=0)
    transaction_type: str = Field(..., max_length=50)
    quantity: int = Field(..., gt=0)
    reference_type: Optional[str] = Field(default=None, max_length=50)
    reference_id: Optional[int] = None


class InventoryTransactionCreate(InventoryTransactionBase):
    """재고 변동 생성 요청 스키마."""

    pass


class InventoryTransactionRead(InventoryTransactionBase, TimestampSchema):
    """재고 변동 응답 스키마."""

    id: int
    created_at: datetime


class WarehouseStockBase(ORMBaseSchema):
    """창고 재고 공통 입력 스키마."""

    warehouse_id: int = Field(..., gt=0)
    sku_id: int = Field(..., gt=0)
    stock_quantity: int = Field(..., ge=0)


class WarehouseStockCreate(WarehouseStockBase):
    """창고 재고 생성 요청 스키마."""

    pass


class WarehouseStockRead(WarehouseStockBase, TimestampSchema):
    """창고 재고 응답 스키마."""

    id: int
    created_at: datetime


class InventoryAdjustmentBase(ORMBaseSchema):
    """재고 조정 공통 입력 스키마."""

    sku_id: int = Field(..., gt=0)
    adjustment_quantity: int = Field(...)
    adjustment_reason: Optional[str] = None
    created_by: Optional[int] = None


class InventoryAdjustmentCreate(InventoryAdjustmentBase):
    """재고 조정 생성 요청 스키마."""

    pass


class InventoryAdjustmentRead(InventoryAdjustmentBase, TimestampSchema):
    """재고 조정 응답 스키마."""

    id: int
    created_at: datetime


# 순환 참조를 해결하기 위해 나중에 import
from app.schemas.product import SKURead
from app.schemas.order import OrderRead

__all__ = [
    "InventoryBase",
    "InventoryCreate",
    "InventoryUpdate",
    "InventoryRead",
    "InventoryReservationBase",
    "InventoryReservationCreate",
    "InventoryReservationUpdate",
    "InventoryReservationRead",
    "InventoryTransactionBase",
    "InventoryTransactionCreate",
    "InventoryTransactionRead",
    "WarehouseStockBase",
    "WarehouseStockCreate",
    "WarehouseStockRead",
    "InventoryAdjustmentBase",
    "InventoryAdjustmentCreate",
    "InventoryAdjustmentRead",
]