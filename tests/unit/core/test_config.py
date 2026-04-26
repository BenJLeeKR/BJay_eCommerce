"""Core 설정(config) 모듈 단위 테스트."""
from __future__ import annotations

from functools import lru_cache
from unittest.mock import patch

import pytest

from app.core.config import Settings, get_settings, settings


class TestSettings:
    """Settings 클래스의 기본 동작을 검증한다."""

    def test_default_values(self, monkeypatch):
        """Settings가 환경 변수 없이 기본값으로 생성되어야 한다."""
        # .env 파일 영향 방지를 위해 환경 변수 초기화
        monkeypatch.delenv("PROJECT_NAME", raising=False)
        monkeypatch.delenv("DEBUG", raising=False)
        monkeypatch.delenv("SECRET_KEY", raising=False)
        monkeypatch.delenv("DB_SCHEMA", raising=False)
        monkeypatch.delenv("POSTGRES_SERVER", raising=False)
        monkeypatch.delenv("POSTGRES_PORT", raising=False)
        monkeypatch.delenv("POSTGRES_USER", raising=False)
        monkeypatch.delenv("POSTGRES_PASSWORD", raising=False)
        monkeypatch.delenv("POSTGRES_DB", raising=False)
        sut = Settings(_env_file=None)
        assert sut.PROJECT_NAME == "E-Commerce API"
        assert sut.APP_VERSION == "0.1.0"
        assert sut.DEBUG is False
        assert sut.API_V1_PREFIX == "/api/v1"
        assert sut.AUTO_CREATE_TABLES is False
        assert sut.DB_SCHEMA == "ecommerce"
        assert sut.SECRET_KEY == "change-me"
        assert sut.ACCESS_TOKEN_EXPIRE_MINUTES == 60
        assert sut.ALGORITHM == "HS256"

    def test_computed_sqlalchemy_uri(self, monkeypatch):
        """SQLALCHEMY_DATABASE_URI computed field가 올바른 URI를 생성해야 한다."""
        monkeypatch.delenv("POSTGRES_SERVER", raising=False)
        monkeypatch.delenv("POSTGRES_PORT", raising=False)
        monkeypatch.delenv("POSTGRES_USER", raising=False)
        monkeypatch.delenv("POSTGRES_PASSWORD", raising=False)
        monkeypatch.delenv("POSTGRES_DB", raising=False)
        sut = Settings(
            POSTGRES_USER="test_user",
            POSTGRES_PASSWORD="test_pass",
            POSTGRES_SERVER="test_host",
            POSTGRES_PORT=15432,
            POSTGRES_DB="test_db",
            _env_file=None,
        )
        expected = "postgresql+psycopg://test_user:test_pass@test_host:15432/test_db"
        assert sut.SQLALCHEMY_DATABASE_URI == expected

    def test_computed_sqlalchemy_uri_with_defaults(self, monkeypatch):
        """SQLALCHEMY_DATABASE_URI가 기본 DB 설정으로 URI를 생성해야 한다."""
        monkeypatch.delenv("POSTGRES_SERVER", raising=False)
        monkeypatch.delenv("POSTGRES_PORT", raising=False)
        monkeypatch.delenv("POSTGRES_USER", raising=False)
        monkeypatch.delenv("POSTGRES_PASSWORD", raising=False)
        monkeypatch.delenv("POSTGRES_DB", raising=False)
        sut = Settings(_env_file=None)
        expected = "postgresql+psycopg://postgres:postgres@postgres:5432/ecommerce"
        assert sut.SQLALCHEMY_DATABASE_URI == expected

    def test_override_via_environment(self, monkeypatch):
        """Settings가 환경 변수를 통해 값을 오버라이드할 수 있어야 한다."""
        monkeypatch.setenv("PROJECT_NAME", "Override API")
        monkeypatch.setenv("SECRET_KEY", "override-secret")
        monkeypatch.setenv("DB_SCHEMA", "test_schema")
        sut = Settings(_env_file=None)
        assert sut.PROJECT_NAME == "Override API"
        assert sut.SECRET_KEY == "override-secret"
        assert sut.DB_SCHEMA == "test_schema"

    def test_debug_mode_enabled(self, monkeypatch):
        """DEBUG=True로 설정되면 debug 속성이 참이어야 한다."""
        monkeypatch.setenv("DEBUG", "true")
        sut = Settings(_env_file=None)
        assert sut.DEBUG is True

    def test_access_token_expire_minutes_custom(self, monkeypatch):
        """ACCESS_TOKEN_EXPIRE_MINUTES를 커스텀 설정할 수 있어야 한다."""
        monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_MINUTES", "120")
        sut = Settings(_env_file=None)
        assert sut.ACCESS_TOKEN_EXPIRE_MINUTES == 120

    def test_extra_fields_are_ignored(self, monkeypatch):
        """SettingsConfigDict(extra='ignore')로 인해 추가 필드가 무시되어야 한다."""
        monkeypatch.setenv("UNKNOWN_FIELD", "should_be_ignored")
        sut = Settings(_env_file=None)
        assert not hasattr(sut, "UNKNOWN_FIELD")

    def test_case_sensitive(self, monkeypatch):
        """설정 필드가 대소문자를 구분해야 한다."""
        sut = Settings(_env_file=None)
        assert hasattr(sut, "DB_SCHEMA")
        assert not hasattr(sut, "db_schema")


class TestGetSettings:
    """get_settings 함수의 동작을 검증한다."""

    def test_get_settings_returns_settings_instance(self):
        """get_settings가 Settings 인스턴스를 반환해야 한다."""
        result = get_settings()
        assert isinstance(result, Settings)

    def test_get_settings_is_cached(self):
        """get_settings가 lru_cache에 의해 동일한 인스턴스를 반환해야 한다."""
        first = get_settings()
        second = get_settings()
        assert first is second

    def test_global_settings_is_instance(self):
        """전역 settings 객체가 Settings 인스턴스여야 한다."""
        assert isinstance(settings, Settings)
        assert settings.PROJECT_NAME == "E-Commerce API"
