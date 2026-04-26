"""Core 예외 처리(exceptions) 모듈 단위 테스트."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI, status
from fastapi.responses import JSONResponse

from app.core.exceptions import (
    ApplicationException,
    ResourceNotFoundException,
    application_exception_handler,
    register_exception_handlers,
    unhandled_exception_handler,
)


class TestApplicationException:
    """ApplicationException 클래스의 동작을 검증한다."""

    def test_default_status_code(self):
        """ApplicationException의 기본 상태 코드는 400이어야 한다."""
        exc = ApplicationException(message="테스트 에러")
        assert exc.status_code == status.HTTP_400_BAD_REQUEST
        assert exc.message == "테스트 에러"

    def test_custom_status_code(self):
        """ApplicationException에 커스텀 상태 코드가 설정되어야 한다."""
        exc = ApplicationException(
            message="Not Found",
            status_code=status.HTTP_404_NOT_FOUND,
        )
        assert exc.status_code == 404
        assert exc.message == "Not Found"

    def test_exception_is_throwable(self):
        """ApplicationException이 실제로 raise될 수 있어야 한다."""
        with pytest.raises(ApplicationException) as exc_info:
            raise ApplicationException(message="에러 발생")
        assert exc_info.value.message == "에러 발생"
        assert exc_info.value.status_code == 400

    def test_exception_inherits_from_exception(self):
        """ApplicationException이 Exception을 상속해야 한다."""
        assert issubclass(ApplicationException, Exception)

    def test_super_init_called(self):
        """ApplicationException이 Exception의 __init__을 호출해야 한다."""
        exc = ApplicationException(message="테스트")
        assert str(exc) == "테스트"

    def test_empty_message(self):
        """ApplicationException이 빈 메시지로 생성될 수 있어야 한다."""
        exc = ApplicationException(message="")
        assert exc.message == ""

    def test_negative_status_code(self):
        """ApplicationException에 음수 상태 코드가 설정될 수 있어야 한다."""
        exc = ApplicationException(message="에러", status_code=-1)
        assert exc.status_code == -1


class TestResourceNotFoundException:
    """ResourceNotFoundException 클래스의 동작을 검증한다."""

    def test_default_message(self):
        """ResourceNotFoundException의 기본 메시지가 올바라야 한다."""
        exc = ResourceNotFoundException()
        assert exc.message == "요청한 리소스를 찾을 수 없습니다."

    def test_status_code_is_404(self):
        """ResourceNotFoundException의 상태 코드는 404여야 한다."""
        exc = ResourceNotFoundException()
        assert exc.status_code == status.HTTP_404_NOT_FOUND

    def test_custom_message(self):
        """ResourceNotFoundException에 커스텀 메시지가 설정되어야 한다."""
        exc = ResourceNotFoundException(message="사용자를 찾을 수 없습니다.")
        assert exc.message == "사용자를 찾을 수 없습니다."

    def test_inherits_from_application_exception(self):
        """ResourceNotFoundException이 ApplicationException을 상속해야 한다."""
        assert issubclass(ResourceNotFoundException, ApplicationException)

    def test_is_throwable(self):
        """ResourceNotFoundException이 raise될 수 있어야 한다."""
        with pytest.raises(ResourceNotFoundException) as exc_info:
            raise ResourceNotFoundException()
        assert exc_info.value.status_code == 404


class TestExceptionHandlers:
    """커스텀 예외 핸들러의 동작을 검증한다."""

    @pytest.mark.asyncio
    async def test_application_exception_handler_returns_json(self):
        """application_exception_handler가 JSONResponse를 반환해야 한다."""
        request_mock = MagicMock()
        exc = ApplicationException(message="테스트 에러", status_code=418)

        response = await application_exception_handler(request_mock, exc)

        assert isinstance(response, JSONResponse)
        assert response.status_code == 418
        content = response.body.decode()
        assert "테스트 에러" in content
        assert "ApplicationException" in content

    @pytest.mark.asyncio
    async def test_application_exception_handler_content(self):
        """application_exception_handler의 응답 본문이 올바른 구조여야 한다."""
        request_mock = MagicMock()
        exc = ApplicationException(message="Bad Request")

        response = await application_exception_handler(request_mock, exc)
        body = response.body.decode()

        # 공백 없이 직렬화된 JSON 확인
        assert '"detail":"Bad Request"' in body
        assert '"error_type":"ApplicationException"' in body

    @pytest.mark.asyncio
    async def test_unhandled_exception_handler_returns_500(self):
        """unhandled_exception_handler가 500 응답을 반환해야 한다."""
        request_mock = MagicMock()
        exc = ValueError("Something broke")

        response = await unhandled_exception_handler(request_mock, exc)

        assert isinstance(response, JSONResponse)
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        body = response.body.decode()
        assert "서버 내부 오류가 발생했습니다." in body
        assert "ValueError" in body

    @pytest.mark.asyncio
    async def test_unhandled_exception_handler_different_exceptions(self):
        """unhandled_exception_handler가 다양한 예외 타입을 처리해야 한다."""
        request_mock = MagicMock()

        for exc_cls, name in [(RuntimeError, "RuntimeError"), (KeyError, "KeyError")]:
            response = await unhandled_exception_handler(request_mock, exc_cls("test"))
            body = response.body.decode()
            assert name in body


class TestRegisterExceptionHandlers:
    """register_exception_handlers 함수의 동작을 검증한다."""

    def test_registers_application_exception_handler(self, mocker):
        """register_exception_handlers가 ApplicationException 핸들러를 등록해야 한다."""
        app_mock = MagicMock(spec=FastAPI)
        register_exception_handlers(app_mock)

        assert app_mock.add_exception_handler.call_count == 2

        first_call_args = app_mock.add_exception_handler.call_args_list[0]
        assert first_call_args[0][0] == ApplicationException
        assert first_call_args[0][1] is application_exception_handler

    def test_registers_generic_exception_handler(self, mocker):
        """register_exception_handlers가 Exception 핸들러를 등록해야 한다."""
        app_mock = MagicMock(spec=FastAPI)
        register_exception_handlers(app_mock)

        second_call_args = app_mock.add_exception_handler.call_args_list[1]
        assert second_call_args[0][0] == Exception
        assert second_call_args[0][1] is unhandled_exception_handler

    def test_register_with_real_app(self):
        """register_exception_handlers가 실제 FastAPI 앱에 정상 등록되어야 한다."""
        app = FastAPI()
        register_exception_handlers(app)

        assert len(app.exception_handlers) >= 2
        assert ApplicationException in app.exception_handlers
        assert Exception in app.exception_handlers
