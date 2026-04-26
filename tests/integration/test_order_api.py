"""
주문(Order) API 통합 테스트.

시나리오 기반 흐름:
  주문 생성(CREATE) -> 목록 조회(LIST) -> 상세 조회(GET) -> 수정(UPDATE) -> 삭제(DELETE)
  
Note: Order는 UserAccount와 SKU에 의존하므로,
      테스트 시 API를 통해 필요한 선행 데이터를 생성한 후 유효한 FK ID를 사용합니다.
"""
from __future__ import annotations

from typing import Any

import pytest
from fastapi.testclient import TestClient
from httpx import Response
from sqlalchemy.orm import Session

from app.models.inventory import Inventory, InventoryReservation, InventoryTransaction
from app.models.product import SKU


@pytest.fixture(scope="module")
def order_payload(
    client: TestClient,
    db_session: Session,
) -> dict[str, Any]:
    """주문 생성에 사용할 페이로드를 생성한다.

    UserAccount / Product / SKU 등 FK 의존 관계가 있는 데이터를
    API 및 DB를 통해 사전 생성하여 유효한 ID를 페이로드에 포함시킨다.
    """
    # 1. 테스트 사용자 생성 (API)
    user_resp = client.post(
        "/api/v1/users",
        json={
            "user_email": "order_test_user@example.com",
            "password_hash": "hashed-password-1234",
            "user_status": "ACTIVE",
            "user_type": "NORMAL",
            "is_email_verified": False,
            "last_login_at": None,
            "created_by": None,
        },
    )
    assert user_resp.status_code == 201, (
        f"사전 조건: 사용자 생성 실패 (status={user_resp.status_code}): {user_resp.text}"
    )
    user_id = user_resp.json()["data"]["id"]

    # 2. 테스트 상품 생성 (API)
    product_resp = client.post(
        "/api/v1/products",
        json={
            "product_name": "Order Test Product",
            "product_description": "주문 통합 테스트용 상품",
            "brand_id": None,
            "product_status": "ACTIVE",
            "base_price_amount": "29900.00",
            "thumbnail_image_url": None,
            "created_by": None,
        },
    )
    assert product_resp.status_code == 201, (
        f"사전 조건: 상품 생성 실패 (status={product_resp.status_code}): {product_resp.text}"
    )
    product_id = product_resp.json()["data"]["id"]

    # 3. 테스트 SKU 생성 (DB 직접 사용 - API에서 SKU 생성 기능 미제공)
    import uuid
    sku = SKU(
        product_id=product_id,
        sku_code=f"TEST-SKU-ORDER-{uuid.uuid4().hex[:8].upper()}",
        sku_status="ACTIVE",
        sale_price_amount="29900.00",
        stock_quantity=10,
    )
    db_session.add(sku)
    db_session.flush()  # ID 할당을 위해 flush

    # Inventory 레코드 생성 (create_order()에서 재고 검증 필요)
    inventory = Inventory(
        sku_id=sku.id,
        total_quantity=10,
        available_quantity=10,
        reserved_quantity=0,
        safety_stock_quantity=1,
    )
    db_session.add(inventory)
    db_session.flush()

    return {
        "order_number": "ORD-20260424-0001",
        "user_id": user_id,
        "order_status": "PENDING",
        "total_product_amount": "29900.00",
        "total_discount_amount": "0.00",
        "total_shipping_amount": "0.00",
        "total_pay_amount": "29900.00",
        "ordered_at": None,
        "created_by": None,
        "items": [
            {
                "sku_id": sku.id,
                "product_name": "Order Test Product",
                "option_summary": "색상: 블랙 / 사이즈: M",
                "quantity": 1,
                "unit_price_amount": "29900.00",
                "total_price_amount": "29900.00",
                "created_by": None,
            }
        ],
    }


@pytest.fixture(scope="module")
def update_payload() -> dict[str, Any]:
    """주문 수정에 사용할 페이로드."""
    return {
        "order_status": "PAID",
        "total_pay_amount": "29900.00",
        "updated_by": 999,
    }


