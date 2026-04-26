"""Core 데이터베이스(database) 모듈 단위 테스트."""
from __future__ import annotations

from unittest.mock import patch

import pytest
from sqlalchemy import Column, Integer, MetaData, String
from sqlalchemy.orm import DeclarativeBase, Session, declared_attr

from app.database import (
    NAMING_CONVENTION,
    Base,
    SessionLocal,
    engine,
    get_db_session,
    metadata,
)
from app.core.config import settings


class TestMetadata:
    """데이터베이스 메타데이터 설정을 검증한다."""

    def test_metadata_has_naming_convention(self):
        """metadata에 명명 규칙이 설정되어 있어야 한다."""
        assert metadata.naming_convention is not None
        assert "ix" in metadata.naming_convention
        assert "uq" in metadata.naming_convention
        assert "fk" in metadata.naming_convention
        assert "pk" in metadata.naming_convention

    def test_naming_convention_keys(self):
        """NAMING_CONVENTION에 필요한 모든 키가 있어야 한다."""
        expected_keys = {"ix", "uq", "ck", "fk", "pk"}
        assert expected_keys.issubset(NAMING_CONVENTION.keys())

    def test_metadata_schema_is_set(self):
        """metadata에 DB_SCHEMA가 설정되어 있어야 한다."""
        assert metadata.schema is not None
        assert metadata.schema == settings.DB_SCHEMA


class TestBase:
    """Base 모델 클래스의 동작을 검증한다."""

    def test_base_is_declarative_base(self):
        """Base가 DeclarativeBase를 상속해야 한다."""
        assert issubclass(Base, DeclarativeBase)

    def test_base_uses_shared_metadata(self):
        """Base가 공통 metadata를 사용해야 한다."""
        assert Base.metadata is metadata

    def test_base_can_create_model(self):
        """Base를 상속받은 모델 클래스를 정의할 수 있어야 한다."""

        class TestModel(Base):
            __tablename__ = "test_table"
            id = Column(Integer, primary_key=True)
            name = Column(String(50))

        assert hasattr(TestModel, "__table__")
        assert TestModel.__tablename__ == "test_table"
        assert TestModel.__table__.c.id.primary_key is True

    def test_base_metadata_contains_tables(self):
        """Base.metadata에 테이블이 누적되어 있어야 한다."""
        # 기존 메타데이터에 테이블이 있어야 함 (모델들이 등록되어 있음)
        assert len(Base.metadata.tables) > 0


class TestEngine:
    """데이터베이스 엔진 설정을 검증한다."""

    def test_engine_is_created(self):
        """engine 객체가 생성되어 있어야 한다."""
        assert engine is not None

    def test_engine_has_pool_pre_ping(self):
        """engine에 pool_pre_ping이 설정되어 있어야 한다."""
        assert engine.pool._pre_ping is True


class TestSessionLocal:
    """SessionLocal 팩토리의 동작을 검증한다."""

    def test_session_local_is_sessionmaker(self):
        """SessionLocal이 sessionmaker 인스턴스여야 한다."""
        from sqlalchemy.orm import sessionmaker
        assert isinstance(SessionLocal, sessionmaker)

    def test_session_local_autocommit_disabled(self):
        """SessionLocal에 autocommit이 False여야 한다."""
        assert SessionLocal.kw.get("autocommit") is False

    def test_session_local_autoflush_disabled(self):
        """SessionLocal에 autoflush가 False여야 한다."""
        assert SessionLocal.kw.get("autoflush") is False

    def test_session_local_expire_on_commit_disabled(self):
        """SessionLocal에 expire_on_commit이 False여야 한다."""
        assert SessionLocal.kw.get("expire_on_commit") is False


class TestGetDbSession:
    """get_db_session 제너레이터의 동작을 검증한다."""

    def test_get_db_session_yields_session(self):
        """get_db_session이 Session 인스턴스를 생성해야 한다."""
        gen = get_db_session()
        session = next(gen)
        assert isinstance(session, Session)

    def test_get_db_session_closes_after_yield(self, mocker):
        """get_db_session이 세션 사용 후 close를 호출해야 한다."""
        close_mock = mocker.patch.object(Session, "close")
        gen = get_db_session()
        session = next(gen)
        with pytest.raises(StopIteration):
            next(gen)
        close_mock.assert_called_once()

    def test_get_db_session_ensures_close_on_exception(self, mocker):
        """get_db_session이 예외 발생 시에도 close를 호출해야 한다."""
        close_mock = mocker.patch.object(Session, "close")
        gen = get_db_session()
        next(gen)
        with pytest.raises(RuntimeError):
            gen.throw(RuntimeError, RuntimeError("test error"))
        close_mock.assert_called_once()


class TestModelRegistration:
    """모델 등록 및 메타데이터 일관성을 검증한다."""

    def test_known_tables_exist_in_metadata(self):
        """주요 도메인 테이블이 메타데이터에 등록되어 있어야 한다."""
        schema = settings.DB_SCHEMA
        expected_tables = {
            f"{schema}.cart",
            f"{schema}.cart_item",
            f"{schema}.cart_item_option_snapshot",
            f"{schema}.cart_coupon",
            f"{schema}.product",
            f"{schema}.sku",
            f"{schema}.user_account",
            f"{schema}.order_header",
            f"{schema}.order_item",
            f"{schema}.payment",
            f"{schema}.shipment",
            f"{schema}.shipment_item",
            f"{schema}.inventory",
            f"{schema}.promotion",
            f"{schema}.review",
            f"{schema}.search_product_index",
        }
        registered = set(Base.metadata.tables.keys())
        missing = expected_tables - registered
        assert not missing, (
            f"다음 테이블이 등록되지 않았습니다: {missing}"
        )
