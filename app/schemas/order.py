from __future__ import annotations
from typing import Optional

from datetime import datetime
from decimal import Decimal

from pydantic import Field

from app.schemas import ORMBaseSchema, TimestampSchema
from app.schemas.user import UserAccountRead


class OrderItemBase(ORMBaseSchema):
    """주문 상품 공통 입력 스키마."""

    sku_id: int
    product_name: str = Field(..., max_length=255)
    option_summary: Optional[str] = None
    quantity: int = Field(..., ge=1)
    unit_price_amount: Decimal = Field(..., max_digits=12, decimal_places=2)
    total_price_amount: Decimal = Field(..., max_digits=12, decimal_places=2)


class OrderItemCreate(OrderItemBase):
    """주문 상품 생성 요청 스키마."""

    created_by: Optional[int] = None


class OrderItemUpdate(ORMBaseSchema):
    """주문 상품 수정 요청 스키마."""

    product_name: Optional[str] = Field(default=None, max_length=255)
    option_summary: Optional[str] = None
    quantity: Optional[int] = Field(default=None, ge=1)
    unit_price_amount: Optional[Decimal] = Field(default=None, max_digits=12, decimal_places=2)
    total_price_amount: Optional[Decimal] = Field(default=None, max_digits=12, decimal_places=2)
    updated_by: Optional[int] = None


class OrderItemRead(OrderItemBase, TimestampSchema):
    """주문 상품 응답 스키마."""

    id: int
    order_id: int
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[int] = None


class OrderStatusHistoryRead(ORMBaseSchema):
    """주문 상태 이력 응답 스키마."""

    id: int
    order_id: int
    order_status: str
    changed_at: datetime
    changed_by: Optional[int] = None
    change_reason: Optional[str] = None


class OrderPaymentRead(ORMBaseSchema):
    """주문 결제 응답 스키마."""

    id: int
    order_id: int
    payment_method: Optional[str] = None
    payment_status: str
    pg_transaction_id: Optional[str] = None
    paid_amount: Decimal
    paid_at: Optional[datetime] = None
    created_at: datetime


class OrderShipmentRead(ORMBaseSchema):
    """주문 배송 응답 스키마."""

    id: int
    order_id: int
    shipment_status: str
    courier_name: Optional[str] = None
    tracking_number: Optional[str] = None
    shipped_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    created_at: datetime


class OrderAddressSnapshotRead(ORMBaseSchema):
    """주문 배송지 스냅샷 응답 스키마."""

    id: int
    order_id: int
    recipient_name: Optional[str] = None
    recipient_phone: Optional[str] = None
    postal_code: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    created_at: datetime


class OrderCouponRead(ORMBaseSchema):
    """주문 쿠폰 응답 스키마."""

    id: int
    order_id: int
    coupon_id: int
    discount_amount: Optional[Decimal] = None
    created_at: datetime


class OrderBase(ORMBaseSchema):
    """주문 공통 입력 스키마."""

    order_number: str = Field(..., max_length=50)
    user_id: int
    order_status: str = Field(..., max_length=30)
    total_product_amount: Decimal = Field(..., max_digits=12, decimal_places=2)
    total_discount_amount: Decimal = Field(default=0, max_digits=12, decimal_places=2)
    total_shipping_amount: Decimal = Field(default=0, max_digits=12, decimal_places=2)
    total_pay_amount: Decimal = Field(..., max_digits=12, decimal_places=2)
    ordered_at: Optional[datetime] = None


class OrderCreate(OrderBase):
    """주문 생성 요청 스키마."""

    cart_id: Optional[int] = None
    created_by: Optional[int] = None
    items: list[OrderItemCreate] = Field(default_factory=list)


class OrderUpdate(ORMBaseSchema):
    """주문 수정 요청 스키마."""

    order_status: Optional[str] = Field(default=None, max_length=30)
    total_discount_amount: Optional[Decimal] = Field(default=None, max_digits=12, decimal_places=2)
    total_shipping_amount: Optional[Decimal] = Field(default=None, max_digits=12, decimal_places=2)
    total_pay_amount: Optional[Decimal] = Field(default=None, max_digits=12, decimal_places=2)
    updated_by: Optional[int] = None


class OrderRead(OrderBase, TimestampSchema):
    """주문 상세 응답 스키마."""

    id: int
    cart_id: Optional[int] = None
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[int] = None
    user: Optional[UserAccountRead] = None
    items: list[OrderItemRead] = Field(default_factory=list)
    status_histories: list[OrderStatusHistoryRead] = Field(default_factory=list)
    payments: list[OrderPaymentRead] = Field(default_factory=list)
    shipments: list[OrderShipmentRead] = Field(default_factory=list)
    address_snapshots: list[OrderAddressSnapshotRead] = Field(default_factory=list)
    coupons: list[OrderCouponRead] = Field(default_factory=list)


__all__ = [
    "OrderBase",
    "OrderCreate",
    "OrderRead",
    "OrderUpdate",
    "OrderItemBase",
    "OrderItemCreate",
    "OrderItemRead",
    "OrderItemUpdate",
    "OrderStatusHistoryRead",
    "OrderPaymentRead",
    "OrderShipmentRead",
    "OrderAddressSnapshotRead",
    "OrderCouponRead",
]