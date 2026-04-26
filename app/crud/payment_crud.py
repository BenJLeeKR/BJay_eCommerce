from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.crud import CRUDBase
from app.models.payment import (
    Payment,
    PaymentLog,
    PaymentMethod,
    PaymentRefund,
    PaymentTransaction,
)
from app.schemas.payment import (
    PaymentCreate,
    PaymentLogCreate,
    PaymentLogRead,
    PaymentMethodCreate,
    PaymentMethodRead,
    PaymentMethodUpdate,
    PaymentRefundCreate,
    PaymentRefundRead,
    PaymentRefundUpdate,
    PaymentTransactionCreate,
    PaymentTransactionRead,
    PaymentTransactionUpdate,
    PaymentUpdate,
)


class PaymentCRUD(CRUDBase[Payment]):
    """결제 CRUD 연산을 담당한다."""

    def __init__(self) -> None:
        super().__init__(Payment)

    def create(self, db: Session, obj_in: PaymentCreate) -> Payment:
        """결제를 생성한다."""
        create_data = obj_in.model_dump(exclude_unset=True)
        db_obj = Payment(**create_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get(self, db: Session, object_id: int) -> Optional[Payment]:
        """결제를 ID로 조회한다."""
        return db.get(Payment, object_id)

    def get_by_order_id(
        self,
        db: Session,
        order_id: int,
    ) -> list[Payment]:
        """주문의 결제 목록을 조회한다."""
        stmt = (
            select(Payment)
            .where(Payment.order_id == order_id)
            .where(Payment.deleted_at.is_(None))
            .order_by(Payment.id)
        )
        return list(db.scalars(stmt).all())

    def get_by_idempotency_key(
        self,
        db: Session,
        idempotency_key: str,
    ) -> Optional[Payment]:
        """멱등성 키로 결제를 조회한다."""
        stmt = select(Payment).where(
            Payment.idempotency_key == idempotency_key,
        )
        return db.scalar(stmt)

    def get_by_status(
        self,
        db: Session,
        status: str,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Payment]:
        """결제 목록을 상태별로 조회한다."""
        stmt = (
            select(Payment)
            .where(Payment.payment_status == status)
            .where(Payment.deleted_at.is_(None))
            .offset(skip)
            .limit(limit)
            .order_by(Payment.id)
        )
        return list(db.scalars(stmt).all())

    def get_multi(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Payment]:
        """결제 목록을 페이징하여 조회한다."""
        stmt = (
            select(Payment)
            .where(Payment.deleted_at.is_(None))
            .offset(skip)
            .limit(limit)
            .order_by(Payment.id)
        )
        return list(db.scalars(stmt).all())

    def update(
        self,
        db: Session,
        db_obj: Payment,
        obj_in: PaymentUpdate,
    ) -> Payment:
        """결제 정보를 수정한다."""
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, object_id: int) -> Optional[Payment]:
        """결제를 소프트 삭제한다."""
        db_obj = db.get(Payment, object_id)
        if db_obj is None:
            return None
        from datetime import datetime, timezone

        db_obj.deleted_at = datetime.now(timezone.utc)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj


