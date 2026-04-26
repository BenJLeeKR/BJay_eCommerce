from __future__ import annotations
import asyncio
import logging
from typing import Optional

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.dependencies import get_db
from app.events.producer import TOPIC_PRODUCT_INDEX_UPDATED, publish_event
from app.events.schemas import ProductIndexUpdatedEvent
from app.models.product import (
    Brand,
    Product,
    ProductCategoryMap,
    ProductImage,
    ProductOption,
    ProductOptionValue,
    SKU,
)
from app.schemas import APIResponse
from app.schemas.product import (
    ProductCreate,
    ProductImageCreate,
    ProductImageRead,
    ProductImageUpdate,
    ProductOptionCreate,
    ProductOptionRead,
    ProductOptionUpdate,
    ProductOptionValueCreate,
    ProductOptionValueRead,
    ProductOptionValueUpdate,
    ProductRead,
    ProductUpdate,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/products", tags=["Products (상품)"])


# ──────────────────────────────────────────────
#  Helper functions
# ──────────────────────────────────────────────


def _product_query():
    return (
        select(Product)
        .options(
            selectinload(Product.brand),
            selectinload(Product.categories),
            selectinload(Product.options).selectinload(ProductOption.values),
            selectinload(Product.images),
            selectinload(Product.skus).selectinload(SKU.option_values),
        )
        .where(Product.deleted_at.is_(None))
    )


def _get_product_or_404(db: Session, product_id: int) -> Product:
    statement = _product_query().where(Product.id == product_id)
    product = db.execute(statement).scalar_one_or_none()

    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="상품을 찾을 수 없습니다.",
        )

    return product


def _get_product_for_write(db: Session, product_id: int) -> Product:
    """수정/삭제용 Product 조회 (relationship 로딩 없이)."""
    statement = select(Product).where(
        Product.id == product_id, Product.deleted_at.is_(None)
    )
    product = db.execute(statement).scalar_one_or_none()
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="상품을 찾을 수 없습니다.",
        )
    return product


def _get_option_or_404(db: Session, option_id: int) -> ProductOption:
    statement = (
        select(ProductOption)
        .where(
            ProductOption.id == option_id,
            ProductOption.deleted_at.is_(None),
        )
        .options(selectinload(ProductOption.values))
    )
    option = db.execute(statement).scalar_one_or_none()
    if option is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="옵션을 찾을 수 없습니다.",
        )
    return option


def _get_option_value_or_404(db: Session, value_id: int) -> ProductOptionValue:
    statement = select(ProductOptionValue).where(
        ProductOptionValue.id == value_id,
        ProductOptionValue.deleted_at.is_(None),
    )
    value = db.execute(statement).scalar_one_or_none()
    if value is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="옵션 값을 찾을 수 없습니다.",
        )
    return value


def _get_image_or_404(db: Session, image_id: int) -> ProductImage:
    statement = select(ProductImage).where(
        ProductImage.id == image_id,
        ProductImage.deleted_at.is_(None),
    )
    image = db.execute(statement).scalar_one_or_none()
    if image is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="이미지를 찾을 수 없습니다.",
        )
    return image


# ──────────────────────────────────────────────
#  Product CRUD
# ──────────────────────────────────────────────


@router.get("", response_model=APIResponse[list[ProductRead]], summary="상품 목록 조회")
def list_products(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    product_status: Optional[str] = Query(default=None, max_length=20),
    db: Session = Depends(get_db),
) -> APIResponse[list[ProductRead]]:
    """상품 목록을 상태와 페이징 조건으로 조회한다."""
    statement = _product_query().offset(skip).limit(limit)

    if product_status is not None:
        statement = statement.where(Product.product_status == product_status)

    products = db.execute(statement).scalars().unique().all()
    return APIResponse(data=products, message="상품 목록을 조회했습니다.")


@router.get("/{product_id}", response_model=APIResponse[ProductRead], summary="상품 상세 조회")
def get_product(product_id: int, db: Session = Depends(get_db)) -> APIResponse[ProductRead]:
    """상품 상세 정보를 조회한다."""
    product = _get_product_or_404(db, product_id)
    return APIResponse(data=product, message="상품 상세 정보를 조회했습니다.")


