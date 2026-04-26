"""Core 의존성(dependencies) 모듈 단위 테스트."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.dependencies import get_current_user, get_db


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
