"""
장바구니(Cart) API 통합 테스트.

시나리오 기반 흐름:
  장바구니 생성 -> 목록 조회 -> 상세 조회 -> 수정 -> 삭제
  (CartItem, OptionSnapshot, Coupon은 의존 관계로 인해 스키마 검증 위주)
"""
from __future__ import annotations

from typing import Any

import pytest
from fastapi.testclient import TestClient
from httpx import Response


@pytest.fixture(scope="module")
def cart_payload() -> dict[str, Any]:
    """장바구니 생성에 사용할 기본 페이로드.
    (session_id는 라우터의 get_session_id()에서 생성되므로 페이로드에 포함하지 않음)
    """
    return {
        "user_id": None,
        "cart_status": "ACTIVE",
        "last_added_at": None,
        "created_by": None,
    }


@pytest.fixture(scope="module")
def update_payload() -> dict[str, Any]:
    """장바구니 수정에 사용할 페이로드."""
    return {
        "cart_status": "ORDERED",
        "updated_by": 999,
    }


class TestCartAPI:
    """장바구니 API CRUD 통합 테스트."""

    CART_URL = "/api/v1/carts"
    _created_cart_id: int | None = None
    _session_id: str | None = None

    # ---------- CREATE ----------
    def test_create_cart_success(
        self, client: TestClient, cart_payload: dict[str, Any]
    ) -> None:
        """장바구니 생성 시 201 Created와 함께 생성된 장바구니 정보를 반환해야 한다."""
        resp: Response = client.post(self.CART_URL, json=cart_payload)
        assert resp.status_code == 201, f"응답 본문: {resp.text}"

        body = resp.json()
        assert body["success"] is True
        assert "생성했습니다." in body["message"]

        data = body["data"]
        # session_id는 Router의 get_session_id()가 생성하므로 UUID 형식인지만 확인
        assert isinstance(data["session_id"], str) and len(data["session_id"]) > 0
        assert data["cart_status"] == cart_payload["cart_status"]
        assert "id" in data
        assert data["deleted_at"] is None
        # 관계 필드
        assert "items" in data
        assert "coupons" in data

        TestCartAPI._created_cart_id = data["id"]
        # session_id를 저장하여 후속 테스트에서 사용
        TestCartAPI._session_id = data["session_id"]

    # ---------- LIST ----------
    def test_list_carts(self, client: TestClient) -> None:
        """장바구니 목록 조회 시 200 OK와 함께 리스트를 반환해야 한다."""
        resp: Response = client.get(self.CART_URL)
        assert resp.status_code == 200

        body = resp.json()
        assert body["success"] is True
        assert isinstance(body["data"], list)
        assert len(body["data"]) >= 1

    def test_list_carts_with_session_filter(
        self, client: TestClient
    ) -> None:
        """session_id 필터를 적용한 목록 조회가 정상 동작해야 한다."""
        session_id = getattr(TestCartAPI, "_session_id", None)
        if session_id is None:
            pytest.skip("이전 테스트에서 생성된 cart의 session_id가 없습니다.")

        resp: Response = client.get(
            self.CART_URL, params={"session_id": session_id}
        )
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["data"]) >= 1
        for cart in body["data"]:
            assert cart["session_id"] == session_id

    def test_list_carts_with_status_filter(
        self, client: TestClient
    ) -> None:
        """cart_status 필터를 적용한 목록 조회가 정상 동작해야 한다."""
        resp: Response = client.get(
            self.CART_URL, params={"cart_status": "ACTIVE"}
        )
        assert resp.status_code == 200
        body = resp.json()
        for cart in body["data"]:
            assert cart["cart_status"] == "ACTIVE"

    def test_list_carts_with_pagination(
        self, client: TestClient
    ) -> None:
        """페이징 파라미터가 정상 적용되어야 한다."""
        resp: Response = client.get(self.CART_URL, params={"skip": 0, "limit": 5})
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["data"]) <= 5

    # ---------- GET ----------
    def test_get_cart_success(self, client: TestClient) -> None:
        """장바구니 상세 조회 시 200 OK와 함께 전체 필드를 반환해야 한다."""
        cart_id = TestCartAPI._created_cart_id
        if cart_id is None:
            pytest.skip("생성된 장바구니 ID가 없습니다.")

        resp: Response = client.get(f"{self.CART_URL}/{cart_id}")
        assert resp.status_code == 200

        body = resp.json()
        assert body["success"] is True
        data = body["data"]
        assert data["id"] == cart_id
        assert data["cart_status"] == "ACTIVE"
        assert "items" in data
        assert "coupons" in data

    def test_get_cart_not_found(self, client: TestClient) -> None:
        """존재하지 않는 장바구니 ID 조회 시 404 에러가 발생해야 한다."""
        resp: Response = client.get(f"{self.CART_URL}/99999")
        assert resp.status_code == 404

    # ---------- UPDATE ----------
    def test_update_cart_success(
        self, client: TestClient, update_payload: dict[str, Any]
    ) -> None:
        """장바구니 수정 시 200 OK와 함께 변경된 정보를 반환해야 한다."""
        cart_id = TestCartAPI._created_cart_id
        if cart_id is None:
            pytest.skip("생성된 장바구니 ID가 없습니다.")

        resp: Response = client.put(
            f"{self.CART_URL}/{cart_id}", json=update_payload
        )
        assert resp.status_code == 200, f"응답 본문: {resp.text}"

        body = resp.json()
        assert body["success"] is True
        assert "수정했습니다." in body["message"]
        data = body["data"]
        assert data["cart_status"] == update_payload["cart_status"]

    def test_update_cart_not_found(
        self, client: TestClient, update_payload: dict[str, Any]
    ) -> None:
        """존재하지 않는 장바구니 수정 시 404 에러가 발생해야 한다."""
        resp: Response = client.put(
            f"{self.CART_URL}/99999", json=update_payload
        )
        assert resp.status_code == 404

    # ---------- DELETE ----------
    def test_delete_cart_success(self, client: TestClient) -> None:
        """장바구니 삭제(소프트) 시 200 OK와 함께 삭제된 ID를 반환해야 한다."""
        cart_id = TestCartAPI._created_cart_id
        if cart_id is None:
            pytest.skip("생성된 장바구니 ID가 없습니다.")

        resp: Response = client.delete(f"{self.CART_URL}/{cart_id}")
        assert resp.status_code == 200, f"응답 본문: {resp.text}"

        body = resp.json()
        assert body["success"] is True
        assert "삭제했습니다." in body["message"]
        assert body["data"]["cart_id"] == cart_id

    def test_get_deleted_cart_returns_404(self, client: TestClient) -> None:
        """삭제된 장바구니를 조회하면 404 에러가 발생해야 한다."""
        cart_id = TestCartAPI._created_cart_id
        if cart_id is None:
            pytest.skip("생성된 장바구니 ID가 없습니다.")

        resp: Response = client.get(f"{self.CART_URL}/{cart_id}")
        assert resp.status_code == 404

    def test_delete_cart_not_found(self, client: TestClient) -> None:
        """존재하지 않는 장바구니 삭제 시 404 에러가 발생해야 한다."""
        resp: Response = client.delete(f"{self.CART_URL}/99999")
        assert resp.status_code == 404

    # ---------- COMPOSITE CREATE VALIDATION ----------
    def test_create_cart_with_invalid_sku_returns_404(
        self, client: TestClient
    ) -> None:
        """존재하지 않는 sku_id로 장바구니 생성 시 404 에러가 발생해야 한다."""
        payload = {
            "cart_status": "ACTIVE",
            "items": [
                {
                    "sku_id": 99999,
                    "quantity": 1,
                    "unit_price_amount": "10000.00",
                    "total_price_amount": "10000.00",
                }
            ],
        }
        resp: Response = client.post(self.CART_URL, json=payload)
        assert resp.status_code == 404, f"응답 본문: {resp.text}"
        body = resp.json()
        assert "찾을 수 없습니다" in body["detail"]
