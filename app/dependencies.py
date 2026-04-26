from __future__ import annotations
from typing import Any, Optional
from uuid import uuid4

from fastapi import Depends, HTTPException, Request, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.database import get_db_session

bearer_scheme = HTTPBearer(auto_error=False)

SESSION_ID_COOKIE_KEY = "session_id"
SESSION_ID_MAX_AGE = 60 * 60 * 24 * 30  # 30일


def get_db() -> Session:
    """라우터에서 사용할 공통 데이터베이스 세션 의존성."""
    yield from get_db_session()


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    _: Session = Depends(get_db),
) -> dict[str, Any]:
    """JWT 토큰을 검증하고 최소 사용자 컨텍스트를 반환한다."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="인증 정보가 필요합니다.",
        )

    payload = decode_access_token(credentials.credentials)
    subject = payload.get("sub")

    if subject is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 토큰입니다.",
        )

    return payload


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

