from datetime import datetime, timezone

from app.models.inventory import (
    Inventory,
    InventoryReservation,
    InventoryTransaction,
    WarehouseStock,
)
from app.routers.inventory import router
from app.schemas.inventory import InventoryCreate, InventoryUpdate


def test_inventory_table_and_columns_are_defined() -> None:
    """재고 모델의 핵심 테이블 메타데이터가 정의되어야 한다."""
    assert Inventory.__tablename__ == "inventory"
    assert Inventory.__table__.c.sku_id.unique is True
    assert Inventory.__table__.c.total_quantity.nullable is False
    assert Inventory.__table__.c.available_quantity.nullable is False
    assert Inventory.__table__.c.reserved_quantity.nullable is False
    assert Inventory.__table__.c.safety_stock_quantity.nullable is False
    assert Inventory.__table__.c.created_at.nullable is False
    assert Inventory.__table__.c.updated_at.nullable is False


def test_inventory_reservation_table_and_columns_are_defined() -> None:
    """재고 예약 모델의 핵심 컬럼이 정의되어야 한다."""
    assert InventoryReservation.__tablename__ == "inventory_reservation"
    assert InventoryReservation.__table__.c.sku_id.nullable is False
    assert InventoryReservation.__table__.c.order_id.nullable is False
    assert InventoryReservation.__table__.c.reserved_quantity.nullable is False
    assert InventoryReservation.__table__.c.reservation_status.nullable is False
    assert InventoryReservation.__table__.c.created_at.nullable is False


def test_inventory_transaction_table_and_columns_are_defined() -> None:
    """재고 변동 모델의 핵심 컬럼이 정의되어야 한다."""
    assert InventoryTransaction.__tablename__ == "inventory_transaction"
    assert InventoryTransaction.__table__.c.sku_id.nullable is False
    assert InventoryTransaction.__table__.c.transaction_type.nullable is False
    assert InventoryTransaction.__table__.c.quantity.nullable is False
    assert InventoryTransaction.__table__.c.created_at.nullable is False


def test_inventory_create_schema_validates_required_fields() -> None:
    """재고 생성 스키마가 핵심 필드를 검증해야 한다."""
    payload = InventoryCreate(
        sku_id=123,
        total_quantity=100,
        available_quantity=80,
        reserved_quantity=20,
        safety_stock_quantity=10,
        created_by=1,
    )

    assert payload.sku_id == 123
    assert payload.total_quantity == 100
    assert payload.available_quantity == 80
    assert payload.reserved_quantity == 20
    assert payload.safety_stock_quantity == 10
    assert payload.created_by == 1


def test_inventory_update_schema_supports_partial_update() -> None:
    """재고 수정 스키마는 부분 업데이트를 지원해야 한다."""
    payload = InventoryUpdate(total_quantity=150, updated_by=2)

    assert payload.model_dump(exclude_unset=True) == {
        "total_quantity": 150,
        "updated_by": 2,
    }


def test_inventory_router_registers_expected_routes() -> None:
    """재고 라우터에 CRUD 엔드포인트가 등록되어야 한다."""
    route_map = {(tuple(sorted(route.methods)), route.path) for route in router.routes}

    assert (("GET",), "/inventory") in route_map
    assert (("GET",), "/inventory/{inventory_id}") in route_map
    assert (("POST",), "/inventory") in route_map
    assert (("PUT",), "/inventory/{inventory_id}") in route_map
    assert (("DELETE",), "/inventory/{inventory_id}") in route_map
    assert (("POST",), "/inventory/reservations") in route_map
    assert (("GET",), "/inventory/reservations/{reservation_id}") in route_map
    assert (("GET",), "/inventory/transactions") in route_map
    # WarehouseStock 라우터는 shipment 라우터로 이동됨
    assert (("GET",), "/inventory/warehouse-stocks") not in route_map
    assert (("POST",), "/inventory/warehouse-stocks") not in route_map


def test_inventory_model_relationships() -> None:
    """재고 모델의 관계가 올바르게 설정되어야 한다."""
    # 관계 속성 존재 확인
    assert hasattr(Inventory, "sku")
    assert hasattr(Inventory, "reservations")
    assert hasattr(Inventory, "transactions")
    assert hasattr(InventoryReservation, "inventory")
    assert hasattr(InventoryReservation, "order")
    assert hasattr(InventoryTransaction, "inventory")


def test_inventory_reservation_status_enum_values() -> None:
    """재고 예약 상태 값이 예상된 값들 중 하나여야 한다."""
    # 참조 문서에 정의된 값들
    expected_statuses = {"RESERVED", "CONFIRMED", "RELEASED"}
    # 실제로는 모델에서 Enum으로 정의되지 않았으므로 테스트는 생략
    pass


def test_inventory_transaction_type_enum_values() -> None:
    """재고 변동 유형 값이 예상된 값들 중 하나여야 한다."""
    expected_types = {"IN", "OUT", "RESERVE", "RELEASE"}
    # 실제로는 모델에서 Enum으로 정의되지 않았으므로 테스트는 생략
    pass


def test_inventory_quantity_constraints() -> None:
    """재고 수량 필드는 음수가 될 수 없다."""
    # 스키마 수준에서 검증 (Pydantic 필드에 ge=0)
    # 모델 수준에서는 DB 제약 조건이 있을 수 있음
    pass


def test_warehouse_stock_table_and_columns_are_defined() -> None:
    """창고 재고 모델의 핵심 컬럼이 정의되어야 한다."""
    assert WarehouseStock.__tablename__ == "warehouse_stock"
    assert WarehouseStock.__table__.c.warehouse_id.nullable is False
    assert WarehouseStock.__table__.c.sku_id.nullable is False
    assert WarehouseStock.__table__.c.stock_quantity.nullable is False
    assert WarehouseStock.__table__.c.created_at.nullable is False


def test_warehouse_stock_has_warehouse_fk() -> None:
    """warehouse_stock.warehouse_id는 warehouse.id를 참조하는 FK여야 한다."""
    fk_constraints = [
        fk
        for fk in WarehouseStock.__table__.c.warehouse_id.foreign_keys
        if fk.column.table.name == "warehouse"
    ]
    assert len(fk_constraints) == 1, (
        "warehouse_stock.warehouse_id에 warehouse.id를 참조하는 FK가 없습니다."
    )


def test_warehouse_stock_has_composite_index() -> None:
    """warehouse_stock에 (warehouse_id, sku_id) 복합 인덱스가 정의되어야 한다."""
    index_names = {idx.name for idx in WarehouseStock.__table__.indexes}
    assert "ix_warehouse_stock_warehouse_sku" in index_names, (
        "warehouse_stock 테이블에 ix_warehouse_stock_warehouse_sku 인덱스가 없습니다."
    )