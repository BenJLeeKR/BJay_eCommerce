"""User 도메인 단위 테스트."""
from __future__ import annotations

from datetime import date, datetime
from typing import Any

import pytest
from pydantic import ValidationError

from app.schemas.user import (
    UserAccountCreate,
    UserAccountRead,
    UserAccountUpdate,
    UserAddressCreate,
    UserAddressRead,
    UserAddressUpdate,
    UserLoginHistoryCreate,
    UserLoginHistoryRead,
    UserProfileCreate,
    UserProfileRead,
    UserProfileUpdate,
    UserRoleCreate,
    UserRoleRead,
    UserRoleUpdate,
    UserRoleMapCreate,
)


# ──────────────────────────────────────────────
# Model / Table Metadata
# ──────────────────────────────────────────────


def test_user_account_table_metadata_is_defined() -> None:
    """UserAccount 모델이 __tablename__과 필수 컬럼을 정의해야 한다."""
    from app.models.user import UserAccount

    assert UserAccount.__tablename__ == "user_account"
    assert hasattr(UserAccount, "id")
    assert hasattr(UserAccount, "user_email")
    assert hasattr(UserAccount, "password_hash")
    assert hasattr(UserAccount, "user_status")
    assert hasattr(UserAccount, "user_type")


def test_user_role_map_has_composite_primary_key() -> None:
    """UserRoleMap이 복합 기본키(user_id, role_id)를 가져야 한다."""
    from app.models.user import UserRoleMap

    pk_names = [c.name for c in UserRoleMap.__table__.primary_key.columns]
    assert "user_id" in pk_names
    assert "role_id" in pk_names


# ──────────────────────────────────────────────
# UserAccount Schemas
# ──────────────────────────────────────────────


def test_user_account_create_schema_validates_required_fields() -> None:
    """UserAccountCreate가 필수 필드를 검증해야 한다."""
    payload: dict[str, Any] = {
        "user_email": "test@example.com",
        "user_status": "ACTIVE",
        "user_type": "NORMAL",
    }
    schema = UserAccountCreate(**payload)
    assert schema.user_email == "test@example.com"
    assert schema.user_status == "ACTIVE"
    assert schema.user_type == "NORMAL"
    assert schema.is_email_verified is False


def test_user_account_create_missing_required_field() -> None:
    """UserAccountCreate에서 필수 필드 누락 시 ValidationError가 발생해야 한다."""
    with pytest.raises(ValidationError):
        UserAccountCreate(user_email="test@example.com")


def test_user_account_update_schema_supports_partial_update() -> None:
    """UserAccountUpdate가 부분 업데이트를 지원해야 한다."""
    payload: dict[str, Any] = {"user_email": "updated@example.com"}
    schema = UserAccountUpdate(**payload)
    assert schema.user_email == "updated@example.com"
    assert schema.user_status is None
    assert schema.user_type is None


# ──────────────────────────────────────────────
# UserProfile Schemas
# ──────────────────────────────────────────────


def test_user_profile_create_schema_validates_fields() -> None:
    """UserProfileCreate가 필드를 검증해야 한다."""
    payload: dict[str, Any] = {
        "user_id": 1,
        "user_name": "홍길동",
        "phone_number": "010-1234-5678",
        "birth_date": "1990-01-01",
        "gender_code": "M",
    }
    schema = UserProfileCreate(**payload)
    assert schema.user_id == 1
    assert schema.user_name == "홍길동"
    assert schema.phone_number == "010-1234-5678"
    assert schema.birth_date == date(1990, 1, 1)
    assert schema.gender_code == "M"


def test_user_profile_create_optional_user_id() -> None:
    """UserProfileCreate에서 user_id는 URL 경로에서 전달되므로 생략 가능해야 한다."""
    schema = UserProfileCreate(user_name="홍길동")
    assert schema.user_name == "홍길동"
    assert schema.user_id is None


def test_user_profile_update_supports_partial_update() -> None:
    """UserProfileUpdate가 부분 업데이트를 지원해야 한다."""
    schema = UserProfileUpdate(user_name="김철수")
    assert schema.user_name == "김철수"
    assert schema.phone_number is None
    assert schema.birth_date is None


def test_user_profile_read_schema() -> None:
    """UserProfileRead가 모든 필드를 포함해야 한다."""
    now = datetime.now()
    data: dict[str, Any] = {
        "id": 1,
        "user_id": 1,
        "user_name": "홍길동",
        "phone_number": "010-1234-5678",
        "birth_date": "1990-01-01",
        "gender_code": "M",
        "created_at": now.isoformat(),
        "created_by": None,
        "updated_at": None,
        "updated_by": None,
        "deleted_at": None,
        "deleted_by": None,
    }
    schema = UserProfileRead(**data)
    assert schema.id == 1
    assert schema.user_name == "홍길동"


# ──────────────────────────────────────────────
# UserAddress Schemas
# ──────────────────────────────────────────────


def test_user_address_create_schema_validates_fields() -> None:
    """UserAddressCreate가 필드를 검증해야 한다."""
    payload: dict[str, Any] = {
        "user_id": 1,
        "address_name": "집",
        "recipient_name": "홍길동",
        "recipient_phone": "010-1234-5678",
        "postal_code": "12345",
        "address_line1": "서울시 강남구",
        "address_line2": "101동 202호",
        "is_default_address": True,
    }
    schema = UserAddressCreate(**payload)
    assert schema.user_id == 1
    assert schema.address_name == "집"
    assert schema.is_default_address is True


