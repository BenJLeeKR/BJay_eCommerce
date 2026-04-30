from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.core.config import settings


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


def _add_cors_headers(response: JSONResponse, request: Request) -> JSONResponse:
    """JSONResponse에 CORS 헤더를 추가한다.

    FastAPI의 CORSMiddleware는 예외 핸들러가 반환한 응답에 대해
    CORS 헤더를 추가하지 않는 경우가 있으므로, 예외 핸들러에서 직접 추가한다.
    """
    origin = request.headers.get("origin")
    if origin:
        allowed_origins = settings.BACKEND_CORS_ORIGINS
        if "*" in allowed_origins or origin in allowed_origins:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Allow-Methods"] = "DELETE, GET, HEAD, OPTIONS, PATCH, POST, PUT"
            response.headers["Access-Control-Allow-Headers"] = "content-type,authorization"
    return response


async def application_exception_handler(
    request: Request,
    exc: ApplicationException,
) -> JSONResponse:
    """커스텀 애플리케이션 예외를 표준 JSON 응답으로 변환한다."""
    response = JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.message,
            "error_type": exc.__class__.__name__,
        },
    )
    return _add_cors_headers(response, request)


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """처리되지 않은 예외를 공통 포맷으로 응답한다."""
    response = JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "서버 내부 오류가 발생했습니다.",
            "error_type": exc.__class__.__name__,
        },
    )
    return _add_cors_headers(response, request)


def register_exception_handlers(application: FastAPI) -> None:
    """FastAPI 애플리케이션에 공통 예외 처리기를 등록한다."""
    application.add_exception_handler(
        ApplicationException,
        application_exception_handler,
    )
    application.add_exception_handler(Exception, unhandled_exception_handler)

