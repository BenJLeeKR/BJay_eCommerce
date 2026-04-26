from __future__ import annotations
from typing import Optional

from datetime import datetime
from decimal import Decimal

from pydantic import Field

from app.schemas import ORMBaseSchema, TimestampSchema


class ShipmentBase(ORMBaseSchema):
    """배송 공통 입력 스키마."""

    order_id: int = Field(..., description="주문 ID")
    shipment_status: str = Field(..., max_length=30, description="배송 상태")
    shipment_type: Optional[str] = Field(None, max_length=30, description="배송 유형")
    total_shipping_amount: Decimal = Field(default=0, max_digits=12, decimal_places=2, description="배송비")
    shipped_at: Optional[datetime] = Field(None, description="출고 시간")
    delivered_at: Optional[datetime] = Field(None, description="배송 완료 시간")
    warehouse_id: Optional[int] = Field(None, description="창고 ID")
    created_by: Optional[int] = Field(None, description="생성자")
    updated_by: Optional[int] = Field(None, description="수정자")


class ShipmentCreate(ShipmentBase):
    """배송 생성 요청 스키마."""

    pass


class ShipmentUpdate(ORMBaseSchema):
    """배송 수정 요청 스키마."""

    shipment_status: Optional[str] = Field(None, max_length=30, description="배송 상태")
    shipment_type: Optional[str] = Field(None, max_length=30, description="배송 유형")
    total_shipping_amount: Optional[Decimal] = Field(None, max_digits=12, decimal_places=2, description="배송비")
    shipped_at: Optional[datetime] = Field(None, description="출고 시간")
    delivered_at: Optional[datetime] = Field(None, description="배송 완료 시간")
    warehouse_id: Optional[int] = Field(None, description="창고 ID")
    updated_by: Optional[int] = Field(None, description="수정자")


class ShipmentRead(ShipmentBase, TimestampSchema):
    """배송 상세 응답 스키마."""

    id: int
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[int] = None
    # 관계 필드는 필요에 따라 추가
    # order: Optional[OrderHeaderRead] = None
    # warehouse: Optional[WarehouseRead] = None
    # items: list[ShipmentItemRead] = Field(default_factory=list)
    # tracking: list[ShipmentTrackingRead] = Field(default_factory=list)
    # status_history: list[ShipmentStatusHistoryRead] = Field(default_factory=list)
    # packages: list[ShipmentPackageRead] = Field(default_factory=list)


class ShipmentItemBase(ORMBaseSchema):
    """배송 상품 공통 입력 스키마."""

    shipment_id: int = Field(..., description="배송 ID")
    order_item_id: int = Field(..., description="주문 상품 ID")
    sku_id: int = Field(..., description="SKU ID")
    shipped_quantity: int = Field(..., ge=0, description="출고 수량")
    delivered_quantity: int = Field(default=0, ge=0, description="수령 수량")
    shipment_item_status: Optional[str] = Field(None, max_length=30, description="배송 상품 상태")
    created_by: Optional[int] = Field(None, description="생성자")
    updated_by: Optional[int] = Field(None, description="수정자")


class ShipmentItemCreate(ShipmentItemBase):
    """배송 상품 생성 요청 스키마."""

    pass


class ShipmentItemUpdate(ORMBaseSchema):
    """배송 상품 수정 요청 스키마."""

    shipped_quantity: Optional[int] = Field(None, ge=0, description="출고 수량")
    delivered_quantity: Optional[int] = Field(None, ge=0, description="수령 수량")
    shipment_item_status: Optional[str] = Field(None, max_length=30, description="배송 상품 상태")
    updated_by: Optional[int] = Field(None, description="수정자")


class ShipmentItemRead(ShipmentItemBase, TimestampSchema):
    """배송 상품 응답 스키마."""

    id: int
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[int] = None
    # 관계 필드
    # shipment: Optional[ShipmentRead] = None
    # order_item: Optional[OrderItemRead] = None
    # sku: Optional[SKURead] = None


class ShipmentTrackingBase(ORMBaseSchema):
    """배송 추적 공통 입력 스키마."""

    shipment_id: int = Field(..., description="배송 ID")
    courier_code: Optional[str] = Field(None, max_length=50, description="택배사 코드")
    tracking_number: Optional[str] = Field(None, max_length=100, description="송장 번호")
    tracking_status: Optional[str] = Field(None, max_length=50, description="추적 상태")
    last_tracked_at: Optional[datetime] = Field(None, description="마지막 추적 시간")


class ShipmentTrackingCreate(ShipmentTrackingBase):
    """배송 추적 생성 요청 스키마."""

    pass


