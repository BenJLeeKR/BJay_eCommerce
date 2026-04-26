from __future__ import annotations
from typing import Optional

from datetime import datetime
from decimal import Decimal

from pydantic import Field

from app.schemas import ORMBaseSchema, TimestampSchema


class PaymentTransactionRead(TimestampSchema):
    """결제 트랜잭션 응답 스키마."""

    id: int
    payment_id: int
    transaction_type: str
    transaction_status: str
    transaction_amount: Decimal
    pg_provider: Optional[str] = None
    pg_transaction_id: Optional[str] = None
    pg_response_raw: Optional[dict] = None
    requested_at: datetime
    responded_at: Optional[datetime] = None


class PaymentMethodRead(TimestampSchema):
    """결제 수단 응답 스키마."""

    id: int
    user_id: int
    payment_method_code: str
    card_token: Optional[str] = None
    card_last4: Optional[str] = None
    is_default: bool = False
    deleted_at: Optional[datetime] = None


class PaymentRefundRead(TimestampSchema):
    """결제 환불 응답 스키마."""

    id: int
    payment_id: int
    refund_amount: Decimal
    refund_reason: Optional[str] = None
    refund_status: str
    requested_at: datetime
    processed_at: Optional[datetime] = None


class PaymentLogRead(TimestampSchema):
    """결제 로그 응답 스키마."""

    id: int
    payment_id: Optional[int] = None
    log_type: Optional[str] = None
    log_message: Optional[str] = None
    log_data: Optional[dict] = None
    created_at: datetime


class PaymentBase(ORMBaseSchema):
    """결제 공통 입력 스키마."""

    order_id: int = Field(..., gt=0)
    payment_status: str = Field(..., max_length=30)
    payment_amount: Decimal = Field(..., max_digits=12, decimal_places=2)
    paid_amount: Decimal = Field(default=0, max_digits=12, decimal_places=2)
    currency_code: str = Field(default="KRW", max_length=10)
    payment_method_code: Optional[str] = Field(default=None, max_length=50)
    idempotency_key: Optional[str] = Field(default=None, max_length=255)


class PaymentCreate(PaymentBase):
    """결제 생성 요청 스키마."""

    created_by: Optional[int] = None


class PaymentUpdate(ORMBaseSchema):
    """결제 수정 요청 스키마."""

    payment_status: Optional[str] = Field(default=None, max_length=30)
    paid_amount: Optional[Decimal] = Field(default=None, max_digits=12, decimal_places=2)
    currency_code: Optional[str] = Field(default=None, max_length=10)
    payment_method_code: Optional[str] = Field(default=None, max_length=50)
    approved_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    updated_by: Optional[int] = None


class PaymentRead(PaymentBase, TimestampSchema):
    """결제 상세 응답 스키마."""

    id: int
    requested_at: datetime
    approved_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[int] = None
    transactions: list[PaymentTransactionRead] = Field(default_factory=list)
    refunds: list[PaymentRefundRead] = Field(default_factory=list)
    logs: list[PaymentLogRead] = Field(default_factory=list)


class PaymentTransactionBase(ORMBaseSchema):
    """결제 트랜잭션 공통 입력 스키마."""

    payment_id: int = Field(..., gt=0)
    transaction_type: str = Field(..., max_length=30)
    transaction_status: str = Field(..., max_length=30)
    transaction_amount: Decimal = Field(..., max_digits=12, decimal_places=2)
    pg_provider: Optional[str] = Field(default=None, max_length=50)
    pg_transaction_id: Optional[str] = Field(default=None, max_length=255)
    pg_response_raw: Optional[dict] = None


class PaymentTransactionCreate(PaymentTransactionBase):
    """결제 트랜잭션 생성 요청 스키마."""

    pass


class PaymentTransactionUpdate(ORMBaseSchema):
    """결제 트랜잭션 수정 요청 스키마."""

    transaction_status: Optional[str] = Field(default=None, max_length=30)
    pg_transaction_id: Optional[str] = Field(default=None, max_length=255)
    pg_response_raw: Optional[dict] = None
    responded_at: Optional[datetime] = None


class PaymentMethodBase(ORMBaseSchema):
    """결제 수단 공통 입력 스키마."""

    user_id: int = Field(..., gt=0)
    payment_method_code: str = Field(..., max_length=50)
    card_token: Optional[str] = Field(default=None, max_length=255)
    card_last4: Optional[str] = Field(default=None, max_length=10)
    is_default: bool = False


class PaymentMethodCreate(PaymentMethodBase):
    """결제 수단 생성 요청 스키마."""

    pass


class PaymentMethodUpdate(ORMBaseSchema):
    """결제 수단 수정 요청 스키마."""

    payment_method_code: Optional[str] = Field(default=None, max_length=50)
    card_token: Optional[str] = Field(default=None, max_length=255)
    card_last4: Optional[str] = Field(default=None, max_length=10)
    is_default: Optional[bool] = None


class PaymentRefundBase(ORMBaseSchema):
    """결제 환불 공통 입력 스키마."""

    payment_id: int = Field(..., gt=0)
    refund_amount: Decimal = Field(..., max_digits=12, decimal_places=2)
    refund_reason: Optional[str] = None
    refund_status: str = Field(..., max_length=30)


class PaymentRefundCreate(PaymentRefundBase):
    """결제 환불 생성 요청 스키마."""

    pass


class PaymentRefundUpdate(ORMBaseSchema):
    """결제 환불 수정 요청 스키마."""

    refund_status: Optional[str] = Field(default=None, max_length=30)
    processed_at: Optional[datetime] = None


class PaymentLogBase(ORMBaseSchema):
    """결제 로그 공통 입력 스키마."""

    payment_id: Optional[int] = Field(default=None, gt=0)
    log_type: Optional[str] = Field(default=None, max_length=50)
    log_message: Optional[str] = None
    log_data: Optional[dict] = None


class PaymentLogCreate(PaymentLogBase):
    """결제 로그 생성 요청 스키마."""

    pass


__all__ = [
    "PaymentBase",
    "PaymentCreate",
    "PaymentRead",
    "PaymentUpdate",
    "PaymentTransactionBase",
    "PaymentTransactionCreate",
    "PaymentTransactionRead",
    "PaymentTransactionUpdate",
    "PaymentMethodBase",
    "PaymentMethodCreate",
    "PaymentMethodRead",
    "PaymentMethodUpdate",
    "PaymentRefundBase",
    "PaymentRefundCreate",
    "PaymentRefundRead",
    "PaymentRefundUpdate",
    "PaymentLogBase",
    "PaymentLogCreate",
    "PaymentLogRead",
]