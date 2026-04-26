from decimal import Decimal

from app.models.order import OrderHeader, OrderItem
from app.routers.order import router
from app.schemas.order import OrderCreate, OrderUpdate, OrderItemCreate


def test_order_header_table_and_indexes_are_defined() -> None:
    """주문 헤더 모델의 핵심 테이블 메타데이터가 정의되어야 한다."""
    index_names = {index.name for index in OrderHeader.__table__.indexes}

    assert OrderHeader.__tablename__ == "order_header"
    assert "idx_order_header_user_id" in index_names
    assert OrderHeader.__table__.c.order_number.nullable is False
    assert OrderHeader.__table__.c.order_number.unique is True
    assert OrderHeader.__table__.c.user_id.nullable is False
    assert OrderHeader.__table__.c.order_status.nullable is False
    assert OrderHeader.__table__.c.total_product_amount.nullable is False
    assert OrderHeader.__table__.c.total_pay_amount.nullable is False


def test_order_item_table_and_indexes_are_defined() -> None:
    """주문 상품 모델의 핵심 제약 조건과 인덱스가 정의되어야 한다."""
    index_names = {index.name for index in OrderItem.__table__.indexes}

    assert OrderItem.__tablename__ == "order_item"
    assert "idx_order_item_order_id" in index_names
    assert "idx_order_item_sku_id" in index_names
    assert OrderItem.__table__.c.order_id.nullable is False
    assert OrderItem.__table__.c.sku_id.nullable is False
    assert OrderItem.__table__.c.product_name.nullable is False
    assert OrderItem.__table__.c.quantity.nullable is False
    assert OrderItem.__table__.c.unit_price_amount.nullable is False
    assert OrderItem.__table__.c.total_price_amount.nullable is False


def test_order_create_schema_validates_required_fields() -> None:
    """주문 생성 스키마가 핵심 필드를 검증해야 한다."""
    payload = OrderCreate(
        order_number="ORD-20250423-001",
        user_id=100,
        order_status="CREATED",
        total_product_amount=Decimal("50000.00"),
        total_discount_amount=Decimal("5000.00"),
        total_shipping_amount=Decimal("3000.00"),
        total_pay_amount=Decimal("48000.00"),
        created_by=1,
        items=[
            OrderItemCreate(
                sku_id=200,
                product_name="테스트 상품",
                option_summary="색상:블랙, 사이즈:L",
                quantity=2,
                unit_price_amount=Decimal("25000.00"),
                total_price_amount=Decimal("50000.00"),
                created_by=1,
            )
        ],
    )

    assert payload.order_number == "ORD-20250423-001"
    assert payload.user_id == 100
    assert payload.order_status == "CREATED"
    assert payload.total_product_amount == Decimal("50000.00")
    assert payload.total_pay_amount == Decimal("48000.00")
    assert len(payload.items) == 1
    assert payload.items[0].sku_id == 200


def test_order_update_schema_supports_partial_update() -> None:
    """주문 수정 스키마는 부분 업데이트를 지원해야 한다."""
    payload = OrderUpdate(order_status="PAID", updated_by=2)

    assert payload.model_dump(exclude_unset=True) == {
        "order_status": "PAID",
        "updated_by": 2,
    }


def test_order_create_schema_supports_cart_id() -> None:
    """OrderCreate 스키마는 cart_id Optional[int] 필드를 지원해야 한다."""
    payload = OrderCreate(
        order_number="ORD-CART-001",
        user_id=100,
        cart_id=42,
        order_status="PENDING",
        total_product_amount=Decimal("50000.00"),
        total_discount_amount=Decimal("0.00"),
        total_shipping_amount=Decimal("0.00"),
        total_pay_amount=Decimal("50000.00"),
        created_by=1,
    )

    assert payload.cart_id == 42

    # cart_id가 제공되지 않은 경우 None이어야 함
    payload_no_cart = OrderCreate(
        order_number="ORD-CART-002",
        user_id=100,
        order_status="PENDING",
        total_product_amount=Decimal("50000.00"),
        total_discount_amount=Decimal("0.00"),
        total_shipping_amount=Decimal("0.00"),
        total_pay_amount=Decimal("50000.00"),
        created_by=1,
    )
    assert payload_no_cart.cart_id is None


def test_order_header_model_has_cart_id_column() -> None:
    """OrderHeader 모델은 cart_id 컬럼을 정의해야 한다."""
    assert hasattr(OrderHeader, "cart_id")
    assert OrderHeader.__table__.c.cart_id.nullable is True


def test_order_router_registers_expected_routes() -> None:
    """주문 라우터에 CRUD 엔드포인트가 등록되어야 한다."""
    route_map = {(tuple(sorted(route.methods)), route.path) for route in router.routes}

    assert (("GET",), "/orders") in route_map
    assert (("GET",), "/orders/{order_id}") in route_map
    assert (("POST",), "/orders") in route_map
    assert (("PUT",), "/orders/{order_id}") in route_map
    assert (("DELETE",), "/orders/{order_id}") in route_map