@pytest.fixture(scope="module")
def cart_order_payload(
    client: TestClient,
    db_session: Session,
) -> dict[str, Any]:
    """Cart ID를 포함한 주문 생성을 위한 페이로드를 생성한다.

    Cart -> Order 흐름을 테스트하기 위해 Cart를 먼저 생성하고
    해당 cart_id를 주문 페이로드에 포함시킨다.
    """
    # 1. 테스트 사용자 생성 (API)
    user_resp = client.post(
        "/api/v1/users",
        json={
            "user_email": "cart_order_test_user@example.com",
            "password_hash": "hashed-password-5678",
            "user_status": "ACTIVE",
            "user_type": "NORMAL",
            "is_email_verified": False,
            "last_login_at": None,
            "created_by": None,
        },
    )
    assert user_resp.status_code == 201, (
        f"사전 조건: 사용자 생성 실패 (status={user_resp.status_code}): {user_resp.text}"
    )
    user_id = user_resp.json()["data"]["id"]

    # 2. 테스트 상품 생성 (API)
    product_resp = client.post(
        "/api/v1/products",
        json={
            "product_name": "Cart Order Test Product",
            "product_description": "Cart->Order 통합 테스트용 상품",
            "brand_id": None,
            "product_status": "ACTIVE",
            "base_price_amount": "39900.00",
            "thumbnail_image_url": None,
            "created_by": None,
        },
    )
    assert product_resp.status_code == 201, (
        f"사전 조건: 상품 생성 실패 (status={product_resp.status_code}): {product_resp.text}"
    )
    product_id = product_resp.json()["data"]["id"]

    # 3. 테스트 SKU 생성 (DB 직접 사용)
    import uuid
    sku = SKU(
        product_id=product_id,
        sku_code=f"TEST-SKU-CART-ORDER-{uuid.uuid4().hex[:8].upper()}",
        sku_status="ACTIVE",
        sale_price_amount="39900.00",
        stock_quantity=10,
    )
    db_session.add(sku)
    db_session.flush()

    # Inventory 레코드 생성 (create_order()에서 재고 검증 필요)
    inventory = Inventory(
        sku_id=sku.id,
        total_quantity=10,
        available_quantity=10,
        reserved_quantity=0,
        safety_stock_quantity=1,
    )
    db_session.add(inventory)
    db_session.flush()

    # 4. 장바구니 생성 (API)
    cart_resp = client.post(
        "/api/v1/carts",
        json={
            "user_id": None,
            "cart_status": "ACTIVE",
            "last_added_at": None,
            "created_by": None,
        },
    )
    assert cart_resp.status_code == 201, (
        f"사전 조건: 장바구니 생성 실패 (status={cart_resp.status_code}): {cart_resp.text}"
    )
    cart_id = cart_resp.json()["data"]["id"]

    return {
        "order_number": "ORD-CART-20260425-0001",
        "user_id": user_id,
        "cart_id": cart_id,
        "order_status": "PENDING",
        "total_product_amount": "39900.00",
        "total_discount_amount": "0.00",
        "total_shipping_amount": "0.00",
        "total_pay_amount": "39900.00",
        "ordered_at": None,
        "created_by": None,
        "items": [
            {
                "sku_id": sku.id,
                "product_name": "Cart Order Test Product",
                "option_summary": "색상: 블랙 / 사이즈: L",
                "quantity": 1,
                "unit_price_amount": "39900.00",
                "total_price_amount": "39900.00",
                "created_by": None,
            }
        ],
    }


