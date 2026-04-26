from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.config import settings
from app.database import Base


class Payment(Base):
    """결제 마스터 정보를 저장한다."""

    __tablename__ = "payment"
    __table_args__ = (
        Index("idx_payment_order_id", "order_id"),
        Index("idx_payment_status", "payment_status"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(f"{settings.DB_SCHEMA}.order_header.id"),
        nullable=False,
    )
    payment_status: Mapped[str] = mapped_column(String(30), nullable=False)
    payment_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    paid_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, server_default="0")
    currency_code: Mapped[str] = mapped_column(String(10), nullable=False, server_default="KRW")
    payment_method_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    idempotency_key: Mapped[Optional[str]] = mapped_column(String(255), unique=True, nullable=True)
    requested_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    deleted_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)

    order: Mapped["OrderHeader"] = relationship(back_populates="payment_records")
    transactions: Mapped[list["PaymentTransaction"]] = relationship(
        back_populates="payment",
        cascade="all, delete-orphan",
    )
    refunds: Mapped[list["PaymentRefund"]] = relationship(
        back_populates="payment",
        cascade="all, delete-orphan",
    )
    logs: Mapped[list["PaymentLog"]] = relationship(
        back_populates="payment",
        cascade="all, delete-orphan",
    )


class PaymentTransaction(Base):
    """결제 트랜잭션 정보를 저장한다."""

    __tablename__ = "payment_transaction"
    __table_args__ = (
        Index("idx_payment_transaction_payment_id", "payment_id"),
        Index("idx_payment_transaction_pg_transaction_id", "pg_transaction_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    payment_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(f"{settings.DB_SCHEMA}.payment.id"),
        nullable=False,
    )
    transaction_type: Mapped[str] = mapped_column(String(30), nullable=False)
    transaction_status: Mapped[str] = mapped_column(String(30), nullable=False)
    transaction_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    pg_provider: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    pg_transaction_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    pg_response_raw: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    requested_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    responded_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())

    payment: Mapped["Payment"] = relationship(back_populates="transactions")


class PaymentMethod(Base):
    """결제 수단 정보를 저장한다."""

    __tablename__ = "payment_method"
    __table_args__ = (
        Index("idx_payment_method_user_id", "user_id"),
        Index("idx_payment_method_is_default", "is_default"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(f"{settings.DB_SCHEMA}.user_account.id"),
        nullable=False,
    )
    payment_method_code: Mapped[str] = mapped_column(String(50), nullable=False)
    card_token: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    card_last4: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    is_default: Mapped[bool] = mapped_column(nullable=False, server_default="false")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    user: Mapped["UserAccount"] = relationship(back_populates="payment_methods")


class PaymentRefund(Base):
    """결제 환불 정보를 저장한다."""

    __tablename__ = "payment_refund"
    __table_args__ = (
        Index("idx_payment_refund_payment_id", "payment_id"),
        Index("idx_payment_refund_status", "refund_status"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    payment_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(f"{settings.DB_SCHEMA}.payment.id"),
        nullable=False,
    )
    refund_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    refund_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    refund_status: Mapped[str] = mapped_column(String(30), nullable=False)
    requested_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())

    payment: Mapped["Payment"] = relationship(back_populates="refunds")


class PaymentLog(Base):
    """결제 로그 정보를 저장한다."""

    __tablename__ = "payment_log"
    __table_args__ = (Index("idx_payment_log_payment_id", "payment_id"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    payment_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey(f"{settings.DB_SCHEMA}.payment.id"),
        nullable=True,
    )
    log_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    log_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    log_data: Mapped[Optional[dict]] = mapped_column(Text, nullable=True)  # JSONB 대신 Text 사용
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())

    payment: Mapped[Optional["Payment"]] = relationship(back_populates="logs")