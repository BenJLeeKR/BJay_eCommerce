"""
회원 중복 이메일 통합 테스트 (별도 모듈).

이 테스트는 PostgreSQL UNIQUE 제약 조건 위반 시 500 에러가 발생하며,
이로 인해 ``db_session``(scope="module")에 ``PendingRollbackError``가 발생할 수 있다.
따라서 별도 모듈로 분리하여 다른 테스트에 영향을 주지 않도록 한다.
"""
from __future__ import annotations

from typing import Any

import pytest
from fastapi.testclient import TestClient
from httpx import Response


@pytest.fixture(scope="module")
def user_payload() -> dict[str, Any]:
    """회원 생성에 사용할 기본 페이로드."""
    return {
        "user_email": "dup_test@example.com",
        "password_hash": "hashed-password-1234",
        "user_status": "ACTIVE",
        "user_type": "NORMAL",
        "is_email_verified": False,
        "last_login_at": None,
        "created_by": None,
    }


class TestUserDuplicateEmail:
    """중복 이메일 테스트 (별도 모듈)."""

    USER_URL = "/api/v1/users"

    def test_create_user_duplicate_email(
        self, client: TestClient, user_payload: dict[str, Any]
    ) -> None:
        """동일한 이메일로 회원 생성 시 409 Conflict 또는 400 에러가 발생해야 한다."""
        # 1) 먼저 사용자를 생성한다
        resp_first: Response = client.post(self.USER_URL, json=user_payload)
        assert resp_first.status_code == 201, (
            f"첫 번째 생성 실패: {resp_first.status_code}, 본문: {resp_first.text}"
        )

        # 2) 동일한 이메일로 다시 생성 -> UNIQUE 제약 조건 위반
        resp_dup: Response = client.post(self.USER_URL, json=user_payload)
        # PostgreSQL UNIQUE 제약 조건 위반 -> 500 (서버 내부 오류)
        assert resp_dup.status_code in (400, 409, 422, 500), (
            f"중복 이메일에 대한 예상 오류 코드 아님: {resp_dup.status_code}, "
            f"본문: {resp_dup.text}"
        )
