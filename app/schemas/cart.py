from __future__ import annotations
from typing import Optional

from datetime import datetime
from decimal import Decimal

from pydantic import Field

from app.schemas import ORMBaseSchema, TimestampSchema


class CartItemOptionSnapshotRead(TimestampSchema):
    """장바구니 상품 옵션 스냅샷 응답 스키마."""

    id: int
    cart_item_id: int
    option_name: Optional[str] = None
    option_value: Optional[str] = None
    created_at: datetime


class CartCouponRead(TimestampSchema):
    """장바구니 쿠폰 응답 스키마."""

    id: int
    cart_id: int
    coupon_id: int
    discount_amount: Optional[Decimal] = None
    created_at: datetime


class CartItemRead(TimestampSchema):
    """장바구니 상품 항목 응답 스키마."""

    id: int
    cart_id: int
    sku_id: int
    quantity: int
    unit_price_amount: Decimal
    total_price_amount: Decimal
    is_selected: Optional[bool] = True
    added_at: datetime
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[int] = None
    option_snapshots: list[CartItemOptionSnapshotRead] = Field(default_factory=list)


class CartBase(ORMBaseSchema):
    """장바구니 공통 입력 스키마."""

    user_id: Optional[int] = None
    cart_status: str = Field(..., max_length=20)
    last_added_at: Optional[datetime] = None


class CartCreate(CartBase):
    """장바구니 생성 요청 스키마 (items, coupons 중첩 생성 지원)."""

    created_by: Optional[int] = None
    items: list[CartItemNestedCreate] = Field(default_factory=list)
    coupons: list[CartCouponNestedCreate] = Field(default_factory=list)


class CartUpdate(ORMBaseSchema):
    """장바구니 수정 요청 스키마."""

    user_id: Optional[int] = None
    cart_status: Optional[str] = Field(default=None, max_length=20)
    last_added_at: Optional[datetime] = None
    updated_by: Optional[int] = None


class CartRead(CartBase, TimestampSchema):
    """장바구니 상세 응답 스키마."""

    id: int
    session_id: Optional[str] = None
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[int] = None
    items: list[CartItemRead] = Field(default_factory=list)
    coupons: list[CartCouponRead] = Field(default_factory=list)


class CartItemNestedCreate(ORMBaseSchema):
    """장바구니 상품 항목 생성 요청 스키마 (복합 생성용 - cart_id 제외)."""

    sku_id: int
    quantity: int = Field(..., ge=1)
    unit_price_amount: Decimal = Field(..., max_digits=12, decimal_places=2)
    total_price_amount: Decimal = Field(..., max_digits=12, decimal_places=2)
    is_selected: Optional[bool] = True
    added_at: Optional[datetime] = None
    created_by: Optional[int] = None
    option_snapshots: list[CartItemOptionSnapshotNestedCreate] = Field(default_factory=list)


class CartItemBase(ORMBaseSchema):
    """장바구니 상품 항목 공통 입력 스키마."""

    sku_id: int
    quantity: int = Field(..., ge=1)
    unit_price_amount: Decimal = Field(..., max_digits=12, decimal_places=2)
    total_price_amount: Decimal = Field(..., max_digits=12, decimal_places=2)
    is_selected: Optional[bool] = True


class CartItemCreate(CartItemBase):
    """장바구니 상품 항목 생성 요청 스키마."""

    cart_id: int
    added_at: Optional[datetime] = None
    created_by: Optional[int] = None


class CartItemUpdate(ORMBaseSchema):
    """장바구니 상품 항목 수정 요청 스키마."""

    quantity: Optional[int] = Field(default=None, ge=1)
    unit_price_amount: Optional[Decimal] = Field(default=None, max_digits=12, decimal_places=2)
    total_price_amount: Optional[Decimal] = Field(default=None, max_digits=12, decimal_places=2)
    is_selected: Optional[bool] = None
    updated_by: Optional[int] = None


class CartItemOptionSnapshotNestedCreate(ORMBaseSchema):
    """장바구니 옵션 스냅샷 생성 요청 스키마 (복합 생성용 - cart_item_id 제외)."""

    option_name: Optional[str] = Field(default=None, max_length=100)
    option_value: Optional[str] = Field(default=None, max_length=100)


class CartItemOptionSnapshotBase(ORMBaseSchema):
    """장바구니 상품 옵션 스냅샷 공통 입력 스키마."""

    option_name: Optional[str] = Field(default=None, max_length=100)
    option_value: Optional[str] = Field(default=None, max_length=100)


class CartItemOptionSnapshotCreate(CartItemOptionSnapshotBase):
    """장바구니 상품 옵션 스냅샷 생성 요청 스키마."""

    cart_item_id: int


class CartCouponNestedCreate(ORMBaseSchema):
    """장바구니 쿠폰 생성 요청 스키마 (복합 생성용 - cart_id 제외)."""

    coupon_id: int
    discount_amount: Optional[Decimal] = Field(default=None, max_digits=12, decimal_places=2)


class CartCouponBase(ORMBaseSchema):
    """장바구니 쿠폰 공통 입력 스키마."""

    coupon_id: int
    discount_amount: Optional[Decimal] = Field(default=None, max_digits=12, decimal_places=2)


class CartCouponCreate(CartCouponBase):
    """장바구니 쿠폰 생성 요청 스키마."""

    cart_id: int


__all__ = [
    "CartBase",
    "CartCreate",
    "CartRead",
    "CartUpdate",
    "CartItemBase",
    "CartItemCreate",
    "CartItemRead",
    "CartItemUpdate",
    "CartItemNestedCreate",
    "CartItemOptionSnapshotBase",
    "CartItemOptionSnapshotCreate",
    "CartItemOptionSnapshotRead",
    "CartItemOptionSnapshotNestedCreate",
    "CartCouponBase",
    "CartCouponCreate",
    "CartCouponRead",
    "CartCouponNestedCreate",
]