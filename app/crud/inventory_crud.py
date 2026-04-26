from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.crud import CRUDBase
from app.models.inventory import (
    Inventory,
    InventoryAdjustment,
    InventoryReservation,
    InventoryTransaction,
    WarehouseStock,
)
from app.schemas.inventory import (
    InventoryAdjustmentCreate,
    InventoryAdjustmentRead,
    InventoryCreate,
    InventoryReservationCreate,
    InventoryReservationRead,
    InventoryReservationUpdate,
    InventoryTransactionCreate,
    InventoryTransactionRead,
    InventoryUpdate,
    WarehouseStockCreate,
    WarehouseStockRead,
)


class InventoryCRUD(CRUDBase[Inventory]):
    """재고 CRUD 연산을 담당한다."""

    def __init__(self) -> None:
        super().__init__(Inventory)

    def create(self, db: Session, obj_in: InventoryCreate) -> Inventory:
        """재고를 생성한다."""
        create_data = obj_in.model_dump(exclude_unset=True)
        db_obj = Inventory(**create_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get(self, db: Session, object_id: int) -> Optional[Inventory]:
        """재고를 ID로 조회한다."""
        return db.get(Inventory, object_id)

    def get_by_sku_id(
        self,
        db: Session,
        sku_id: int,
    ) -> Optional[Inventory]:
        """재고를 SKU ID로 조회한다."""
        stmt = select(Inventory).where(Inventory.sku_id == sku_id)
        return db.scalar(stmt)

    def get_multi(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Inventory]:
        """재고 목록을 페이징하여 조회한다."""
        stmt = (
            select(Inventory)
            .offset(skip)
            .limit(limit)
            .order_by(Inventory.id)
        )
        return list(db.scalars(stmt).all())

    def update(
        self,
        db: Session,
        db_obj: Inventory,
        obj_in: InventoryUpdate,
    ) -> Inventory:
        """재고 정보를 수정한다."""
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, object_id: int) -> Optional[Inventory]:
        """재고를 삭제한다."""
        db_obj = db.get(Inventory, object_id)
        if db_obj is None:
            return None
        db.delete(db_obj)
        db.commit()
        return db_obj


