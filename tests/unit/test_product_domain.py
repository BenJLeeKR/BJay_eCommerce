from decimal import Decimal

from app.models.product import Product, SKU, SKUOptionValueMap
from app.routers.product import router as product_router
from app.routers.sku import router as sku_router
from app.schemas.product import ProductCreate, ProductUpdate, SKUCreate


def test_product_table_and_indexes_are_defined() -> None:
    """상품 모델의 핵심 테이블 메타데이터가 정의되어야 한다."""
    index_names = {index.name for index in Product.__table__.indexes}

    assert Product.__tablename__ == "product"
    assert "idx_product_status" in index_names
    assert Product.__table__.c.product_name.nullable is False
    assert Product.__table__.c.base_price_amount.nullable is False


def test_sku_table_and_indexes_are_defined() -> None:
    """SKU 모델의 핵심 제약 조건과 인덱스가 정의되어야 한다."""
    index_names = {index.name for index in SKU.__table__.indexes}

    assert SKU.__tablename__ == "sku"
    assert "idx_sku_product_id" in index_names
    assert SKU.__table__.c.sku_code.unique is True


def test_product_create_schema_validates_required_fields() -> None:
    """상품 생성 스키마가 핵심 필드를 검증해야 한다."""
    payload = ProductCreate(
        product_name="테스트 상품",
        product_description="설명",
        brand_id=1,
        product_status="ACTIVE",
        base_price_amount=Decimal("12900.00"),
        thumbnail_image_url="https://example.com/image.png",
        created_by=100,
    )

    assert payload.product_name == "테스트 상품"
    assert payload.base_price_amount == Decimal("12900.00")
    assert payload.product_status == "ACTIVE"


def test_product_update_schema_supports_partial_update() -> None:
    """상품 수정 스키마는 부분 업데이트를 지원해야 한다."""
    payload = ProductUpdate(product_status="INACTIVE", updated_by=200)

    assert payload.model_dump(exclude_unset=True) == {
        "product_status": "INACTIVE",
        "updated_by": 200,
    }


def test_product_router_registers_expected_routes() -> None:
    """상품 라우터에 CRUD 엔드포인트가 등록되어야 한다."""
    route_map = {(tuple(sorted(route.methods)), route.path) for route in product_router.routes}

    assert (("GET",), "/products") in route_map
    assert (("GET",), "/products/{product_id}") in route_map
    assert (("POST",), "/products") in route_map
    assert (("PUT",), "/products/{product_id}") in route_map
    assert (("DELETE",), "/products/{product_id}") in route_map


def test_sku_create_schema_supports_option_value_ids() -> None:
    """SKUCreate 스키마가 option_value_ids 리스트를 받을 수 있어야 한다."""
    payload = SKUCreate(
        product_id=1,
        sku_code="TEST-SKU-001",
        sale_price_amount=Decimal("10000.00"),
        stock_quantity=10,
        sku_status="ACTIVE",
        option_value_ids=[1, 2, 3],
    )

    assert payload.product_id == 1
    assert payload.sku_code == "TEST-SKU-001"
    assert payload.option_value_ids == [1, 2, 3]


def test_sku_create_schema_default_option_value_ids_is_empty() -> None:
    """SKUCreate의 option_value_ids 기본값은 빈 리스트여야 한다."""
    payload = SKUCreate(
        product_id=2,
        sku_code="TEST-SKU-002",
        sale_price_amount=Decimal("20000.00"),
        stock_quantity=5,
        sku_status="ACTIVE",
    )

    assert payload.option_value_ids == []


def test_sku_option_value_map_table_is_defined() -> None:
    """SKUOptionValueMap 모델의 복합 PK와 테이블명이 정의되어야 한다."""
    pk_columns = list(SKUOptionValueMap.__table__.primary_key.columns)

    assert SKUOptionValueMap.__tablename__ == "sku_option_value_map"
    assert len(pk_columns) == 2
    assert pk_columns[0].name == "sku_id"
    assert pk_columns[1].name == "option_value_id"
    assert SKUOptionValueMap.__table__.c.sku_id.foreign_keys
    assert SKUOptionValueMap.__table__.c.option_value_id.foreign_keys


def test_sku_router_registers_expected_routes() -> None:
    """SKU 라우터에 CRUD 엔드포인트가 등록되어야 한다."""
    route_map = {(tuple(sorted(route.methods)), route.path) for route in sku_router.routes}

    assert (("GET",), "/skus") in route_map
    assert (("GET",), "/skus/{sku_id}") in route_map
    assert (("POST",), "/skus") in route_map
    assert (("PUT",), "/skus/{sku_id}") in route_map
    assert (("DELETE",), "/skus/{sku_id}") in route_map

