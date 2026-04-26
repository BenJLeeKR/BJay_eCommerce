"""
상품(Product) API 통합 테스트.

시나리오 기반 흐름:
  생성(CREATE) -> 목록 조회(LIST) -> 상세 조회(GET) -> 수정(UPDATE) -> 삭제(DELETE)
"""
from __future__ import annotations

from decimal import Decimal
from typing import Any

import pytest
from fastapi.testclient import TestClient
from httpx import Response

from app.schemas.product import ProductCreate


@pytest.fixture(scope="module")
def product_payload() -> dict[str, Any]:
    """상품 생성에 사용할 기본 페이로드."""
    return {
        "product_name": "테스트 상품",
        "product_description": "통합 테스트를 위한 상품입니다.",
        "brand_id": None,
        "product_status": "ACTIVE",
        "base_price_amount": "19900.00",
        "thumbnail_image_url": "https://example.com/thumb.png",
        "created_by": None,
    }


@pytest.fixture(scope="module")
def update_payload() -> dict[str, Any]:
    """상품 수정에 사용할 페이로드."""
    return {
        "product_name": "수정된 상품명",
        "product_status": "INACTIVE",
        "base_price_amount": "9900.00",
        "updated_by": 999,
    }


class TestProductAPI:
    """상품 API CRUD 통합 테스트."""

    PRODUCT_URL = "/api/v1/products"
    _created_product_id: int | None = None

    # ---------- CREATE ----------
    def test_create_product_success(
        self, client: TestClient, product_payload: dict[str, Any]
    ) -> None:
        """상품 생성 시 201 Created와 함께 생성된 상품 정보를 반환해야 한다."""
        resp: Response = client.post(self.PRODUCT_URL, json=product_payload)
        assert resp.status_code == 201, f"응답 본문: {resp.text}"

        body = resp.json()
        assert body["success"] is True
        assert "생성했습니다." in body["message"]

        data = body["data"]
        assert data["product_name"] == product_payload["product_name"]
        assert data["product_status"] == product_payload["product_status"]
        assert data["base_price_amount"] == product_payload["base_price_amount"]
        assert "id" in data
        assert data["deleted_at"] is None

        TestProductAPI._created_product_id = data["id"]

    # ---------- LIST ----------
    def test_list_products(self, client: TestClient) -> None:
        """상품 목록 조회 시 200 OK와 함께 상품 리스트를 반환해야 한다."""
        resp: Response = client.get(self.PRODUCT_URL)
        assert resp.status_code == 200

        body = resp.json()
        assert body["success"] is True
        assert isinstance(body["data"], list)
        assert len(body["data"]) >= 1

    def test_list_products_with_status_filter(
        self, client: TestClient
    ) -> None:
        """product_status 필터를 적용한 목록 조회가 정상 동작해야 한다."""
        resp: Response = client.get(
            self.PRODUCT_URL, params={"product_status": "ACTIVE"}
        )
        assert resp.status_code == 200

        body = resp.json()
        for product in body["data"]:
            assert product["product_status"] == "ACTIVE"

    def test_list_products_with_pagination(
        self, client: TestClient
    ) -> None:
        """페이징 파라미터(skip, limit)가 정상 적용되어야 한다."""
        resp: Response = client.get(self.PRODUCT_URL, params={"skip": 0, "limit": 5})
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["data"]) <= 5

    # ---------- GET ----------
    def test_get_product_success(self, client: TestClient) -> None:
        """상품 상세 조회 시 200 OK와 함께 전체 필드를 반환해야 한다."""
        product_id = TestProductAPI._created_product_id
        if product_id is None:
            pytest.skip("생성된 상품 ID가 없습니다.")

        resp: Response = client.get(f"{self.PRODUCT_URL}/{product_id}")
        assert resp.status_code == 200

        body = resp.json()
        assert body["success"] is True
        data = body["data"]

        assert data["id"] == product_id
        assert data["product_name"] == "테스트 상품"
        assert data["product_status"] == "ACTIVE"
        # 관계 필드 존재 여부
        assert "brand" in data
        assert "categories" in data
        assert "options" in data
        assert "images" in data
        assert "skus" in data

    def test_get_product_not_found(self, client: TestClient) -> None:
        """존재하지 않는 상품 ID 조회 시 404 에러가 발생해야 한다."""
        resp: Response = client.get(f"{self.PRODUCT_URL}/99999")
        assert resp.status_code == 404

        body = resp.json()
        # 일반적인 404 응답 확인
        assert "찾을 수 없습니다" in body.get("detail", "")

    # ---------- UPDATE ----------
    def test_update_product_success(
        self, client: TestClient, update_payload: dict[str, Any]
    ) -> None:
        """상품 수정 시 200 OK와 함께 변경된 정보를 반환해야 한다."""
        product_id = TestProductAPI._created_product_id
        if product_id is None:
            pytest.skip("생성된 상품 ID가 없습니다.")

        resp: Response = client.put(
            f"{self.PRODUCT_URL}/{product_id}", json=update_payload
        )
        assert resp.status_code == 200, f"응답 본문: {resp.text}"

        body = resp.json()
        assert body["success"] is True
        assert "수정했습니다." in body["message"]

        data = body["data"]
        assert data["product_name"] == update_payload["product_name"]
        assert data["product_status"] == update_payload["product_status"]
        assert data["base_price_amount"] == update_payload["base_price_amount"]

    def test_update_product_not_found(
        self, client: TestClient, update_payload: dict[str, Any]
    ) -> None:
        """존재하지 않는 상품 수정 시 404 에러가 발생해야 한다."""
        resp: Response = client.put(
            f"{self.PRODUCT_URL}/99999", json=update_payload
        )
        assert resp.status_code == 404

    # ---------- DELETE ----------
    def test_delete_product_success(self, client: TestClient) -> None:
        """상품 삭제(소프트) 시 200 OK와 함께 삭제된 ID를 반환해야 한다."""
        product_id = TestProductAPI._created_product_id
        if product_id is None:
            pytest.skip("생성된 상품 ID가 없습니다.")

        resp: Response = client.delete(f"{self.PRODUCT_URL}/{product_id}")
        assert resp.status_code == 200, f"응답 본문: {resp.text}"

        body = resp.json()
        assert body["success"] is True
        assert "삭제했습니다." in body["message"]
        assert body["data"]["product_id"] == product_id

    def test_get_deleted_product_returns_404(
        self, client: TestClient
    ) -> None:
        """삭제된 상품을 조회하면 404 에러가 발생해야 한다."""
        product_id = TestProductAPI._created_product_id
        if product_id is None:
            pytest.skip("생성된 상품 ID가 없습니다.")

        resp: Response = client.get(f"{self.PRODUCT_URL}/{product_id}")
        assert resp.status_code == 404

    def test_delete_product_not_found(self, client: TestClient) -> None:
        """존재하지 않는 상품 삭제 시 404 에러가 발생해야 한다."""
        resp: Response = client.delete(f"{self.PRODUCT_URL}/99999")
        assert resp.status_code == 404
