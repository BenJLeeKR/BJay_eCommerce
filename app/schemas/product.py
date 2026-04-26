from __future__ import annotations
from typing import Optional

from datetime import datetime
from decimal import Decimal

from pydantic import Field

from app.schemas import ORMBaseSchema, TimestampSchema


class BrandCreate(ORMBaseSchema):
    """브랜드 생성 요청 스키마."""

    brand_name: str = Field(..., max_length=255)
    created_by: Optional[int] = None


class BrandRead(TimestampSchema):
    """브랜드 응답 스키마."""

    id: int
    brand_name: str
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[int] = None


class CategoryCreate(ORMBaseSchema):
    """카테고리 생성 요청 스키마."""

    parent_category_id: Optional[int] = None
    category_name: str = Field(..., max_length=255)
    category_depth: int
    created_by: Optional[int] = None


class CategoryUpdate(ORMBaseSchema):
    """카테고리 수정 요청 스키마."""

    parent_category_id: Optional[int] = None
    category_name: Optional[str] = Field(default=None, max_length=255)
    category_depth: Optional[int] = None
    updated_by: Optional[int] = None


class CategoryRead(TimestampSchema):
    """카테고리 응답 스키마."""

    id: int
    parent_category_id: Optional[int] = None
    category_name: str
    category_depth: int
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[int] = None


class ProductOptionValueCreate(ORMBaseSchema):
    """상품 옵션 값 생성 요청 스키마 (nested create 용)."""

    option_value: str = Field(..., max_length=100)


class ProductOptionCreate(ORMBaseSchema):
    """상품 옵션 생성 요청 스키마 (nested create 용 - values 포함)."""

    option_name: str = Field(..., max_length=100)
    sort_order: Optional[int] = None
    values: list[ProductOptionValueCreate] = Field(default_factory=list)
    created_by: Optional[int] = None


class ProductOptionUpdate(ORMBaseSchema):
    """상품 옵션 수정 요청 스키마."""

    option_name: Optional[str] = Field(default=None, max_length=100)
    sort_order: Optional[int] = None
    updated_by: Optional[int] = None


class ProductOptionValueUpdate(ORMBaseSchema):
    """상품 옵션 값 수정 요청 스키마."""

    option_value: Optional[str] = Field(default=None, max_length=100)


class ProductOptionValueRead(TimestampSchema):
    """상품 옵션 값 응답 스키마."""

    id: int
    option_id: int
    option_value: str
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[int] = None


class ProductOptionRead(TimestampSchema):
    """상품 옵션 응답 스키마."""

    id: int
    product_id: int
    option_name: str
    sort_order: Optional[int] = None
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[int] = None
    values: list[ProductOptionValueRead] = Field(default_factory=list)


class ProductImageCreate(ORMBaseSchema):
    """상품 이미지 생성 요청 스키마 (nested create 용)."""

    image_url: str = Field(..., max_length=500)
    is_main_image: Optional[bool] = None
    sort_order: Optional[int] = None
    created_by: Optional[int] = None


class ProductImageUpdate(ORMBaseSchema):
    """상품 이미지 수정 요청 스키마."""

    image_url: Optional[str] = Field(default=None, max_length=500)
    is_main_image: Optional[bool] = None
    sort_order: Optional[int] = None
    updated_by: Optional[int] = None


class ProductImageRead(TimestampSchema):
    """상품 이미지 응답 스키마."""

    id: int
    product_id: int
    image_url: str
    is_main_image: Optional[bool] = None
    sort_order: Optional[int] = None
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[int] = None


class SKUCreate(ORMBaseSchema):
    """SKU 생성 요청 스키마 (option_value_ids로 옵션 값 연결 지원)."""

    product_id: int
    sku_code: str = Field(..., max_length=100)
    sale_price_amount: Decimal = Field(..., max_digits=12, decimal_places=2)
    stock_quantity: int = Field(default=0)
    sku_status: str = Field(..., max_length=20)
    created_by: Optional[int] = None
    option_value_ids: list[int] = Field(default_factory=list)


class SKUUpdate(ORMBaseSchema):
    """SKU 수정 요청 스키마."""

    sku_code: Optional[str] = Field(default=None, max_length=100)
    sale_price_amount: Optional[Decimal] = Field(default=None, max_digits=12, decimal_places=2)
    stock_quantity: Optional[int] = None
    sku_status: Optional[str] = Field(default=None, max_length=20)
    updated_by: Optional[int] = None


class SKURead(TimestampSchema):
    """SKU 응답 스키마."""

    id: int
    product_id: int
    sku_code: str
    sale_price_amount: Decimal
    stock_quantity: int
    sku_status: str
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[int] = None
    option_values: list[ProductOptionValueRead] = Field(default_factory=list)


class ProductBase(ORMBaseSchema):
    """상품 공통 입력 스키마."""

    product_name: str = Field(..., max_length=255)
    product_description: Optional[str] = None
    brand_id: Optional[int] = None
    product_status: str = Field(..., max_length=20)
    base_price_amount: Decimal = Field(..., max_digits=12, decimal_places=2)
    thumbnail_image_url: Optional[str] = None


class ProductCreate(ProductBase):
    """상품 생성 요청 스키마 (category_ids, options, images 중첩 생성 지원)."""

    created_by: Optional[int] = None
    category_ids: list[int] = Field(default_factory=list)
    options: list[ProductOptionCreate] = Field(default_factory=list)
    images: list[ProductImageCreate] = Field(default_factory=list)


class ProductUpdate(ORMBaseSchema):
    """상품 수정 요청 스키마."""

    product_name: Optional[str] = Field(default=None, max_length=255)
    product_description: Optional[str] = None
    brand_id: Optional[int] = None
    product_status: Optional[str] = Field(default=None, max_length=20)
    base_price_amount: Optional[Decimal] = Field(default=None, max_digits=12, decimal_places=2)
    thumbnail_image_url: Optional[str] = None
    updated_by: Optional[int] = None
    category_ids: Optional[list[int]] = None


class ProductRead(ProductBase, TimestampSchema):
    """상품 상세 응답 스키마."""

    id: int
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[int] = None
    brand: Optional[BrandRead] = None
    categories: list[CategoryRead] = Field(default_factory=list)
    options: list[ProductOptionRead] = Field(default_factory=list)
    images: list[ProductImageRead] = Field(default_factory=list)
    skus: list[SKURead] = Field(default_factory=list)


__all__ = [
    "BrandCreate",
    "BrandRead",
    "CategoryCreate",
    "CategoryUpdate",
    "CategoryRead",
    "ProductBase",
    "ProductCreate",
    "ProductImageCreate",
    "ProductImageUpdate",
    "ProductImageRead",
    "ProductOptionCreate",
    "ProductOptionUpdate",
    "ProductOptionValueCreate",
    "ProductOptionValueUpdate",
    "ProductOptionRead",
    "ProductOptionValueRead",
    "ProductRead",
    "ProductUpdate",
    "SKUCreate",
    "SKURead",
    "SKUUpdate",
]
