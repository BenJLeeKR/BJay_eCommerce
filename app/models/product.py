from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Index, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.config import settings
from app.database import Base


class Brand(Base):
    """상품 브랜드 정보를 저장한다."""

    __tablename__ = "brand"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    brand_name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    deleted_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)

    products: Mapped[list["Product"]] = relationship(back_populates="brand")


class Category(Base):
    """상품 카테고리 계층 구조를 저장한다."""

    __tablename__ = "category"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    parent_category_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey(f"{settings.DB_SCHEMA}.category.id"),
        nullable=True,
    )
    category_name: Mapped[str] = mapped_column(String(255), nullable=False)
    category_depth: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    deleted_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)

    parent: Mapped[Optional["Category"]] = relationship(remote_side=[id], back_populates="children")
    children: Mapped[list["Category"]] = relationship(back_populates="parent")
    products: Mapped[list["Product"]] = relationship(
        secondary=lambda: ProductCategoryMap.__table__,
        back_populates="categories",
    )


class Product(Base):
    """상품 기본 정보를 저장한다."""

    __tablename__ = "product"
    __table_args__ = (Index("idx_product_status", "product_status"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    product_name: Mapped[str] = mapped_column(String(255), nullable=False)
    product_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    brand_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey(f"{settings.DB_SCHEMA}.brand.id"),
        nullable=True,
    )
    product_status: Mapped[str] = mapped_column(String(20), nullable=False)
    base_price_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    thumbnail_image_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    deleted_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)

    brand: Mapped[Optional["Brand"]] = relationship(back_populates="products")
    categories: Mapped[list["Category"]] = relationship(
        secondary=lambda: ProductCategoryMap.__table__,
        back_populates="products",
    )
    options: Mapped[list["ProductOption"]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan",
    )
    images: Mapped[list["ProductImage"]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan",
    )
    skus: Mapped[list["SKU"]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan",
    )
    reviews: Mapped[list["Review"]] = relationship(back_populates="product")
    review_summary: Mapped[Optional["ProductReviewSummary"]] = relationship(back_populates="product", uselist=False)


class ProductCategoryMap(Base):
    """상품과 카테고리의 다대다 연결을 저장한다."""

    __tablename__ = "product_category_map"

    product_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(f"{settings.DB_SCHEMA}.product.id"),
        primary_key=True,
    )
    category_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(f"{settings.DB_SCHEMA}.category.id"),
        primary_key=True,
    )


class ProductOption(Base):
    """상품 옵션 그룹 정보를 저장한다."""

    __tablename__ = "product_option"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(f"{settings.DB_SCHEMA}.product.id"),
        nullable=False,
    )
    option_name: Mapped[str] = mapped_column(String(100), nullable=False)
    sort_order: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    deleted_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)

    product: Mapped["Product"] = relationship(back_populates="options")
    values: Mapped[list["ProductOptionValue"]] = relationship(
        back_populates="option",
        cascade="all, delete-orphan",
    )


class ProductOptionValue(Base):
    """옵션 그룹에 속한 개별 옵션 값을 저장한다."""

    __tablename__ = "product_option_value"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    option_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(f"{settings.DB_SCHEMA}.product_option.id"),
        nullable=False,
    )
    option_value: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    deleted_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)

    option: Mapped["ProductOption"] = relationship(back_populates="values")
    skus: Mapped[list["SKU"]] = relationship(
        secondary=lambda: SKUOptionValueMap.__table__,
        back_populates="option_values",
    )


class SKU(Base):
    """실제 판매 단위 SKU 정보를 저장한다."""

    __tablename__ = "sku"
    __table_args__ = (Index("idx_sku_product_id", "product_id"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(f"{settings.DB_SCHEMA}.product.id"),
        nullable=False,
    )
    sku_code: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    sale_price_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    stock_quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    sku_status: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    deleted_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)

    product: Mapped["Product"] = relationship(back_populates="skus")
    option_values: Mapped[list["ProductOptionValue"]] = relationship(
        secondary=lambda: SKUOptionValueMap.__table__,
        back_populates="skus",
    )
    cart_items: Mapped[list["CartItem"]] = relationship(back_populates="sku")
    order_items: Mapped[list["OrderItem"]] = relationship(back_populates="sku")
    inventory: Mapped["Inventory"] = relationship(back_populates="sku", uselist=False)
    shipment_items: Mapped[list["ShipmentItem"]] = relationship(back_populates="sku")


class SKUOptionValueMap(Base):
    """SKU와 옵션 값의 다대다 연결을 저장한다."""

    __tablename__ = "sku_option_value_map"

    sku_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(f"{settings.DB_SCHEMA}.sku.id"),
        primary_key=True,
    )
    option_value_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(f"{settings.DB_SCHEMA}.product_option_value.id"),
        primary_key=True,
    )


class ProductImage(Base):
    """상품 이미지를 저장한다."""

    __tablename__ = "product_image"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(f"{settings.DB_SCHEMA}.product.id"),
        nullable=False,
    )
    image_url: Mapped[str] = mapped_column(Text, nullable=False)
    is_main_image: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True, default=False, server_default="false")
    sort_order: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    deleted_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)

    product: Mapped["Product"] = relationship(back_populates="images")