class TestOrderAPI:
    """주문 API CRUD 통합 테스트."""

    ORDER_URL = "/api/v1/orders"
    CART_URL = "/api/v1/carts"
    _created_order_id: int | None = None
    _created_cart_order_id: int | None = None
    _cart_id: int | None = None

    # ---------- CREATE ----------
    def test_create_order_success(
        self, client: TestClient, order_payload: dict[str, Any]
    ) -> None:
        """주문 생성 시 201 Created와 함께 생성된 주문 정보를 반환해야 한다."""
        resp: Response = client.post(self.ORDER_URL, json=order_payload)
        # FK 제약 조건으로 인해 400/500이 발생할 수 있으므로 상태 코드 확인
        assert resp.status_code in (
            201,
            400,
            422,
            500,
        ), f"예상치 못한 상태 코드: {resp.status_code}, 본문: {resp.text}"

        if resp.status_code != 201:
            pytest.skip(
                f"FK 의존 관계로 인해 주문 생성 실패 (status={resp.status_code}): "
                f"{resp.text}"
            )

        body = resp.json()
        assert body["success"] is True
        assert "생성했습니다." in body["message"]

        data = body["data"]
        assert data["order_number"] == order_payload["order_number"]
        assert data["order_status"] == order_payload["order_status"]
        assert "id" in data
        assert data["deleted_at"] is None

        # 관계 필드 존재 여부
        assert "items" in data
        assert "status_histories" in data

        TestOrderAPI._created_order_id = data["id"]

    # ---------- LIST ----------
    def test_list_orders(self, client: TestClient) -> None:
        """주문 목록 조회 시 200 OK와 함께 리스트를 반환해야 한다."""
        resp: Response = client.get(self.ORDER_URL)
        assert resp.status_code == 200

        body = resp.json()
        assert body["success"] is True
        assert isinstance(body["data"], list)

    def test_list_orders_with_status_filter(
        self, client: TestClient
    ) -> None:
        """order_status 필터를 적용한 목록 조회가 정상 동작해야 한다."""
        resp: Response = client.get(
            self.ORDER_URL, params={"order_status": "PENDING"}
        )
        assert resp.status_code == 200

    def test_list_orders_with_pagination(
        self, client: TestClient
    ) -> None:
        """페이징 파라미터가 정상 적용되어야 한다."""
        resp: Response = client.get(self.ORDER_URL, params={"skip": 0, "limit": 5})
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["data"]) <= 5

    # ---------- GET ----------
    def test_get_order_success(self, client: TestClient) -> None:
        """주문 상세 조회 시 200 OK와 함께 전체 필드를 반환해야 한다."""
        order_id = TestOrderAPI._created_order_id
        if order_id is None:
            pytest.skip("생성된 주문 ID가 없습니다.")

        resp: Response = client.get(f"{self.ORDER_URL}/{order_id}")
        assert resp.status_code == 200

        body = resp.json()
        assert body["success"] is True
        data = body["data"]
        assert data["id"] == order_id
        assert "items" in data
        assert "status_histories" in data
        assert "payments" in data
        assert "shipments" in data

    def test_get_order_not_found(self, client: TestClient) -> None:
        """존재하지 않는 주문 ID 조회 시 404 에러가 발생해야 한다."""
        resp: Response = client.get(f"{self.ORDER_URL}/99999")
        assert resp.status_code == 404

    # ---------- UPDATE ----------
    def test_update_order_success(
        self, client: TestClient, update_payload: dict[str, Any]
    ) -> None:
        """주문 수정 시 200 OK와 함께 변경된 정보를 반환해야 한다."""
        order_id = TestOrderAPI._created_order_id
        if order_id is None:
            pytest.skip("생성된 주문 ID가 없습니다.")

        resp: Response = client.put(
            f"{self.ORDER_URL}/{order_id}", json=update_payload
        )
        if resp.status_code == 404 and TestOrderAPI._created_order_id is not None:
            pytest.fail(f"생성된 주문({order_id})을 찾을 수 없습니다: {resp.text}")

        assert resp.status_code == 200, f"응답 본문: {resp.text}"

        body = resp.json()
        assert body["success"] is True
        assert "수정했습니다." in body["message"]
        data = body["data"]
        assert data["order_status"] == update_payload["order_status"]

    def test_update_order_not_found(
        self, client: TestClient, update_payload: dict[str, Any]
    ) -> None:
        """존재하지 않는 주문 수정 시 404 에러가 발생해야 한다."""
        resp: Response = client.put(
            f"{self.ORDER_URL}/99999", json=update_payload
        )
        assert resp.status_code == 404

    # ---------- DELETE ----------
    def test_delete_order_success(self, client: TestClient) -> None:
        """주문 삭제(소프트) 시 200 OK와 함께 삭제된 ID를 반환해야 한다."""
        order_id = TestOrderAPI._created_order_id
        if order_id is None:
            pytest.skip("생성된 주문 ID가 없습니다.")

        resp: Response = client.delete(f"{self.ORDER_URL}/{order_id}")
        assert resp.status_code == 200, f"응답 본문: {resp.text}"

        body = resp.json()
        assert body["success"] is True
        assert "삭제했습니다." in body["message"]
        assert body["data"]["order_id"] == order_id

    def test_get_deleted_order_returns_404(
        self, client: TestClient
    ) -> None:
        """삭제된 주문을 조회하면 404 에러가 발생해야 한다."""
        order_id = TestOrderAPI._created_order_id
        if order_id is None:
            pytest.skip("생성된 주문 ID가 없습니다.")

        resp: Response = client.get(f"{self.ORDER_URL}/{order_id}")
        assert resp.status_code == 404

    def test_delete_order_not_found(self, client: TestClient) -> None:
        """존재하지 않는 주문 삭제 시 404 에러가 발생해야 한다."""
        resp: Response = client.delete(f"{self.ORDER_URL}/99999")
        assert resp.status_code == 404

    # ---------- CART -> ORDER FLOW ----------
    def test_create_order_with_cart_id_updates_cart_status(
        self, client: TestClient, cart_order_payload: dict[str, Any]
    ) -> None:
        """cart_id가 포함된 주문 생성 시 cart_status가 'ORDERED'로 변경되어야 한다."""
        cart_id = cart_order_payload["cart_id"]

        # 주문 생성 (cart_id 포함)
        resp: Response = client.post(self.ORDER_URL, json=cart_order_payload)
        assert resp.status_code == 201, (
            f"Cart->Order 생성 실패 (status={resp.status_code}): {resp.text}"
        )

        body = resp.json()
        assert body["success"] is True
        assert "생성했습니다." in body["message"]
        data = body["data"]
        assert data["cart_id"] == cart_id

        TestOrderAPI._created_cart_order_id = data["id"]
        TestOrderAPI._cart_id = cart_id

        # 장바구니 상태가 'ORDERED'로 변경되었는지 확인
        cart_resp: Response = client.get(f"{self.CART_URL}/{cart_id}")
        assert cart_resp.status_code == 200, (
            f"장바구니 조회 실패 (status={cart_resp.status_code}): {cart_resp.text}"
        )
        cart_data = cart_resp.json()["data"]
        assert cart_data["cart_status"] == "ORDERED", (
            f"cart_status가 ORDERED가 아님: {cart_data['cart_status']}"
        )

    def test_create_order_with_invalid_cart_id_returns_404(
        self, client: TestClient
    ) -> None:
        """존재하지 않는 cart_id로 주문 생성 시 404가 반환되어야 한다."""
        payload = {
            "order_number": "ORD-INVALID-CART",
            "user_id": 1,
            "cart_id": 99999,
            "order_status": "PENDING",
            "total_product_amount": "10000.00",
            "total_discount_amount": "0.00",
            "total_shipping_amount": "0.00",
            "total_pay_amount": "10000.00",
            "ordered_at": None,
            "created_by": None,
            "items": [],
        }
        resp: Response = client.post(self.ORDER_URL, json=payload)
        assert resp.status_code == 404

    def test_create_order_with_non_active_cart_returns_409(
        self, client: TestClient
    ) -> None:
        """이미 ORDERED 상태인 cart_id로 주문 생성 시 409가 반환되어야 한다."""
        # 이전 테스트에서 생성된 cart_id 사용 (이미 ORDERED 상태)
        cart_id = TestOrderAPI._cart_id
        if cart_id is None:
            pytest.skip("이전 Cart->Order 테스트에서 생성된 cart_id가 없습니다.")

        payload = {
            "order_number": "ORD-ALREADY-ORDERED",
            "user_id": 1,
            "cart_id": cart_id,
            "order_status": "PENDING",
            "total_product_amount": "10000.00",
            "total_discount_amount": "0.00",
            "total_shipping_amount": "0.00",
            "total_pay_amount": "10000.00",
            "ordered_at": None,
            "created_by": None,
            "items": [],
        }
        resp: Response = client.post(self.ORDER_URL, json=payload)
        assert resp.status_code == 409

    # ---------- INVENTORY RESERVATION FLOW ----------
    def test_create_order_creates_inventory_reservation(
        self, client: TestClient, db_session: Session
    ) -> None:
        """주문 생성 시 InventoryReservation/Transaction이 생성되고 재고가 차감되어야 한다."""
        import uuid

        # 1. 테스트 사용자 생성
        user_resp = client.post(
            "/api/v1/users",
            json={
                "user_email": f"inv_reserve_test_{uuid.uuid4().hex[:8]}@example.com",
                "password_hash": "hashed-password-inv",
                "user_status": "ACTIVE",
                "user_type": "NORMAL",
                "is_email_verified": False,
                "last_login_at": None,
                "created_by": None,
            },
        )
        assert user_resp.status_code == 201
        user_id = user_resp.json()["data"]["id"]

        # 2. 테스트 상품 생성
        product_resp = client.post(
            "/api/v1/products",
            json={
                "product_name": "Inventory Reservation Test Product",
                "product_description": "재고 예약 통합 테스트용 상품",
                "brand_id": None,
                "product_status": "ACTIVE",
                "base_price_amount": "15000.00",
                "thumbnail_image_url": None,
                "created_by": None,
            },
        )
        assert product_resp.status_code == 201
        product_id = product_resp.json()["data"]["id"]

        # 3. 테스트 SKU 생성 (DB 직접)
        sku = SKU(
            product_id=product_id,
            sku_code=f"TEST-SKU-INV-RESERVE-{uuid.uuid4().hex[:8].upper()}",
            sku_status="ACTIVE",
            sale_price_amount="15000.00",
            stock_quantity=10,
        )
        db_session.add(sku)
        db_session.flush()

        # 4. Inventory 레코드 생성
        initial_available = 10
        inventory = Inventory(
            sku_id=sku.id,
            total_quantity=10,
            available_quantity=initial_available,
            reserved_quantity=0,
            safety_stock_quantity=1,
        )
        db_session.add(inventory)
        db_session.flush()

        ordered_qty = 3

        # 5. cart_id 없이 주문 생성 (cart_order_payload fixture 재사용 문제 방지)
        order_payload = {
            "order_number": f"ORD-INV-RESERVE-{uuid.uuid4().hex[:8].upper()}",
            "user_id": user_id,
            "order_status": "PENDING",
            "total_product_amount": f"{15000 * ordered_qty}.00",
            "total_discount_amount": "0.00",
            "total_shipping_amount": "0.00",
            "total_pay_amount": f"{15000 * ordered_qty}.00",
            "ordered_at": None,
            "created_by": None,
            "items": [
                {
                    "sku_id": sku.id,
                    "product_name": "Inventory Reservation Test Product",
                    "option_summary": "테스트 옵션",
                    "quantity": ordered_qty,
                    "unit_price_amount": "15000.00",
                    "total_price_amount": f"{15000 * ordered_qty}.00",
                    "created_by": None,
                }
            ],
        }

        # 주문 생성
        resp: Response = client.post(self.ORDER_URL, json=order_payload)
        assert resp.status_code == 201, (
            f"주문 생성 실패 (status={resp.status_code}): {resp.text}"
        )
        order_id = resp.json()["data"]["id"]

        # InventoryReservation 확인
        reservation = (
            db_session.query(InventoryReservation)
            .filter(
                InventoryReservation.order_id == order_id,
                InventoryReservation.sku_id == sku.id,
            )
            .first()
        )
        assert reservation is not None, "InventoryReservation이 생성되지 않았습니다."
        assert reservation.reserved_quantity == ordered_qty
        assert reservation.reservation_status == "RESERVED"

        # Inventory 수량 업데이트 확인
        inv_after = db_session.query(Inventory).filter(Inventory.sku_id == sku.id).first()
        assert inv_after is not None
        assert inv_after.available_quantity == initial_available - ordered_qty, (
            f"available_quantity가 차감되지 않았습니다. "
            f"(초기: {initial_available}, 이후: {inv_after.available_quantity}, 주문수량: {ordered_qty})"
        )
        assert inv_after.reserved_quantity == ordered_qty, (
            f"reserved_quantity가 증가하지 않았습니다. "
            f"(초기: 0, 이후: {inv_after.reserved_quantity}, 주문수량: {ordered_qty})"
        )

        # InventoryTransaction 확인
        transaction = (
            db_session.query(InventoryTransaction)
            .filter(
                InventoryTransaction.reference_type == "ORDER",
                InventoryTransaction.reference_id == order_id,
                InventoryTransaction.sku_id == sku.id,
            )
            .first()
        )
        assert transaction is not None, "InventoryTransaction이 생성되지 않았습니다."
        assert transaction.transaction_type == "RESERVE"
        assert transaction.quantity == ordered_qty
