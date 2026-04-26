from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from app.models.cart import Cart, CartItem, CartItemOptionSnapshot, CartCoupon
from app.models.inventory import Inventory
from app.models.product import SKU
from app.routers.cart import _validate_sku_for_cart, router
from app.schemas.cart import (
    CartCouponCreate,
    CartCouponNestedCreate,
    CartCreate,
    CartItemCreate,
    CartItemNestedCreate,
    CartItemOptionSnapshotCreate,
    CartItemOptionSnapshotNestedCreate,
    CartItemUpdate,
    CartUpdate,
)


def test_cart_table_and_indexes_are_defined() -> None:
    """장바구니 모델의 핵심 테이블 메타데이터가 정의되어야 한다."""
    index_names = {index.name for index in Cart.__table__.indexes}

    assert Cart.__tablename__ == "cart"
    assert "idx_cart_user_id" in index_names
    assert "idx_cart_session_id" in index_names
    assert Cart.__table__.c.cart_status.nullable is False
    assert Cart.__table__.c.created_at.nullable is False


def test_cart_item_table_and_indexes_are_defined() -> None:
    """장바구니 상품 항목 모델의 핵심 제약 조건과 인덱스가 정의되어야 한다."""
    index_names = {index.name for index in CartItem.__table__.indexes}

    assert CartItem.__tablename__ == "cart_item"
    assert "idx_cart_item_cart_id" in index_names
    assert "uq_cart_item" in index_names
    assert CartItem.__table__.c.quantity.nullable is False
    assert CartItem.__table__.c.unit_price_amount.nullable is False
    assert CartItem.__table__.c.total_price_amount.nullable is False


def test_cart_item_option_snapshot_table_is_defined() -> None:
    """장바구니 상품 옵션 스냅샷 테이블이 정의되어야 한다."""
    assert CartItemOptionSnapshot.__tablename__ == "cart_item_option_snapshot"
    assert CartItemOptionSnapshot.__table__.c.cart_item_id.nullable is False
    assert CartItemOptionSnapshot.__table__.c.created_at.nullable is False


def test_cart_coupon_table_is_defined() -> None:
    """장바구니 쿠폰 테이블이 정의되어야 한다."""
    assert CartCoupon.__tablename__ == "cart_coupon"
    assert CartCoupon.__table__.c.cart_id.nullable is False
    assert CartCoupon.__table__.c.coupon_id.nullable is False
    assert CartCoupon.__table__.c.created_at.nullable is False


def test_cart_create_schema_validates_required_fields() -> None:
    """장바구니 생성 스키마가 핵심 필드를 검증해야 한다.
    (session_id는 라우터의 get_session_id()에서 생성되므로 스키마에 포함되지 않음)
    """
    payload = CartCreate(
        user_id=1,
        cart_status="ACTIVE",
        last_added_at=None,
        created_by=100,
    )

    assert payload.user_id == 1
    assert payload.cart_status == "ACTIVE"
    assert payload.created_by == 100


def test_cart_update_schema_supports_partial_update() -> None:
    """장바구니 수정 스키마는 부분 업데이트를 지원해야 한다."""
    payload = CartUpdate(cart_status="ORDERED", updated_by=200)

    assert payload.model_dump(exclude_unset=True) == {
        "cart_status": "ORDERED",
        "updated_by": 200,
    }


def test_cart_item_create_schema_validates_required_fields() -> None:
    """장바구니 상품 항목 생성 스키마가 핵심 필드를 검증해야 한다."""
    payload = CartItemCreate(
        cart_id=1,
        sku_id=100,
        quantity=2,
        unit_price_amount=Decimal("15000.00"),
        total_price_amount=Decimal("30000.00"),
        is_selected=True,
        added_at=None,
        created_by=100,
    )

    assert payload.cart_id == 1
    assert payload.sku_id == 100
    assert payload.quantity == 2
    assert payload.unit_price_amount == Decimal("15000.00")
    assert payload.total_price_amount == Decimal("30000.00")
    assert payload.is_selected is True


def test_cart_item_update_schema_supports_partial_update() -> None:
    """장바구니 상품 항목 수정 스키마는 부분 업데이트를 지원해야 한다."""
    payload = CartItemUpdate(quantity=5, updated_by=200)

    assert payload.model_dump(exclude_unset=True) == {
        "quantity": 5,
        "updated_by": 200,
    }


def test_cart_item_option_snapshot_create_schema_validates_fields() -> None:
    """장바구니 상품 옵션 스냅샷 생성 스키마가 필드를 검증해야 한다."""
    payload = CartItemOptionSnapshotCreate(
        cart_item_id=10,
        option_name="색상",
        option_value="블랙",
    )

    assert payload.cart_item_id == 10
    assert payload.option_name == "색상"
    assert payload.option_value == "블랙"