@router.post(
    "",
    response_model=APIResponse[ProductRead],
    status_code=status.HTTP_201_CREATED,
    summary="상품 생성 (옵션/이미지/카테고리 포함)",
)
def create_product(
    payload: ProductCreate,
    db: Session = Depends(get_db),
) -> APIResponse[ProductRead]:
    """상품 기본 정보와 함께 옵션(값), 이미지, 카테고리 매핑을 한 번에 생성한다."""
    # 1. Product 기본 정보 생성
    product = Product(
        product_name=payload.product_name,
        product_description=payload.product_description,
        brand_id=payload.brand_id,
        product_status=payload.product_status,
        base_price_amount=payload.base_price_amount,
        thumbnail_image_url=payload.thumbnail_image_url,
        created_by=payload.created_by,
    )
    db.add(product)
    db.flush()  # product.id 확보

    # 2. category_ids → product_category_map INSERT
    for cat_id in payload.category_ids:
        db.add(ProductCategoryMap(product_id=product.id, category_id=cat_id))

    # 3. options → product_option + product_option_value INSERT
    for opt in payload.options:
        option = ProductOption(
            product_id=product.id,
            option_name=opt.option_name,
            sort_order=opt.sort_order,
            created_by=opt.created_by or payload.created_by,
        )
        db.add(option)
        db.flush()  # option.id 확보
        for val in opt.values:
            db.add(
                ProductOptionValue(
                    option_id=option.id,
                    option_value=val.option_value,
                )
            )

    # 4. images → product_image INSERT
    for img in payload.images:
        db.add(
            ProductImage(
                product_id=product.id,
                image_url=img.image_url,
                is_main_image=img.is_main_image,
                sort_order=img.sort_order,
                created_by=img.created_by or payload.created_by,
            )
        )

    db.commit()
    db.refresh(product)

    # 5. ProductIndexUpdated 이벤트 발행 (sync context → run_coroutine_threadsafe)
    try:
        brand_name = product.brand.brand_name if product.brand else None
        category_ids = [cat.id for cat in product.categories]
        price_amount = min(
            (sku.sale_price_amount for sku in product.skus if sku.sku_status == "ACTIVE"),
            default=None,
        )
        event = ProductIndexUpdatedEvent(
            product_id=product.id,
            product_name=product.product_name,
            product_description=product.product_description,
            category_ids=category_ids,
            brand_name=brand_name,
            price_amount=price_amount,
            is_active=(product.product_status == "ACTIVE"),
        )
        # 지연 import로 순환 참조 방지
        from app.main import main_event_loop as _main_loop
        if _main_loop is not None:
            future = asyncio.run_coroutine_threadsafe(
                publish_event(
                    topic=TOPIC_PRODUCT_INDEX_UPDATED,
                    key=str(product.id),
                    event=event,
                ),
                _main_loop,
            )
            future.result(timeout=10)
    except Exception as exc:
        logger.warning("Failed to publish ProductIndexUpdated: %s", exc)

    created_product = _get_product_or_404(db, product.id)
    return APIResponse(data=created_product, message="상품을 생성했습니다.")


