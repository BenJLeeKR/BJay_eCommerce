from __future__ import annotations

from pydantic import Field

from app.schemas import ORMBaseSchema


class LoginRequest(ORMBaseSchema):
    """로그인 요청 스키마."""

    user_email: str = Field(..., max_length=255, description="회원 이메일")
    password: str = Field(..., min_length=1, description="비밀번호 (평문)")


class LoginResponse(ORMBaseSchema):
    """로그인 응답 스키마 (JWT 토큰).

    Note:
        ``refresh_token``은 Phase 2에서 도입 예정입니다.
        현재는 항상 ``None``을 반환합니다.
    """

    access_token: str = Field(..., description="JWT 액세스 토큰")
    refresh_token: str | None = Field(default=None, description="JWT 리프레시 토큰 (Phase 2 도입 예정)")
    token_type: str = Field(default="bearer", description="토큰 타입")
