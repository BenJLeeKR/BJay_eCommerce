from __future__ import annotations

from datetime import datetime
from typing import Optional
from decimal import Decimal
from typing import Optional

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.config import settings
from app.database import Base


class Shipment(Base):
    """배송 정보를 저장한다."""

    __tablename__ = "shipment"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(f"{settings.DB_SCHEMA}.order_header.id"),
        nullable=False,
    )
    shipment_status: Mapped[str] = mapped_column(String(30), nullable=False)
    shipment_type: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    total_shipping_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True, default=0)
    shipped_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    delivered_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    warehouse_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey(f"{settings.DB_SCHEMA}.warehouse.id"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    deleted_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)

    order: Mapped["OrderHeader"] = relationship(back_populates="order_shipments")
    warehouse: Mapped["Warehouse | None"] = relationship(back_populates="shipments")
    items: Mapped[list["ShipmentItem"]] = relationship(
        back_populates="shipment",
        cascade="all, delete-orphan",
    )
    tracking: Mapped[list["ShipmentTracking"]] = relationship(
        back_populates="shipment",
        cascade="all, delete-orphan",
    )
    status_history: Mapped[list["ShipmentStatusHistory"]] = relationship(
        back_populates="shipment",
        cascade="all, delete-orphan",
    )
    packages: Mapped[list["ShipmentPackage"]] = relationship(
        back_populates="shipment",
        cascade="all, delete-orphan",
    )


class ShipmentItem(Base):
    """배송 상품 정보를 저장한다."""

    __tablename__ = "shipment_item"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    shipment_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(f"{settings.DB_SCHEMA}.shipment.id"),
        nullable=False,
    )
    order_item_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(f"{settings.DB_SCHEMA}.order_item.id"),
        nullable=False,
    )
    sku_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(f"{settings.DB_SCHEMA}.sku.id"),
        nullable=False,
    )
    shipped_quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    delivered_quantity: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, default=0)
    shipment_item_status: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    deleted_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)

    shipment: Mapped["Shipment"] = relationship(back_populates="items")
    order_item: Mapped["OrderItem"] = relationship(back_populates="shipment_items")
    sku: Mapped["SKU"] = relationship(back_populates="shipment_items")


class ShipmentTracking(Base):
    """배송 추적 정보를 저장한다."""

    __tablename__ = "shipment_tracking"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    shipment_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(f"{settings.DB_SCHEMA}.shipment.id"),
        nullable=False,
    )
    courier_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    tracking_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    tracking_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    last_tracked_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())

    shipment: Mapped["Shipment"] = relationship(back_populates="tracking")


class ShipmentStatusHistory(Base):
    """배송 상태 변경 이력을 저장한다."""

    __tablename__ = "shipment_status_history"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    shipment_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(f"{settings.DB_SCHEMA}.shipment.id"),
        nullable=False,
    )
    shipment_status: Mapped[str] = mapped_column(String(30), nullable=False)
    changed_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    changed_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    change_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    shipment: Mapped["Shipment"] = relationship(back_populates="status_history")


class Warehouse(Base):
    """창고 정보를 저장한다."""

    __tablename__ = "warehouse"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    warehouse_name: Mapped[str] = mapped_column(String(255), nullable=False)
    postal_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    address_line1: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    address_line2: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())

    shipments: Mapped[list["Shipment"]] = relationship(back_populates="warehouse")


class ShipmentPackage(Base):
    """배송 패키지 정보를 저장한다."""

    __tablename__ = "shipment_package"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    shipment_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(f"{settings.DB_SCHEMA}.shipment.id"),
        nullable=False,
    )
    package_weight: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    package_volume: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())

    shipment: Mapped["Shipment"] = relationship(back_populates="packages")