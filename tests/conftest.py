"""
통합(Integration) 테스트를 위한 공통 Fixture 및 설정.

- PostgreSQL (Docker: agent_db)을 사용하여 운영 DB와 동일한 환경에서 테스트
- FastAPI의 dependency_overrides를 활용하여 DB 세션을 테스트용으로 교체
- 각 테스트마다 트랜잭션 롤백을 통해 격리된 환경 보장
"""
from __future__ import annotations

import os
from collections.abc import Generator
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.database import Base
from app.dependencies import get_db
from app.main import create_application

# ---------------------------------------------------------------
# 1. 테스트 전용 엔진 & 세션 팩토리 (PostgreSQL - ecommerce_test DB)
# ---------------------------------------------------------------
# 운영 DB(ecommerce) 대신 테스트 전용 DB(ecommerce_test) 사용
# Docker 컨테이너(agent_db)는 localhost:5432에서 수신 대기 중이며,
# 비밀번호는 "your-password"로 설정되어 있음 (.env의 "postgres"와 다름)
TEST_DATABASE_URL = (
    f"postgresql+psycopg://{settings.POSTGRES_USER}:your-password"
    f"@localhost:{settings.POSTGRES_PORT}/ecommerce_test"
)

test_engine = create_engine(
    TEST_DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
)

TestSessionLocal = sessionmaker(
    bind=test_engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
    class_=Session,
)


def _build_override_get_db(get_session: Session) -> Any:
    """주어진 세션을 반환하는 get_db 오버라이드 함수를 생성한다."""

    def override_get_db() -> Generator[Session, None, None]:
        yield get_session

    return override_get_db


# ---------------------------------------------------------------
# 2. Application & Client Fixture (session scope)
# ---------------------------------------------------------------
@pytest.fixture(scope="session")
def app() -> FastAPI:
    """FastAPI 애플리케이션 인스턴스 (오버라이드 미적용 상태)."""
    return create_application()


@pytest.fixture(scope="session")
def client(app: FastAPI) -> Generator[TestClient, None, None]:
    """TestClient를 통해 HTTP 요청을 시뮬레이션한다.

    ``raise_server_exceptions=False``로 설정하여 서버 내부 오류(500)가
    예외로 전파되지 않고 HTTP 응답으로 수신되도록 한다.
    """
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


# ---------------------------------------------------------------
# 3. DB 테이블 생성 (session scope, autouse)
# ---------------------------------------------------------------
@pytest.fixture(scope="session", autouse=True)
def setup_database() -> Generator[None, None, None]:
    """테스트 세션 시작 시 ecommerce/meta 스키마 아래 모든 테이블을 생성한다."""
    with test_engine.connect() as conn:
        conn.execute(
            text(f"CREATE SCHEMA IF NOT EXISTS {settings.DB_SCHEMA}")
        )
        conn.execute(
            text("CREATE SCHEMA IF NOT EXISTS meta")
        )
        conn.execute(
            text(f"SET search_path TO {settings.DB_SCHEMA}, meta, public")
        )
        conn.commit()

    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


# ---------------------------------------------------------------
# 4. 모듈 단위 DB 세션 공유 (의존성 오버라이드)
# ---------------------------------------------------------------
# NOTE: function-scoped connection.begin() + Session(bind=connection) 패턴은
# session.commit()이 connection의 root transaction을 commit하지 않아
# 데이터가 영구 저장되지 않는 문제가 있습니다.
# 따라서 TestSessionLocal()을 직접 사용하여 session.commit()이
# 실제 DB에 commit되도록 하고, 모듈 스코프로 공유합니다.
@pytest.fixture(scope="module", autouse=True)
def db_session(app: FastAPI) -> Generator[Session, None, None]:
    """모듈 내 모든 테스트가 하나의 DB 세션을 공유한다.

    - ``TestSessionLocal()``을 직접 생성하므로 session.commit()이 실제 DB에 반영됨
    - 모듈 단위로 공유되므로 CREATE → LIST → GET → UPDATE → DELETE 시나리오가 정상 동작
    - 모든 변경사항은 ``setup_database`` fixture의 session-scoped teardown에서
      ``Base.metadata.drop_all()``로 정리됨
    """
    session = TestSessionLocal()
    app.dependency_overrides[get_db] = _build_override_get_db(session)

    yield session

    session.close()
    app.dependency_overrides.pop(get_db, None)


# ---------------------------------------------------------------
# 5. API Prefix Helper
# ---------------------------------------------------------------
@pytest.fixture
def api_prefix() -> str:
    """API 버전 prefix를 반환한다."""
    return settings.API_V1_PREFIX
