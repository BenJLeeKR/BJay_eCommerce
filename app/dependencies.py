from __future__ import annotations
import logging
from typing import Any, Optional
from uuid import uuid4

from fastapi import Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import decode_access_token
from app.database import get_db_session
from app.models.user import UserAccount

logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_PREFIX}/auth/token",
    auto_error=False,
)

SESSION_ID_COOKIE_KEY = "session_id"
SESSION_ID_MAX_AGE = 60 * 60 * 24 * 30  # 30일


def get_db() -> Session:
    """라우터에서 사용할 공통 데이터베이스 세션 의존성."""
    yield from get_db_session()


def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    _: Session = Depends(get_db),
) -> dict[str, Any]:
    """JWT 토큰을 검증하고 최소 사용자 컨텍스트를 반환한다."""
    if token is None:
        logger.warning(
            "[get_current_user] Authorization 헤더가 없음. "
            "Swagger Authorize가 제대로 설정되었는지 확인 필요."
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="인증 정보가 필요합니다.",
        )

    logger.debug(
        "[get_current_user] Authorization 헤더 수신: Bearer %s... (len=%d)",
        token[:20] if len(token) > 20 else token,
        len(token),
    )

    payload = decode_access_token(token)
    subject = payload.get("sub")

    if subject is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 토큰입니다.",
        )

    return payload


def get_current_user_entity(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> UserAccount:
    """JWT 토큰의 sub(user_id)로 실제 UserAccount 엔티티를 조회한다.

    프론트엔드가 user_id를 별도 관리하지 않고 JWT만으로
    현재 로그인된 사용자의 전체 정보가 필요할 때 사용한다.
    """
    if token is None:
        logger.warning(
            "[get_current_user_entity] Authorization 헤더가 없음. "
            "Swagger Authorize가 제대로 설정되었는지 확인 필요."
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="인증 정보가 필요합니다.",
        )

    logger.debug(
        "[get_current_user_entity] Authorization 헤더 수신: Bearer %s... (len=%d)",
        token[:20] if len(token) > 20 else token,
        len(token),
    )

    payload = decode_access_token(token)
    subject = payload.get("sub")

    if subject is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 토큰입니다.",
        )

    try:
        user_id = int(subject)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 토큰입니다.",
        )

    stmt = select(UserAccount).where(
        UserAccount.id == user_id,
        UserAccount.deleted_at.is_(None),
    )
    user = db.execute(stmt).scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="사용자를 찾을 수 없습니다.",
        )

    return user


def require_user_types(*allowed_types: str):
    """RBAC 의존성 팩토리. 지정된 user_type만 접근을 허용한다.

    사용 예:
        @router.get("/admin/dashboard/stats")
        def dashboard_stats(
            _: UserAccount = Depends(require_user_types("ADMIN")),
            db: Session = Depends(get_db),
        ):
            ...

    프론트엔드는 403 응답의 detail.code 필드로 권한 부족을 식별할 수 있다.
    """
    if not allowed_types:
        allowed_types = ("ADMIN",)

    class _RequireUserTypes:
        def __init__(self, current_user: UserAccount = Depends(get_current_user_entity)):
            if current_user.user_type not in allowed_types:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "code": "FORBIDDEN",
                        "message": "접근 권한이 없습니다.",
                        "required_user_types": list(allowed_types),
                        "user_type": current_user.user_type,
                    },
                )

    return _RequireUserTypes


def get_session_id(request: Request, response: Response) -> str:
    """요청 쿠키에서 session_id를 읽거나 없으면 새로 생성하여 쿠키에 설정한다.

    비회원 장바구니 식별을 위해 사용된다.
    생성된 session_id는 HttpOnly 쿠키로 응답에 설정되어 프론트엔드에서
    자동으로 관리된다.
    """
    session_id = request.cookies.get(SESSION_ID_COOKIE_KEY)
    if not session_id:
        session_id = str(uuid4())
        response.set_cookie(
            key=SESSION_ID_COOKIE_KEY,
            value=session_id,
            max_age=SESSION_ID_MAX_AGE,
            httponly=True,
            samesite="lax",
        )
    return session_id

