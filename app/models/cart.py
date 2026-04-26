from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Index, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.config import settings
from app.database import Base
from app.models.user import UserAccount


class Cart(Base):
    """장바구니 기본 정보를 저장한다."""

    __tablename__ = "cart"
    __table_args__ = (
        Index("idx_cart_user_id", "user_id"),
        Index("idx_cart_session_id", "session_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey(f"{settings.DB_SCHEMA}.user_account.id"),
        nullable=True,
    )
    session_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    cart_status: Mapped[str] = mapped_column(String(20), nullable=False)
    last_added_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    deleted_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)

    user: Mapped["UserAccount"] = relationship(back_populates="carts")
    items: Mapped[list["CartItem"]] = relationship(
        back_populates="cart",
        cascade="all, delete-orphan",
    )
    coupons: Mapped[list["CartCoupon"]] = relationship(
        back_populates="cart",
        cascade="all, delete-orphan",
    )
    orders: Mapped[list["OrderHeader"]] = relationship(back_populates="cart")


class CartItem(Base):
    """장바구니에 담긴 상품 항목을 저장한다."""

    __tablename__ = "cart_item"
    __table_args__ = (
        Index("idx_cart_item_cart_id", "cart_id"),
        Index("uq_cart_item", "cart_id", "sku_id", unique=True),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    cart_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(f"{settings.DB_SCHEMA}.cart.id"),
        nullable=False,
    )
    sku_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(f"{settings.DB_SCHEMA}.sku.id"),
        nullable=False,
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    total_price_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    is_selected: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True, default=True, server_default="true")
    added_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    deleted_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)

    cart: Mapped["Cart"] = relationship(back_populates="items")
    sku: Mapped["SKU"] = relationship(back_populates="cart_items")
    option_snapshots: Mapped[list["CartItemOptionSnapshot"]] = relationship(
        back_populates="cart_item",
        cascade="all, delete-orphan",
    )


class CartItemOptionSnapshot(Base):
    """장바구니 상품의 옵션 스냅샷을 저장한다."""

    __tablename__ = "cart_item_option_snapshot"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    cart_item_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(f"{settings.DB_SCHEMA}.cart_item.id"),
        nullable=False,
    )
    option_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    option_value: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())

    cart_item: Mapped["CartItem"] = relationship(back_populates="option_snapshots")


class CartCoupon(Base):
    """장바구니에 적용된 쿠폰 정보를 저장한다."""

    __tablename__ = "cart_coupon"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    cart_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(f"{settings.DB_SCHEMA}.cart.id"),
        nullable=False,
    )
    coupon_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(f"{settings.DB_SCHEMA}.coupon.id"),
        nullable=False,
    )
    discount_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())

    cart: Mapped["Cart"] = relationship(back_populates="coupons")
    coupon: Mapped["Coupon"] = relationship(back_populates="cart_coupons")


__all__ = ["Cart", "CartItem", "CartItemOptionSnapshot", "CartCoupon"]