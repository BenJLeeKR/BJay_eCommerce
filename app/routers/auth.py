from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import create_access_token, verify_password
from app.crud import cart_crud
from app.dependencies import get_db, get_session_id
from app.models.user import UserAccount, UserLoginHistory
from app.schemas import APIResponse
from app.schemas.auth import LoginRequest, LoginResponse

router = APIRouter(prefix="/auth", tags=["Auth (로그인)"])


def _record_login_history(
    db: Session,
    user_id: int | None,
    ip_address: str | None,
    user_agent: str | None,
    login_result: str,
) -> None:
    """로그인 이력을 기록한다."""
    login_history = UserLoginHistory(
        user_id=user_id,
        ip_address=ip_address,
        user_agent=user_agent,
        login_result=login_result,
        login_at=datetime.now(timezone.utc).replace(tzinfo=None),
    )
    db.add(login_history)
    db.commit()


@router.post(
    "/login",
    response_model=APIResponse[LoginResponse],
    summary="로그인",
)
def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> APIResponse[LoginResponse]:
    """이메일과 비밀번호로 로그인하여 JWT 액세스 토큰을 발급한다.

    로그인 성공 시 session_id 기반 비회원 장바구니를
    회원 장바구니로 자동 병합한다.
    """
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    statement = select(UserAccount).where(
        UserAccount.user_email == payload.user_email,
        UserAccount.deleted_at.is_(None),
    )
    user = db.execute(statement).scalar_one_or_none()

    if user is None or user.password_hash is None:
        _record_login_history(
            db=db,
            user_id=user.id if user else None,
            ip_address=ip_address,
            user_agent=user_agent,
            login_result="FAILURE",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이메일 또는 비밀번호가 올바르지 않습니다.",
        )

    if not verify_password(payload.password, user.password_hash):
        _record_login_history(
            db=db,
            user_id=user.id,
            ip_address=ip_address,
            user_agent=user_agent,
            login_result="FAILURE",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이메일 또는 비밀번호가 올바르지 않습니다.",
        )

    access_token = create_access_token(subject=str(user.id))

    _record_login_history(
        db=db,
        user_id=user.id,
        ip_address=ip_address,
        user_agent=user_agent,
        login_result="SUCCESS",
    )

    # ── 비회원 장바구니 → 회원 장바구니 병합 ──
    session_id = get_session_id(request, response)
    cart_crud.merge_guest_cart(db, user_id=user.id, session_id=session_id)

    return APIResponse(
        data=LoginResponse(access_token=access_token, token_type="bearer"),
        message="로그인에 성공했습니다.",
    )


@router.post(
    "/token",
    summary="Swagger OAuth2 토큰 발급 (Authorize 버튼 전용)",
)
def token_login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    request: Request = None,  # type: ignore[assignment]
    db: Session = Depends(get_db),
) -> dict[str, str]:
    """Swagger UI의 Authorize 버튼에서 OAuth2 password flow로 호출하는
    토큰 발급 엔드포인트. `username` 필드에 `user_email`을 입력한다."""
    ip_address = request.client.host if request and request.client else None
    user_agent = request.headers.get("user-agent") if request else None

    statement = select(UserAccount).where(
        UserAccount.user_email == form_data.username,
        UserAccount.deleted_at.is_(None),
    )
    user = db.execute(statement).scalar_one_or_none()

    if user is None or user.password_hash is None:
        _record_login_history(
            db=db,
            user_id=user.id if user else None,
            ip_address=ip_address,
            user_agent=user_agent,
            login_result="FAILURE",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이메일 또는 비밀번호가 올바르지 않습니다.",
        )

    if not verify_password(form_data.password, user.password_hash):
        _record_login_history(
            db=db,
            user_id=user.id,
            ip_address=ip_address,
            user_agent=user_agent,
            login_result="FAILURE",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이메일 또는 비밀번호가 올바르지 않습니다.",
        )

    access_token = create_access_token(subject=str(user.id))

    _record_login_history(
        db=db,
        user_id=user.id,
        ip_address=ip_address,
        user_agent=user_agent,
        login_result="SUCCESS",
    )

    return {"access_token": access_token, "token_type": "bearer"}
