import asyncio
import logging
import sys
from contextlib import asynccontextmanager
from typing import Any, Optional

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.database import Base, engine
from app.events.consumer import consume_loop
from app.events.producer import stop_producer
# AUTO-IMPORT-START
from app.routers import api_router
# AUTO-IMPORT-END
from fastapi import FastAPI, HTTPException, status

# 메인 이벤트 루프 참조 (sync 함수에서 async publish_event 호출 시 사용)
main_event_loop: Optional[asyncio.AbstractEventLoop] = None

# 로깅 구성: app.* 로거만 INFO 레벨로 출력 (aiokafka 등 외부 라이브러리 로그는 제외)
_log_format = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
_handler = logging.StreamHandler(sys.stdout)
_handler.setFormatter(logging.Formatter(_log_format, datefmt="%Y-%m-%d %H:%M:%S"))

# app 패키지 로거에만 핸들러 추가 (루트 로거는 건드리지 않음)
_app_logger = logging.getLogger("app")
_app_logger.setLevel(logging.INFO)
_app_logger.addHandler(_handler)
_app_logger.propagate = False

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    """애플리케이션 시작/종료 시 공통 리소스를 관리한다."""
    global main_event_loop
    main_event_loop = asyncio.get_running_loop()

    if settings.AUTO_CREATE_TABLES:
        Base.metadata.create_all(bind=engine)

    # Kafka Consumer 백그라운드 태스크 시작
    # (KAFKA_BOOTSTRAP_SERVERS가 설정된 경우에만)
    consumer_task: Optional[asyncio.Task[None]] = None
    if settings.KAFKA_BOOTSTRAP_SERVERS:
        consumer_task = asyncio.create_task(consume_loop())
        logger.info(
            "Kafka consumer background task started (bootstrap: %s)",
            settings.KAFKA_BOOTSTRAP_SERVERS,
        )
    else:
        logger.info("KAFKA_BOOTSTRAP_SERVERS not set, Kafka consumer disabled")

    yield

    # Consumer 종료
    if consumer_task is not None:
        consumer_task.cancel()
        try:
            await consumer_task
        except asyncio.CancelledError:
            pass

    await stop_producer()
    logger.info("Kafka producer stopped")


def create_application() -> FastAPI:
    """FastAPI 애플리케이션 인스턴스를 생성한다."""
    application = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.APP_VERSION,
        debug=settings.DEBUG,
        openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
        swagger_ui_parameters={"persistAuthorization": True},
    )

    register_exception_handlers(application)

    @application.get("/", include_in_schema=False)
    async def root_access_block():
        """루트 경로 접속 시 403 Forbidden 에러를 반환하여 차단한다."""
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access to root is not allowed."
        )

    # AUTO-ROUTER-START
    application.include_router(api_router, prefix=settings.API_V1_PREFIX)
    # AUTO-ROUTER-END

    _configure_openapi_security_scheme(application)

    return application


def _configure_openapi_security_scheme(application: FastAPI) -> None:
    """OpenAPI 스키마에 OAuth2 password flow 보안 스키마를 추가하여
    Swagger UI에 'Authorize' 버튼이 나타나고,
    user_email/password로 직접 로그인할 수 있도록 설정한다."""

    def custom_openapi() -> dict[str, Any]:
        if application.openapi_schema:
            return application.openapi_schema
        openapi_schema = get_openapi(
            title=settings.PROJECT_NAME,
            version=settings.APP_VERSION,
            routes=application.routes,
        )
        openapi_schema.setdefault("components", {})
        openapi_schema["components"]["securitySchemes"] = {
            "BearerAuth": {
                "type": "oauth2",
                "flows": {
                    "password": {
                        "tokenUrl": f"{settings.API_V1_PREFIX}/auth/token",
                    }
                },
                "description": "user_email과 password를 입력하여 로그인합니다. (user_email 필드에 이메일 입력)",
            }
        }
        openapi_schema["security"] = [{"BearerAuth": []}]
        application.openapi_schema = openapi_schema
        return application.openapi_schema

    application.openapi = custom_openapi


app = create_application()
