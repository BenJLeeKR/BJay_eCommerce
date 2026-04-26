from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.crud import CRUDBase
from app.models.product import (
    Brand,
    Category,
    Product,
    ProductCategoryMap,
    ProductImage,
    ProductOption,
    ProductOptionValue,
    SKU,
    SKUOptionValueMap,
)
from app.schemas.product import (
    BrandRead,
    CategoryRead,
    ProductCreate,
    ProductImageRead,
    ProductOptionRead,
    ProductOptionValueRead,
    ProductUpdate,
    SKURead,
)


class BrandCRUD(CRUDBase[Brand]):
    """브랜드 CRUD 연산을 담당한다."""

    def __init__(self) -> None:
        super().__init__(Brand)

    def create(self, db: Session, obj_in: BrandRead) -> Brand:
        """브랜드를 생성한다."""
        create_data = obj_in.model_dump(exclude_unset=True)
        db_obj = Brand(**create_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get(self, db: Session, object_id: int) -> Optional[Brand]:
        """브랜드를 ID로 조회한다."""
        return db.get(Brand, object_id)

    def get_by_name(self, db: Session, brand_name: str) -> Optional[Brand]:
        """브랜드를 이름으로 조회한다."""
        stmt = select(Brand).where(Brand.brand_name == brand_name)
        return db.scalar(stmt)

    def get_multi(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Brand]:
        """브랜드 목록을 페이징하여 조회한다."""
        stmt = (
            select(Brand)
            .where(Brand.deleted_at.is_(None))
            .offset(skip)
            .limit(limit)
            .order_by(Brand.id)
        )
        return list(db.scalars(stmt).all())

    def update(
        self,
        db: Session,
        db_obj: Brand,
        obj_in: BrandRead,
    ) -> Brand:
        """브랜드 정보를 수정한다."""
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, object_id: int) -> Optional[Brand]:
        """브랜드를 소프트 삭제한다."""
        db_obj = db.get(Brand, object_id)
        if db_obj is None:
            return None
        from datetime import datetime, timezone

        db_obj.deleted_at = datetime.now(timezone.utc)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj


class CategoryCRUD(CRUDBase[Category]):
    """카테고리 CRUD 연산을 담당한다."""

    def __init__(self) -> None:
        super().__init__(Category)

    def create(self, db: Session, obj_in: CategoryRead) -> Category:
        """카테고리를 생성한다."""
        create_data = obj_in.model_dump(exclude_unset=True)
        db_obj = Category(**create_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get(self, db: Session, object_id: int) -> Optional[Category]:
        """카테고리를 ID로 조회한다."""
        return db.get(Category, object_id)

    def get_by_parent_id(
        self,
        db: Session,
        parent_id: int,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Category]:
        """하위 카테고리 목록을 부모 ID로 조회한다."""
        stmt = (
            select(Category)
            .where(Category.parent_category_id == parent_id)
            .where(Category.deleted_at.is_(None))
            .offset(skip)
            .limit(limit)
            .order_by(Category.id)
        )
        return list(db.scalars(stmt).all())

    def get_multi(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Category]:
        """카테고리 목록을 페이징하여 조회한다."""
        stmt = (
            select(Category)
            .where(Category.deleted_at.is_(None))
            .offset(skip)
            .limit(limit)
            .order_by(Category.id)
        )
        return list(db.scalars(stmt).all())

    def update(
        self,
        db: Session,
        db_obj: Category,
        obj_in: CategoryRead,
    ) -> Category:
        """카테고리 정보를 수정한다."""
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, object_id: int) -> Optional[Category]:
        """카테고리를 소프트 삭제한다."""
        db_obj = db.get(Category, object_id)
        if db_obj is None:
            return None
        from datetime import datetime, timezone

        db_obj.deleted_at = datetime.now(timezone.utc)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj


