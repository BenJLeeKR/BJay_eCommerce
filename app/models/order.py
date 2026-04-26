from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.config import settings
from app.database import Base


class OrderHeader(Base):
    """주문 헤더 정보를 저장한다."""

    __tablename__ = "order_header"
    __table_args__ = (Index("idx_order_header_user_id", "user_id"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    order_number: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(f"{settings.DB_SCHEMA}.user_account.id"),
        nullable=False,
    )
    cart_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey(f"{settings.DB_SCHEMA}.cart.id"),
        nullable=True,
    )
    order_status: Mapped[str] = mapped_column(String(30), nullable=False)
    total_product_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    total_discount_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, server_default="0")
    total_shipping_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, server_default="0")
    total_pay_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    ordered_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    deleted_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)

    user: Mapped["UserAccount"] = relationship(back_populates="orders")
    cart: Mapped[Optional["Cart"]] = relationship(back_populates="orders")
    items: Mapped[list["OrderItem"]] = relationship(back_populates="order", cascade="all, delete-orphan")
    status_histories: Mapped[list["OrderStatusHistory"]] = relationship(back_populates="order", cascade="all, delete-orphan")
    payments: Mapped[list["OrderPayment"]] = relationship(back_populates="order", cascade="all, delete-orphan")
    shipments: Mapped[list["OrderShipment"]] = relationship(back_populates="order", cascade="all, delete-orphan")
    address_snapshots: Mapped[list["OrderAddressSnapshot"]] = relationship(back_populates="order", cascade="all, delete-orphan")
    coupons: Mapped[list["OrderCoupon"]] = relationship(back_populates="order", cascade="all, delete-orphan")
    payment_records: Mapped[list["Payment"]] = relationship(back_populates="order")
    inventory_reservations: Mapped[list["InventoryReservation"]] = relationship(back_populates="order")
    order_shipments: Mapped[list["Shipment"]] = relationship(back_populates="order")


class OrderItem(Base):
    """주문 상품 정보를 저장한다."""

    __tablename__ = "order_item"
    __table_args__ = (
        Index("idx_order_item_order_id", "order_id"),
        Index("idx_order_item_sku_id", "sku_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(f"{settings.DB_SCHEMA}.order_header.id"),
        nullable=False,
    )
    sku_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(f"{settings.DB_SCHEMA}.sku.id"),
        nullable=False,
    )
    product_name: Mapped[str] = mapped_column(String(255), nullable=False)
    option_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    total_price_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    deleted_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)

    order: Mapped["OrderHeader"] = relationship(back_populates="items")
    sku: Mapped["SKU"] = relationship(back_populates="order_items")
    review: Mapped["Review"] = relationship(back_populates="order_item", uselist=False)
    shipment_items: Mapped[list["ShipmentItem"]] = relationship(back_populates="order_item")


class OrderStatusHistory(Base):
    """주문 상태 변경 이력을 저장한다."""

    __tablename__ = "order_status_history"
    __table_args__ = (Index("idx_order_status_history_order_id", "order_id"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(f"{settings.DB_SCHEMA}.order_header.id"),
        nullable=False,
    )
    order_status: Mapped[str] = mapped_column(String(30), nullable=False)
    changed_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    changed_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    change_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    order: Mapped["OrderHeader"] = relationship(back_populates="status_histories")


class OrderPayment(Base):
    """주문 결제 정보를 저장한다."""

    __tablename__ = "order_payment"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(f"{settings.DB_SCHEMA}.order_header.id"),
        nullable=False,
    )
    payment_method: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    payment_status: Mapped[str] = mapped_column(String(30), nullable=False, server_default="PENDING")
    pg_transaction_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    paid_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    paid_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())

    order: Mapped["OrderHeader"] = relationship(back_populates="payments")


class OrderShipment(Base):
    """주문 배송 정보를 저장한다."""

    __tablename__ = "order_shipment"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(f"{settings.DB_SCHEMA}.order_header.id"),
        nullable=False,
    )
    shipment_status: Mapped[str] = mapped_column(String(30), nullable=False)
    courier_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    tracking_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    shipped_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    delivered_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())

    order: Mapped["OrderHeader"] = relationship(back_populates="shipments")


class OrderAddressSnapshot(Base):
    """주문 배송지 스냅샷 정보를 저장한다."""

    __tablename__ = "order_address_snapshot"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(f"{settings.DB_SCHEMA}.order_header.id"),
        nullable=False,
    )
    recipient_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    recipient_phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    postal_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    address_line1: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    address_line2: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())

    order: Mapped["OrderHeader"] = relationship(back_populates="address_snapshots")


class OrderCoupon(Base):
    """주문 쿠폰 사용 정보를 저장한다."""

    __tablename__ = "order_coupon"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(f"{settings.DB_SCHEMA}.order_header.id"),
        nullable=False,
    )
    coupon_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(f"{settings.DB_SCHEMA}.coupon.id"),
        nullable=False,
    )
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())

    order: Mapped["OrderHeader"] = relationship(back_populates="coupons")
    coupon: Mapped["Coupon"] = relationship(back_populates="order_coupons")