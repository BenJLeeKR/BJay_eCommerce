from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import BigInteger, Boolean, DateTime, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from app.core.config import settings
from app.database import Base


class SearchProductIndex(Base):
    """검색 인덱스 데이터를 저장한다."""

    __tablename__ = "search_product_index"

    product_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    product_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    product_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    category_ids: Mapped[Optional[list[int]]] = mapped_column(ARRAY(BigInteger), nullable=True)
    brand_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    price_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    average_rating: Mapped[Optional[Decimal]] = mapped_column(Numeric(3, 2), nullable=True)
    review_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    stock_quantity: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    search_keywords: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())


class SearchKeyword(Base):
    """검색 키워드 집계를 저장한다."""

    __tablename__ = "search_keyword"

    keyword: Mapped[str] = mapped_column(String(255), primary_key=True)
    search_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_searched_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class SearchAutocomplete(Base):
    """자동완성 데이터를 저장한다."""

    __tablename__ = "search_autocomplete"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    keyword: Mapped[str] = mapped_column(String(255), nullable=False)
    weight: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())


class SearchSynonym(Base):
    """동의어 데이터를 저장한다."""

    __tablename__ = "search_synonym"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    keyword: Mapped[str] = mapped_column(String(255), nullable=False)
    synonym: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())