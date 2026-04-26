from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.models.product import Product, ProductOptionValue, SKU, SKUOptionValueMap
from app.schemas import APIResponse
from app.schemas.product import SKUCreate, SKURead, SKUUpdate

router = APIRouter(prefix="/skus", tags=["sku"])


def _sku_query():
    """삭제되지 않은 SKU 기본 쿼리."""
    return select(SKU).where(SKU.deleted_at.is_(None))


def _get_sku_or_404(db: Session, sku_id: int) -> SKU:
    """sku_id로 SKU를 조회하고 없으면 404를 반환한다."""
    statement = _sku_query().where(SKU.id == sku_id)
    sku = db.execute(statement).scalar_one_or_none()
    if sku is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SKU를 찾을 수 없습니다.",
        )
    return sku


def _validate_product_exists(db: Session, product_id: int) -> None:
    """product_id가 유효한 상품인지 검증한다."""
    statement = select(Product).where(
        Product.id == product_id,
        Product.deleted_at.is_(None),
    )
    product = db.execute(statement).scalar_one_or_none()
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="존재하지 않는 상품입니다.",
        )


def _validate_option_values_exist(db: Session, option_value_ids: list[int]) -> None:
    """option_value_id들이 유효한 값인지 검증한다."""
    if not option_value_ids:
        return
    for ov_id in option_value_ids:
        stmt = select(ProductOptionValue).where(
            ProductOptionValue.id == ov_id,
            ProductOptionValue.deleted_at.is_(None),
        )
        ov = db.execute(stmt).scalar_one_or_none()
        if ov is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"OptionValue(ID={ov_id})를 찾을 수 없습니다.",
            )


@router.get("", response_model=APIResponse[list[SKURead]], summary="SKU 목록 조회")
def list_skus(
    product_id: int | None = None,
    db: Session = Depends(get_db),
) -> APIResponse[list[SKURead]]:
    """전체 SKU 목록을 조회한다. (product_id 필터링 가능)"""
    statement = _sku_query()
    if product_id is not None:
        statement = statement.where(SKU.product_id == product_id)
    statement = statement.order_by(SKU.id)
    skus = db.execute(statement).scalars().all()
    return APIResponse(data=skus)


@router.get("/{sku_id}", response_model=APIResponse[SKURead], summary="SKU 상세 조회")
def get_sku(
    sku_id: int,
    db: Session = Depends(get_db),
) -> APIResponse[SKURead]:
    """특정 SKU의 상세 정보를 조회한다."""
    sku = _get_sku_or_404(db, sku_id)
    return APIResponse(data=sku)


@router.post("", response_model=APIResponse[SKURead], summary="SKU 생성")
def create_sku(
    payload: SKUCreate,
    db: Session = Depends(get_db),
) -> APIResponse[SKURead]:
    """새로운 SKU를 생성하고, 옵션 값 매핑도 함께 처리한다."""
    _validate_product_exists(db, payload.product_id)
    _validate_option_values_exist(db, payload.option_value_ids)

    sku = SKU(
        product_id=payload.product_id,
        sku_code=payload.sku_code,
        sale_price_amount=payload.sale_price_amount,
        stock_quantity=payload.stock_quantity,
        sku_status=payload.sku_status,
        created_by=payload.created_by,
    )
    db.add(sku)
    db.flush()  # sku.id 확보

    # option_value_ids → sku_option_value_map INSERT
    for ov_id in payload.option_value_ids:
        mapping = SKUOptionValueMap(sku_id=sku.id, option_value_id=ov_id)
        db.add(mapping)

    db.commit()
    db.refresh(sku)
    return APIResponse(data=sku, message="SKU를 생성했습니다.")


@router.put("/{sku_id}", response_model=APIResponse[SKURead], summary="SKU 수정")
def update_sku(
    sku_id: int,
    payload: SKUUpdate,
    db: Session = Depends(get_db),
) -> APIResponse[SKURead]:
    """SKU 정보를 수정한다."""
    sku = _get_sku_or_404(db, sku_id)

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if value is not None:
            setattr(sku, field, value)

    db.commit()
    db.refresh(sku)
    return APIResponse(data=sku, message="SKU를 수정했습니다.")


@router.delete("/{sku_id}", response_model=APIResponse[dict[str, int]], summary="SKU 삭제")
def delete_sku(
    sku_id: int,
    db: Session = Depends(get_db),
) -> APIResponse[dict[str, int]]:
    """SKU를 소프트 삭제한다."""
    from datetime import datetime, timezone

    sku = _get_sku_or_404(db, sku_id)
    sku.deleted_at = datetime.now(timezone.utc)
    db.commit()
    return APIResponse(data={"id": sku_id}, message="SKU를 삭제했습니다.")
