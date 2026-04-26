from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.crud import CRUDBase
from app.models.order import (
    OrderAddressSnapshot,
    OrderCoupon,
    OrderHeader,
    OrderItem,
    OrderPayment,
    OrderShipment,
    OrderStatusHistory,
)
from app.schemas.order import (
    OrderAddressSnapshotRead,
    OrderCouponRead,
    OrderCreate,
    OrderItemCreate,
    OrderItemRead,
    OrderItemUpdate,
    OrderPaymentRead,
    OrderShipmentRead,
    OrderStatusHistoryRead,
    OrderUpdate,
)


class OrderHeaderCRUD(CRUDBase[OrderHeader]):
    """주문 헤더 CRUD 연산을 담당한다."""

    def __init__(self) -> None:
        super().__init__(OrderHeader)

    def create(self, db: Session, obj_in: OrderCreate) -> OrderHeader:
        """주문을 생성한다."""
        create_data = obj_in.model_dump(exclude_unset=True)
        items_data = create_data.pop("items", [])
        db_obj = OrderHeader(**create_data)
        db.add(db_obj)
        db.flush()
        for item_data in items_data:
            order_item = OrderItem(**item_data)
            db_obj.items.append(order_item)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get(self, db: Session, object_id: int) -> Optional[OrderHeader]:
        """주문을 ID로 조회한다."""
        return db.get(OrderHeader, object_id)

    def get_by_order_number(
        self,
        db: Session,
        order_number: str,
    ) -> Optional[OrderHeader]:
        """주문을 주문번호로 조회한다."""
        stmt = select(OrderHeader).where(
            OrderHeader.order_number == order_number,
        )
        return db.scalar(stmt)

    def get_by_user_id(
        self,
        db: Session,
        user_id: int,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[OrderHeader]:
        """사용자의 주문 목록을 조회한다."""
        stmt = (
            select(OrderHeader)
            .where(OrderHeader.user_id == user_id)
            .where(OrderHeader.deleted_at.is_(None))
            .offset(skip)
            .limit(limit)
            .order_by(OrderHeader.ordered_at.desc())
        )
        return list(db.scalars(stmt).all())

    def get_by_status(
        self,
        db: Session,
        status: str,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[OrderHeader]:
        """주문 목록을 상태별로 조회한다."""
        stmt = (
            select(OrderHeader)
            .where(OrderHeader.order_status == status)
            .where(OrderHeader.deleted_at.is_(None))
            .offset(skip)
            .limit(limit)
            .order_by(OrderHeader.id)
        )
        return list(db.scalars(stmt).all())

    def get_multi(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[OrderHeader]:
        """주문 목록을 페이징하여 조회한다."""
        stmt = (
            select(OrderHeader)
            .where(OrderHeader.deleted_at.is_(None))
            .offset(skip)
            .limit(limit)
            .order_by(OrderHeader.id)
        )
        return list(db.scalars(stmt).all())

    def update(
        self,
        db: Session,
        db_obj: OrderHeader,
        obj_in: OrderUpdate,
    ) -> OrderHeader:
        """주문 정보를 수정한다."""
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, object_id: int) -> Optional[OrderHeader]:
        """주문을 소프트 삭제한다."""
        db_obj = db.get(OrderHeader, object_id)
        if db_obj is None:
            return None
        from datetime import datetime, timezone

        db_obj.deleted_at = datetime.now(timezone.utc)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj


class OrderItemCRUD(CRUDBase[OrderItem]):
    """주문 상품 CRUD 연산을 담당한다."""

    def __init__(self) -> None:
        super().__init__(OrderItem)

    def create(self, db: Session, obj_in: OrderItemCreate) -> OrderItem:
        """주문 상품을 생성한다."""
        create_data = obj_in.model_dump(exclude_unset=True)
        db_obj = OrderItem(**create_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get(self, db: Session, object_id: int) -> Optional[OrderItem]:
        """주문 상품을 ID로 조회한다."""
        return db.get(OrderItem, object_id)

    def get_by_order_id(
        self,
        db: Session,
        order_id: int,
    ) -> list[OrderItem]:
        """주문의 상품 목록을 조회한다."""
        stmt = (
            select(OrderItem)
            .where(OrderItem.order_id == order_id)
            .where(OrderItem.deleted_at.is_(None))
            .order_by(OrderItem.id)
        )
        return list(db.scalars(stmt).all())

    def get_multi(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[OrderItem]:
        """주문 상품 목록을 페이징하여 조회한다."""
        stmt = (
            select(OrderItem)
            .where(OrderItem.deleted_at.is_(None))
            .offset(skip)
            .limit(limit)
            .order_by(OrderItem.id)
        )
        return list(db.scalars(stmt).all())

    def update(
        self,
        db: Session,
        db_obj: OrderItem,
        obj_in: OrderItemUpdate,
    ) -> OrderItem:
        """주문 상품을 수정한다."""
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, object_id: int) -> Optional[OrderItem]:
        """주문 상품을 소프트 삭제한다."""
        db_obj = db.get(OrderItem, object_id)
        if db_obj is None:
            return None
        from datetime import datetime, timezone

        db_obj.deleted_at = datetime.now(timezone.utc)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj


class OrderStatusHistoryCRUD(CRUDBase[OrderStatusHistory]):
    """주문 상태 이력 CRUD 연산을 담당한다."""

    def __init__(self) -> None:
        super().__init__(OrderStatusHistory)

    def create(
        self,
        db: Session,
        obj_in: OrderStatusHistoryRead,
    ) -> OrderStatusHistory:
        """주문 상태 이력을 생성한다."""
        create_data = obj_in.model_dump(exclude_unset=True)
        db_obj = OrderStatusHistory(**create_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get(
        self,
        db: Session,
        object_id: int,
    ) -> Optional[OrderStatusHistory]:
        """주문 상태 이력을 ID로 조회한다."""
        return db.get(OrderStatusHistory, object_id)

    def get_by_order_id(
        self,
        db: Session,
        order_id: int,
    ) -> list[OrderStatusHistory]:
        """주문의 상태 이력 목록을 조회한다."""
        stmt = (
            select(OrderStatusHistory)
            .where(OrderStatusHistory.order_id == order_id)
            .order_by(OrderStatusHistory.changed_at)
        )
        return list(db.scalars(stmt).all())

    def get_multi(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[OrderStatusHistory]:
        """주문 상태 이력 목록을 페이징하여 조회한다."""
        stmt = (
            select(OrderStatusHistory)
            .offset(skip)
            .limit(limit)
            .order_by(OrderStatusHistory.id)
        )
        return list(db.scalars(stmt).all())

    def remove(
        self,
        db: Session,
        object_id: int,
    ) -> Optional[OrderStatusHistory]:
        """주문 상태 이력을 삭제한다."""
        db_obj = db.get(OrderStatusHistory, object_id)
        if db_obj is None:
            return None
        db.delete(db_obj)
        db.commit()
        return db_obj


class OrderPaymentCRUD(CRUDBase[OrderPayment]):
    """주문 결제 CRUD 연산을 담당한다."""

    def __init__(self) -> None:
        super().__init__(OrderPayment)

    def create(
        self,
        db: Session,
        obj_in: OrderPaymentRead,
    ) -> OrderPayment:
        """주문 결제 정보를 생성한다."""
        create_data = obj_in.model_dump(exclude_unset=True)
        db_obj = OrderPayment(**create_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get(self, db: Session, object_id: int) -> Optional[OrderPayment]:
        """주문 결제 정보를 ID로 조회한다."""
        return db.get(OrderPayment, object_id)

    def get_by_order_id(
        self,
        db: Session,
        order_id: int,
    ) -> list[OrderPayment]:
        """주문의 결제 정보 목록을 조회한다."""
        stmt = (
            select(OrderPayment)
            .where(OrderPayment.order_id == order_id)
            .order_by(OrderPayment.id)
        )
        return list(db.scalars(stmt).all())

    def get_multi(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[OrderPayment]:
        """주문 결제 정보 목록을 페이징하여 조회한다."""
        stmt = (
            select(OrderPayment)
            .offset(skip)
            .limit(limit)
            .order_by(OrderPayment.id)
        )
        return list(db.scalars(stmt).all())

    def remove(self, db: Session, object_id: int) -> Optional[OrderPayment]:
        """주문 결제 정보를 삭제한다."""
        db_obj = db.get(OrderPayment, object_id)
        if db_obj is None:
            return None
        db.delete(db_obj)
        db.commit()
        return db_obj


class OrderShipmentCRUD(CRUDBase[OrderShipment]):
    """주문 배송 CRUD 연산을 담당한다."""

    def __init__(self) -> None:
        super().__init__(OrderShipment)

    def create(
        self,
        db: Session,
        obj_in: OrderShipmentRead,
    ) -> OrderShipment:
        """주문 배송 정보를 생성한다."""
        create_data = obj_in.model_dump(exclude_unset=True)
        db_obj = OrderShipment(**create_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get(self, db: Session, object_id: int) -> Optional[OrderShipment]:
        """주문 배송 정보를 ID로 조회한다."""
        return db.get(OrderShipment, object_id)

    def get_by_order_id(
        self,
        db: Session,
        order_id: int,
    ) -> list[OrderShipment]:
        """주문의 배송 정보 목록을 조회한다."""
        stmt = (
            select(OrderShipment)
            .where(OrderShipment.order_id == order_id)
            .order_by(OrderShipment.id)
        )
        return list(db.scalars(stmt).all())

    def get_multi(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[OrderShipment]:
        """주문 배송 정보 목록을 페이징하여 조회한다."""
        stmt = (
            select(OrderShipment)
            .offset(skip)
            .limit(limit)
            .order_by(OrderShipment.id)
        )
        return list(db.scalars(stmt).all())

    def remove(self, db: Session, object_id: int) -> Optional[OrderShipment]:
        """주문 배송 정보를 삭제한다."""
        db_obj = db.get(OrderShipment, object_id)
        if db_obj is None:
            return None
        db.delete(db_obj)
        db.commit()
        return db_obj


class OrderAddressSnapshotCRUD(CRUDBase[OrderAddressSnapshot]):
    """주문 배송지 스냅샷 CRUD 연산을 담당한다."""

    def __init__(self) -> None:
        super().__init__(OrderAddressSnapshot)

    def create(
        self,
        db: Session,
        obj_in: OrderAddressSnapshotRead,
    ) -> OrderAddressSnapshot:
        """주문 배송지 스냅샷을 생성한다."""
        create_data = obj_in.model_dump(exclude_unset=True)
        db_obj = OrderAddressSnapshot(**create_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get(
        self,
        db: Session,
        object_id: int,
    ) -> Optional[OrderAddressSnapshot]:
        """주문 배송지 스냅샷을 ID로 조회한다."""
        return db.get(OrderAddressSnapshot, object_id)

    def get_by_order_id(
        self,
        db: Session,
        order_id: int,
    ) -> list[OrderAddressSnapshot]:
        """주문의 배송지 스냅샷 목록을 조회한다."""
        stmt = (
            select(OrderAddressSnapshot)
            .where(OrderAddressSnapshot.order_id == order_id)
            .order_by(OrderAddressSnapshot.id)
        )
        return list(db.scalars(stmt).all())

    def get_multi(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[OrderAddressSnapshot]:
        """주문 배송지 스냅샷 목록을 페이징하여 조회한다."""
        stmt = (
            select(OrderAddressSnapshot)
            .offset(skip)
            .limit(limit)
            .order_by(OrderAddressSnapshot.id)
        )
        return list(db.scalars(stmt).all())

    def remove(
        self,
        db: Session,
        object_id: int,
    ) -> Optional[OrderAddressSnapshot]:
        """주문 배송지 스냅샷을 삭제한다."""
        db_obj = db.get(OrderAddressSnapshot, object_id)
        if db_obj is None:
            return None
        db.delete(db_obj)
        db.commit()
        return db_obj


class OrderCouponCRUD(CRUDBase[OrderCoupon]):
    """주문 쿠폰 CRUD 연산을 담당한다."""

    def __init__(self) -> None:
        super().__init__(OrderCoupon)

    def create(
        self,
        db: Session,
        obj_in: OrderCouponRead,
    ) -> OrderCoupon:
        """주문 쿠폰을 생성한다."""
        create_data = obj_in.model_dump(exclude_unset=True)
        db_obj = OrderCoupon(**create_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get(self, db: Session, object_id: int) -> Optional[OrderCoupon]:
        """주문 쿠폰을 ID로 조회한다."""
        return db.get(OrderCoupon, object_id)

    def get_by_order_id(
        self,
        db: Session,
        order_id: int,
    ) -> list[OrderCoupon]:
        """주문의 쿠폰 목록을 조회한다."""
        stmt = (
            select(OrderCoupon)
            .where(OrderCoupon.order_id == order_id)
            .order_by(OrderCoupon.id)
        )
        return list(db.scalars(stmt).all())

    def get_multi(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[OrderCoupon]:
        """주문 쿠폰 목록을 페이징하여 조회한다."""
        stmt = (
            select(OrderCoupon)
            .offset(skip)
            .limit(limit)
            .order_by(OrderCoupon.id)
        )
        return list(db.scalars(stmt).all())

    def remove(self, db: Session, object_id: int) -> Optional[OrderCoupon]:
        """주문 쿠폰을 삭제한다."""
        db_obj = db.get(OrderCoupon, object_id)
        if db_obj is None:
            return None
        db.delete(db_obj)
        db.commit()
        return db_obj


order_header_crud = OrderHeaderCRUD()
order_item_crud = OrderItemCRUD()
order_status_history_crud = OrderStatusHistoryCRUD()
order_payment_crud = OrderPaymentCRUD()
order_shipment_crud = OrderShipmentCRUD()
order_address_snapshot_crud = OrderAddressSnapshotCRUD()
order_coupon_crud = OrderCouponCRUD()


__all__ = [
    "OrderHeaderCRUD",
    "OrderItemCRUD",
    "OrderStatusHistoryCRUD",
    "OrderPaymentCRUD",
    "OrderShipmentCRUD",
    "OrderAddressSnapshotCRUD",
    "OrderCouponCRUD",
    "order_header_crud",
    "order_item_crud",
    "order_status_history_crud",
    "order_payment_crud",
    "order_shipment_crud",
    "order_address_snapshot_crud",
    "order_coupon_crud",
]
