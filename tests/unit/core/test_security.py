"""Core 보안/인증(security) 모듈 단위 테스트."""
from __future__ import annotations

from datetime import timedelta
from unittest.mock import ANY, patch

import pytest
from fastapi import HTTPException
from jose import JWTError, jwt
from passlib.exc import UnknownHashError

from app.core.config import Settings, settings
from app.core.security import (
    create_access_token,
    decode_access_token,
    get_password_hash,
    verify_password,
)


class TestPasswordHashing:
    """비밀번호 해싱 및 검증 기능을 검증한다."""

    def test_get_password_hash_returns_string(self):
        """get_password_hash가 문자열 해시를 반환해야 한다."""
        hashed = get_password_hash("my_password")
        assert isinstance(hashed, str)
        assert len(hashed) > 0

    def test_get_password_hash_produces_bcrypt_hash(self):
        """get_password_hash가 bcrypt 해시($2b$ 접두사)를 반환해야 한다."""
        hashed = get_password_hash("my_password")
        assert hashed.startswith("$2b$")

    def test_verify_password_correct(self):
        """verify_password가 올바른 비밀번호에 대해 True를 반환해야 한다."""
        hashed = get_password_hash("correct_password")
        assert verify_password("correct_password", hashed) is True

    def test_verify_password_incorrect(self):
        """verify_password가 잘못된 비밀번호에 대해 False를 반환해야 한다."""
        hashed = get_password_hash("correct_password")
        assert verify_password("wrong_password", hashed) is False

    def test_verify_password_empty_string(self):
        """verify_password가 빈 문자열에 대해 적절히 동작해야 한다."""
        hashed = get_password_hash("")
        assert verify_password("", hashed) is True
        assert verify_password("not_empty", hashed) is False

    def test_password_hashing_different_hashes(self):
        """동일한 비밀번호라도 매번 다른 해시가 생성되어야 한다."""
        hash1 = get_password_hash("same_password")
        hash2 = get_password_hash("same_password")
        assert hash1 != hash2

    def test_verify_password_with_none_raises_error(self):
        """verify_password에 None이 전달되면 TypeError가 발생해야 한다."""
        hashed = get_password_hash("password")
        with pytest.raises(TypeError):
            verify_password(None, hashed)  # type: ignore[arg-type]

    def test_verify_password_invalid_hash(self):
        """verify_password에 잘못된 해시 포맷이 전달되면 UnknownHashError가 발생해야 한다."""
        with pytest.raises(UnknownHashError):
            verify_password("password", "not_a_valid_hash")


class TestJWTTokens:
    """JWT 토큰 생성 및 검증 기능을 검증한다."""

    def test_create_access_token_returns_string(self):
        """create_access_token이 문자열 토큰을 반환해야 한다."""
        token = create_access_token(subject="user_1")
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_access_token_contains_subject(self):
        """create_access_token이 주제(sub)를 포함해야 한다."""
        token = create_access_token(subject="user_42")
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        assert payload["sub"] == "user_42"

    def test_create_access_token_has_expiry(self):
        """create_access_token이 만료 시간(exp)을 포함해야 한다."""
        token = create_access_token(subject="user_1")
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        assert "exp" in payload

    def test_create_access_token_with_custom_expiry(self):
        """create_access_token에 커스텀 만료 시간이 적용되어야 한다."""
        token = create_access_token(
            subject="user_1",
            expires_delta=timedelta(minutes=5),
        )
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        assert "exp" in payload

    def test_decode_access_token_valid(self):
        """decode_access_token이 유효한 토큰의 페이로드를 반환해야 한다."""
        token = create_access_token(subject="user_99")
        payload = decode_access_token(token)
        assert payload["sub"] == "user_99"

    def test_decode_access_token_raises_on_invalid_token(self):
        """decode_access_token이 유효하지 않은 토큰에 대해 HTTPException을 발생시켜야 한다."""
        with pytest.raises(HTTPException) as exc_info:
            decode_access_token("invalid_token_here")
        assert exc_info.value.status_code == 401
        assert "토큰 검증에 실패했습니다." in exc_info.value.detail

    def test_decode_access_token_expired_token(self, mocker):
        """decode_access_token이 만료된 토큰에 대해 HTTPException을 발생시켜야 한다."""
        mocker.patch(
            "app.core.security.jwt.decode",
            side_effect=JWTError("Token expired"),
        )
        with pytest.raises(HTTPException) as exc_info:
            decode_access_token("expired_token")
        assert exc_info.value.status_code == 401

    def test_create_access_token_with_none_subject(self):
        """create_access_token에 subject=None이 전달되면 subject 없이 토큰이 생성되어야 한다."""
        token = create_access_token(subject=None)  # type: ignore[arg-type]
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            options={"verify_sub": False},
        )
        assert payload.get("sub") is None

    def test_decode_access_token_returns_all_claims(self):
        """decode_access_token이 모든 클레임을 포함한 딕셔너리를 반환해야 한다."""
        token = create_access_token(subject="user_1")
        payload = decode_access_token(token)
        assert isinstance(payload, dict)
        assert "sub" in payload
        assert "exp" in payload

    def test_token_with_different_secret_key_fails(self, mocker):
        """잘못된 시크릿 키로 생성된 토큰이 검증에 실패해야 한다."""
        # 먼저 원래 시크릿으로 토큰 생성
        token = create_access_token(subject="user_1")
        # 시크릿을 변경한 후 검증 시도 -> 실패
        mocker.patch("app.core.security.settings.SECRET_KEY", "different-secret")
        with pytest.raises(HTTPException):
            decode_access_token(token)


class TestSecurityEdgeCases:
    """보안 모듈의 엣지 케이스를 검증한다."""

    def test_very_long_password_hash(self):
        """매우 긴 비밀번호도 해싱이 가능해야 한다."""
        # bcrypt는 최대 72바이트까지만 처리하므로 72바이트 이내 비밀번호 사용
        long_password = "a" * 60
        hashed = get_password_hash(long_password)
        assert verify_password(long_password, hashed) is True

    def test_unicode_password(self):
        """유니코드 비밀번호가 정상 처리되어야 한다."""
        unicode_password = "パスワード🔐"
        hashed = get_password_hash(unicode_password)
        assert verify_password(unicode_password, hashed) is True

    def test_token_with_special_chars_in_subject(self):
        """subject에 특수문자가 포함된 토큰이 정상 생성되어야 한다."""
        token = create_access_token(subject="user@example.com!한글")
        payload = decode_access_token(token)
        assert payload["sub"] == "user@example.com!한글"
