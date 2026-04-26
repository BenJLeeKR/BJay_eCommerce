from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.crud import CRUDBase
from app.models.shipment import (
    Shipment,
    ShipmentItem,
    ShipmentPackage,
    ShipmentStatusHistory,
    ShipmentTracking,
    Warehouse,
)
from app.schemas.shipment import (
    ShipmentCreate,
    ShipmentItemCreate,
    ShipmentItemRead,
    ShipmentItemUpdate,
    ShipmentPackageCreate,
    ShipmentPackageRead,
    ShipmentPackageUpdate,
    ShipmentStatusHistoryCreate,
    ShipmentStatusHistoryRead,
    ShipmentStatusHistoryUpdate,
    ShipmentTrackingCreate,
    ShipmentTrackingRead,
    ShipmentTrackingUpdate,
    ShipmentUpdate,
    WarehouseCreate,
    WarehouseRead,
    WarehouseUpdate,
)


class ShipmentCRUD(CRUDBase[Shipment]):
    """배송 CRUD 연산을 담당한다."""

    def __init__(self) -> None:
        super().__init__(Shipment)

    def create(self, db: Session, obj_in: ShipmentCreate) -> Shipment:
        """배송을 생성한다."""
        create_data = obj_in.model_dump(exclude_unset=True)
        db_obj = Shipment(**create_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get(self, db: Session, object_id: int) -> Optional[Shipment]:
        """배송을 ID로 조회한다."""
        return db.get(Shipment, object_id)

    def get_by_order_id(
        self,
        db: Session,
        order_id: int,
    ) -> list[Shipment]:
        """주문의 배송 목록을 조회한다."""
        stmt = (
            select(Shipment)
            .where(Shipment.order_id == order_id)
            .where(Shipment.deleted_at.is_(None))
            .order_by(Shipment.id)
        )
        return list(db.scalars(stmt).all())

    def get_by_status(
        self,
        db: Session,
        status: str,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Shipment]:
        """배송 목록을 상태별로 조회한다."""
        stmt = (
            select(Shipment)
            .where(Shipment.shipment_status == status)
            .where(Shipment.deleted_at.is_(None))
            .offset(skip)
            .limit(limit)
            .order_by(Shipment.id)
        )
        return list(db.scalars(stmt).all())

    def get_multi(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Shipment]:
        """배송 목록을 페이징하여 조회한다."""
        stmt = (
            select(Shipment)
            .where(Shipment.deleted_at.is_(None))
            .offset(skip)
            .limit(limit)
            .order_by(Shipment.id)
        )
        return list(db.scalars(stmt).all())

    def update(
        self,
        db: Session,
        db_obj: Shipment,
        obj_in: ShipmentUpdate,
    ) -> Shipment:
        """배송 정보를 수정한다."""
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, object_id: int) -> Optional[Shipment]:
        """배송을 소프트 삭제한다."""
        db_obj = db.get(Shipment, object_id)
        if db_obj is None:
            return None
        from datetime import datetime, timezone

        db_obj.deleted_at = datetime.now(timezone.utc)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj


