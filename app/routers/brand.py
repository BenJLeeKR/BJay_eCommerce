from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.models.product import Brand
from app.schemas import APIResponse
from app.schemas.product import BrandCreate, BrandRead

router = APIRouter(prefix="/brands", tags=["brand"])


def _brand_query():
    """삭제되지 않은 Brand 기본 쿼리."""
    return select(Brand).where(Brand.deleted_at.is_(None))


def _get_brand_or_404(db: Session, brand_id: int) -> Brand:
    """brand_id로 Brand를 조회하고 없으면 404를 반환한다."""
    statement = _brand_query().where(Brand.id == brand_id)
    brand = db.execute(statement).scalar_one_or_none()
    if brand is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="브랜드를 찾을 수 없습니다.",
        )
    return brand


@router.get("", response_model=APIResponse[list[BrandRead]], summary="브랜드 목록 조회")
def list_brands(
    db: Session = Depends(get_db),
) -> APIResponse[list[BrandRead]]:
    """전체 브랜드 목록을 조회한다."""
    statement = _brand_query().order_by(Brand.id)
    brands = db.execute(statement).scalars().all()
    return APIResponse(data=brands)


@router.get("/{brand_id}", response_model=APIResponse[BrandRead], summary="브랜드 상세 조회")
def get_brand(
    brand_id: int,
    db: Session = Depends(get_db),
) -> APIResponse[BrandRead]:
    """특정 브랜드의 상세 정보를 조회한다."""
    brand = _get_brand_or_404(db, brand_id)
    return APIResponse(data=brand)


@router.post("", response_model=APIResponse[BrandRead], summary="브랜드 생성")
def create_brand(
    payload: BrandCreate,
    db: Session = Depends(get_db),
) -> APIResponse[BrandRead]:
    """새로운 브랜드를 생성한다."""
    brand = Brand(
        brand_name=payload.brand_name,
        created_by=payload.created_by,
    )
    db.add(brand)
    db.commit()
    db.refresh(brand)
    return APIResponse(data=brand, message="브랜드를 생성했습니다.")


@router.put("/{brand_id}", response_model=APIResponse[BrandRead], summary="브랜드 수정")
def update_brand(
    brand_id: int,
    payload: BrandCreate,
    db: Session = Depends(get_db),
) -> APIResponse[BrandRead]:
    """브랜드 정보를 수정한다."""
    brand = _get_brand_or_404(db, brand_id)
    brand.brand_name = payload.brand_name
    brand.updated_by = payload.created_by
    db.commit()
    db.refresh(brand)
    return APIResponse(data=brand, message="브랜드를 수정했습니다.")


@router.delete("/{brand_id}", response_model=APIResponse[dict[str, int]], summary="브랜드 삭제")
def delete_brand(
    brand_id: int,
    db: Session = Depends(get_db),
) -> APIResponse[dict[str, int]]:
    """브랜드를 소프트 삭제한다."""
    from datetime import datetime, timezone

    brand = _get_brand_or_404(db, brand_id)
    brand.deleted_at = datetime.now(timezone.utc)
    db.commit()
    return APIResponse(data={"id": brand_id}, message="브랜드를 삭제했습니다.")
