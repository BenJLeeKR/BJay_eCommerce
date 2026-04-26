"""Core 메인 애플리케이션(main) 모듈 단위 테스트."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI

from app.main import app, create_application, lifespan


class TestCreateApplication:
    """create_application 함수의 동작을 검증한다."""

    def test_create_application_returns_fastapi(self):
        """create_application이 FastAPI 인스턴스를 반환해야 한다."""
        application = create_application()
        assert isinstance(application, FastAPI)

    @patch("app.main.register_exception_handlers")
    def test_register_exception_handlers_called(self, mock_register):
        """create_application에서 register_exception_handlers가 호출되어야 한다."""
        application = create_application()
        # FastAPI 생성자에서도 호출될 수 있으므로 최소 1회 호출 확인
        assert mock_register.call_count >= 1

    def test_application_title_and_version(self):
        """생성된 애플리케이션의 title과 version이 설정값과 일치해야 한다."""
        application = create_application()
        assert application.title == "E-Commerce API"
        assert application.version == "0.1.0"

    def test_docs_urls_configured(self):
        """문서 URL이 설정되어 있어야 한다."""
        application = create_application()
        assert application.docs_url == "/docs"
        assert application.redoc_url == "/redoc"
        assert application.openapi_url == "/api/v1/openapi.json"

    def test_routers_are_included(self, mocker):
        """create_application에서 라우터들이 include_router되어야 한다."""
        application = create_application()
        # 라우트가 등록되어 있는지 확인 (헬스 체크 등)
        routes = [route.path for route in application.routes]
        # include_router로 등록된 라우트 경로 확인
        assert "/api/v1/health" in routes


class TestLifespan:
    """lifespan 컨텍스트 매니저의 동작을 검증한다."""

    @pytest.mark.asyncio
    async def test_lifespan_context_enter_and_exit(self, mocker):
        """lifespan이 컨텍스트 매니저로 정상 진입/종료되어야 한다."""
        mock_app = MagicMock(spec=FastAPI)
        async with lifespan(mock_app):
            pass  # 정상 종료 확인

    @pytest.mark.asyncio
    async def test_lifespan_with_create_tables_disabled(self, mocker):
        """AUTO_CREATE_TABLES=False일 때 create_all이 호출되지 않아야 한다."""
        mocker.patch(
            "app.main.settings.AUTO_CREATE_TABLES",
            False,
        )
        mock_create_all = mocker.patch("app.main.Base.metadata.create_all")

        mock_app = MagicMock(spec=FastAPI)
        async with lifespan(mock_app):
            pass

        mock_create_all.assert_not_called()

    @pytest.mark.asyncio
    async def test_lifespan_with_create_tables_enabled(self, mocker):
        """AUTO_CREATE_TABLES=True일 때 create_all이 호출되어야 한다."""
        mocker.patch(
            "app.main.settings.AUTO_CREATE_TABLES",
            True,
        )
        mock_create_all = mocker.patch("app.main.Base.metadata.create_all")

        mock_app = MagicMock(spec=FastAPI)
        async with lifespan(mock_app):
            pass

        mock_create_all.assert_called_once_with(bind=mocker.ANY)


class TestGlobalApp:
    """전역 app 인스턴스의 동작을 검증한다."""

    def test_app_is_fastapi_instance(self):
        """app이 FastAPI 인스턴스여야 한다."""
        assert isinstance(app, FastAPI)

    def test_app_has_routes(self):
        """app에 라우트가 등록되어 있어야 한다."""
        assert len(app.routes) > 0

    def test_app_health_check_route(self):
        """app에 /health 엔드포인트가 등록되어 있어야 한다."""
        route_paths = [route.path for route in app.routes]
        assert "/api/v1/health" in route_paths
