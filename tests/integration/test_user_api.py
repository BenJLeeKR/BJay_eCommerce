"""
회원(User) API 통합 테스트.

시나리오 기반 흐름:
  생성(CREATE) -> 목록 조회(LIST) -> 상세 조회(GET) -> 수정(UPDATE) -> 삭제(DELETE)

추가 시나리오:
  - Profile CRUD (user_id 기반)
  - Address CRUD (user_id + address_id 기반)
  - Role CRUD
  - User-Role Assignment
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
        "user_email": "testuser@example.com",
        "password_hash": "hashed-password-1234",
        "user_status": "ACTIVE",
        "user_type": "NORMAL",
        "is_email_verified": False,
        "last_login_at": None,
        "created_by": None,
    }


@pytest.fixture(scope="module")
def update_payload() -> dict[str, Any]:
    """회원 수정에 사용할 페이로드."""
    return {
        "user_email": "updated@example.com",
        "user_status": "SUSPENDED",
        "updated_by": 999,
    }


@pytest.fixture(scope="module")
def profile_payload() -> dict[str, Any]:
    """프로필 생성에 사용할 페이로드."""
    return {
        "user_name": "홍길동",
        "phone_number": "010-1234-5678",
        "birth_date": "1990-01-01",
        "gender_code": "M",
    }


@pytest.fixture(scope="module")
def profile_update_payload() -> dict[str, Any]:
    """프로필 수정에 사용할 페이로드."""
    return {
        "user_name": "김철수",
        "phone_number": "010-9876-5432",
    }


@pytest.fixture(scope="module")
def address_payload() -> dict[str, Any]:
    """배송지 생성에 사용할 페이로드."""
    return {
        "address_name": "집",
        "recipient_name": "홍길동",
        "recipient_phone": "010-1234-5678",
        "postal_code": "12345",
        "address_line1": "서울시 강남구 테헤란로",
        "address_line2": "101동 202호",
        "is_default_address": True,
    }


@pytest.fixture(scope="module")
def address_update_payload() -> dict[str, Any]:
    """배송지 수정에 사용할 페이로드."""
    return {
        "address_name": "회사",
        "recipient_name": "홍길동",
        "is_default_address": False,
    }


@pytest.fixture(scope="module")
def role_payload() -> dict[str, Any]:
    """역할 생성에 사용할 페이로드."""
    return {"role_name": "TEST_ROLE"}


@pytest.fixture(scope="module")
def role_update_payload() -> dict[str, Any]:
    """역할 수정에 사용할 페이로드."""
    return {"role_name": "TEST_ROLE_UPDATED"}


class TestUserAPI:
    """회원 API CRUD 통합 테스트."""

    USER_URL = "/api/v1/users"

    def test_health_check(self, client: TestClient) -> None:
        """헬스 체크 엔드포인트가 정상 응답해야 한다."""
        resp: Response = client.get("/api/v1/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"

    # ---------- CREATE ----------
    def test_create_user_success(
        self, client: TestClient, user_payload: dict[str, Any]
    ) -> None:
        """회원 생성 시 201 Created와 함께 생성된 회원 정보를 반환해야 한다."""
        resp: Response = client.post(self.USER_URL, json=user_payload)
        assert resp.status_code == 201, f"응답 본문: {resp.text}"

        body = resp.json()
        assert body["success"] is True
        assert "회원을 생성했습니다." in body["message"]

        data = body["data"]
        assert data["user_email"] == user_payload["user_email"]
        assert data["user_status"] == user_payload["user_status"]
        assert data["user_type"] == user_payload["user_type"]
        assert "id" in data
        assert data["deleted_at"] is None

        # 생성된 ID 저장 (다른 테스트에서 사용)
        pytest.created_user_id = data["id"]

    # ---------- LIST ----------
    def test_list_users(self, client: TestClient) -> None:
        """회원 목록 조회 시 200 OK와 함께 회원 리스트를 반환해야 한다."""
        resp: Response = client.get(self.USER_URL)
        assert resp.status_code == 200

        body = resp.json()
        assert body["success"] is True
        assert isinstance(body["data"], list)
        assert len(body["data"]) >= 1

    def test_list_users_with_status_filter(
        self, client: TestClient
    ) -> None:
        """user_status 필터를 적용한 목록 조회가 정상 동작해야 한다."""
        resp: Response = client.get(self.USER_URL, params={"user_status": "ACTIVE"})
        assert resp.status_code == 200

        body = resp.json()
        for user in body["data"]:
            assert user["user_status"] == "ACTIVE"

    def test_list_users_with_pagination(
        self, client: TestClient
    ) -> None:
        """페이징 파라미터(skip, limit)가 정상 적용되어야 한다."""
        resp: Response = client.get(self.USER_URL, params={"skip": 0, "limit": 5})
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["data"]) <= 5

    # ---------- GET ----------
    def test_get_user_success(self, client: TestClient) -> None:
        """회원 상세 조회 시 200 OK와 함께 전체 필드를 반환해야 한다."""
        user_id = getattr(pytest, "created_user_id", None)
        if user_id is None:
            pytest.skip("생성된 회원 ID가 없습니다.")

        resp: Response = client.get(f"{self.USER_URL}/{user_id}")
        assert resp.status_code == 200

        body = resp.json()
        assert body["success"] is True
        data = body["data"]

        assert data["id"] == user_id
        assert data["user_email"] == "testuser@example.com"
        assert data["user_status"] == "ACTIVE"
        assert data["user_type"] == "NORMAL"
        # 관계 필드 존재 여부
        assert "profile" in data
        assert "addresses" in data
        assert "auth_methods" in data
        assert "login_histories" in data
        assert "roles" in data

    def test_get_user_not_found(self, client: TestClient) -> None:
        """존재하지 않는 회원 ID 조회 시 404 에러가 발생해야 한다."""
        resp: Response = client.get(f"{self.USER_URL}/99999")
        assert resp.status_code == 404

        body = resp.json()
        assert "찾을 수 없습니다" in body.get("detail", "")

    # ---------- UPDATE ----------
    def test_update_user_success(
        self, client: TestClient, update_payload: dict[str, Any]
    ) -> None:
        """회원 수정 시 200 OK와 함께 변경된 정보를 반환해야 한다."""
        user_id = getattr(pytest, "created_user_id", None)
        if user_id is None:
            pytest.skip("생성된 회원 ID가 없습니다.")

        resp: Response = client.put(
            f"{self.USER_URL}/{user_id}", json=update_payload
        )
        assert resp.status_code == 200, f"응답 본문: {resp.text}"

        body = resp.json()
        assert body["success"] is True
        assert "수정했습니다." in body["message"]

        data = body["data"]
        assert data["user_email"] == update_payload["user_email"]
        assert data["user_status"] == update_payload["user_status"]

    def test_update_user_not_found(
        self, client: TestClient, update_payload: dict[str, Any]
    ) -> None:
        """존재하지 않는 회원 수정 시 404 에러가 발생해야 한다."""
        resp: Response = client.put(
            f"{self.USER_URL}/99999", json=update_payload
        )
        assert resp.status_code == 404

    # ---------- DELETE ----------
    def test_delete_user_success(self, client: TestClient) -> None:
        """회원 삭제(소프트) 시 200 OK와 함께 삭제된 ID를 반환해야 한다."""
        user_id = getattr(pytest, "created_user_id", None)
        if user_id is None:
            pytest.skip("생성된 회원 ID가 없습니다.")

        resp: Response = client.delete(f"{self.USER_URL}/{user_id}")
        assert resp.status_code == 200, f"응답 본문: {resp.text}"

        body = resp.json()
        assert body["success"] is True
        assert "삭제했습니다." in body["message"]
        assert body["data"]["user_id"] == user_id

    def test_delete_user_after_deletion_returns_404(
        self, client: TestClient
    ) -> None:
        """이미 삭제된 회원을 다시 조회하면 404 에러가 발생해야 한다."""
        user_id = getattr(pytest, "created_user_id", None)
        if user_id is None:
            pytest.skip("생성된 회원 ID가 없습니다.")

        resp: Response = client.get(f"{self.USER_URL}/{user_id}")
        assert resp.status_code == 404

    def test_delete_user_not_found(self, client: TestClient) -> None:
        """존재하지 않는 회원 삭제 시 404 에러가 발생해야 한다."""
        resp: Response = client.delete(f"{self.USER_URL}/99999")
        assert resp.status_code == 404

class TestUserProfileAPI:
    """회원 프로필 API 통합 테스트."""

    @property
    def _user_id(self) -> int:
        uid = getattr(pytest, "created_profile_user_id", None)
        if uid is None:
            pytest.skip("프로필 테스트용 회원 ID가 없습니다.")
        return uid

    @pytest.fixture(scope="class", autouse=True)
    def _setup_user(self, client: TestClient) -> None:
        """프로필 테스트용 회원을 생성한다."""
        payload = {
            "user_email": "profile_test@example.com",
            "password_hash": "hashed-pw",
            "user_status": "ACTIVE",
            "user_type": "NORMAL",
        }
        resp = client.post("/api/v1/users", json=payload)
        assert resp.status_code == 201
        pytest.created_profile_user_id = resp.json()["data"]["id"]

    # ---------- CREATE ----------
    def test_create_user_profile_success(
        self, client: TestClient, profile_payload: dict[str, Any]
    ) -> None:
        """프로필 생성 시 201 Created를 반환해야 한다."""
        resp = client.post(
            f"/api/v1/users/{self._user_id}/profile",
            json=profile_payload,
        )
        assert resp.status_code == 201, f"응답 본문: {resp.text}"

        body = resp.json()
        assert body["success"] is True
        assert "생성했습니다." in body["message"]

        data = body["data"]
        assert data["user_name"] == profile_payload["user_name"]
        assert data["phone_number"] == profile_payload["phone_number"]
        assert data["gender_code"] == profile_payload["gender_code"]

    def test_create_duplicate_profile_returns_409(
        self, client: TestClient, profile_payload: dict[str, Any]
    ) -> None:
        """이미 프로필이 있을 때 생성 시 409 Conflict를 반환해야 한다."""
        resp = client.post(
            f"/api/v1/users/{self._user_id}/profile",
            json=profile_payload,
        )
        assert resp.status_code == 409, f"응답 본문: {resp.text}"

    # ---------- GET ----------
    def test_get_user_profile_success(
        self, client: TestClient
    ) -> None:
        """프로필 조회 시 200 OK를 반환해야 한다."""
        resp = client.get(f"/api/v1/users/{self._user_id}/profile")
        assert resp.status_code == 200

        body = resp.json()
        assert body["success"] is True
        assert body["data"]["user_name"] == "홍길동"

    def test_get_user_profile_not_found(self, client: TestClient) -> None:
        """존재하지 않는 사용자의 프로필 조회 시 404를 반환해야 한다."""
        resp = client.get("/api/v1/users/99999/profile")
        assert resp.status_code == 404

    # ---------- UPDATE ----------
    def test_update_user_profile_success(
        self, client: TestClient, profile_update_payload: dict[str, Any]
    ) -> None:
        """프로필 수정 시 200 OK를 반환해야 한다."""
        resp = client.put(
            f"/api/v1/users/{self._user_id}/profile",
            json=profile_update_payload,
        )
        assert resp.status_code == 200, f"응답 본문: {resp.text}"

        body = resp.json()
        assert body["success"] is True
        assert "수정했습니다." in body["message"]
        assert body["data"]["user_name"] == "김철수"
        assert body["data"]["phone_number"] == "010-9876-5432"

    # ---------- DELETE ----------
    def test_delete_user_profile_success(self, client: TestClient) -> None:
        """프로필 삭제 시 200 OK를 반환해야 한다."""
        resp = client.delete(f"/api/v1/users/{self._user_id}/profile")
        assert resp.status_code == 200, f"응답 본문: {resp.text}"

        body = resp.json()
        assert body["success"] is True
        assert "삭제했습니다." in body["message"]

    def test_get_deleted_profile_returns_404(self, client: TestClient) -> None:
        """삭제된 프로필 조회 시 404를 반환해야 한다."""
        resp = client.get(f"/api/v1/users/{self._user_id}/profile")
        assert resp.status_code == 404


class TestUserAddressAPI:
    """회원 배송지 API 통합 테스트."""

    @property
    def _user_id(self) -> int:
        uid = getattr(pytest, "created_address_user_id", None)
        if uid is None:
            pytest.skip("배송지 테스트용 회원 ID가 없습니다.")
        return uid

    @pytest.fixture(scope="class", autouse=True)
    def _setup_user(self, client: TestClient) -> None:
        """배송지 테스트용 회원을 생성한다."""
        payload = {
            "user_email": "address_test@example.com",
            "password_hash": "hashed-pw",
            "user_status": "ACTIVE",
            "user_type": "NORMAL",
        }
        resp = client.post("/api/v1/users", json=payload)
        assert resp.status_code == 201
        pytest.created_address_user_id = resp.json()["data"]["id"]

    # ---------- CREATE ----------
    def test_create_user_address_success(
        self, client: TestClient, address_payload: dict[str, Any]
    ) -> None:
        """배송지 생성 시 201 Created를 반환해야 한다."""
        resp = client.post(
            f"/api/v1/users/{self._user_id}/addresses",
            json=address_payload,
        )
        assert resp.status_code == 201, f"응답 본문: {resp.text}"

        body = resp.json()
        assert body["success"] is True
        assert "생성했습니다." in body["message"]

        data = body["data"]
        assert data["address_name"] == "집"
        assert data["is_default_address"] is True
        assert data["recipient_name"] == "홍길동"

        # 생성된 주소 ID 저장
        pytest.created_address_id = data["id"]

    def test_create_second_address_not_default(
        self, client: TestClient
    ) -> None:
        """두 번째 배송지는 기본값이 False여야 한다."""
        payload = {
            "address_name": "회사",
            "recipient_name": "홍길동",
            "recipient_phone": "010-1234-5678",
            "postal_code": "54321",
            "address_line1": "서울시 서초구",
            "is_default_address": False,
        }
        resp = client.post(
            f"/api/v1/users/{self._user_id}/addresses",
            json=payload,
        )
        assert resp.status_code == 201, f"응답 본문: {resp.text}"
        data = resp.json()["data"]
        assert data["is_default_address"] is False

    # ---------- LIST ----------
    def test_list_user_addresses(self, client: TestClient) -> None:
        """배송지 목록 조회 시 200 OK를 반환해야 한다."""
        resp = client.get(f"/api/v1/users/{self._user_id}/addresses")
        assert resp.status_code == 200

        body = resp.json()
        assert body["success"] is True
        assert isinstance(body["data"], list)
        assert len(body["data"]) >= 1

    # ---------- GET ----------
    def test_get_user_address_success(self, client: TestClient) -> None:
        """배송지 상세 조회 시 200 OK를 반환해야 한다."""
        address_id = getattr(pytest, "created_address_id", None)
        if address_id is None:
            pytest.skip("생성된 배송지 ID가 없습니다.")

        resp = client.get(
            f"/api/v1/users/{self._user_id}/addresses/{address_id}"
        )
        assert resp.status_code == 200

        body = resp.json()
        assert body["success"] is True
        assert body["data"]["id"] == address_id

    def test_get_user_address_not_found(self, client: TestClient) -> None:
        """존재하지 않는 배송지 조회 시 404를 반환해야 한다."""
        resp = client.get(f"/api/v1/users/{self._user_id}/addresses/99999")
        assert resp.status_code == 404

    # ---------- UPDATE ----------
    def test_update_user_address_success(
        self, client: TestClient, address_update_payload: dict[str, Any]
    ) -> None:
        """배송지 수정 시 200 OK를 반환해야 한다."""
        address_id = getattr(pytest, "created_address_id", None)
        if address_id is None:
            pytest.skip("생성된 배송지 ID가 없습니다.")

        resp = client.put(
            f"/api/v1/users/{self._user_id}/addresses/{address_id}",
            json=address_update_payload,
        )
        assert resp.status_code == 200, f"응답 본문: {resp.text}"

        body = resp.json()
        assert body["success"] is True
        assert "수정했습니다." in body["message"]
        assert body["data"]["address_name"] == "회사"

    # ---------- DELETE ----------
    def test_delete_user_address_success(self, client: TestClient) -> None:
        """배송지 삭제 시 200 OK를 반환해야 한다."""
        address_id = getattr(pytest, "created_address_id", None)
        if address_id is None:
            pytest.skip("생성된 배송지 ID가 없습니다.")

        resp = client.delete(
            f"/api/v1/users/{self._user_id}/addresses/{address_id}"
        )
        assert resp.status_code == 200, f"응답 본문: {resp.text}"

        body = resp.json()
        assert body["success"] is True
        assert "삭제했습니다." in body["message"]

    def test_get_deleted_address_returns_404(self, client: TestClient) -> None:
        """삭제된 배송지 조회 시 404를 반환해야 한다."""
        address_id = getattr(pytest, "created_address_id", None)
        if address_id is None:
            pytest.skip("생성된 배송지 ID가 없습니다.")

        resp = client.get(
            f"/api/v1/users/{self._user_id}/addresses/{address_id}"
        )
        assert resp.status_code == 404


class TestUserRoleAPI:
    """역할(Role) API 통합 테스트."""

    ROLE_URL = "/api/v1/roles"

    # ---------- CREATE ----------
    def test_create_role_success(
        self, client: TestClient, role_payload: dict[str, Any]
    ) -> None:
        """역할 생성 시 201 Created를 반환해야 한다."""
        resp = client.post(self.ROLE_URL, json=role_payload)
        assert resp.status_code == 201, f"응답 본문: {resp.text}"

        body = resp.json()
        assert body["success"] is True
        assert "생성했습니다." in body["message"]
        assert body["data"]["role_name"] == "TEST_ROLE"

        pytest.created_role_id = body["data"]["id"]

    # ---------- LIST ----------
    def test_list_roles(self, client: TestClient) -> None:
        """역할 목록 조회 시 200 OK를 반환해야 한다."""
        resp = client.get(self.ROLE_URL)
        assert resp.status_code == 200

        body = resp.json()
        assert body["success"] is True
        assert isinstance(body["data"], list)
        assert len(body["data"]) >= 1

    # ---------- GET ----------
    def test_get_role_success(self, client: TestClient) -> None:
        """역할 상세 조회 시 200 OK를 반환해야 한다."""
        role_id = getattr(pytest, "created_role_id", None)
        if role_id is None:
            pytest.skip("생성된 역할 ID가 없습니다.")

        resp = client.get(f"{self.ROLE_URL}/{role_id}")
        assert resp.status_code == 200

        body = resp.json()
        assert body["success"] is True
        assert body["data"]["role_name"] == "TEST_ROLE"

    def test_get_role_not_found(self, client: TestClient) -> None:
        """존재하지 않는 역할 조회 시 404를 반환해야 한다."""
        resp = client.get(f"{self.ROLE_URL}/99999")
        assert resp.status_code == 404

    # ---------- UPDATE ----------
    def test_update_role_success(
        self, client: TestClient, role_update_payload: dict[str, Any]
    ) -> None:
        """역할 수정 시 200 OK를 반환해야 한다."""
        role_id = getattr(pytest, "created_role_id", None)
        if role_id is None:
            pytest.skip("생성된 역할 ID가 없습니다.")

        resp = client.put(
            f"{self.ROLE_URL}/{role_id}",
            json=role_update_payload,
        )
        assert resp.status_code == 200, f"응답 본문: {resp.text}"

        body = resp.json()
        assert body["success"] is True
        assert "수정했습니다." in body["message"]
        assert body["data"]["role_name"] == "TEST_ROLE_UPDATED"

    # ---------- DELETE ----------
    def test_delete_role_success(self, client: TestClient) -> None:
        """역할 삭제 시 200 OK를 반환해야 한다."""
        role_id = getattr(pytest, "created_role_id", None)
        if role_id is None:
            pytest.skip("생성된 역할 ID가 없습니다.")

        resp = client.delete(f"{self.ROLE_URL}/{role_id}")
        assert resp.status_code == 200, f"응답 본문: {resp.text}"

        body = resp.json()
        assert body["success"] is True
        assert "삭제했습니다." in body["message"]

    def test_get_deleted_role_returns_404(self, client: TestClient) -> None:
        """삭제된 역할 조회 시 404를 반환해야 한다."""
        role_id = getattr(pytest, "created_role_id", None)
        if role_id is None:
            pytest.skip("생성된 역할 ID가 없습니다.")

        resp = client.get(f"{self.ROLE_URL}/{role_id}")
        assert resp.status_code == 404


class TestUserRoleAssignmentAPI:
    """사용자-역할 할당 API 통합 테스트."""

    @property
    def _user_id(self) -> int:
        uid = getattr(pytest, "created_assign_user_id", None)
        if uid is None:
            pytest.skip("할당 테스트용 회원 ID가 없습니다.")
        return uid

    @property
    def _role_id(self) -> int:
        rid = getattr(pytest, "created_assign_role_id", None)
        if rid is None:
            pytest.skip("할당 테스트용 역할 ID가 없습니다.")
        return rid

    @pytest.fixture(scope="class", autouse=True)
    def _setup_data(self, client: TestClient) -> None:
        """할당 테스트용 회원과 역할을 생성한다."""
        # 회원 생성
        user_payload = {
            "user_email": "assign_test@example.com",
            "password_hash": "hashed-pw",
            "user_status": "ACTIVE",
            "user_type": "NORMAL",
        }
        resp = client.post("/api/v1/users", json=user_payload)
        assert resp.status_code == 201
        pytest.created_assign_user_id = resp.json()["data"]["id"]

        # 역할 생성
        role_payload = {"role_name": "ASSIGN_TEST_ROLE"}
        resp = client.post("/api/v1/roles", json=role_payload)
        assert resp.status_code == 201
        pytest.created_assign_role_id = resp.json()["data"]["id"]

    # ---------- ASSIGN ----------
    def test_assign_role_to_user_success(self, client: TestClient) -> None:
        """사용자에게 역할 할당 시 200 OK를 반환해야 한다."""
        resp = client.post(
            f"/api/v1/users/{self._user_id}/roles",
            json={"role_id": self._role_id},
        )
        assert resp.status_code == 200, f"응답 본문: {resp.text}"

        body = resp.json()
        assert body["success"] is True
        assert "할당했습니다." in body["message"]
        assert body["data"]["user_id"] == self._user_id
        assert body["data"]["role_id"] == self._role_id

    def test_assign_duplicate_role_returns_409(self, client: TestClient) -> None:
        """이미 할당된 역할을 다시 할당하면 409 Conflict를 반환해야 한다."""
        resp = client.post(
            f"/api/v1/users/{self._user_id}/roles",
            json={"role_id": self._role_id},
        )
        assert resp.status_code == 409, f"응답 본문: {resp.text}"

    # ---------- VERIFY IN USER DETAIL ----------
    def test_get_user_includes_roles(self, client: TestClient) -> None:
        """회원 상세 조회 시 roles 필드에 할당된 역할이 포함되어야 한다."""
        resp = client.get(f"/api/v1/users/{self._user_id}")
        assert resp.status_code == 200

        body = resp.json()
        roles = body["data"]["roles"]
        role_names = [r["role_name"] for r in roles]
        assert "ASSIGN_TEST_ROLE" in role_names

    # ---------- REMOVE ----------
    def test_remove_role_from_user_success(self, client: TestClient) -> None:
        """사용자 역할 해제 시 200 OK를 반환해야 한다."""
        resp = client.delete(
            f"/api/v1/users/{self._user_id}/roles/{self._role_id}",
        )
        assert resp.status_code == 200, f"응답 본문: {resp.text}"

        body = resp.json()
        assert body["success"] is True
        assert "해제했습니다." in body["message"]

    def test_remove_nonexistent_role_returns_404(self, client: TestClient) -> None:
        """할당되지 않은 역할 해제 시 404를 반환해야 한다."""
        resp = client.delete(
            f"/api/v1/users/{self._user_id}/roles/{self._role_id}",
        )
        assert resp.status_code == 404


class TestGetMyUser:
    """GET /users/me 엔드포인트 테스트."""

    _user_id: int | None = None

    @pytest.fixture(autouse=True)
    def _setup(self, client: TestClient, api_prefix: str) -> None:
        """테스트용 회원을 생성한다."""
        if TestGetMyUser._user_id is not None:
            return
        resp = client.post(
            f"{api_prefix}/users",
            json={
                "user_email": "me_test@example.com",
                "password_hash": "hashed-pw",
                "user_status": "ACTIVE",
                "user_type": "NORMAL",
            },
        )
        assert resp.status_code == 200
        TestGetMyUser._user_id = resp.json()["data"]["id"]

    def test_get_my_user_without_auth_returns_401(self, client: TestClient, api_prefix: str) -> None:
        """인증 없이 /users/me 호출 시 401을 반환해야 한다."""
        resp = client.get(f"{api_prefix}/users/me")
        assert resp.status_code == 401

    def test_get_my_user_with_valid_token(self, client: TestClient, api_prefix: str) -> None:
        """유효한 토큰으로 /users/me 호출 시 회원 정보를 반환해야 한다."""
        from app.core.security import create_access_token

        token = create_access_token(subject=str(self._user_id))
        resp = client.get(
            f"{api_prefix}/users/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200, f"응답 본문: {resp.text}"
        body = resp.json()
        assert body["success"] is True
        assert body["data"]["id"] == self._user_id
        assert body["data"]["user_email"] == "me_test@example.com"

    def test_get_my_user_with_invalid_token_returns_401(self, client: TestClient, api_prefix: str) -> None:
        """유효하지 않은 토큰으로 /users/me 호출 시 401을 반환해야 한다."""
        resp = client.get(
            f"{api_prefix}/users/me",
            headers={"Authorization": "Bearer invalid_token_xxx"},
        )
        assert resp.status_code == 401


class TestGetMyCoupons:
    """GET /users/me/coupons 엔드포인트 테스트."""

    _user_id: int | None = None

    @pytest.fixture(autouse=True)
    def _setup(self, client: TestClient, api_prefix: str) -> None:
        """테스트용 회원을 생성한다."""
        if TestGetMyCoupons._user_id is not None:
            return
        resp = client.post(
            f"{api_prefix}/users",
            json={
                "user_email": "coupon_test@example.com",
                "password_hash": "hashed-pw",
                "user_status": "ACTIVE",
                "user_type": "NORMAL",
            },
        )
        assert resp.status_code == 200
        TestGetMyCoupons._user_id = resp.json()["data"]["id"]

    def test_get_my_coupons_without_auth_returns_401(self, client: TestClient, api_prefix: str) -> None:
        """인증 없이 /users/me/coupons 호출 시 401을 반환해야 한다."""
        resp = client.get(f"{api_prefix}/users/me/coupons")
        assert resp.status_code == 401

    def test_get_my_coupons_returns_empty_list(self, client: TestClient, api_prefix: str) -> None:
        """쿠폰이 없는 회원이 조회 시 빈 목록을 반환해야 한다."""
        from app.core.security import create_access_token

        token = create_access_token(subject=str(self._user_id))
        resp = client.get(
            f"{api_prefix}/users/me/coupons",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200, f"응답 본문: {resp.text}"
        body = resp.json()
        assert body["success"] is True
        assert isinstance(body["data"], list)