class ProductCRUD(CRUDBase[Product]):
    """상품 CRUD 연산을 담당한다."""

    def __init__(self) -> None:
        super().__init__(Product)

    def create(self, db: Session, obj_in: ProductCreate) -> Product:
        """상품을 생성한다."""
        create_data = obj_in.model_dump(exclude_unset=True)
        db_obj = Product(**create_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get(self, db: Session, object_id: int) -> Optional[Product]:
        """상품을 ID로 조회한다."""
        return db.get(Product, object_id)

    def get_by_status(
        self,
        db: Session,
        status: str,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Product]:
        """상품 목록을 상태별로 조회한다."""
        stmt = (
            select(Product)
            .where(Product.product_status == status)
            .where(Product.deleted_at.is_(None))
            .offset(skip)
            .limit(limit)
            .order_by(Product.id)
        )
        return list(db.scalars(stmt).all())

    def get_by_brand_id(
        self,
        db: Session,
        brand_id: int,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Product]:
        """상품 목록을 브랜드 ID로 조회한다."""
        stmt = (
            select(Product)
            .where(Product.brand_id == brand_id)
            .where(Product.deleted_at.is_(None))
            .offset(skip)
            .limit(limit)
            .order_by(Product.id)
        )
        return list(db.scalars(stmt).all())

    def get_multi(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Product]:
        """상품 목록을 페이징하여 조회한다."""
        stmt = (
            select(Product)
            .where(Product.deleted_at.is_(None))
            .offset(skip)
            .limit(limit)
            .order_by(Product.id)
        )
        return list(db.scalars(stmt).all())

    def update(
        self,
        db: Session,
        db_obj: Product,
        obj_in: ProductUpdate,
    ) -> Product:
        """상품 정보를 수정한다."""
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, object_id: int) -> Optional[Product]:
        """상품을 소프트 삭제한다."""
        db_obj = db.get(Product, object_id)
        if db_obj is None:
            return None
        from datetime import datetime, timezone

        db_obj.deleted_at = datetime.now(timezone.utc)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj


