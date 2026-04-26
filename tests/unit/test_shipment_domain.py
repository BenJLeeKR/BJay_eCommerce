from decimal import Decimal

from app.models.inventory import WarehouseStock
from app.models.shipment import Shipment, ShipmentItem, Warehouse
from app.routers.shipment import router
from app.schemas.inventory import WarehouseStockCreate
from app.schemas.shipment import (
    ShipmentCreate,
    ShipmentUpdate,
    ShipmentItemCreate,
    ShipmentItemUpdate,
    WarehouseCreate,
    WarehouseUpdate,
)


def test_shipment_table_and_columns_are_defined() -> None:
    """배송 모델의 핵심 테이블 메타데이터가 정의되어야 한다."""
    assert Shipment.__tablename__ == "shipment"
    assert Shipment.__table__.c.order_id.nullable is False
    assert Shipment.__table__.c.shipment_status.nullable is False
    assert Shipment.__table__.c.total_shipping_amount.nullable is True  # default 0
    assert Shipment.__table__.c.created_at.nullable is False


def test_shipment_item_table_and_columns_are_defined() -> None:
    """배송 상품 모델의 핵심 컬럼이 정의되어야 한다."""
    assert ShipmentItem.__tablename__ == "shipment_item"
    assert ShipmentItem.__table__.c.shipment_id.nullable is False
    assert ShipmentItem.__table__.c.order_item_id.nullable is False
    assert ShipmentItem.__table__.c.sku_id.nullable is False
    assert ShipmentItem.__table__.c.shipped_quantity.nullable is False
    assert ShipmentItem.__table__.c.delivered_quantity.nullable is True  # default 0


def test_warehouse_table_and_columns_are_defined() -> None:
    """창고 모델의 핵심 컬럼이 정의되어야 한다."""
    assert Warehouse.__tablename__ == "warehouse"
    assert Warehouse.__table__.c.warehouse_name.nullable is False
    assert Warehouse.__table__.c.postal_code.nullable is True
    assert Warehouse.__table__.c.address_line1.nullable is True
    assert Warehouse.__table__.c.created_at.nullable is False


def test_shipment_create_schema_validates_required_fields() -> None:
    """배송 생성 스키마가 핵심 필드를 검증해야 한다."""
    payload = ShipmentCreate(
        order_id=123,
        shipment_status="READY",
        shipment_type="NORMAL",
        total_shipping_amount=Decimal("3000.00"),
        shipped_at=None,
        delivered_at=None,
        warehouse_id=1,
        created_by=100,
    )

    assert payload.order_id == 123
    assert payload.shipment_status == "READY"
    assert payload.total_shipping_amount == Decimal("3000.00")
    assert payload.warehouse_id == 1


def test_shipment_update_schema_supports_partial_update() -> None:
    """배송 수정 스키마는 부분 업데이트를 지원해야 한다."""
    payload = ShipmentUpdate(
        shipment_status="SHIPPED",
        shipped_at=None,
        updated_by=200,
    )

    assert payload.model_dump(exclude_unset=True) == {
        "shipment_status": "SHIPPED",
        "shipped_at": None,
        "updated_by": 200,
    }


def test_shipment_item_create_schema_validates_required_fields() -> None:
    """배송 상품 생성 스키마가 핵심 필드를 검증해야 한다."""
    payload = ShipmentItemCreate(
        shipment_id=456,
        order_item_id=789,
        sku_id=999,
        shipped_quantity=2,
        delivered_quantity=0,
        shipment_item_status="READY",
        created_by=100,
    )

    assert payload.shipment_id == 456
    assert payload.order_item_id == 789
    assert payload.shipped_quantity == 2
    assert payload.delivered_quantity == 0


def test_shipment_item_update_schema_supports_partial_update() -> None:
    """배송 상품 수정 스키마는 부분 업데이트를 지원해야 한다."""
    payload = ShipmentItemUpdate(
        delivered_quantity=2,
        updated_by=300,
    )

    assert payload.model_dump(exclude_unset=True) == {
        "delivered_quantity": 2,
        "updated_by": 300,
    }


def test_warehouse_create_schema_validates_required_fields() -> None:
    """창고 생성 스키마가 핵심 필드를 검증해야 한다."""
    payload = WarehouseCreate(
        warehouse_name="서울 창고",
        postal_code="12345",
        address_line1="서울시 강남구",
        address_line2="테헤란로 123",
    )

    assert payload.warehouse_name == "서울 창고"
    assert payload.postal_code == "12345"
    assert payload.address_line1 == "서울시 강남구"
    assert payload.address_line2 == "테헤란로 123"


def test_warehouse_stock_create_schema_validates_required_fields() -> None:
    """창고 재고 생성 스키마가 핵심 필드를 검증해야 한다."""
    payload = WarehouseStockCreate(
        warehouse_id=1,
        sku_id=100,
        stock_quantity=50,
    )

    assert payload.warehouse_id == 1
    assert payload.sku_id == 100
    assert payload.stock_quantity == 50


def test_warehouse_update_schema_supports_partial_update() -> None:
    """창고 수정 스키마는 부분 업데이트를 지원해야 한다."""
    payload = WarehouseUpdate(
        warehouse_name="부산 창고",
        postal_code="54321",
    )

    assert payload.model_dump(exclude_unset=True) == {
        "warehouse_name": "부산 창고",
        "postal_code": "54321",
    }


def test_shipment_router_registers_expected_routes() -> None:
    """배송 라우터에 CRUD 엔드포인트가 등록되어야 한다."""
    route_map = {(tuple(sorted(route.methods)), route.path) for route in router.routes}

    assert (("GET",), "/shipments") in route_map
    assert (("GET",), "/shipments/{shipment_id}") in route_map
    assert (("POST",), "/shipments") in route_map
    assert (("PUT",), "/shipments/{shipment_id}") in route_map
    assert (("DELETE",), "/shipments/{shipment_id}") in route_map

    # 하위 라우터 확인
    assert (("GET",), "/shipments/{shipment_id}/items") in route_map
    assert (("GET",), "/shipments/{shipment_id}/items/{item_id}") in route_map
    assert (("POST",), "/shipments/{shipment_id}/items") in route_map
    assert (("PUT",), "/shipments/{shipment_id}/items/{item_id}") in route_map
    assert (("DELETE",), "/shipments/{shipment_id}/items/{item_id}") in route_map

    # 창고 라우터 확인
    assert (("GET",), "/warehouses") in route_map
    assert (("GET",), "/warehouses/{warehouse_id}") in route_map
    assert (("POST",), "/warehouses") in route_map
    assert (("PUT",), "/warehouses/{warehouse_id}") in route_map
    assert (("DELETE",), "/warehouses/{warehouse_id}") in route_map

    # 창고 재고 라우터 확인
    assert (("GET",), "/warehouses/{warehouse_id}/stocks") in route_map
    assert (("GET",), "/warehouses/{warehouse_id}/stocks/{stock_id}") in route_map
    assert (("POST",), "/warehouses/{warehouse_id}/stocks") in route_map
    assert (("PUT",), "/warehouses/{warehouse_id}/stocks/{stock_id}") in route_map
    assert (("DELETE",), "/warehouses/{warehouse_id}/stocks/{stock_id}") in route_map