@router.put("/{product_id}", response_model=APIResponse[ProductRead], summary="상품 수정")
def update_product(
    product_id: int,
    payload: ProductUpdate,
    db: Session = Depends(get_db),
) -> APIResponse[ProductRead]:
    """상품 기본 정보와 카테고리 매핑을 수정한다."""
    product = _get_product_for_write(db, product_id)
    update_data = payload.model_dump(exclude_unset=True)

    # 1. Product 기본 필드 업데이트 (category_ids 제외)
    for field_name, field_value in update_data.items():
        if field_name != "category_ids" and hasattr(product, field_name):
            setattr(product, field_name, field_value)

    # 2. category_ids 제공 시 기존 매핑 삭제 후 재INSERT
    if "category_ids" in update_data and payload.category_ids is not None:
        db.query(ProductCategoryMap).filter(
            ProductCategoryMap.product_id == product_id
        ).delete()
        for cat_id in payload.category_ids:
            db.add(ProductCategoryMap(product_id=product_id, category_id=cat_id))

    if update_data:
        product.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)

    db.add(product)
    db.commit()

    # ProductIndexUpdated 이벤트 발행 (sync context → run_coroutine_threadsafe)
    try:
        brand_name = product.brand.brand_name if product.brand else None
        category_ids = [cat.id for cat in product.categories]
        price_amount = min(
            (sku.sale_price_amount for sku in product.skus if sku.sku_status == "ACTIVE"),
            default=None,
        )
        event = ProductIndexUpdatedEvent(
            product_id=product.id,
            product_name=product.product_name,
            product_description=product.product_description,
            category_ids=category_ids,
            brand_name=brand_name,
            price_amount=price_amount,
            is_active=(product.product_status == "ACTIVE"),
        )
        # 지연 import로 순환 참조 방지
        from app.main import main_event_loop as _main_loop
        if _main_loop is not None:
            future = asyncio.run_coroutine_threadsafe(
                publish_event(
                    topic=TOPIC_PRODUCT_INDEX_UPDATED,
                    key=str(product.id),
                    event=event,
                ),
                _main_loop,
            )
            future.result(timeout=10)
    except Exception as exc:
        logger.warning("Failed to publish ProductIndexUpdated: %s", exc)

    updated_product = _get_product_or_404(db, product_id)
    return APIResponse(data=updated_product, message="상품을 수정했습니다.")


@router.delete(
    "/{product_id}",
    response_model=APIResponse[dict[str, int]],
    summary="상품 삭제",
)
def delete_product(product_id: int, db: Session = Depends(get_db)) -> APIResponse[dict[str, int]]:
    """상품을 소프트 삭제한다."""
    product = _get_product_for_write(db, product_id)
    product.deleted_at = datetime.now(timezone.utc).replace(tzinfo=None)
    db.add(product)
    db.commit()

    # ProductIndexUpdated 이벤트 발행 (is_active=false, sync context → run_coroutine_threadsafe)
    try:
        event = ProductIndexUpdatedEvent(
            product_id=product_id,
            is_active=False,
        )
        # 지연 import로 순환 참조 방지
        from app.main import main_event_loop as _main_loop
        if _main_loop is not None:
            future = asyncio.run_coroutine_threadsafe(
                publish_event(
                    topic=TOPIC_PRODUCT_INDEX_UPDATED,
                    key=str(product_id),
                    event=event,
                ),
                _main_loop,
            )
            future.result(timeout=10)
    except Exception as exc:
        logger.warning("Failed to publish ProductIndexUpdated: %s", exc)

    return APIResponse(data={"product_id": product_id}, message="상품을 삭제했습니다.")


# ──────────────────────────────────────────────
#  ProductOption / ProductOptionValue sub-resources
# ──────────────────────────────────────────────


@router.get(
    "/{product_id}/options",
    response_model=APIResponse[list[ProductOptionRead]],
    summary="상품 옵션 목록 조회",
)
def list_product_options(
    product_id: int,
    db: Session = Depends(get_db),
) -> APIResponse[list[ProductOptionRead]]:
    """특정 상품의 전체 옵션 목록을 조회한다."""
    _get_product_for_write(db, product_id)  # 존재 여부 확인
    statement = (
        select(ProductOption)
        .where(
            ProductOption.product_id == product_id,
            ProductOption.deleted_at.is_(None),
        )
        .options(selectinload(ProductOption.values))
        .order_by(ProductOption.sort_order, ProductOption.id)
    )
    options = db.execute(statement).scalars().all()
    return APIResponse(data=options)


@router.post(
    "/{product_id}/options",
    response_model=APIResponse[ProductOptionRead],
    status_code=status.HTTP_201_CREATED,
    summary="상품 옵션 생성",
)
def create_product_option(
    product_id: int,
    payload: ProductOptionCreate,
    db: Session = Depends(get_db),
) -> APIResponse[ProductOptionRead]:
    """특정 상품에 새 옵션(값 포함)을 추가한다."""
    _get_product_for_write(db, product_id)  # 존재 여부 확인

    option = ProductOption(
        product_id=product_id,
        option_name=payload.option_name,
        sort_order=payload.sort_order,
        created_by=payload.created_by,
    )
    db.add(option)
    db.flush()

    for val in payload.values:
        db.add(
            ProductOptionValue(
                option_id=option.id,
                option_value=val.option_value,
            )
        )

    db.commit()
    db.refresh(option)
    created = _get_option_or_404(db, option.id)
    return APIResponse(data=created, message="옵션을 생성했습니다.")


