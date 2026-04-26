from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse


class ApplicationException(Exception):
    """애플리케이션 전역에서 사용하는 공통 예외 클래스."""

    def __init__(self, message: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class ResourceNotFoundException(ApplicationException):
    """리소스를 찾을 수 없을 때 사용하는 예외 클래스."""

    def __init__(self, message: str = "요청한 리소스를 찾을 수 없습니다."):
        super().__init__(message=message, status_code=status.HTTP_404_NOT_FOUND)


async def application_exception_handler(
    _: Request,
    exc: ApplicationException,
) -> JSONResponse:
    """커스텀 애플리케이션 예외를 표준 JSON 응답으로 변환한다."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.message,
            "error_type": exc.__class__.__name__,
        },
    )


async def unhandled_exception_handler(_: Request, exc: Exception) -> JSONResponse:
    """처리되지 않은 예외를 공통 포맷으로 응답한다."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "서버 내부 오류가 발생했습니다.",
            "error_type": exc.__class__.__name__,
        },
    )


def register_exception_handlers(application: FastAPI) -> None:
    """FastAPI 애플리케이션에 공통 예외 처리기를 등록한다."""
    application.add_exception_handler(
        ApplicationException,
        application_exception_handler,
    )
    application.add_exception_handler(Exception, unhandled_exception_handler)

