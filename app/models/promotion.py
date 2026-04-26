from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Index, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.config import settings
from app.database import Base


class Promotion(Base):
    """프로모션 정의 정보를 저장한다."""

    __tablename__ = "promotion"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    promotion_name: Mapped[str] = mapped_column(String(255), nullable=False)
    promotion_type: Mapped[str] = mapped_column(String(50), nullable=False)  # COUPON / AUTO
    discount_type: Mapped[str] = mapped_column(String(50), nullable=False)  # RATE / FIXED
    discount_value: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    max_discount_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    start_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    deleted_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)

    conditions: Mapped[list["PromotionCondition"]] = relationship(
        back_populates="promotion",
        cascade="all, delete-orphan",
    )
    targets: Mapped[list["PromotionTarget"]] = relationship(
        back_populates="promotion",
        cascade="all, delete-orphan",
    )
    coupons: Mapped[list["Coupon"]] = relationship(
        back_populates="promotion",
        cascade="all, delete-orphan",
    )


class PromotionCondition(Base):
    """프로모션 적용 조건을 저장한다."""

    __tablename__ = "promotion_condition"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    promotion_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(f"{settings.DB_SCHEMA}.promotion.id"),
        nullable=False,
    )
    condition_type: Mapped[str] = mapped_column(String(50), nullable=False)
    condition_value: Mapped[Optional[dict]] = mapped_column(Text, nullable=True)  # JSONB 대신 Text 사용 (SQLAlchemy JSONB는 PostgreSQL에 따라 다름)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())

    promotion: Mapped["Promotion"] = relationship(back_populates="conditions")


class PromotionTarget(Base):
    """프로모션 적용 대상을 저장한다."""

    __tablename__ = "promotion_target"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    promotion_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(f"{settings.DB_SCHEMA}.promotion.id"),
        nullable=False,
    )
    target_type: Mapped[str] = mapped_column(String(50), nullable=False)  # PRODUCT / CATEGORY / ALL
    target_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())

    promotion: Mapped["Promotion"] = relationship(back_populates="targets")


class Coupon(Base):
    """쿠폰 정의 정보를 저장한다."""

    __tablename__ = "coupon"
    __table_args__ = (Index("idx_coupon_promotion_id", "promotion_id"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    promotion_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(f"{settings.DB_SCHEMA}.promotion.id"),
        nullable=False,
    )
    coupon_code: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    total_quantity: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    issued_quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    per_user_limit: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    valid_from: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    valid_to: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    promotion: Mapped["Promotion"] = relationship(back_populates="coupons")
    issues: Mapped[list["CouponIssue"]] = relationship(
        back_populates="coupon",
        cascade="all, delete-orphan",
    )
    cart_coupons: Mapped[list["CartCoupon"]] = relationship(back_populates="coupon")
    order_coupons: Mapped[list["OrderCoupon"]] = relationship(back_populates="coupon")


class CouponIssue(Base):
    """쿠폰 발급 내역을 저장한다."""

    __tablename__ = "coupon_issue"
    __table_args__ = (Index("idx_coupon_issue_coupon_id", "coupon_id"), Index("idx_coupon_issue_user_id", "user_id"))

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    coupon_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(f"{settings.DB_SCHEMA}.coupon.id"),
        nullable=False,
    )
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    issued_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    expire_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    is_used: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())

    coupon: Mapped["Coupon"] = relationship(back_populates="issues")
    usages: Mapped[list["CouponUsage"]] = relationship(
        back_populates="coupon_issue",
        cascade="all, delete-orphan",
    )


class CouponUsage(Base):
    """쿠폰 사용 내역을 저장한다."""

    __tablename__ = "coupon_usage"
    __table_args__ = (
        Index("idx_coupon_usage_coupon_issue_id", "coupon_issue_id"),
        Index("idx_coupon_usage_order_id", "order_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    coupon_issue_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(f"{settings.DB_SCHEMA}.coupon_issue.id"),
        nullable=False,
    )
    order_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    used_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())

    coupon_issue: Mapped["CouponIssue"] = relationship(back_populates="usages")