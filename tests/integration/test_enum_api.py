"""
Enum API 통합 테스트.

meta.meta_enum 테이블에서 enum 값을 조회하는 GET /api/v1/enums 엔드포인트를 검증한다.

시나리오:
  - 전체 enum 목록 조회 (enum_type 필터 없음)
  - 특정 enum_type 필터 조회
  - 존재하지 않는 enum_type 조회 시 빈 결과
"""
from __future__ import annotations

from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session


# 운영 insert_meta_enums.sql에 정의된 enum_type 목록
OPERATIONAL_ENUM_TYPES = {
    "order_status",
    "payment_status",
    "shipment_status",
    "user_status",
    "user_type",
    "review_status",
    "inventory_change_reason",
    "discount_type",
    "discount_scope",
    "discount_method",
    "coupon_status",
    "promotion_status",
    "refund_status",
    "refund_method",
    "report_type",
    "report_status",
    "login_result",
    "tracking_status",
    "action_type",
    "log_type",
    "admin_status",
    "permission_action",
    "error_code",
}


@pytest.fixture(scope="module", autouse=True)
def _ensure_meta_schema(db_session: Session) -> None:
    """meta 스키마와 meta_enum 테이블이 존재하는지 확인한다."""
    # 테이블 존재 여부 확인
    result = db_session.execute(
        text(
            "SELECT EXISTS ("
            "  SELECT FROM information_schema.tables "
            "  WHERE table_schema = 'meta' AND table_name = 'meta_enum'"
            ")"
        )
    ).scalar()
    if not result:
        # 테이블이 없으면 생성 (운영 DB와 동일한 DDL)
        db_session.execute(text("CREATE SCHEMA IF NOT EXISTS meta"))
        db_session.execute(
            text(
                "CREATE TABLE meta.meta_enum ("
                "  enum_type VARCHAR(50) NOT NULL,"
                "  enum_value VARCHAR(50) NOT NULL,"
                "  description TEXT,"
                "  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,"
                "  PRIMARY KEY (enum_type, enum_value)"
                ")"
            )
        )
        db_session.commit()


class TestListEnums:
    """GET /api/v1/enums 엔드포인트 테스트."""

    def test_list_all_enums(
        self, client: TestClient, api_prefix: str
    ) -> None:
        """enum_type 필터 없이 전체 enum 목록을 조회한다."""
        response = client.get(f"{api_prefix}/enums")
        assert response.status_code == 200

        body = response.json()
        assert body["success"] is True
        assert body["message"] == "enum 목록을 조회했습니다."

        data: list[dict[str, Any]] = body["data"]
        assert len(data) > 0  # 최소 1개 이상의 enum_type 그룹

        # 각 그룹은 enum_type과 values 필드를 가져야 함
        for group in data:
            assert "enum_type" in group
            assert "values" in group
            assert isinstance(group["values"], list)
            assert len(group["values"]) > 0  # 각 그룹에 최소 1개 값

            # 각 값은 enum_type, enum_value, description 필드를 가져야 함
            for value in group["values"]:
                assert "enum_type" in value
                assert "enum_value" in value
                assert "description" in value

    def test_filter_by_enum_type(
        self, client: TestClient, api_prefix: str
    ) -> None:
        """특정 enum_type으로 필터링하여 조회한다."""
        response = client.get(
            f"{api_prefix}/enums",
            params={"enum_type": "order_status"},
        )
        assert response.status_code == 200

        body = response.json()
        assert body["success"] is True

        data: list[dict[str, Any]] = body["data"]
        assert len(data) == 1  # 하나의 그룹만 반환
        assert data[0]["enum_type"] == "order_status"

        values = data[0]["values"]
        assert len(values) > 0
        # 모든 값의 enum_type이 order_status여야 함
        for v in values:
            assert v["enum_type"] == "order_status"

    def test_filter_nonexistent_enum_type(
        self, client: TestClient, api_prefix: str
    ) -> None:
        """존재하지 않는 enum_type을 필터링하면 빈 목록이 반환된다."""
        response = client.get(
            f"{api_prefix}/enums",
            params={"enum_type": "nonexistent_type"},
        )
        assert response.status_code == 200

        body = response.json()
        assert body["success"] is True
        data: list[dict[str, Any]] = body["data"]
        assert data == []  # 빈 리스트

    def test_values_ordered_by_enum_type_and_value(
        self, client: TestClient, api_prefix: str
    ) -> None:
        """결과가 enum_type, enum_value 순으로 정렬되어야 한다."""
        response = client.get(f"{api_prefix}/enums")
        assert response.status_code == 200

        body = response.json()
        data: list[dict[str, Any]] = body["data"]

        # enum_type 알파벳 순서 확인
        type_order = [g["enum_type"] for g in data]
        assert type_order == sorted(type_order)

        # 각 그룹 내 enum_value 알파벳 순서 확인
        for group in data:
            values = [v["enum_value"] for v in group["values"]]
            assert values == sorted(values)

    def test_response_schema(
        self, client: TestClient, api_prefix: str
    ) -> None:
        """응답 스키마가 APIResponse[list[EnumTypeGroup]] 형식을 준수하는지 확인한다."""
        response = client.get(f"{api_prefix}/enums")
        assert response.status_code == 200

        body = response.json()
        # 최상위 필드
        assert "success" in body
        assert "message" in body
        assert "data" in body

        data: list[dict[str, Any]] = body["data"]
        assert isinstance(data, list)

        if data:
            group = data[0]
            # EnumTypeGroup 필드
            assert "enum_type" in group
            assert "values" in group
            assert isinstance(group["values"], list)

            if group["values"]:
                value = group["values"][0]
                # EnumValueRead 필드
                assert "enum_type" in value
                assert "enum_value" in value
                assert "description" in value