def test_cart_coupon_create_schema_validates_fields() -> None:
    """장바구니 쿠폰 생성 스키마가 필드를 검증해야 한다."""
    payload = CartCouponCreate(
        cart_id=1,
        coupon_id=5,
        discount_amount=Decimal("5000.00"),
    )

    assert payload.cart_id == 1
    assert payload.coupon_id == 5
    assert payload.discount_amount == Decimal("5000.00")


def test_cart_create_schema_supports_nested_items() -> None:
    """장바구니 생성 스키마는 items와 coupons 중첩 필드를 지원해야 한다."""
    payload = CartCreate(
        user_id=1,
        cart_status="ACTIVE",
        created_by=100,
        items=[
            CartItemNestedCreate(
                sku_id=100,
                quantity=2,
                unit_price_amount=Decimal("15000.00"),
                total_price_amount=Decimal("30000.00"),
            ),
        ],
        coupons=[
            CartCouponNestedCreate(
                coupon_id=5,
                discount_amount=Decimal("5000.00"),
            ),
        ],
    )

    assert len(payload.items) == 1
    assert payload.items[0].sku_id == 100
    assert payload.items[0].quantity == 2
    assert payload.items[0].is_selected is True
    assert len(payload.coupons) == 1
    assert payload.coupons[0].coupon_id == 5
    assert payload.coupons[0].discount_amount == Decimal("5000.00")


def test_cart_create_schema_empty_items_coupons_default() -> None:
    """장바구니 생성 스키마는 items/coupons를 지정하지 않으면 빈 리스트가 기본값이어야 한다."""
    payload = CartCreate(
        cart_status="ACTIVE",
    )

    assert payload.items == []
    assert payload.coupons == []


def test_cart_item_nested_create_schema_validates_fields() -> None:
    """CartItemNestedCreate가 필수 필드를 검증해야 한다."""
    payload = CartItemNestedCreate(
        sku_id=100,
        quantity=2,
        unit_price_amount=Decimal("15000.00"),
        total_price_amount=Decimal("30000.00"),
        option_snapshots=[
            CartItemOptionSnapshotNestedCreate(
                option_name="색상",
                option_value="블랙",
            ),
        ],
    )

    assert payload.sku_id == 100
    assert payload.quantity == 2
    assert payload.unit_price_amount == Decimal("15000.00")
    assert payload.total_price_amount == Decimal("30000.00")
    assert payload.is_selected is True
    assert len(payload.option_snapshots) == 1
    assert payload.option_snapshots[0].option_name == "색상"
    assert payload.option_snapshots[0].option_value == "블랙"


def test_cart_item_nested_create_empty_snapshots_default() -> None:
    """CartItemNestedCreate의 option_snapshots는 지정하지 않으면 빈 리스트여야 한다."""
    payload = CartItemNestedCreate(
        sku_id=100,
        quantity=1,
        unit_price_amount=Decimal("10000.00"),
        total_price_amount=Decimal("10000.00"),
    )

    assert payload.option_snapshots == []


def test_cart_coupon_nested_create_schema_validates_fields() -> None:
    """CartCouponNestedCreate가 필수 필드를 검증해야 한다."""
    payload = CartCouponNestedCreate(
        coupon_id=5,
        discount_amount=Decimal("5000.00"),
    )

    assert payload.coupon_id == 5
    assert payload.discount_amount == Decimal("5000.00")


def test_cart_item_option_snapshot_nested_create_schema_validates_fields() -> None:
    """CartItemOptionSnapshotNestedCreate가 필드를 검증해야 한다."""
    payload = CartItemOptionSnapshotNestedCreate(
        option_name="사이즈",
        option_value="L",
    )

    assert payload.option_name == "사이즈"
    assert payload.option_value == "L"


def test_cart_router_registers_expected_routes() -> None:
    """장바구니 라우터에 CRUD 엔드포인트가 등록되어야 한다."""
    route_map = {(tuple(sorted(route.methods)), route.path) for route in router.routes}

    assert (("GET",), "/carts") in route_map
    assert (("GET",), "/carts/{cart_id}") in route_map
    assert (("POST",), "/carts") in route_map
    assert (("PUT",), "/carts/{cart_id}") in route_map
    assert (("DELETE",), "/carts/{cart_id}") in route_map
    assert (("GET",), "/carts/{cart_id}/items") in route_map
    assert (("POST",), "/carts/{cart_id}/items") in route_map
    assert (("PUT",), "/items/{cart_item_id}") in route_map
    assert (("DELETE",), "/items/{cart_item_id}") in route_map
    assert (("POST",), "/items/{cart_item_id}/option-snapshots") in route_map
    assert (("POST",), "/carts/{cart_id}/coupons") in route_map