@router.put(
    "/{product_id}/options/{option_id}",
    response_model=APIResponse[ProductOptionRead],
    summary="상품 옵션 수정",
)
def update_product_option(
    product_id: int,
    option_id: int,
    payload: ProductOptionUpdate,
    db: Session = Depends(get_db),
) -> APIResponse[ProductOptionRead]:
    """옵션명 또는 정렬순서를 수정한다."""
    _get_product_for_write(db, product_id)  # 존재 여부 확인
    option = _get_option_or_404(db, option_id)

    if option.product_id != product_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="해당 상품에 속한 옵션이 아닙니다.",
        )

    update_data = payload.model_dump(exclude_unset=True)
    for field_name, field_value in update_data.items():
        if hasattr(option, field_name):
            setattr(option, field_name, field_value)

    option.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
    db.commit()
    db.refresh(option)
    updated = _get_option_or_404(db, option_id)
    return APIResponse(data=updated, message="옵션을 수정했습니다.")


@router.delete(
    "/{product_id}/options/{option_id}",
    response_model=APIResponse[dict[str, int]],
    summary="상품 옵션 삭제",
)
def delete_product_option(
    product_id: int,
    option_id: int,
    db: Session = Depends(get_db),
) -> APIResponse[dict[str, int]]:
    """옵션과 하위 값들을 전체 삭제한다."""
    _get_product_for_write(db, product_id)
    option = _get_option_or_404(db, option_id)

    if option.product_id != product_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="해당 상품에 속한 옵션이 아닙니다.",
        )

    option.deleted_at = datetime.now(timezone.utc).replace(tzinfo=None)
    db.commit()
    return APIResponse(data={"option_id": option_id}, message="옵션을 삭제했습니다.")


# ──────────────────────────────────────────────
#  ProductOptionValue sub-resources
# ──────────────────────────────────────────────


@router.post(
    "/{product_id}/options/{option_id}/values",
    response_model=APIResponse[ProductOptionValueRead],
    status_code=status.HTTP_201_CREATED,
    summary="옵션 값 추가",
)
def create_product_option_value(
    product_id: int,
    option_id: int,
    payload: ProductOptionValueCreate,
    db: Session = Depends(get_db),
) -> APIResponse[ProductOptionValueRead]:
    """특정 옵션에 새 값을 추가한다."""
    _get_product_for_write(db, product_id)
    option = _get_option_or_404(db, option_id)

    if option.product_id != product_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="해당 상품에 속한 옵션이 아닙니다.",
        )

    value = ProductOptionValue(
        option_id=option_id,
        option_value=payload.option_value,
    )
    db.add(value)
    db.commit()
    db.refresh(value)
    return APIResponse(data=value, message="옵션 값을 추가했습니다.")


@router.put(
    "/{product_id}/options/{option_id}/values/{value_id}",
    response_model=APIResponse[ProductOptionValueRead],
    summary="옵션 값 수정",
)
def update_product_option_value(
    product_id: int,
    option_id: int,
    value_id: int,
    payload: ProductOptionValueUpdate,
    db: Session = Depends(get_db),
) -> APIResponse[ProductOptionValueRead]:
    """옵션 값을 수정한다."""
    _get_product_for_write(db, product_id)
    option = _get_option_or_404(db, option_id)

    if option.product_id != product_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="해당 상품에 속한 옵션이 아닙니다.",
        )

    value = _get_option_value_or_404(db, value_id)
    if value.option_id != option_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="해당 옵션에 속한 값이 아닙니다.",
        )

    update_data = payload.model_dump(exclude_unset=True)
    for field_name, field_value in update_data.items():
        if hasattr(value, field_name):
            setattr(value, field_name, field_value)

    value.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
    db.commit()
    db.refresh(value)
    return APIResponse(data=value, message="옵션 값을 수정했습니다.")


