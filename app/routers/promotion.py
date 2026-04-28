from __future__ import annotations
from typing import Optional

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.orm import Session, selectinload

from app.dependencies import get_db
from app.models.promotion import Promotion, PromotionCondition, PromotionTarget, Coupon, CouponIssue
from app.schemas import APIResponse, PagedResult
from app.schemas.promotion import PromotionCreate, PromotionRead, PromotionUpdate

router = APIRouter(prefix="/promotions", tags=["Promotions (프로모션)"])


def _promotion_query():
    """프로모션 상세 조회를 위한 기본 쿼리."""
    return (
        select(Promotion)
        .options(
            selectinload(Promotion.conditions),
            selectinload(Promotion.targets),
            selectinload(Promotion.coupons).selectinload(Coupon.issues),
        )
        .where(Promotion.deleted_at.is_(None))
    )


def _get_promotion_or_404(db: Session, promotion_id: int) -> Promotion:
    """프로모션을 조회하거나 404 오류를 발생시킨다."""
    statement = _promotion_query().where(Promotion.id == promotion_id)
    promotion = db.execute(statement).scalar_one_or_none()

    if promotion is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="프로모션을 찾을 수 없습니다.",
        )

    return promotion


@router.get("", response_model=APIResponse[PagedResult[PromotionRead]], summary="프로모션 목록 조회")
def list_promotions(
    skip: int = Query(default=0, ge=0, description="건너뛸 레코드 수"),
    limit: int = Query(default=20, ge=1, le=100, description="페이지당 최대 아이템 수"),
    is_active: Optional[bool] = Query(default=None, description="활성 상태 필터"),
    promotion_type: Optional[str] = Query(default=None, max_length=50, description="프로모션 유형 필터"),
    db: Session = Depends(get_db),
) -> APIResponse[PagedResult[PromotionRead]]:
    """프로모션 목록을 상태와 페이징 조건으로 조회한다."""
    base_query = _promotion_query()

    if is_active is not None:
        base_query = base_query.where(Promotion.is_active == is_active)
    if promotion_type is not None:
        base_query = base_query.where(Promotion.promotion_type == promotion_type)

    total_count = db.execute(select(func.count()).select_from(base_query.subquery())).scalar_one()
    promotions = db.execute(base_query.offset(skip).limit(limit)).scalars().unique().all()
    return APIResponse(
        data=PagedResult[PromotionRead](
            items=promotions,
            total_count=total_count,
            skip=skip,
            limit=limit,
        ),
        message="프로모션 목록을 조회했습니다.",
    )


@router.get("/{promotion_id}", response_model=APIResponse[PromotionRead], summary="프로모션 상세 조회")
def get_promotion(promotion_id: int, db: Session = Depends(get_db)) -> APIResponse[PromotionRead]:
    """프로모션 상세 정보를 조회한다."""
    promotion = _get_promotion_or_404(db, promotion_id)
    return APIResponse(data=promotion, message="프로모션 상세 정보를 조회했습니다.")


@router.post(
    "",
    response_model=APIResponse[PromotionRead],
    status_code=status.HTTP_201_CREATED,
    summary="프로모션 생성",
)
def create_promotion(payload: PromotionCreate, db: Session = Depends(get_db)) -> APIResponse[PromotionRead]:
    """프로모션 기본 정보를 생성한다."""
    promotion = Promotion(
        promotion_name=payload.promotion_name,
        promotion_type=payload.promotion_type,
        discount_type=payload.discount_type,
        discount_value=payload.discount_value,
        max_discount_amount=payload.max_discount_amount,
        start_at=payload.start_at,
        end_at=payload.end_at,
        is_active=payload.is_active,
        priority=payload.priority,
        created_by=payload.created_by,
    )
    db.add(promotion)
    db.commit()
    db.refresh(promotion)

    created_promotion = _get_promotion_or_404(db, promotion.id)
    return APIResponse(data=created_promotion, message="프로모션을 생성했습니다.")


@router.put("/{promotion_id}", response_model=APIResponse[PromotionRead], summary="프로모션 수정")
def update_promotion(
    promotion_id: int,
    payload: PromotionUpdate,
    db: Session = Depends(get_db),
) -> APIResponse[PromotionRead]:
    """프로모션 기본 정보를 수정한다."""
    promotion = _get_promotion_or_404(db, promotion_id)
    update_data = payload.model_dump(exclude_unset=True)

    for field_name, field_value in update_data.items():
        setattr(promotion, field_name, field_value)

    if update_data:
        promotion.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)

    db.add(promotion)
    db.commit()
    db.refresh(promotion)

    updated_promotion = _get_promotion_or_404(db, promotion_id)
    return APIResponse(data=updated_promotion, message="프로모션을 수정했습니다.")


@router.delete(
    "/{promotion_id}",
    response_model=APIResponse[dict[str, int]],
    summary="프로모션 삭제",
)
def delete_promotion(promotion_id: int, db: Session = Depends(get_db)) -> APIResponse[dict[str, int]]:
    """프로모션을 소프트 삭제한다."""
    promotion = _get_promotion_or_404(db, promotion_id)
    promotion.deleted_at = datetime.now(timezone.utc).replace(tzinfo=None)
    db.add(promotion)
    db.commit()
    db.refresh(promotion)

    return APIResponse(data={"promotion_id": promotion_id}, message="프로모션을 삭제했습니다.")


__all__ = ["router"]