class ShipmentItemCRUD(CRUDBase[ShipmentItem]):
    """배송 상품 CRUD 연산을 담당한다."""

    def __init__(self) -> None:
        super().__init__(ShipmentItem)

    def create(
        self,
        db: Session,
        obj_in: ShipmentItemCreate,
    ) -> ShipmentItem:
        """배송 상품을 생성한다."""
        create_data = obj_in.model_dump(exclude_unset=True)
        db_obj = ShipmentItem(**create_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get(self, db: Session, object_id: int) -> Optional[ShipmentItem]:
        """배송 상품을 ID로 조회한다."""
        return db.get(ShipmentItem, object_id)

    def get_by_shipment_id(
        self,
        db: Session,
        shipment_id: int,
    ) -> list[ShipmentItem]:
        """배송의 상품 목록을 조회한다."""
        stmt = (
            select(ShipmentItem)
            .where(ShipmentItem.shipment_id == shipment_id)
            .where(ShipmentItem.deleted_at.is_(None))
            .order_by(ShipmentItem.id)
        )
        return list(db.scalars(stmt).all())

    def get_by_order_item_id(
        self,
        db: Session,
        order_item_id: int,
    ) -> list[ShipmentItem]:
        """주문 상품의 배송 상품 목록을 조회한다."""
        stmt = (
            select(ShipmentItem)
            .where(ShipmentItem.order_item_id == order_item_id)
            .where(ShipmentItem.deleted_at.is_(None))
            .order_by(ShipmentItem.id)
        )
        return list(db.scalars(stmt).all())

    def get_multi(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[ShipmentItem]:
        """배송 상품 목록을 페이징하여 조회한다."""
        stmt = (
            select(ShipmentItem)
            .where(ShipmentItem.deleted_at.is_(None))
            .offset(skip)
            .limit(limit)
            .order_by(ShipmentItem.id)
        )
        return list(db.scalars(stmt).all())

    def update(
        self,
        db: Session,
        db_obj: ShipmentItem,
        obj_in: ShipmentItemUpdate,
    ) -> ShipmentItem:
        """배송 상품을 수정한다."""
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, object_id: int) -> Optional[ShipmentItem]:
        """배송 상품을 소프트 삭제한다."""
        db_obj = db.get(ShipmentItem, object_id)
        if db_obj is None:
            return None
        from datetime import datetime, timezone

        db_obj.deleted_at = datetime.now(timezone.utc)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj


class ShipmentTrackingCRUD(CRUDBase[ShipmentTracking]):
    """배송 추적 CRUD 연산을 담당한다."""

    def __init__(self) -> None:
        super().__init__(ShipmentTracking)

    def create(
        self,
        db: Session,
        obj_in: ShipmentTrackingCreate,
    ) -> ShipmentTracking:
        """배송 추적 정보를 생성한다."""
        create_data = obj_in.model_dump(exclude_unset=True)
        db_obj = ShipmentTracking(**create_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get(
        self,
        db: Session,
        object_id: int,
    ) -> Optional[ShipmentTracking]:
        """배송 추적 정보를 ID로 조회한다."""
        return db.get(ShipmentTracking, object_id)

    def get_by_shipment_id(
        self,
        db: Session,
        shipment_id: int,
    ) -> list[ShipmentTracking]:
        """배송의 추적 정보 목록을 조회한다."""
        stmt = (
            select(ShipmentTracking)
            .where(ShipmentTracking.shipment_id == shipment_id)
            .order_by(ShipmentTracking.id)
        )
        return list(db.scalars(stmt).all())

    def get_multi(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[ShipmentTracking]:
        """배송 추적 정보 목록을 페이징하여 조회한다."""
        stmt = (
            select(ShipmentTracking)
            .offset(skip)
            .limit(limit)
            .order_by(ShipmentTracking.id)
        )
        return list(db.scalars(stmt).all())

    def update(
        self,
        db: Session,
        db_obj: ShipmentTracking,
        obj_in: ShipmentTrackingUpdate,
    ) -> ShipmentTracking:
        """배송 추적 정보를 수정한다."""
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
    ) -> Optional[ShipmentTracking]:
        """배송 추적 정보를 삭제한다."""
        db_obj = db.get(ShipmentTracking, object_id)
        if db_obj is None:
            return None
        db.delete(db_obj)
        db.commit()
        return db_obj


class ShipmentStatusHistoryCRUD(CRUDBase[ShipmentStatusHistory]):
    """배송 상태 이력 CRUD 연산을 담당한다."""

    def __init__(self) -> None:
        super().__init__(ShipmentStatusHistory)

    def create(
        self,
        db: Session,
        obj_in: ShipmentStatusHistoryCreate,
    ) -> ShipmentStatusHistory:
        """배송 상태 이력을 생성한다."""
        create_data = obj_in.model_dump(exclude_unset=True)
        db_obj = ShipmentStatusHistory(**create_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get(
        self,
        db: Session,
        object_id: int,
    ) -> Optional[ShipmentStatusHistory]:
        """배송 상태 이력을 ID로 조회한다."""
        return db.get(ShipmentStatusHistory, object_id)

    def get_by_shipment_id(
        self,
        db: Session,
        shipment_id: int,
    ) -> list[ShipmentStatusHistory]:
        """배송의 상태 이력 목록을 조회한다."""
        stmt = (
            select(ShipmentStatusHistory)
            .where(ShipmentStatusHistory.shipment_id == shipment_id)
            .order_by(ShipmentStatusHistory.changed_at)
        )
        return list(db.scalars(stmt).all())

    def get_multi(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[ShipmentStatusHistory]:
        """배송 상태 이력 목록을 페이징하여 조회한다."""
        stmt = (
            select(ShipmentStatusHistory)
            .offset(skip)
            .limit(limit)
            .order_by(ShipmentStatusHistory.id)
        )
        return list(db.scalars(stmt).all())

    def update(
        self,
        db: Session,
        db_obj: ShipmentStatusHistory,
        obj_in: ShipmentStatusHistoryUpdate,
    ) -> ShipmentStatusHistory:
        """배송 상태 이력을 수정한다."""
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
    ) -> Optional[ShipmentStatusHistory]:
        """배송 상태 이력을 삭제한다."""
        db_obj = db.get(ShipmentStatusHistory, object_id)
        if db_obj is None:
            return None
        db.delete(db_obj)
        db.commit()
        return db_obj


class WarehouseCRUD(CRUDBase[Warehouse]):
    """창고 CRUD 연산을 담당한다."""

    def __init__(self) -> None:
        super().__init__(Warehouse)

    def create(self, db: Session, obj_in: WarehouseCreate) -> Warehouse:
        """창고를 생성한다."""
        create_data = obj_in.model_dump(exclude_unset=True)
        db_obj = Warehouse(**create_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get(self, db: Session, object_id: int) -> Optional[Warehouse]:
        """창고를 ID로 조회한다."""
        return db.get(Warehouse, object_id)

    def get_multi(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Warehouse]:
        """창고 목록을 페이징하여 조회한다."""
        stmt = (
            select(Warehouse)
            .offset(skip)
            .limit(limit)
            .order_by(Warehouse.id)
        )
        return list(db.scalars(stmt).all())

    def update(
        self,
        db: Session,
        db_obj: Warehouse,
        obj_in: WarehouseUpdate,
    ) -> Warehouse:
        """창고 정보를 수정한다."""
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, object_id: int) -> Optional[Warehouse]:
        """창고를 삭제한다."""
        db_obj = db.get(Warehouse, object_id)
        if db_obj is None:
            return None
        db.delete(db_obj)
        db.commit()
        return db_obj


class ShipmentPackageCRUD(CRUDBase[ShipmentPackage]):
    """배송 패키지 CRUD 연산을 담당한다."""

    def __init__(self) -> None:
        super().__init__(ShipmentPackage)

    def create(
        self,
        db: Session,
        obj_in: ShipmentPackageCreate,
    ) -> ShipmentPackage:
        """배송 패키지를 생성한다."""
        create_data = obj_in.model_dump(exclude_unset=True)
        db_obj = ShipmentPackage(**create_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get(
        self,
        db: Session,
        object_id: int,
    ) -> Optional[ShipmentPackage]:
        """배송 패키지를 ID로 조회한다."""
        return db.get(ShipmentPackage, object_id)

    def get_by_shipment_id(
        self,
        db: Session,
        shipment_id: int,
    ) -> list[ShipmentPackage]:
        """배송의 패키지 목록을 조회한다."""
        stmt = (
            select(ShipmentPackage)
            .where(ShipmentPackage.shipment_id == shipment_id)
            .order_by(ShipmentPackage.id)
        )
        return list(db.scalars(stmt).all())

    def get_multi(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[ShipmentPackage]:
        """배송 패키지 목록을 페이징하여 조회한다."""
        stmt = (
            select(ShipmentPackage)
            .offset(skip)
            .limit(limit)
            .order_by(ShipmentPackage.id)
        )
        return list(db.scalars(stmt).all())

    def update(
        self,
        db: Session,
        db_obj: ShipmentPackage,
        obj_in: ShipmentPackageUpdate,
    ) -> ShipmentPackage:
        """배송 패키지를 수정한다."""
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
    ) -> Optional[ShipmentPackage]:
        """배송 패키지를 삭제한다."""
        db_obj = db.get(ShipmentPackage, object_id)
        if db_obj is None:
            return None
        db.delete(db_obj)
        db.commit()
        return db_obj


shipment_crud = ShipmentCRUD()
shipment_item_crud = ShipmentItemCRUD()
shipment_tracking_crud = ShipmentTrackingCRUD()
shipment_status_history_crud = ShipmentStatusHistoryCRUD()
warehouse_crud = WarehouseCRUD()
shipment_package_crud = ShipmentPackageCRUD()


__all__ = [
    "ShipmentCRUD",
    "ShipmentItemCRUD",
    "ShipmentTrackingCRUD",
    "ShipmentStatusHistoryCRUD",
    "WarehouseCRUD",
    "ShipmentPackageCRUD",
    "shipment_crud",
    "shipment_item_crud",
    "shipment_tracking_crud",
    "shipment_status_history_crud",
    "warehouse_crud",
    "shipment_package_crud",
]