def test_user_address_create_default_is_false() -> None:
    """UserAddressCreate의 is_default_address 기본값은 False여야 한다."""
    schema = UserAddressCreate(user_id=1)
    assert schema.is_default_address is False


def test_user_address_update_supports_partial_update() -> None:
    """UserAddressUpdate가 부분 업데이트를 지원해야 한다."""
    schema = UserAddressUpdate(address_name="회사")
    assert schema.address_name == "회사"
    assert schema.recipient_name is None


def test_user_address_read_schema() -> None:
    """UserAddressRead가 모든 필드를 포함해야 한다."""
    now = datetime.now()
    data: dict[str, Any] = {
        "id": 1,
        "user_id": 1,
        "address_name": "집",
        "recipient_name": "홍길동",
        "recipient_phone": "010-1234-5678",
        "postal_code": "12345",
        "address_line1": "서울시 강남구",
        "address_line2": "101동 202호",
        "is_default_address": True,
        "created_at": now.isoformat(),
        "created_by": None,
        "updated_at": None,
        "updated_by": None,
        "deleted_at": None,
        "deleted_by": None,
    }
    schema = UserAddressRead(**data)
    assert schema.id == 1
    assert schema.is_default_address is True


# ──────────────────────────────────────────────
# UserLoginHistory Schemas
# ──────────────────────────────────────────────


def test_user_login_history_create_schema() -> None:
    """UserLoginHistoryCreate가 필드를 검증해야 한다."""
    payload: dict[str, Any] = {
        "user_id": 1,
        "ip_address": "192.168.1.1",
        "user_agent": "Mozilla/5.0",
        "login_result": "SUCCESS",
    }
    schema = UserLoginHistoryCreate(**payload)
    assert schema.user_id == 1
    assert schema.ip_address == "192.168.1.1"
    assert schema.login_result == "SUCCESS"


def test_user_login_history_read_schema() -> None:
    """UserLoginHistoryRead가 모든 필드를 포함해야 한다."""
    now = datetime.now()
    data: dict[str, Any] = {
        "id": 1,
        "user_id": 1,
        "login_at": now.isoformat(),
        "ip_address": "192.168.1.1",
        "user_agent": "Mozilla/5.0",
        "login_result": "SUCCESS",
        "created_at": now.isoformat(),
    }
    schema = UserLoginHistoryRead(**data)
    assert schema.id == 1
    assert schema.login_result == "SUCCESS"


# ──────────────────────────────────────────────
# UserRole Schemas
# ──────────────────────────────────────────────


def test_user_role_create_schema() -> None:
    """UserRoleCreate가 role_name을 검증해야 한다."""
    schema = UserRoleCreate(role_name="ADMIN")
    assert schema.role_name == "ADMIN"


def test_user_role_create_missing_role_name() -> None:
    """UserRoleCreate에서 role_name 누락 시 ValidationError가 발생해야 한다."""
    with pytest.raises(ValidationError):
        UserRoleCreate()


def test_user_role_update_supports_partial_update() -> None:
    """UserRoleUpdate가 부분 업데이트를 지원해야 한다."""
    schema = UserRoleUpdate(role_name="SELLER")
    assert schema.role_name == "SELLER"


def test_user_role_read_schema() -> None:
    """UserRoleRead가 모든 필드를 포함해야 한다."""
    now = datetime.now()
    data: dict[str, Any] = {
        "id": 1,
        "role_name": "ADMIN",
        "created_at": now.isoformat(),
    }
    schema = UserRoleRead(**data)
    assert schema.id == 1
    assert schema.role_name == "ADMIN"


# ──────────────────────────────────────────────
# UserRoleMap Schemas
# ──────────────────────────────────────────────


def test_user_role_map_create_schema() -> None:
    """UserRoleMapCreate가 user_id와 role_id를 검증해야 한다."""
    schema = UserRoleMapCreate(user_id=1, role_id=2)
    assert schema.user_id == 1
    assert schema.role_id == 2


def test_user_role_map_create_missing_fields() -> None:
    """UserRoleMapCreate에서 필드 누락 시 ValidationError가 발생해야 한다."""
    with pytest.raises(ValidationError):
        UserRoleMapCreate(user_id=1)


# ──────────────────────────────────────────────
# Router Registration
# ──────────────────────────────────────────────


def test_user_router_registers_expected_routes() -> None:
    """User 라우터가 예상된 엔드포인트를 등록해야 한다."""
    from app.routers.user import router, role_router

    user_paths = {route.path for route in router.routes}
    role_paths = {route.path for route in role_router.routes}

    # UserAccount
    assert "/users" in user_paths
    assert "/users/{user_id}" in user_paths

    # UserProfile
    assert "/users/{user_id}/profile" in user_paths

    # UserAddress
    assert "/users/{user_id}/addresses" in user_paths
    assert "/users/{user_id}/addresses/{address_id}" in user_paths

    # User-Role Assignment
    assert "/users/{user_id}/roles" in user_paths
    assert "/users/{user_id}/roles/{role_id}" in user_paths

    # Role CRUD
    assert "/roles" in role_paths
    assert "/roles/{role_id}" in role_paths