class ProductCategoryMapCRUD(CRUDBase[ProductCategoryMap]):
    """상품-카테고리 매핑 CRUD 연산을 담당한다."""

    def __init__(self) -> None:
        super().__init__(ProductCategoryMap)

    def create(
        self,
        db: Session,
        product_id: int,
        category_id: int,
    ) -> ProductCategoryMap:
        """상품과 카테고리를 매핑한다."""
        db_obj = ProductCategoryMap(
            product_id=product_id,
            category_id=category_id,
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get(
        self,
        db: Session,
        product_id: int,
        category_id: int,
    ) -> Optional[ProductCategoryMap]:
        """상품-카테고리 매핑을 조회한다."""
        return db.get(ProductCategoryMap, (product_id, category_id))

    def get_by_product_id(
        self,
        db: Session,
        product_id: int,
    ) -> list[ProductCategoryMap]:
        """상품의 카테고리 매핑 목록을 조회한다."""
        stmt = select(ProductCategoryMap).where(
            ProductCategoryMap.product_id == product_id,
        )
        return list(db.scalars(stmt).all())

    def remove(
        self,
        db: Session,
        product_id: int,
        category_id: int,
    ) -> Optional[ProductCategoryMap]:
        """상품-카테고리 매핑을 삭제한다."""
        db_obj = db.get(ProductCategoryMap, (product_id, category_id))
        if db_obj is None:
            return None
        db.delete(db_obj)
        db.commit()
        return db_obj


class ProductOptionCRUD(CRUDBase[ProductOption]):
    """상품 옵션 그룹 CRUD 연산을 담당한다."""

    def __init__(self) -> None:
        super().__init__(ProductOption)

    def create(self, db: Session, obj_in: ProductOptionRead) -> ProductOption:
        """상품 옵션 그룹을 생성한다."""
        create_data = obj_in.model_dump(exclude_unset=True)
        db_obj = ProductOption(**create_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get(self, db: Session, object_id: int) -> Optional[ProductOption]:
        """상품 옵션 그룹을 ID로 조회한다."""
        return db.get(ProductOption, object_id)

    def get_by_product_id(
        self,
        db: Session,
        product_id: int,
    ) -> list[ProductOption]:
        """상품의 옵션 그룹 목록을 조회한다."""
        stmt = (
            select(ProductOption)
            .where(ProductOption.product_id == product_id)
            .where(ProductOption.deleted_at.is_(None))
            .order_by(ProductOption.sort_order)
        )
        return list(db.scalars(stmt).all())

    def get_multi(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[ProductOption]:
        """상품 옵션 그룹 목록을 페이징하여 조회한다."""
        stmt = (
            select(ProductOption)
            .where(ProductOption.deleted_at.is_(None))
            .offset(skip)
            .limit(limit)
            .order_by(ProductOption.id)
        )
        return list(db.scalars(stmt).all())

    def update(
        self,
        db: Session,
        db_obj: ProductOption,
        obj_in: ProductOptionRead,
    ) -> ProductOption:
        """상품 옵션 그룹을 수정한다."""
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, object_id: int) -> Optional[ProductOption]:
        """상품 옵션 그룹을 소프트 삭제한다."""
        db_obj = db.get(ProductOption, object_id)
        if db_obj is None:
            return None
        from datetime import datetime, timezone

        db_obj.deleted_at = datetime.now(timezone.utc)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj


class ProductOptionValueCRUD(CRUDBase[ProductOptionValue]):
    """상품 옵션 값 CRUD 연산을 담당한다."""

    def __init__(self) -> None:
        super().__init__(ProductOptionValue)

    def create(
        self,
        db: Session,
        obj_in: ProductOptionValueRead,
    ) -> ProductOptionValue:
        """상품 옵션 값을 생성한다."""
        create_data = obj_in.model_dump(exclude_unset=True)
        db_obj = ProductOptionValue(**create_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get(self, db: Session, object_id: int) -> Optional[ProductOptionValue]:
        """상품 옵션 값을 ID로 조회한다."""
        return db.get(ProductOptionValue, object_id)

    def get_by_option_id(
        self,
        db: Session,
        option_id: int,
    ) -> list[ProductOptionValue]:
        """옵션 그룹의 값 목록을 조회한다."""
        stmt = (
            select(ProductOptionValue)
            .where(ProductOptionValue.option_id == option_id)
            .where(ProductOptionValue.deleted_at.is_(None))
            .order_by(ProductOptionValue.id)
        )
        return list(db.scalars(stmt).all())

    def get_multi(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[ProductOptionValue]:
        """상품 옵션 값 목록을 페이징하여 조회한다."""
        stmt = (
            select(ProductOptionValue)
            .where(ProductOptionValue.deleted_at.is_(None))
            .offset(skip)
            .limit(limit)
            .order_by(ProductOptionValue.id)
        )
        return list(db.scalars(stmt).all())

    def update(
        self,
        db: Session,
        db_obj: ProductOptionValue,
        obj_in: ProductOptionValueRead,
    ) -> ProductOptionValue:
        """상품 옵션 값을 수정한다."""
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(
        self,
        db: Session,
        object_id: int,
    ) -> Optional[ProductOptionValue]:
        """상품 옵션 값을 소프트 삭제한다."""
        db_obj = db.get(ProductOptionValue, object_id)
        if db_obj is None:
            return None
        from datetime import datetime, timezone

        db_obj.deleted_at = datetime.now(timezone.utc)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj


class SKUCRUD(CRUDBase[SKU]):
    """SKU CRUD 연산을 담당한다."""

    def __init__(self) -> None:
        super().__init__(SKU)

    def create(self, db: Session, obj_in: SKURead) -> SKU:
        """SKU를 생성한다."""
        create_data = obj_in.model_dump(exclude_unset=True)
        db_obj = SKU(**create_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get(self, db: Session, object_id: int) -> Optional[SKU]:
        """SKU를 ID로 조회한다."""
        return db.get(SKU, object_id)

    def get_by_sku_code(self, db: Session, sku_code: str) -> Optional[SKU]:
        """SKU를 코드로 조회한다."""
        stmt = select(SKU).where(SKU.sku_code == sku_code)
        return db.scalar(stmt)

    def get_by_product_id(
        self,
        db: Session,
        product_id: int,
    ) -> list[SKU]:
        """상품의 SKU 목록을 조회한다."""
        stmt = (
            select(SKU)
            .where(SKU.product_id == product_id)
            .where(SKU.deleted_at.is_(None))
            .order_by(SKU.id)
        )
        return list(db.scalars(stmt).all())

    def get_multi(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[SKU]:
        """SKU 목록을 페이징하여 조회한다."""
        stmt = (
            select(SKU)
            .where(SKU.deleted_at.is_(None))
            .offset(skip)
            .limit(limit)
            .order_by(SKU.id)
        )
        return list(db.scalars(stmt).all())

    def update(
        self,
        db: Session,
        db_obj: SKU,
        obj_in: SKURead,
    ) -> SKU:
        """SKU 정보를 수정한다."""
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, object_id: int) -> Optional[SKU]:
        """SKU를 소프트 삭제한다."""
        db_obj = db.get(SKU, object_id)
        if db_obj is None:
            return None
        from datetime import datetime, timezone

        db_obj.deleted_at = datetime.now(timezone.utc)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj


class SKUOptionValueMapCRUD(CRUDBase[SKUOptionValueMap]):
    """SKU-옵션값 매핑 CRUD 연산을 담당한다."""

    def __init__(self) -> None:
        super().__init__(SKUOptionValueMap)

    def create(
        self,
        db: Session,
        sku_id: int,
        option_value_id: int,
    ) -> SKUOptionValueMap:
        """SKU와 옵션 값을 매핑한다."""
        db_obj = SKUOptionValueMap(
            sku_id=sku_id,
            option_value_id=option_value_id,
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get(
        self,
        db: Session,
        sku_id: int,
        option_value_id: int,
    ) -> Optional[SKUOptionValueMap]:
        """SKU-옵션값 매핑을 조회한다."""
        return db.get(SKUOptionValueMap, (sku_id, option_value_id))

    def get_by_sku_id(
        self,
        db: Session,
        sku_id: int,
    ) -> list[SKUOptionValueMap]:
        """SKU의 옵션값 매핑 목록을 조회한다."""
        stmt = select(SKUOptionValueMap).where(
            SKUOptionValueMap.sku_id == sku_id,
        )
        return list(db.scalars(stmt).all())

    def remove(
        self,
        db: Session,
        sku_id: int,
        option_value_id: int,
    ) -> Optional[SKUOptionValueMap]:
        """SKU-옵션값 매핑을 삭제한다."""
        db_obj = db.get(SKUOptionValueMap, (sku_id, option_value_id))
        if db_obj is None:
            return None
        db.delete(db_obj)
        db.commit()
        return db_obj


class ProductImageCRUD(CRUDBase[ProductImage]):
    """상품 이미지 CRUD 연산을 담당한다."""

    def __init__(self) -> None:
        super().__init__(ProductImage)

    def create(self, db: Session, obj_in: ProductImageRead) -> ProductImage:
        """상품 이미지를 생성한다."""
        create_data = obj_in.model_dump(exclude_unset=True)
        db_obj = ProductImage(**create_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get(self, db: Session, object_id: int) -> Optional[ProductImage]:
        """상품 이미지를 ID로 조회한다."""
        return db.get(ProductImage, object_id)

    def get_by_product_id(
        self,
        db: Session,
        product_id: int,
    ) -> list[ProductImage]:
        """상품의 이미지 목록을 조회한다."""
        stmt = (
            select(ProductImage)
            .where(ProductImage.product_id == product_id)
            .where(ProductImage.deleted_at.is_(None))
            .order_by(ProductImage.sort_order)
        )
        return list(db.scalars(stmt).all())

    def get_multi(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[ProductImage]:
        """상품 이미지 목록을 페이징하여 조회한다."""
        stmt = (
            select(ProductImage)
            .where(ProductImage.deleted_at.is_(None))
            .offset(skip)
            .limit(limit)
            .order_by(ProductImage.id)
        )
        return list(db.scalars(stmt).all())

    def update(
        self,
        db: Session,
        db_obj: ProductImage,
        obj_in: ProductImageRead,
    ) -> ProductImage:
        """상품 이미지를 수정한다."""
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, object_id: int) -> Optional[ProductImage]:
        """상품 이미지를 소프트 삭제한다."""
        db_obj = db.get(ProductImage, object_id)
        if db_obj is None:
            return None
        from datetime import datetime, timezone

        db_obj.deleted_at = datetime.now(timezone.utc)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj


brand_crud = BrandCRUD()
category_crud = CategoryCRUD()
product_crud = ProductCRUD()
product_category_map_crud = ProductCategoryMapCRUD()
product_option_crud = ProductOptionCRUD()
product_option_value_crud = ProductOptionValueCRUD()
sku_crud = SKUCRUD()
sku_option_value_map_crud = SKUOptionValueMapCRUD()
product_image_crud = ProductImageCRUD()


__all__ = [
    "BrandCRUD",
    "CategoryCRUD",
    "ProductCRUD",
    "ProductCategoryMapCRUD",
    "ProductOptionCRUD",
    "ProductOptionValueCRUD",
    "SKUCRUD",
    "SKUOptionValueMapCRUD",
    "ProductImageCRUD",
    "brand_crud",
    "category_crud",
    "product_crud",
    "product_category_map_crud",
    "product_option_crud",
    "product_option_value_crud",
    "sku_crud",
    "sku_option_value_map_crud",
    "product_image_crud",
]