@router.delete(
    "/{product_id}/options/{option_id}/values/{value_id}",
    response_model=APIResponse[dict[str, int]],
    summary="옵션 값 삭제",
)
def delete_product_option_value(
    product_id: int,
    option_id: int,
    value_id: int,
    db: Session = Depends(get_db),
) -> APIResponse[dict[str, int]]:
    """옵션 값을 삭제한다."""
    _get_product_for_write(db, product_id)
    option = _get_option_or_404(db, option_id)

    if option.product_id != product_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="해당 상품에 속한 옵션이 아닙니다.",
        )

    value = _get_option_value_or_404(db, value_id)
    if value.option_id != option_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="해당 옵션에 속한 값이 아닙니다.",
        )

    value.deleted_at = datetime.now(timezone.utc).replace(tzinfo=None)
    db.commit()
    return APIResponse(data={"value_id": value_id}, message="옵션 값을 삭제했습니다.")


# ──────────────────────────────────────────────
#  ProductImage sub-resources
# ──────────────────────────────────────────────


@router.get(
    "/{product_id}/images",
    response_model=APIResponse[list[ProductImageRead]],
    summary="상품 이미지 목록 조회",
)
def list_product_images(
    product_id: int,
    db: Session = Depends(get_db),
) -> APIResponse[list[ProductImageRead]]:
    """특정 상품의 전체 이미지 목록을 조회한다."""
    _get_product_for_write(db, product_id)
    statement = (
        select(ProductImage)
        .where(
            ProductImage.product_id == product_id,
            ProductImage.deleted_at.is_(None),
        )
        .order_by(ProductImage.sort_order, ProductImage.id)
    )
    images = db.execute(statement).scalars().all()
    return APIResponse(data=images)


@router.post(
    "/{product_id}/images",
    response_model=APIResponse[ProductImageRead],
    status_code=status.HTTP_201_CREATED,
    summary="상품 이미지 추가",
)
def create_product_image(
    product_id: int,
    payload: ProductImageCreate,
    db: Session = Depends(get_db),
) -> APIResponse[ProductImageRead]:
    """특정 상품에 새 이미지를 추가한다."""
    _get_product_for_write(db, product_id)

    image = ProductImage(
        product_id=product_id,
        image_url=payload.image_url,
        is_main_image=payload.is_main_image,
        sort_order=payload.sort_order,
        created_by=payload.created_by,
    )
    db.add(image)
    db.commit()
    db.refresh(image)
    return APIResponse(data=image, message="이미지를 추가했습니다.")


@router.put(
    "/{product_id}/images/{image_id}",
    response_model=APIResponse[ProductImageRead],
    summary="상품 이미지 수정",
)
def update_product_image(
    product_id: int,
    image_id: int,
    payload: ProductImageUpdate,
    db: Session = Depends(get_db),
) -> APIResponse[ProductImageRead]:
    """이미지 URL, 대표이미지 여부, 정렬순서를 수정한다."""
    _get_product_for_write(db, product_id)
    image = _get_image_or_404(db, image_id)

    if image.product_id != product_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="해당 상품에 속한 이미지가 아닙니다.",
        )

    update_data = payload.model_dump(exclude_unset=True)
    for field_name, field_value in update_data.items():
        if hasattr(image, field_name):
            setattr(image, field_name, field_value)

    image.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
    db.commit()
    db.refresh(image)
    return APIResponse(data=image, message="이미지를 수정했습니다.")


@router.delete(
    "/{product_id}/images/{image_id}",
    response_model=APIResponse[dict[str, int]],
    summary="상품 이미지 삭제",
)
def delete_product_image(
    product_id: int,
    image_id: int,
    db: Session = Depends(get_db),
) -> APIResponse[dict[str, int]]:
    """상품 이미지를 삭제한다."""
    _get_product_for_write(db, product_id)
    image = _get_image_or_404(db, image_id)

    if image.product_id != product_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="해당 상품에 속한 이미지가 아닙니다.",
        )

    image.deleted_at = datetime.now(timezone.utc).replace(tzinfo=None)
    db.commit()
    return APIResponse(data={"image_id": image_id}, message="이미지를 삭제했습니다.")


__all__ = ["router"]
