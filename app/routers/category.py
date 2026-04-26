from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.models.product import Category
from app.schemas import APIResponse
from app.schemas.product import CategoryCreate, CategoryRead, CategoryUpdate

router = APIRouter(prefix="/categories", tags=["category"])


def _category_query():
    """삭제되지 않은 Category 기본 쿼리."""
    return select(Category).where(Category.deleted_at.is_(None))


def _get_category_or_404(db: Session, category_id: int) -> Category:
    """category_id로 Category를 조회하고 없으면 404를 반환한다."""
    statement = _category_query().where(Category.id == category_id)
    category = db.execute(statement).scalar_one_or_none()
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="카테고리를 찾을 수 없습니다.",
        )
    return category


@router.get("", response_model=APIResponse[list[CategoryRead]], summary="카테고리 목록 조회")
def list_categories(
    db: Session = Depends(get_db),
) -> APIResponse[list[CategoryRead]]:
    """전체 카테고리 목록을 계층 구조로 조회한다."""
    statement = _category_query().order_by(Category.category_depth, Category.id)
    categories = db.execute(statement).scalars().all()
    return APIResponse(data=categories)


@router.get("/{category_id}", response_model=APIResponse[CategoryRead], summary="카테고리 상세 조회")
def get_category(
    category_id: int,
    db: Session = Depends(get_db),
) -> APIResponse[CategoryRead]:
    """특정 카테고리의 상세 정보와 하위 카테고리를 조회한다."""
    category = _get_category_or_404(db, category_id)
    return APIResponse(data=category)


@router.post("", response_model=APIResponse[CategoryRead], summary="카테고리 생성")
def create_category(
    payload: CategoryCreate,
    db: Session = Depends(get_db),
) -> APIResponse[CategoryRead]:
    """새로운 카테고리를 생성한다. parent_category_id로 계층 구조를 지정할 수 있다."""
    category = Category(
        parent_category_id=payload.parent_category_id,
        category_name=payload.category_name,
        category_depth=payload.category_depth,
        created_by=payload.created_by,
    )
    db.add(category)
    db.commit()
    db.refresh(category)
    created = _get_category_or_404(db, category.id)
    return APIResponse(data=created, message="카테고리를 생성했습니다.")


@router.put("/{category_id}", response_model=APIResponse[CategoryRead], summary="카테고리 수정")
def update_category(
    category_id: int,
    payload: CategoryUpdate,
    db: Session = Depends(get_db),
) -> APIResponse[CategoryRead]:
    """카테고리 정보를 수정한다."""
    category = _get_category_or_404(db, category_id)
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(category, field):
            setattr(category, field, value)
    db.commit()
    db.refresh(category)
    updated = _get_category_or_404(db, category_id)
    return APIResponse(data=updated, message="카테고리를 수정했습니다.")


@router.delete("/{category_id}", response_model=APIResponse[dict[str, int]], summary="카테고리 삭제")
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
) -> APIResponse[dict[str, int]]:
    """카테고리를 소프트 삭제한다."""
    from datetime import datetime, timezone

    category = _get_category_or_404(db, category_id)
    category.deleted_at = datetime.now(timezone.utc)
    db.commit()
    return APIResponse(data={"id": category_id}, message="카테고리를 삭제했습니다.")
