from __future__ import annotations
from typing import Optional

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.dependencies import get_db
from app.models.review import Review, ReviewRating, ReviewImage, ReviewLike, ReviewReport, ReviewComment
from app.schemas import APIResponse
from app.schemas.review import ReviewCreate, ReviewRead, ReviewUpdate

router = APIRouter(prefix="/reviews", tags=["Reviews (리뷰)"])


def _review_query():
    return (
        select(Review)
        .options(
            selectinload(Review.ratings),
            selectinload(Review.images),
            selectinload(Review.likes),
            selectinload(Review.reports),
            selectinload(Review.comments),
        )
        .where(Review.deleted_at.is_(None))
    )


def _get_review_or_404(db: Session, review_id: int) -> Review:
    statement = _review_query().where(Review.id == review_id)
    review = db.execute(statement).scalar_one_or_none()

    if review is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="리뷰를 찾을 수 없습니다.",
        )

    return review


@router.get("", response_model=APIResponse[list[ReviewRead]], summary="리뷰 목록 조회")
def list_reviews(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    product_id: Optional[int] = Query(default=None),
    user_id: Optional[int] = Query(default=None),
    review_status: Optional[str] = Query(default=None, max_length=30),
    db: Session = Depends(get_db),
) -> APIResponse[list[ReviewRead]]:
    """리뷰 목록을 조건과 페이징으로 조회한다."""
    statement = _review_query().offset(skip).limit(limit)

    if product_id is not None:
        statement = statement.where(Review.product_id == product_id)
    if user_id is not None:
        statement = statement.where(Review.user_id == user_id)
    if review_status is not None:
        statement = statement.where(Review.review_status == review_status)

    reviews = db.execute(statement).scalars().unique().all()
    return APIResponse(data=reviews, message="리뷰 목록을 조회했습니다.")


@router.get("/{review_id}", response_model=APIResponse[ReviewRead], summary="리뷰 상세 조회")
def get_review(review_id: int, db: Session = Depends(get_db)) -> APIResponse[ReviewRead]:
    """리뷰 상세 정보를 조회한다."""
    review = _get_review_or_404(db, review_id)
    return APIResponse(data=review, message="리뷰 상세 정보를 조회했습니다.")


@router.post(
    "",
    response_model=APIResponse[ReviewRead],
    status_code=status.HTTP_201_CREATED,
    summary="리뷰 생성",
)
def create_review(payload: ReviewCreate, db: Session = Depends(get_db)) -> APIResponse[ReviewRead]:
    """리뷰를 생성한다."""
    review = Review(
        product_id=payload.product_id,
        user_id=payload.user_id,
        order_item_id=payload.order_item_id,
        review_title=payload.review_title,
        review_content=payload.review_content,
        review_status=payload.review_status,
        is_verified_purchase=payload.is_verified_purchase,
        like_count=payload.like_count,
        comment_count=payload.comment_count,
        created_by=payload.created_by,
    )
    db.add(review)
    db.commit()
    db.refresh(review)

    created_review = _get_review_or_404(db, review.id)
    return APIResponse(data=created_review, message="리뷰를 생성했습니다.")


@router.put("/{review_id}", response_model=APIResponse[ReviewRead], summary="리뷰 수정")
def update_review(
    review_id: int,
    payload: ReviewUpdate,
    db: Session = Depends(get_db),
) -> APIResponse[ReviewRead]:
    """리뷰 정보를 수정한다."""
    review = _get_review_or_404(db, review_id)

    if payload.review_title is not None:
        review.review_title = payload.review_title
    if payload.review_content is not None:
        review.review_content = payload.review_content
    if payload.review_status is not None:
        review.review_status = payload.review_status
    if payload.is_verified_purchase is not None:
        review.is_verified_purchase = payload.is_verified_purchase
    if payload.like_count is not None:
        review.like_count = payload.like_count
    if payload.comment_count is not None:
        review.comment_count = payload.comment_count
    if payload.updated_by is not None:
        review.updated_by = payload.updated_by
        review.updated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(review)

    updated_review = _get_review_or_404(db, review.id)
    return APIResponse(data=updated_review, message="리뷰를 수정했습니다.")


@router.delete("/{review_id}", response_model=APIResponse[None], summary="리뷰 삭제")
def delete_review(
    review_id: int,
    deleted_by: Optional[int] = Query(default=None),
    db: Session = Depends(get_db),
) -> APIResponse[None]:
    """리뷰를 논리 삭제한다."""
    review = _get_review_or_404(db, review_id)

    review.deleted_at = datetime.now(timezone.utc)
    if deleted_by is not None:
        review.deleted_by = deleted_by

    db.commit()
    return APIResponse(data=None, message="리뷰를 삭제했습니다.")