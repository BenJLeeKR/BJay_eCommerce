from __future__ import annotations
from typing import Optional

from datetime import datetime
from decimal import Decimal

from pydantic import Field

from app.schemas import ORMBaseSchema, TimestampSchema


class PromotionConditionRead(TimestampSchema):
    """프로모션 조건 응답 스키마."""

    id: int
    promotion_id: int
    condition_type: str
    condition_value: Optional[dict] = None


class PromotionTargetRead(TimestampSchema):
    """프로모션 대상 응답 스키마."""

    id: int
    promotion_id: int
    target_type: str
    target_id: Optional[int] = None


class CouponIssueRead(TimestampSchema):
    """쿠폰 발급 응답 스키마."""

    id: int
    coupon_id: int
    user_id: int
    issued_at: datetime
    expire_at: Optional[datetime] = None
    is_used: bool = False


class CouponUsageRead(TimestampSchema):
    """쿠폰 사용 응답 스키마."""

    id: int
    coupon_issue_id: int
    order_id: int
    discount_amount: Decimal
    used_at: datetime


class CouponRead(TimestampSchema):
    """쿠폰 응답 스키마."""

    id: int
    promotion_id: int
    coupon_code: str
    total_quantity: Optional[int] = None
    issued_quantity: int = 0
    per_user_limit: int = 1
    valid_from: Optional[datetime] = None
    valid_to: Optional[datetime] = None
    created_by: Optional[int] = None
    deleted_at: Optional[datetime] = None
    issues: list[CouponIssueRead] = Field(default_factory=list)


class PromotionBase(ORMBaseSchema):
    """프로모션 공통 입력 스키마."""

    promotion_name: str = Field(..., max_length=255)
    promotion_type: str = Field(..., max_length=50)  # COUPON / AUTO
    discount_type: str = Field(..., max_length=50)  # RATE / FIXED
    discount_value: Decimal = Field(..., max_digits=12, decimal_places=2)
    max_discount_amount: Optional[Decimal] = Field(None, max_digits=12, decimal_places=2)
    start_at: datetime
    end_at: datetime
    is_active: bool = True
    priority: int = 0


class PromotionCreate(PromotionBase):
    """프로모션 생성 요청 스키마."""

    created_by: Optional[int] = None


class PromotionUpdate(ORMBaseSchema):
    """프로모션 수정 요청 스키마."""

    promotion_name: Optional[str] = Field(default=None, max_length=255)
    promotion_type: Optional[str] = Field(default=None, max_length=50)
    discount_type: Optional[str] = Field(default=None, max_length=50)
    discount_value: Optional[Decimal] = Field(default=None, max_digits=12, decimal_places=2)
    max_discount_amount: Optional[Decimal] = Field(default=None, max_digits=12, decimal_places=2)
    start_at: Optional[datetime] = None
    end_at: Optional[datetime] = None
    is_active: Optional[bool] = None
    priority: Optional[int] = None
    updated_by: Optional[int] = None


class PromotionRead(PromotionBase, TimestampSchema):
    """프로모션 상세 응답 스키마."""

    id: int
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[int] = None
    conditions: list[PromotionConditionRead] = Field(default_factory=list)
    targets: list[PromotionTargetRead] = Field(default_factory=list)
    coupons: list[CouponRead] = Field(default_factory=list)


class CouponBase(ORMBaseSchema):
    """쿠폰 공통 입력 스키마."""

    promotion_id: int
    coupon_code: str = Field(..., max_length=100)
    total_quantity: Optional[int] = Field(None, ge=1)
    per_user_limit: int = Field(default=1, ge=1)
    valid_from: Optional[datetime] = None
    valid_to: Optional[datetime] = None


class CouponCreate(CouponBase):
    """쿠폰 생성 요청 스키마."""

    created_by: Optional[int] = None


class CouponUpdate(ORMBaseSchema):
    """쿠폰 수정 요청 스키마."""

    coupon_code: Optional[str] = Field(default=None, max_length=100)
    total_quantity: Optional[int] = Field(default=None, ge=1)
    per_user_limit: Optional[int] = Field(default=None, ge=1)
    valid_from: Optional[datetime] = None
    valid_to: Optional[datetime] = None
    deleted_at: Optional[datetime] = None


class CouponIssueBase(ORMBaseSchema):
    """쿠폰 발급 공통 입력 스키마."""

    coupon_id: int
    user_id: int
    expire_at: Optional[datetime] = None


class CouponIssueCreate(CouponIssueBase):
    """쿠폰 발급 요청 스키마."""

    pass


class CouponUsageBase(ORMBaseSchema):
    """쿠폰 사용 공통 입력 스키마."""

    coupon_issue_id: int
    order_id: int
    discount_amount: Decimal = Field(..., max_digits=12, decimal_places=2)


class CouponUsageCreate(CouponUsageBase):
    """쿠폰 사용 요청 스키마."""

    pass


__all__ = [
    "PromotionBase",
    "PromotionCreate",
    "PromotionRead",
    "PromotionUpdate",
    "PromotionConditionRead",
    "PromotionTargetRead",
    "CouponBase",
    "CouponCreate",
    "CouponRead",
    "CouponUpdate",
    "CouponIssueBase",
    "CouponIssueCreate",
    "CouponIssueRead",
    "CouponUsageBase",
    "CouponUsageCreate",
    "CouponUsageRead",
]