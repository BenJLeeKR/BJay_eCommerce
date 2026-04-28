"""Core 의존성(dependencies) 모듈 단위 테스트."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.dependencies import get_current_user, get_current_user_entity, get_db, require_user_types


class TestGetDb:
    """get_db 의존성 함수의 동작을 검증한다."""

    def test_get_db_yields_session(self, mocker):
        """get_db가 데이터베이스 세션을 생성해야 한다."""
        mock_session = MagicMock()
        mocker.patch("app.dependencies.get_db_session", return_value=iter([mock_session]))

        gen = get_db()
        session = next(gen)
        assert session is mock_session

    def test_get_db_delegates_to_get_db_session(self, mocker):
        """get_db가 내부적으로 get_db_session을 호출해야 한다."""
        mock_get_db_session = mocker.patch("app.dependencies.get_db_session")
        mock_get_db_session.return_value = iter([MagicMock()])

        gen = get_db()
        next(gen)
        mock_get_db_session.assert_called_once()


class TestGetCurrentUser:
    """get_current_user 의존성 함수의 동작을 검증한다."""

    def test_valid_token_returns_payload(self, mocker):
        """유효한 JWT 토큰이 전달되면 페이로드를 반환해야 한다."""
        mock_payload = {"sub": "user_1", "exp": 9999999999}
        mocker.patch(
            "app.dependencies.decode_access_token",
            return_value=mock_payload,
        )

        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="valid_token",
        )
        result = get_current_user(credentials=credentials)
        assert result == mock_payload
        assert result["sub"] == "user_1"

    def test_missing_credentials_raises_401(self):
        """인증 정보가 없으면 401 예외가 발생해야 한다."""
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(credentials=None)
        assert exc_info.value.status_code == 401
        assert "인증 정보가 필요합니다." in exc_info.value.detail

    def test_missing_subject_raises_401(self, mocker):
        """토큰에 sub 클레임이 없으면 401 예외가 발생해야 한다."""
        mocker.patch(
            "app.dependencies.decode_access_token",
            return_value={"exp": 9999999999},  # sub 없음
        )

        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="token_no_subject",
        )
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(credentials=credentials)
        assert exc_info.value.status_code == 401
        assert "유효하지 않은 토큰입니다." in exc_info.value.detail

    def test_none_subject_raises_401(self, mocker):
        """토큰의 sub 클레임이 None이면 401 예외가 발생해야 한다."""
        mocker.patch(
            "app.dependencies.decode_access_token",
            return_value={"sub": None, "exp": 9999999999},
        )

        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="token_none_sub",
        )
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(credentials=credentials)
        assert exc_info.value.status_code == 401
        assert "유효하지 않은 토큰입니다." in exc_info.value.detail

    def test_invalid_token_raises_401(self, mocker):
        """유효하지 않은 토큰이 전달되면 401 예외가 발생해야 한다."""
        mocker.patch(
            "app.dependencies.decode_access_token",
            side_effect=HTTPException(
                status_code=401,
                detail="토큰 검증에 실패했습니다.",
            ),
        )

        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="invalid_token",
        )
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(credentials=credentials)
        assert exc_info.value.status_code == 401

    def test_decode_access_token_called_with_credentials(self, mocker):
        """decode_access_token이 credentials 문자열로 호출되어야 한다."""
        mock_decode = mocker.patch(
            "app.dependencies.decode_access_token",
            return_value={"sub": "test_user"},
        )

        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="my_token_value",
        )
        get_current_user(credentials=credentials)
        mock_decode.assert_called_once_with("my_token_value")

    def test_returns_additional_claims(self, mocker):
        """get_current_user가 추가 클레임을 포함한 전체 페이로드를 반환해야 한다."""
        mock_payload = {
            "sub": "admin_1",
            "exp": 9999999999,
            "role": "admin",
            "permissions": ["read", "write"],
        }
        mocker.patch(
            "app.dependencies.decode_access_token",
            return_value=mock_payload,
        )

        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="admin_token",
        )
        result = get_current_user(credentials=credentials)
        assert result["role"] == "admin"
        assert "write" in result["permissions"]


class TestGetCurrentUserEntity:
    """get_current_user_entity 의존성 함수의 동작을 검증한다."""

    def test_valid_user_returns_entity(self, mocker):
        """유효한 user_id로 UserAccount 엔티티를 반환해야 한다."""
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.user_type = "NORMAL"
        mock_user.user_email = "test@example.com"

        mock_credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="valid_token",
        )
        mocker.patch(
            "app.dependencies.get_current_user",
            return_value={"sub": "user_1"},
        )
        mock_execute = MagicMock()
        mock_scalar = MagicMock()
        mock_scalar.scalar_one_or_none.return_value = mock_user
        mock_execute.return_value = mock_scalar
        mock_db = MagicMock()
        mock_db.execute = mock_execute

        result = get_current_user_entity(
            credentials=mock_credentials,
            db=mock_db,
        )
        assert result is mock_user
        assert result.user_type == "NORMAL"

    def test_nonexistent_user_raises_401(self, mocker):
        """존재하지 않는 user_id면 401 예외가 발생해야 한다."""
        mock_credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="valid_token",
        )
        mocker.patch(
            "app.dependencies.get_current_user",
            return_value={"sub": "user_999"},
        )
        mock_execute = MagicMock()
        mock_scalar = MagicMock()
        mock_scalar.scalar_one_or_none.return_value = None
        mock_execute.return_value = mock_scalar
        mock_db = MagicMock()
        mock_db.execute = mock_execute

        with pytest.raises(HTTPException) as exc_info:
            get_current_user_entity(
                credentials=mock_credentials,
                db=mock_db,
            )
        assert exc_info.value.status_code == 401
        assert "사용자를 찾을 수 없습니다." in exc_info.value.detail


class TestRequireUserTypes:
    """require_user_types RBAC 의존성 팩토리의 동작을 검증한다."""

    def test_allowed_type_passes(self, mocker):
        """허용된 user_type이면 통과해야 한다."""
        mock_user = MagicMock()
        mock_user.user_type = "ADMIN"

        dependency_class = require_user_types("ADMIN")
        instance = dependency_class(current_user=mock_user)
        assert instance is not None

    def test_disallowed_type_raises_403(self, mocker):
        """허용되지 않은 user_type이면 403 예외가 발생해야 한다."""
        mock_user = MagicMock()
        mock_user.user_type = "NORMAL"

        dependency_class = require_user_types("ADMIN")
        with pytest.raises(HTTPException) as exc_info:
            dependency_class(current_user=mock_user)
        assert exc_info.value.status_code == 403
        detail = exc_info.value.detail
        assert detail["code"] == "FORBIDDEN"
        assert detail["required_user_types"] == ["ADMIN"]
        assert detail["user_type"] == "NORMAL"

    def test_multiple_allowed_types(self, mocker):
        """여러 user_type이 허용된 경우 그중 하나면 통과해야 한다."""
        mock_user = MagicMock()
        mock_user.user_type = "SELLER"

        dependency_class = require_user_types("ADMIN", "SELLER", "MANAGER")
        instance = dependency_class(current_user=mock_user)
        assert instance is not None

    def test_default_is_admin_only(self, mocker):
        """인자 없이 호출하면 ADMIN만 허용해야 한다."""
        mock_admin = MagicMock()
        mock_admin.user_type = "ADMIN"
        mock_normal = MagicMock()
        mock_normal.user_type = "NORMAL"

        dependency_class = require_user_types()

        # ADMIN은 통과
        instance = dependency_class(current_user=mock_admin)
        assert instance is not None

        # NORMAL은 403
        with pytest.raises(HTTPException) as exc_info:
            dependency_class(current_user=mock_normal)
        assert exc_info.value.status_code == 403