class InventoryReservationCRUD(CRUDBase[InventoryReservation]):
    """재고 예약 CRUD 연산을 담당한다."""

    def __init__(self) -> None:
        super().__init__(InventoryReservation)

    def create(
        self,
        db: Session,
        obj_in: InventoryReservationCreate,
    ) -> InventoryReservation:
        """재고 예약을 생성한다."""
        create_data = obj_in.model_dump(exclude_unset=True)
        db_obj = InventoryReservation(**create_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get(
        self,
        db: Session,
        object_id: int,
    ) -> Optional[InventoryReservation]:
        """재고 예약을 ID로 조회한다."""
        return db.get(InventoryReservation, object_id)

    def get_by_order_id(
        self,
        db: Session,
        order_id: int,
    ) -> list[InventoryReservation]:
        """주문의 재고 예약 목록을 조회한다."""
        stmt = (
            select(InventoryReservation)
            .where(InventoryReservation.order_id == order_id)
            .order_by(InventoryReservation.id)
        )
        return list(db.scalars(stmt).all())

    def get_by_sku_id(
        self,
        db: Session,
        sku_id: int,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[InventoryReservation]:
        """SKU의 재고 예약 목록을 조회한다."""
        stmt = (
            select(InventoryReservation)
            .where(InventoryReservation.sku_id == sku_id)
            .offset(skip)
            .limit(limit)
            .order_by(InventoryReservation.id)
        )
        return list(db.scalars(stmt).all())

    def get_by_status(
        self,
        db: Session,
        status: str,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[InventoryReservation]:
        """재고 예약 목록을 상태별로 조회한다."""
        stmt = (
            select(InventoryReservation)
            .where(InventoryReservation.reservation_status == status)
            .offset(skip)
            .limit(limit)
            .order_by(InventoryReservation.id)
        )
        return list(db.scalars(stmt).all())

    def get_multi(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[InventoryReservation]:
        """재고 예약 목록을 페이징하여 조회한다."""
        stmt = (
            select(InventoryReservation)
            .offset(skip)
            .limit(limit)
            .order_by(InventoryReservation.id)
        )
        return list(db.scalars(stmt).all())

    def update(
        self,
        db: Session,
        db_obj: InventoryReservation,
        obj_in: InventoryReservationUpdate,
    ) -> InventoryReservation:
        """재고 예약을 수정한다."""
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(
        self,
        db: Session,
        object_id: int,
    ) -> Optional[InventoryReservation]:
        """재고 예약을 삭제한다."""
        db_obj = db.get(InventoryReservation, object_id)
        if db_obj is None:
            return None
        db.delete(db_obj)
        db.commit()
        return db_obj


class InventoryTransactionCRUD(CRUDBase[InventoryTransaction]):
    """재고 변동 이력 CRUD 연산을 담당한다."""

    def __init__(self) -> None:
        super().__init__(InventoryTransaction)

    def create(
        self,
        db: Session,
        obj_in: InventoryTransactionCreate,
    ) -> InventoryTransaction:
        """재고 변동 이력을 생성한다."""
        create_data = obj_in.model_dump(exclude_unset=True)
        db_obj = InventoryTransaction(**create_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get(
        self,
        db: Session,
        object_id: int,
    ) -> Optional[InventoryTransaction]:
        """재고 변동 이력을 ID로 조회한다."""
        return db.get(InventoryTransaction, object_id)

    def get_by_sku_id(
        self,
        db: Session,
        sku_id: int,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[InventoryTransaction]:
        """SKU의 재고 변동 이력 목록을 조회한다."""
        stmt = (
            select(InventoryTransaction)
            .where(InventoryTransaction.sku_id == sku_id)
            .offset(skip)
            .limit(limit)
            .order_by(InventoryTransaction.created_at.desc())
        )
        return list(db.scalars(stmt).all())

    def get_multi(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[InventoryTransaction]:
        """재고 변동 이력 목록을 페이징하여 조회한다."""
        stmt = (
            select(InventoryTransaction)
            .offset(skip)
            .limit(limit)
            .order_by(InventoryTransaction.id)
        )
        return list(db.scalars(stmt).all())

    def remove(
        self,
        db: Session,
        object_id: int,
    ) -> Optional[InventoryTransaction]:
        """재고 변동 이력을 삭제한다."""
        db_obj = db.get(InventoryTransaction, object_id)
        if db_obj is None:
            return None
        db.delete(db_obj)
        db.commit()
        return db_obj


class WarehouseStockCRUD(CRUDBase[WarehouseStock]):
    """창고 재고 CRUD 연산을 담당한다."""

    def __init__(self) -> None:
        super().__init__(WarehouseStock)

    def create(
        self,
        db: Session,
        obj_in: WarehouseStockCreate,
    ) -> WarehouseStock:
        """창고 재고를 생성한다."""
        create_data = obj_in.model_dump(exclude_unset=True)
        db_obj = WarehouseStock(**create_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get(self, db: Session, object_id: int) -> Optional[WarehouseStock]:
        """창고 재고를 ID로 조회한다."""
        return db.get(WarehouseStock, object_id)

    def get_by_sku_id(
        self,
        db: Session,
        sku_id: int,
    ) -> list[WarehouseStock]:
        """SKU의 창고 재고 목록을 조회한다."""
        stmt = (
            select(WarehouseStock)
            .where(WarehouseStock.sku_id == sku_id)
            .order_by(WarehouseStock.id)
        )
        return list(db.scalars(stmt).all())

    def get_by_warehouse_id(
        self,
        db: Session,
        warehouse_id: int,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[WarehouseStock]:
        """창고의 재고 목록을 조회한다."""
        stmt = (
            select(WarehouseStock)
            .where(WarehouseStock.warehouse_id == warehouse_id)
            .offset(skip)
            .limit(limit)
            .order_by(WarehouseStock.id)
        )
        return list(db.scalars(stmt).all())

    def get_multi(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[WarehouseStock]:
        """창고 재고 목록을 페이징하여 조회한다."""
        stmt = (
            select(WarehouseStock)
            .offset(skip)
            .limit(limit)
            .order_by(WarehouseStock.id)
        )
        return list(db.scalars(stmt).all())

    def update(
        self,
        db: Session,
        db_obj: WarehouseStock,
        obj_in: WarehouseStockCreate,
    ) -> WarehouseStock:
        """창고 재고를 수정한다."""
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, object_id: int) -> Optional[WarehouseStock]:
        """창고 재고를 삭제한다."""
        db_obj = db.get(WarehouseStock, object_id)
        if db_obj is None:
            return None
        db.delete(db_obj)
        db.commit()
        return db_obj


class InventoryAdjustmentCRUD(CRUDBase[InventoryAdjustment]):
    """재고 조정 이력 CRUD 연산을 담당한다."""

    def __init__(self) -> None:
        super().__init__(InventoryAdjustment)

    def create(
        self,
        db: Session,
        obj_in: InventoryAdjustmentCreate,
    ) -> InventoryAdjustment:
        """재고 조정 이력을 생성한다."""
        create_data = obj_in.model_dump(exclude_unset=True)
        db_obj = InventoryAdjustment(**create_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get(
        self,
        db: Session,
        object_id: int,
    ) -> Optional[InventoryAdjustment]:
        """재고 조정 이력을 ID로 조회한다."""
        return db.get(InventoryAdjustment, object_id)

    def get_by_sku_id(
        self,
        db: Session,
        sku_id: int,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[InventoryAdjustment]:
        """SKU의 재고 조정 이력 목록을 조회한다."""
        stmt = (
            select(InventoryAdjustment)
            .where(InventoryAdjustment.sku_id == sku_id)
            .offset(skip)
            .limit(limit)
            .order_by(InventoryAdjustment.created_at.desc())
        )
        return list(db.scalars(stmt).all())

    def get_multi(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[InventoryAdjustment]:
        """재고 조정 이력 목록을 페이징하여 조회한다."""
        stmt = (
            select(InventoryAdjustment)
            .offset(skip)
            .limit(limit)
            .order_by(InventoryAdjustment.id)
        )
        return list(db.scalars(stmt).all())

    def remove(
        self,
        db: Session,
        object_id: int,
    ) -> Optional[InventoryAdjustment]:
        """재고 조정 이력을 삭제한다."""
        db_obj = db.get(InventoryAdjustment, object_id)
        if db_obj is None:
            return None
        db.delete(db_obj)
        db.commit()
        return db_obj


inventory_crud = InventoryCRUD()
inventory_reservation_crud = InventoryReservationCRUD()
inventory_transaction_crud = InventoryTransactionCRUD()
warehouse_stock_crud = WarehouseStockCRUD()
inventory_adjustment_crud = InventoryAdjustmentCRUD()


__all__ = [
    "InventoryCRUD",
    "InventoryReservationCRUD",
    "InventoryTransactionCRUD",
    "WarehouseStockCRUD",
    "InventoryAdjustmentCRUD",
    "inventory_crud",
    "inventory_reservation_crud",
    "inventory_transaction_crud",
    "warehouse_stock_crud",
    "inventory_adjustment_crud",
]
