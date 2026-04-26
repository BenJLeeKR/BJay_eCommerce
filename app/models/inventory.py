from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.config import settings
from app.database import Base


class Inventory(Base):
    """재고 상태를 저장한다."""

    __tablename__ = "inventory"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    sku_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(f"{settings.DB_SCHEMA}.sku.id"),
        nullable=False,
        unique=True,
    )
    total_quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    available_quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    reserved_quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    safety_stock_quantity: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)

    sku: Mapped["SKU"] = relationship(back_populates="inventory")
    reservations: Mapped[list["InventoryReservation"]] = relationship(
        back_populates="inventory",
        primaryjoin="Inventory.sku_id==InventoryReservation.sku_id",
        foreign_keys="InventoryReservation.sku_id",
        cascade="all, delete-orphan",
    )
    transactions: Mapped[list["InventoryTransaction"]] = relationship(
        back_populates="inventory",
        primaryjoin="Inventory.sku_id==InventoryTransaction.sku_id",
        foreign_keys="InventoryTransaction.sku_id",
        cascade="all, delete-orphan",
    )
    warehouse_stocks: Mapped[list["WarehouseStock"]] = relationship(
        back_populates="inventory",
        primaryjoin="Inventory.sku_id==WarehouseStock.sku_id",
        foreign_keys="WarehouseStock.sku_id",
    )
    adjustments: Mapped[list["InventoryAdjustment"]] = relationship(
        back_populates="inventory",
        primaryjoin="Inventory.sku_id==InventoryAdjustment.sku_id",
        foreign_keys="InventoryAdjustment.sku_id",
        cascade="all, delete-orphan",
    )


class InventoryReservation(Base):
    """재고 예약 정보를 저장한다."""

    __tablename__ = "inventory_reservation"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    sku_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(f"{settings.DB_SCHEMA}.sku.id"),
        nullable=False,
    )
    order_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(f"{settings.DB_SCHEMA}.order_header.id"),
        nullable=False,
    )
    reserved_quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    reservation_status: Mapped[str] = mapped_column(String(30), nullable=False)
    expired_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    inventory: Mapped["Inventory"] = relationship(
        back_populates="reservations",
        primaryjoin="Inventory.sku_id==InventoryReservation.sku_id",
        foreign_keys="InventoryReservation.sku_id",
    )
    order: Mapped["OrderHeader"] = relationship(back_populates="inventory_reservations")


class InventoryTransaction(Base):
    """재고 변동 이력을 저장한다."""

    __tablename__ = "inventory_transaction"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    sku_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(f"{settings.DB_SCHEMA}.sku.id"),
        nullable=False,
    )
    transaction_type: Mapped[str] = mapped_column(String(50), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    reference_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    reference_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())

    inventory: Mapped["Inventory"] = relationship(
        back_populates="transactions",
        primaryjoin="Inventory.sku_id==InventoryTransaction.sku_id",
        foreign_keys="InventoryTransaction.sku_id",
    )


class WarehouseStock(Base):
    """창고 재고를 저장한다."""

    __tablename__ = "warehouse_stock"
    __table_args__ = (
        Index("ix_warehouse_stock_warehouse_sku", "warehouse_id", "sku_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    warehouse_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(f"{settings.DB_SCHEMA}.warehouse.id"),
        nullable=False,
    )
    sku_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(f"{settings.DB_SCHEMA}.sku.id"),
        nullable=False,
    )
    stock_quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())

    inventory: Mapped["Inventory"] = relationship(
        back_populates="warehouse_stocks",
        primaryjoin="Inventory.sku_id==WarehouseStock.sku_id",
        foreign_keys="WarehouseStock.sku_id",
    )


class InventoryAdjustment(Base):
    """재고 조정 이력을 저장한다."""

    __tablename__ = "inventory_adjustment"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    sku_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(f"{settings.DB_SCHEMA}.sku.id"),
        nullable=False,
    )
    adjustment_quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    adjustment_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())

    inventory: Mapped["Inventory"] = relationship(
        back_populates="adjustments",
        primaryjoin="Inventory.sku_id==InventoryAdjustment.sku_id",
        foreign_keys="InventoryAdjustment.sku_id",
    )