class PaymentTransactionCRUD(CRUDBase[PaymentTransaction]):
    """결제 트랜잭션 CRUD 연산을 담당한다."""

    def __init__(self) -> None:
        super().__init__(PaymentTransaction)

    def create(
        self,
        db: Session,
        obj_in: PaymentTransactionCreate,
    ) -> PaymentTransaction:
        """결제 트랜잭션을 생성한다."""
        create_data = obj_in.model_dump(exclude_unset=True)
        db_obj = PaymentTransaction(**create_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get(
        self,
        db: Session,
        object_id: int,
    ) -> Optional[PaymentTransaction]:
        """결제 트랜잭션을 ID로 조회한다."""
        return db.get(PaymentTransaction, object_id)

    def get_by_payment_id(
        self,
        db: Session,
        payment_id: int,
    ) -> list[PaymentTransaction]:
        """결제의 트랜잭션 목록을 조회한다."""
        stmt = (
            select(PaymentTransaction)
            .where(PaymentTransaction.payment_id == payment_id)
            .order_by(PaymentTransaction.id)
        )
        return list(db.scalars(stmt).all())

    def get_by_pg_transaction_id(
        self,
        db: Session,
        pg_transaction_id: str,
    ) -> Optional[PaymentTransaction]:
        """PG 트랜잭션 ID로 조회한다."""
        stmt = select(PaymentTransaction).where(
            PaymentTransaction.pg_transaction_id == pg_transaction_id,
        )
        return db.scalar(stmt)

    def get_multi(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[PaymentTransaction]:
        """결제 트랜잭션 목록을 페이징하여 조회한다."""
        stmt = (
            select(PaymentTransaction)
            .offset(skip)
            .limit(limit)
            .order_by(PaymentTransaction.id)
        )
        return list(db.scalars(stmt).all())

    def update(
        self,
        db: Session,
        db_obj: PaymentTransaction,
        obj_in: PaymentTransactionUpdate,
    ) -> PaymentTransaction:
        """결제 트랜잭션을 수정한다."""
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
    ) -> Optional[PaymentTransaction]:
        """결제 트랜잭션을 삭제한다."""
        db_obj = db.get(PaymentTransaction, object_id)
        if db_obj is None:
            return None
        db.delete(db_obj)
        db.commit()
        return db_obj


class PaymentMethodCRUD(CRUDBase[PaymentMethod]):
    """결제 수단 CRUD 연산을 담당한다."""

    def __init__(self) -> None:
        super().__init__(PaymentMethod)

    def create(
        self,
        db: Session,
        obj_in: PaymentMethodCreate,
    ) -> PaymentMethod:
        """결제 수단을 생성한다."""
        create_data = obj_in.model_dump(exclude_unset=True)
        db_obj = PaymentMethod(**create_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get(self, db: Session, object_id: int) -> Optional[PaymentMethod]:
        """결제 수단을 ID로 조회한다."""
        return db.get(PaymentMethod, object_id)

    def get_by_user_id(
        self,
        db: Session,
        user_id: int,
    ) -> list[PaymentMethod]:
        """사용자의 결제 수단 목록을 조회한다."""
        stmt = (
            select(PaymentMethod)
            .where(PaymentMethod.user_id == user_id)
            .where(PaymentMethod.deleted_at.is_(None))
            .order_by(PaymentMethod.id)
        )
        return list(db.scalars(stmt).all())

    def get_default_by_user_id(
        self,
        db: Session,
        user_id: int,
    ) -> Optional[PaymentMethod]:
        """사용자의 기본 결제 수단을 조회한다."""
        stmt = (
            select(PaymentMethod)
            .where(PaymentMethod.user_id == user_id)
            .where(PaymentMethod.is_default.is_(True))
            .where(PaymentMethod.deleted_at.is_(None))
        )
        return db.scalar(stmt)

    def get_multi(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[PaymentMethod]:
        """결제 수단 목록을 페이징하여 조회한다."""
        stmt = (
            select(PaymentMethod)
            .where(PaymentMethod.deleted_at.is_(None))
            .offset(skip)
            .limit(limit)
            .order_by(PaymentMethod.id)
        )
        return list(db.scalars(stmt).all())

    def update(
        self,
        db: Session,
        db_obj: PaymentMethod,
        obj_in: PaymentMethodUpdate,
    ) -> PaymentMethod:
        """결제 수단을 수정한다."""
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, object_id: int) -> Optional[PaymentMethod]:
        """결제 수단을 소프트 삭제한다."""
        db_obj = db.get(PaymentMethod, object_id)
        if db_obj is None:
            return None
        from datetime import datetime, timezone

        db_obj.deleted_at = datetime.now(timezone.utc)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj


class PaymentRefundCRUD(CRUDBase[PaymentRefund]):
    """결제 환불 CRUD 연산을 담당한다."""

    def __init__(self) -> None:
        super().__init__(PaymentRefund)

    def create(
        self,
        db: Session,
        obj_in: PaymentRefundCreate,
    ) -> PaymentRefund:
        """결제 환불을 생성한다."""
        create_data = obj_in.model_dump(exclude_unset=True)
        db_obj = PaymentRefund(**create_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get(self, db: Session, object_id: int) -> Optional[PaymentRefund]:
        """결제 환불을 ID로 조회한다."""
        return db.get(PaymentRefund, object_id)

    def get_by_payment_id(
        self,
        db: Session,
        payment_id: int,
    ) -> list[PaymentRefund]:
        """결제의 환불 목록을 조회한다."""
        stmt = (
            select(PaymentRefund)
            .where(PaymentRefund.payment_id == payment_id)
            .order_by(PaymentRefund.id)
        )
        return list(db.scalars(stmt).all())

    def get_by_status(
        self,
        db: Session,
        status: str,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[PaymentRefund]:
        """환불 목록을 상태별로 조회한다."""
        stmt = (
            select(PaymentRefund)
            .where(PaymentRefund.refund_status == status)
            .offset(skip)
            .limit(limit)
            .order_by(PaymentRefund.id)
        )
        return list(db.scalars(stmt).all())

    def get_multi(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[PaymentRefund]:
        """결제 환불 목록을 페이징하여 조회한다."""
        stmt = (
            select(PaymentRefund)
            .offset(skip)
            .limit(limit)
            .order_by(PaymentRefund.id)
        )
        return list(db.scalars(stmt).all())

    def update(
        self,
        db: Session,
        db_obj: PaymentRefund,
        obj_in: PaymentRefundUpdate,
    ) -> PaymentRefund:
        """결제 환불을 수정한다."""
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, object_id: int) -> Optional[PaymentRefund]:
        """결제 환불을 삭제한다."""
        db_obj = db.get(PaymentRefund, object_id)
        if db_obj is None:
            return None
        db.delete(db_obj)
        db.commit()
        return db_obj


class PaymentLogCRUD(CRUDBase[PaymentLog]):
    """결제 로그 CRUD 연산을 담당한다."""

    def __init__(self) -> None:
        super().__init__(PaymentLog)

    def create(
        self,
        db: Session,
        obj_in: PaymentLogCreate,
    ) -> PaymentLog:
        """결제 로그를 생성한다."""
        create_data = obj_in.model_dump(exclude_unset=True)
        db_obj = PaymentLog(**create_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get(self, db: Session, object_id: int) -> Optional[PaymentLog]:
        """결제 로그를 ID로 조회한다."""
        return db.get(PaymentLog, object_id)

    def get_by_payment_id(
        self,
        db: Session,
        payment_id: int,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[PaymentLog]:
        """결제의 로그 목록을 조회한다."""
        stmt = (
            select(PaymentLog)
            .where(PaymentLog.payment_id == payment_id)
            .offset(skip)
            .limit(limit)
            .order_by(PaymentLog.id)
        )
        return list(db.scalars(stmt).all())

    def get_multi(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[PaymentLog]:
        """결제 로그 목록을 페이징하여 조회한다."""
        stmt = (
            select(PaymentLog)
            .offset(skip)
            .limit(limit)
            .order_by(PaymentLog.id)
        )
        return list(db.scalars(stmt).all())

    def remove(self, db: Session, object_id: int) -> Optional[PaymentLog]:
        """결제 로그를 삭제한다."""
        db_obj = db.get(PaymentLog, object_id)
        if db_obj is None:
            return None
        db.delete(db_obj)
        db.commit()
        return db_obj


payment_crud = PaymentCRUD()
payment_transaction_crud = PaymentTransactionCRUD()
payment_method_crud = PaymentMethodCRUD()
payment_refund_crud = PaymentRefundCRUD()
payment_log_crud = PaymentLogCRUD()


__all__ = [
    "PaymentCRUD",
    "PaymentTransactionCRUD",
    "PaymentMethodCRUD",
    "PaymentRefundCRUD",
    "PaymentLogCRUD",
    "payment_crud",
    "payment_transaction_crud",
    "payment_method_crud",
    "payment_refund_crud",
    "payment_log_crud",
]
