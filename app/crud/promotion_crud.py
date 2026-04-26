from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.crud import CRUDBase
from app.models.promotion import (
    Coupon,
    CouponIssue,
    CouponUsage,
    Promotion,
    PromotionCondition,
    PromotionTarget,
)
from app.schemas.promotion import (
    CouponCreate,
    CouponIssueCreate,
    CouponIssueRead,
    CouponRead,
    CouponUpdate,
    CouponUsageCreate,
    CouponUsageRead,
    PromotionConditionRead,
    PromotionCreate,
    PromotionTargetRead,
    PromotionUpdate,
)


class PromotionCRUD(CRUDBase[Promotion]):
    """프로모션 CRUD 연산을 담당한다."""

    def __init__(self) -> None:
        super().__init__(Promotion)

    def create(self, db: Session, obj_in: PromotionCreate) -> Promotion:
        """프로모션을 생성한다."""
        create_data = obj_in.model_dump(exclude_unset=True)
        db_obj = Promotion(**create_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get(self, db: Session, object_id: int) -> Optional[Promotion]:
        """프로모션을 ID로 조회한다."""
        return db.get(Promotion, object_id)

    def get_active(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Promotion]:
        """활성화된 프로모션 목록을 조회한다."""
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc)
        stmt = (
            select(Promotion)
            .where(Promotion.is_active.is_(True))
            .where(Promotion.start_at <= now)
            .where(Promotion.end_at >= now)
            .where(Promotion.deleted_at.is_(None))
            .offset(skip)
            .limit(limit)
            .order_by(Promotion.priority.desc())
        )
        return list(db.scalars(stmt).all())

    def get_by_type(
        self,
        db: Session,
        promotion_type: str,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Promotion]:
        """프로모션 목록을 유형별로 조회한다."""
        stmt = (
            select(Promotion)
            .where(Promotion.promotion_type == promotion_type)
            .where(Promotion.deleted_at.is_(None))
            .offset(skip)
            .limit(limit)
            .order_by(Promotion.id)
        )
        return list(db.scalars(stmt).all())

    def get_multi(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Promotion]:
        """프로모션 목록을 페이징하여 조회한다."""
        stmt = (
            select(Promotion)
            .where(Promotion.deleted_at.is_(None))
            .offset(skip)
            .limit(limit)
            .order_by(Promotion.id)
        )
        return list(db.scalars(stmt).all())

    def update(
        self,
        db: Session,
        db_obj: Promotion,
        obj_in: PromotionUpdate,
    ) -> Promotion:
        """프로모션 정보를 수정한다."""
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, object_id: int) -> Optional[Promotion]:
        """프로모션을 소프트 삭제한다."""
        db_obj = db.get(Promotion, object_id)
        if db_obj is None:
            return None
        from datetime import datetime, timezone

        db_obj.deleted_at = datetime.now(timezone.utc)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj


class PromotionConditionCRUD(CRUDBase[PromotionCondition]):
    """프로모션 조건 CRUD 연산을 담당한다."""

    def __init__(self) -> None:
        super().__init__(PromotionCondition)

    def create(
        self,
        db: Session,
        obj_in: PromotionConditionRead,
    ) -> PromotionCondition:
        """프로모션 조건을 생성한다."""
        create_data = obj_in.model_dump(exclude_unset=True)
        db_obj = PromotionCondition(**create_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get(
        self,
        db: Session,
        object_id: int,
    ) -> Optional[PromotionCondition]:
        """프로모션 조건을 ID로 조회한다."""
        return db.get(PromotionCondition, object_id)

    def get_by_promotion_id(
        self,
        db: Session,
        promotion_id: int,
    ) -> list[PromotionCondition]:
        """프로모션의 조건 목록을 조회한다."""
        stmt = (
            select(PromotionCondition)
            .where(PromotionCondition.promotion_id == promotion_id)
            .order_by(PromotionCondition.id)
        )
        return list(db.scalars(stmt).all())

    def get_multi(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[PromotionCondition]:
        """프로모션 조건 목록을 페이징하여 조회한다."""
        stmt = (
            select(PromotionCondition)
            .offset(skip)
            .limit(limit)
            .order_by(PromotionCondition.id)
        )
        return list(db.scalars(stmt).all())

    def remove(
        self,
        db: Session,
        object_id: int,
    ) -> Optional[PromotionCondition]:
        """프로모션 조건을 삭제한다."""
        db_obj = db.get(PromotionCondition, object_id)
        if db_obj is None:
            return None
        db.delete(db_obj)
        db.commit()
        return db_obj


class PromotionTargetCRUD(CRUDBase[PromotionTarget]):
    """프로모션 대상 CRUD 연산을 담당한다."""

    def __init__(self) -> None:
        super().__init__(PromotionTarget)

    def create(
        self,
        db: Session,
        obj_in: PromotionTargetRead,
    ) -> PromotionTarget:
        """프로모션 대상을 생성한다."""
        create_data = obj_in.model_dump(exclude_unset=True)
        db_obj = PromotionTarget(**create_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get(
        self,
        db: Session,
        object_id: int,
    ) -> Optional[PromotionTarget]:
        """프로모션 대상을 ID로 조회한다."""
        return db.get(PromotionTarget, object_id)

    def get_by_promotion_id(
        self,
        db: Session,
        promotion_id: int,
    ) -> list[PromotionTarget]:
        """프로모션의 대상 목록을 조회한다."""
        stmt = (
            select(PromotionTarget)
            .where(PromotionTarget.promotion_id == promotion_id)
            .order_by(PromotionTarget.id)
        )
        return list(db.scalars(stmt).all())

    def get_multi(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[PromotionTarget]:
        """프로모션 대상 목록을 페이징하여 조회한다."""
        stmt = (
            select(PromotionTarget)
            .offset(skip)
            .limit(limit)
            .order_by(PromotionTarget.id)
        )
        return list(db.scalars(stmt).all())

    def remove(
        self,
        db: Session,
        object_id: int,
    ) -> Optional[PromotionTarget]:
        """프로모션 대상을 삭제한다."""
        db_obj = db.get(PromotionTarget, object_id)
        if db_obj is None:
            return None
        db.delete(db_obj)
        db.commit()
        return db_obj


class CouponCRUD(CRUDBase[Coupon]):
    """쿠폰 CRUD 연산을 담당한다."""

    def __init__(self) -> None:
        super().__init__(Coupon)

    def create(self, db: Session, obj_in: CouponCreate) -> Coupon:
        """쿠폰을 생성한다."""
        create_data = obj_in.model_dump(exclude_unset=True)
        db_obj = Coupon(**create_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get(self, db: Session, object_id: int) -> Optional[Coupon]:
        """쿠폰을 ID로 조회한다."""
        return db.get(Coupon, object_id)

    def get_by_code(
        self,
        db: Session,
        coupon_code: str,
    ) -> Optional[Coupon]:
        """쿠폰을 코드로 조회한다."""
        stmt = select(Coupon).where(Coupon.coupon_code == coupon_code)
        return db.scalar(stmt)

    def get_by_promotion_id(
        self,
        db: Session,
        promotion_id: int,
    ) -> list[Coupon]:
        """프로모션의 쿠폰 목록을 조회한다."""
        stmt = (
            select(Coupon)
            .where(Coupon.promotion_id == promotion_id)
            .where(Coupon.deleted_at.is_(None))
            .order_by(Coupon.id)
        )
        return list(db.scalars(stmt).all())

    def get_multi(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Coupon]:
        """쿠폰 목록을 페이징하여 조회한다."""
        stmt = (
            select(Coupon)
            .where(Coupon.deleted_at.is_(None))
            .offset(skip)
            .limit(limit)
            .order_by(Coupon.id)
        )
        return list(db.scalars(stmt).all())

    def update(
        self,
        db: Session,
        db_obj: Coupon,
        obj_in: CouponUpdate,
    ) -> Coupon:
        """쿠폰 정보를 수정한다."""
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, object_id: int) -> Optional[Coupon]:
        """쿠폰을 소프트 삭제한다."""
        db_obj = db.get(Coupon, object_id)
        if db_obj is None:
            return None
        from datetime import datetime, timezone

        db_obj.deleted_at = datetime.now(timezone.utc)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj


class CouponIssueCRUD(CRUDBase[CouponIssue]):
    """쿠폰 발급 CRUD 연산을 담당한다."""

    def __init__(self) -> None:
        super().__init__(CouponIssue)

    def create(
        self,
        db: Session,
        obj_in: CouponIssueCreate,
    ) -> CouponIssue:
        """쿠폰을 발급한다."""
        create_data = obj_in.model_dump(exclude_unset=True)
        db_obj = CouponIssue(**create_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get(self, db: Session, object_id: int) -> Optional[CouponIssue]:
        """쿠폰 발급 내역을 ID로 조회한다."""
        return db.get(CouponIssue, object_id)

    def get_by_coupon_id(
        self,
        db: Session,
        coupon_id: int,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[CouponIssue]:
        """쿠폰의 발급 내역 목록을 조회한다."""
        stmt = (
            select(CouponIssue)
            .where(CouponIssue.coupon_id == coupon_id)
            .offset(skip)
            .limit(limit)
            .order_by(CouponIssue.id)
        )
        return list(db.scalars(stmt).all())

    def get_by_user_id(
        self,
        db: Session,
        user_id: int,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[CouponIssue]:
        """사용자의 쿠폰 발급 내역 목록을 조회한다."""
        stmt = (
            select(CouponIssue)
            .where(CouponIssue.user_id == user_id)
            .offset(skip)
            .limit(limit)
            .order_by(CouponIssue.issued_at.desc())
        )
        return list(db.scalars(stmt).all())

    def get_available_by_user_id(
        self,
        db: Session,
        user_id: int,
    ) -> list[CouponIssue]:
        """사용자가 사용 가능한 쿠폰 목록을 조회한다."""
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc)
        stmt = (
            select(CouponIssue)
            .where(CouponIssue.user_id == user_id)
            .where(CouponIssue.is_used.is_(False))
            .where(
                (CouponIssue.expire_at.is_(None))
                | (CouponIssue.expire_at >= now)
            )
            .order_by(CouponIssue.issued_at.desc())
        )
        return list(db.scalars(stmt).all())

    def get_multi(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[CouponIssue]:
        """쿠폰 발급 내역 목록을 페이징하여 조회한다."""
        stmt = (
            select(CouponIssue)
            .offset(skip)
            .limit(limit)
            .order_by(CouponIssue.id)
        )
        return list(db.scalars(stmt).all())

    def update(
        self,
        db: Session,
        db_obj: CouponIssue,
        obj_in: CouponIssueRead,
    ) -> CouponIssue:
        """쿠폰 발급 내역을 수정한다."""
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def mark_as_used(
        self,
        db: Session,
        issue_id: int,
    ) -> Optional[CouponIssue]:
        """쿠폰을 사용 처리한다."""
        db_obj = db.get(CouponIssue, issue_id)
        if db_obj is None:
            return None
        db_obj.is_used = True
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, object_id: int) -> Optional[CouponIssue]:
        """쿠폰 발급 내역을 삭제한다."""
        db_obj = db.get(CouponIssue, object_id)
        if db_obj is None:
            return None
        db.delete(db_obj)
        db.commit()
        return db_obj


class CouponUsageCRUD(CRUDBase[CouponUsage]):
    """쿠폰 사용 내역 CRUD 연산을 담당한다."""

    def __init__(self) -> None:
        super().__init__(CouponUsage)

    def create(
        self,
        db: Session,
        obj_in: CouponUsageCreate,
    ) -> CouponUsage:
        """쿠폰 사용 내역을 생성한다."""
        create_data = obj_in.model_dump(exclude_unset=True)
        db_obj = CouponUsage(**create_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get(self, db: Session, object_id: int) -> Optional[CouponUsage]:
        """쿠폰 사용 내역을 ID로 조회한다."""
        return db.get(CouponUsage, object_id)

    def get_by_coupon_issue_id(
        self,
        db: Session,
        coupon_issue_id: int,
    ) -> list[CouponUsage]:
        """쿠폰 발급 건의 사용 내역 목록을 조회한다."""
        stmt = (
            select(CouponUsage)
            .where(CouponUsage.coupon_issue_id == coupon_issue_id)
            .order_by(CouponUsage.id)
        )
        return list(db.scalars(stmt).all())

    def get_by_order_id(
        self,
        db: Session,
        order_id: int,
    ) -> list[CouponUsage]:
        """주문의 쿠폰 사용 내역 목록을 조회한다."""
        stmt = (
            select(CouponUsage)
            .where(CouponUsage.order_id == order_id)
            .order_by(CouponUsage.id)
        )
        return list(db.scalars(stmt).all())

    def get_multi(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[CouponUsage]:
        """쿠폰 사용 내역 목록을 페이징하여 조회한다."""
        stmt = (
            select(CouponUsage)
            .offset(skip)
            .limit(limit)
            .order_by(CouponUsage.id)
        )
        return list(db.scalars(stmt).all())

    def remove(
        self,
        db: Session,
        object_id: int,
    ) -> Optional[CouponUsage]:
        """쿠폰 사용 내역을 삭제한다."""
        db_obj = db.get(CouponUsage, object_id)
        if db_obj is None:
            return None
        db.delete(db_obj)
        db.commit()
        return db_obj


promotion_crud = PromotionCRUD()
promotion_condition_crud = PromotionConditionCRUD()
promotion_target_crud = PromotionTargetCRUD()
coupon_crud = CouponCRUD()
coupon_issue_crud = CouponIssueCRUD()
coupon_usage_crud = CouponUsageCRUD()


__all__ = [
    "PromotionCRUD",
    "PromotionConditionCRUD",
    "PromotionTargetCRUD",
    "CouponCRUD",
    "CouponIssueCRUD",
    "CouponUsageCRUD",
    "promotion_crud",
    "promotion_condition_crud",
    "promotion_target_crud",
    "coupon_crud",
    "coupon_issue_crud",
    "coupon_usage_crud",
]