class ShipmentTrackingUpdate(ORMBaseSchema):
    """배송 추적 수정 요청 스키마."""

    courier_code: Optional[str] = Field(None, max_length=50, description="택배사 코드")
    tracking_number: Optional[str] = Field(None, max_length=100, description="송장 번호")
    tracking_status: Optional[str] = Field(None, max_length=50, description="추적 상태")
    last_tracked_at: Optional[datetime] = Field(None, description="마지막 추적 시간")


class ShipmentTrackingRead(ShipmentTrackingBase, TimestampSchema):
    """배송 추적 응답 스키마."""

    id: int
    # shipment: Optional[ShipmentRead] = None


class ShipmentStatusHistoryBase(ORMBaseSchema):
    """배송 상태 이력 공통 입력 스키마."""

    shipment_id: int = Field(..., description="배송 ID")
    shipment_status: str = Field(..., max_length=30, description="배송 상태")
    changed_by: Optional[int] = Field(None, description="변경자")
    change_reason: Optional[str] = Field(None, description="변경 사유")


class ShipmentStatusHistoryCreate(ShipmentStatusHistoryBase):
    """배송 상태 이력 생성 요청 스키마."""

    pass


class ShipmentStatusHistoryUpdate(ORMBaseSchema):
    """배송 상태 이력 수정 요청 스키마."""

    shipment_status: Optional[str] = Field(None, max_length=30, description="배송 상태")
    changed_by: Optional[int] = Field(None, description="변경자")
    change_reason: Optional[str] = Field(None, description="변경 사유")


class ShipmentStatusHistoryRead(ShipmentStatusHistoryBase, TimestampSchema):
    """배송 상태 이력 응답 스키마."""

    id: int
    changed_at: datetime
    # shipment: Optional[ShipmentRead] = None


class WarehouseBase(ORMBaseSchema):
    """창고 공통 입력 스키마."""

    warehouse_name: str = Field(..., max_length=255, description="창고명")
    postal_code: Optional[str] = Field(None, max_length=20, description="우편번호")
    address_line1: Optional[str] = Field(None, max_length=255, description="주소 1")
    address_line2: Optional[str] = Field(None, max_length=255, description="주소 2")


class WarehouseCreate(WarehouseBase):
    """창고 생성 요청 스키마."""

    pass


class WarehouseUpdate(ORMBaseSchema):
    """창고 수정 요청 스키마."""

    warehouse_name: Optional[str] = Field(None, max_length=255, description="창고명")
    postal_code: Optional[str] = Field(None, max_length=20, description="우편번호")
    address_line1: Optional[str] = Field(None, max_length=255, description="주소 1")
    address_line2: Optional[str] = Field(None, max_length=255, description="주소 2")


class WarehouseRead(WarehouseBase, TimestampSchema):
    """창고 응답 스키마."""

    id: int
    # shipments: list[ShipmentRead] = Field(default_factory=list)


class ShipmentPackageBase(ORMBaseSchema):
    """배송 패키지 공통 입력 스키마."""

    shipment_id: int = Field(..., description="배송 ID")
    package_weight: Optional[Decimal] = Field(None, max_digits=10, decimal_places=2, description="패키지 무게")
    package_volume: Optional[Decimal] = Field(None, max_digits=10, decimal_places=2, description="패키지 부피")


class ShipmentPackageCreate(ShipmentPackageBase):
    """배송 패키지 생성 요청 스키마."""

    pass


class ShipmentPackageUpdate(ORMBaseSchema):
    """배송 패키지 수정 요청 스키마."""

    package_weight: Optional[Decimal] = Field(None, max_digits=10, decimal_places=2, description="패키지 무게")
    package_volume: Optional[Decimal] = Field(None, max_digits=10, decimal_places=2, description="패키지 부피")


class ShipmentPackageRead(ShipmentPackageBase, TimestampSchema):
    """배송 패키지 응답 스키마."""

    id: int
    # shipment: Optional[ShipmentRead] = None


__all__ = [
    "ShipmentBase",
    "ShipmentCreate",
    "ShipmentRead",
    "ShipmentUpdate",
    "ShipmentItemBase",
    "ShipmentItemCreate",
    "ShipmentItemRead",
    "ShipmentItemUpdate",
    "ShipmentTrackingBase",
    "ShipmentTrackingCreate",
    "ShipmentTrackingRead",
    "ShipmentTrackingUpdate",
    "ShipmentStatusHistoryBase",
    "ShipmentStatusHistoryCreate",
    "ShipmentStatusHistoryRead",
    "ShipmentStatusHistoryUpdate",
    "WarehouseBase",
    "WarehouseCreate",
    "WarehouseRead",
    "WarehouseUpdate",
    "ShipmentPackageBase",
    "ShipmentPackageCreate",
    "ShipmentPackageRead",
    "ShipmentPackageUpdate",
]