# ---------- SKU Validation Tests ----------


def _make_mock_sku(
    sku_id: int = 100,
    sku_status: str = "ACTIVE",
    stock_quantity: int = 10,
    deleted_at=None,
) -> MagicMock:
    """_validate_sku_for_cart 테스트용 Mock SKU 객체를 생성한다."""
    sku = MagicMock(spec=SKU)
    sku.id = sku_id
    sku.sku_status = sku_status
    sku.stock_quantity = stock_quantity
    sku.deleted_at = deleted_at
    return sku


def _make_mock_inventory(
    sku_id: int = 100,
    available_quantity: int = 10,
    total_quantity: int = 10,
    reserved_quantity: int = 0,
) -> MagicMock:
    """_validate_sku_for_cart 테스트용 Mock Inventory 객체를 생성한다."""
    inventory = MagicMock(spec=Inventory)
    inventory.sku_id = sku_id
    inventory.available_quantity = available_quantity
    inventory.total_quantity = total_quantity
    inventory.reserved_quantity = reserved_quantity
    return inventory


def _make_mock_db_with_inventory(
    mock_inventory: MagicMock,
) -> MagicMock:
    """db.query(Inventory).filter().first() 체인을 반환하는 Mock DB를 생성한다."""
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = mock_inventory
    return mock_db


class TestValidateSkuForCart:
    """_validate_sku_for_cart() 함수의 검증 로직을 테스트한다."""

    def test_valid_sku_passes_validation(self) -> None:
        """유효한 SKU와 충분한 재고가 있으면 검증을 통과해야 한다."""
        mock_sku = _make_mock_sku()
        mock_inventory = _make_mock_inventory(available_quantity=10)
        mock_db = _make_mock_db_with_inventory(mock_inventory)
        with patch("app.routers.cart.sku_crud.get", return_value=mock_sku):
            result = _validate_sku_for_cart(mock_db, sku_id=100, quantity=5)
        assert result is mock_sku

    def test_nonexistent_sku_raises_404(self) -> None:
        """존재하지 않는 SKU는 404 에러를 발생시켜야 한다."""
        with patch("app.routers.cart.sku_crud.get", return_value=None):
            with pytest.raises(HTTPException) as exc_info:
                _validate_sku_for_cart(MagicMock(), sku_id=99999, quantity=1)
        assert exc_info.value.status_code == 404
        assert "찾을 수 없습니다" in exc_info.value.detail

    def test_deleted_sku_raises_404(self) -> None:
        """삭제된 SKU는 404 에러를 발생시켜야 한다."""
        from datetime import datetime, timezone

        mock_sku = _make_mock_sku(deleted_at=datetime.now(timezone.utc))
        with patch("app.routers.cart.sku_crud.get", return_value=mock_sku):
            with pytest.raises(HTTPException) as exc_info:
                _validate_sku_for_cart(MagicMock(), sku_id=100, quantity=1)
        assert exc_info.value.status_code == 404
        assert "삭제된 상품" in exc_info.value.detail

    def test_inactive_sku_raises_409(self) -> None:
        """비활성 상태의 SKU는 409 에러를 발생시켜야 한다."""
        mock_sku = _make_mock_sku(sku_status="INACTIVE")
        with patch("app.routers.cart.sku_crud.get", return_value=mock_sku):
            with pytest.raises(HTTPException) as exc_info:
                _validate_sku_for_cart(MagicMock(), sku_id=100, quantity=1)
        assert exc_info.value.status_code == 409
        assert "판매 중인 상품이 아닙니다" in exc_info.value.detail

    def test_no_inventory_record_raises_409(self) -> None:
        """Inventory 레코드가 없으면 409 에러를 발생시켜야 한다."""
        mock_sku = _make_mock_sku()
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        with patch("app.routers.cart.sku_crud.get", return_value=mock_sku):
            with pytest.raises(HTTPException) as exc_info:
                _validate_sku_for_cart(mock_db, sku_id=100, quantity=1)
        assert exc_info.value.status_code == 409
        assert "재고 정보가 존재하지 않습니다" in exc_info.value.detail

    def test_insufficient_stock_raises_409(self) -> None:
        """Inventory.available_quantity가 부족하면 409 에러를 발생시켜야 한다."""
        mock_sku = _make_mock_sku()
        mock_inventory = _make_mock_inventory(available_quantity=0)
        mock_db = _make_mock_db_with_inventory(mock_inventory)
        with patch("app.routers.cart.sku_crud.get", return_value=mock_sku):
            with pytest.raises(HTTPException) as exc_info:
                _validate_sku_for_cart(mock_db, sku_id=100, quantity=1)
        assert exc_info.value.status_code == 409
        assert "재고가 부족합니다" in exc_info.value.detail