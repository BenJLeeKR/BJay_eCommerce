from __future__ import annotations
from typing import Optional

from datetime import datetime
from decimal import Decimal

from pydantic import Field

from app.schemas import ORMBaseSchema, TimestampSchema


class SearchProductIndexBase(ORMBaseSchema):
    """검색 인덱스 공통 입력 스키마."""

    product_id: int
    product_name: Optional[str] = None
    product_description: Optional[str] = None
    category_ids: Optional[list[int]] = None
    brand_name: Optional[str] = None
    price_amount: Optional[Decimal] = Field(None, max_digits=12, decimal_places=2)
    average_rating: Optional[Decimal] = Field(None, max_digits=3, decimal_places=2)
    review_count: Optional[int] = None
    stock_quantity: Optional[int] = None
    is_active: Optional[bool] = None
    search_keywords: Optional[str] = None


class SearchProductIndexCreate(SearchProductIndexBase):
    """검색 인덱스 생성 스키마."""

    pass


class SearchProductIndexUpdate(ORMBaseSchema):
    """검색 인덱스 수정 스키마."""

    product_name: Optional[str] = None
    product_description: Optional[str] = None
    category_ids: Optional[list[int]] = None
    brand_name: Optional[str] = None
    price_amount: Optional[Decimal] = Field(None, max_digits=12, decimal_places=2)
    average_rating: Optional[Decimal] = Field(None, max_digits=3, decimal_places=2)
    review_count: Optional[int] = None
    stock_quantity: Optional[int] = None
    is_active: Optional[bool] = None
    search_keywords: Optional[str] = None


class SearchProductIndexRead(SearchProductIndexBase, TimestampSchema):
    """검색 인덱스 응답 스키마."""

    updated_at: datetime


class SearchKeywordBase(ORMBaseSchema):
    """검색 키워드 공통 입력 스키마."""

    keyword: str = Field(..., max_length=255)
    search_count: int = 0


class SearchKeywordCreate(SearchKeywordBase):
    """검색 키워드 생성 스키마."""

    pass


class SearchKeywordUpdate(ORMBaseSchema):
    """검색 키워드 수정 스키마."""

    search_count: Optional[int] = None
    last_searched_at: Optional[datetime] = None


class SearchKeywordRead(SearchKeywordBase, TimestampSchema):
    """검색 키워드 응답 스키마."""

    last_searched_at: Optional[datetime] = None


class SearchAutocompleteBase(ORMBaseSchema):
    """자동완성 공통 입력 스키마."""

    keyword: str = Field(..., max_length=255)
    weight: int = 0


class SearchAutocompleteCreate(SearchAutocompleteBase):
    """자동완성 생성 스키마."""

    pass


class SearchAutocompleteUpdate(ORMBaseSchema):
    """자동완성 수정 스키마."""

    keyword: Optional[str] = Field(None, max_length=255)
    weight: Optional[int] = None


class SearchAutocompleteRead(SearchAutocompleteBase, TimestampSchema):
    """자동완성 응답 스키마."""

    id: int
    created_at: datetime


class SearchSynonymBase(ORMBaseSchema):
    """동의어 공통 입력 스키마."""

    keyword: str = Field(..., max_length=255)
    synonym: str = Field(..., max_length=255)


class SearchSynonymCreate(SearchSynonymBase):
    """동의어 생성 스키마."""

    pass


class SearchSynonymUpdate(ORMBaseSchema):
    """동의어 수정 스키마."""

    keyword: Optional[str] = Field(None, max_length=255)
    synonym: Optional[str] = Field(None, max_length=255)


class SearchSynonymRead(SearchSynonymBase, TimestampSchema):
    """동의어 응답 스키마."""

    id: int
    created_at: datetime