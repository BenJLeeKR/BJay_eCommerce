from __future__ import annotations
from typing import Optional

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.core.security import get_password_hash
from sqlalchemy import select, func
from sqlalchemy.orm import Session, selectinload

from app.dependencies import get_db, get_current_user_entity
from app.models.user import UserAccount, UserAddress, UserProfile, UserRole, UserRoleMap
from app.models.promotion import CouponIssue, Coupon
from app.schemas import APIResponse, PagedResult
from app.schemas.user import (
    UserAccountCreate,
    UserAccountRead,
    UserAccountUpdate,
    UserAddressCreate,
    UserAddressRead,
    UserAddressUpdate,
    UserProfileCreate,
    UserProfileRead,
    UserProfileUpdate,
    UserRoleCreate,
    UserRoleRead,
    UserRoleUpdate,
    UserCouponRead,
)

router = APIRouter(prefix="/users", tags=["Users (회원)"])
role_router = APIRouter(prefix="/roles", tags=["Roles (역할)"])


# ──────────────────────────────────────────────
# Helper functions
# ──────────────────────────────────────────────


def _user_query():
    return (
        select(UserAccount)
        .options(
            selectinload(UserAccount.profile),
            selectinload(UserAccount.addresses),
            selectinload(UserAccount.auth_methods),
            selectinload(UserAccount.login_histories),
            selectinload(UserAccount.roles),
        )
        .where(UserAccount.deleted_at.is_(None))
    )


def _get_user_or_404(db: Session, user_id: int) -> UserAccount:
    statement = _user_query().where(UserAccount.id == user_id)
    user = db.execute(statement).scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="회원을 찾을 수 없습니다.",
        )

    return user


def _get_profile_or_404(db: Session, user_id: int) -> UserProfile:
    """회원 프로필을 조회하고 없으면 404를 반환한다."""
    stmt = select(UserProfile).where(
        UserProfile.user_id == user_id,
        UserProfile.deleted_at.is_(None),
    )
    profile = db.scalar(stmt)
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="프로필을 찾을 수 없습니다.",
        )
    return profile


def _get_address_or_404(db: Session, address_id: int, user_id: int) -> UserAddress:
    """회원 배송지를 조회하고 없으면 404를 반환한다."""
    stmt = select(UserAddress).where(
        UserAddress.id == address_id,
        UserAddress.user_id == user_id,
        UserAddress.deleted_at.is_(None),
    )
    address = db.scalar(stmt)
    if address is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="배송지를 찾을 수 없습니다.",
        )
    return address


def _unset_default_address(db: Session, user_id: int, exclude_id: int | None = None) -> None:
    """회원의 기본 배송지를 해제한다."""
    stmt = select(UserAddress).where(
        UserAddress.user_id == user_id,
        UserAddress.is_default_address.is_(True),
        UserAddress.deleted_at.is_(None),
    )
    if exclude_id is not None:
        stmt = stmt.where(UserAddress.id != exclude_id)

    current_default = db.scalar(stmt)
    if current_default is not None:
        current_default.is_default_address = False
        db.add(current_default)


def _get_role_or_404(db: Session, role_id: int) -> UserRole:
    """역할을 조회하고 없으면 404를 반환한다."""
    role = db.get(UserRole, role_id)
    if role is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="역할을 찾을 수 없습니다.",
        )
    return role


# ──────────────────────────────────────────────
# UserAccount CRUD
# ──────────────────────────────────────────────


@router.get("/me", response_model=APIResponse[UserAccountRead], summary="내 회원 정보 조회")
def get_my_user(
    current_user: UserAccount = Depends(get_current_user_entity),
) -> APIResponse[UserAccountRead]:
    """JWT 토큰의 sub(user_id)를 기반으로 현재 로그인된 본인의 회원 정보를 조회한다.

    프론트엔드에서 user_id를 별도로 관리하지 않고
    JWT만으로 사용자 정보를 가져올 때 사용한다.
    """
    return APIResponse(data=current_user, message="내 회원 정보를 조회했습니다.")


@router.get("/me/coupons", response_model=APIResponse[list[UserCouponRead]], summary="내 보유 쿠폰 목록 조회")
def get_my_coupons(
    available_only: bool = Query(default=True, description="사용 가능한 쿠폰만 조회"),
    include_used: bool = Query(default=False, description="사용한 쿠폰 포함"),
    include_expired: bool = Query(default=False, description="만료된 쿠폰 포함"),
    current_user: UserAccount = Depends(get_current_user_entity),
    db: Session = Depends(get_db),
) -> APIResponse[list[UserCouponRead]]:
    """현재 로그인된 사용자가 보유한 쿠폰 목록을 조회한다."""
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    stmt = (
        select(CouponIssue)
        .options(
            selectinload(CouponIssue.coupon).selectinload(Coupon.promotion),
        )
        .where(CouponIssue.user_id == current_user.id)
        .order_by(CouponIssue.issued_at.desc())
    )

    issues = db.execute(stmt).scalars().unique().all()

    result: list[UserCouponRead] = []
    for issue in issues:
        coupon = issue.coupon
        promotion = coupon.promotion if coupon else None

        is_used = issue.is_used
        is_expired = issue.expire_at is not None and issue.expire_at <= now

        if available_only and (is_used or is_expired):
            continue
        if not include_used and is_used:
            continue
        if not include_expired and is_expired:
            continue

        result.append(
            UserCouponRead(
                coupon_issue_id=issue.id,
                coupon_id=coupon.id if coupon else 0,
                coupon_code=coupon.coupon_code if coupon else "",
                promotion_name=promotion.promotion_name if promotion else None,
                discount_type=promotion.discount_type if promotion else "",
                discount_value=promotion.discount_value if promotion else 0,
                max_discount_amount=promotion.max_discount_amount if promotion else None,
                issued_at=issue.issued_at,
                expire_at=issue.expire_at,
                is_used=is_used,
                is_expired=is_expired,
            )
        )

    return APIResponse(data=result, message="내 보유 쿠폰 목록을 조회했습니다.")


@router.get("", response_model=APIResponse[PagedResult[UserAccountRead]], summary="회원 목록 조회")
def list_users(
    skip: int = Query(default=0, ge=0, description="건너뛸 레코드 수"),
    limit: int = Query(default=20, ge=1, le=100, description="페이지당 최대 아이템 수"),
    user_status: Optional[str] = Query(default=None, max_length=20, description="회원 상태 필터"),
    user_type: Optional[str] = Query(default=None, max_length=20, description="회원 유형 필터"),
    db: Session = Depends(get_db),
) -> APIResponse[PagedResult[UserAccountRead]]:
    """회원 목록을 조건과 페이징 기준으로 조회한다."""
    base_query = _user_query()

    if user_status is not None:
        base_query = base_query.where(UserAccount.user_status == user_status)

    if user_type is not None:
        base_query = base_query.where(UserAccount.user_type == user_type)

    total_count = db.execute(select(func.count()).select_from(base_query.subquery())).scalar_one()
    users = db.execute(base_query.offset(skip).limit(limit)).scalars().unique().all()
    return APIResponse(
        data=PagedResult[UserAccountRead](
            items=users,
            total_count=total_count,
            skip=skip,
            limit=limit,
        ),
        message="회원 목록을 조회했습니다.",
    )


@router.get("/{user_id}", response_model=APIResponse[UserAccountRead], summary="회원 상세 조회")
def get_user(user_id: int, db: Session = Depends(get_db)) -> APIResponse[UserAccountRead]:
    """회원 상세 정보를 조회한다."""
    user = _get_user_or_404(db, user_id)
    return APIResponse(data=user, message="회원 상세 정보를 조회했습니다.")


@router.post(
    "",
    response_model=APIResponse[UserAccountRead],
    status_code=status.HTTP_201_CREATED,
    summary="회원 생성",
)
def create_user(payload: UserAccountCreate, db: Session = Depends(get_db)) -> APIResponse[UserAccountRead]:
    """회원 계정 기본 정보를 생성한다."""
    hashed_password = get_password_hash(payload.password_hash) if payload.password_hash else None
    user = UserAccount(
        user_email=payload.user_email,
        password_hash=hashed_password,
        user_status=payload.user_status,
        user_type=payload.user_type,
        is_email_verified=payload.is_email_verified,
        last_login_at=payload.last_login_at,
        created_by=payload.created_by,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    created_user = _get_user_or_404(db, user.id)
    return APIResponse(data=created_user, message="회원을 생성했습니다.")


@router.put("/{user_id}", response_model=APIResponse[UserAccountRead], summary="회원 수정")
def update_user(
    user_id: int,
    payload: UserAccountUpdate,
    db: Session = Depends(get_db),
) -> APIResponse[UserAccountRead]:
    """회원 계정 기본 정보를 수정한다."""
    user = _get_user_or_404(db, user_id)
    update_data = payload.model_dump(exclude_unset=True)

    for field_name, field_value in update_data.items():
        setattr(user, field_name, field_value)

    if update_data:
        user.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)

    db.add(user)
    db.commit()
    db.refresh(user)

    updated_user = _get_user_or_404(db, user_id)
    return APIResponse(data=updated_user, message="회원 정보를 수정했습니다.")


@router.delete("/{user_id}", response_model=APIResponse[dict[str, int]], summary="회원 삭제")
def delete_user(user_id: int, db: Session = Depends(get_db)) -> APIResponse[dict[str, int]]:
    """회원 계정을 소프트 삭제한다."""
    user = _get_user_or_404(db, user_id)
    user.deleted_at = datetime.now(timezone.utc).replace(tzinfo=None)
    db.add(user)
    db.commit()
    db.refresh(user)

    return APIResponse(data={"user_id": user_id}, message="회원을 삭제했습니다.")


# ──────────────────────────────────────────────
# UserProfile CRUD
# ──────────────────────────────────────────────


@router.get(
    "/{user_id}/profile",
    response_model=APIResponse[UserProfileRead],
    summary="프로필 조회",
)
def get_user_profile(
    user_id: int,
    db: Session = Depends(get_db),
) -> APIResponse[UserProfileRead]:
    """회원 프로필을 조회한다."""
    _get_user_or_404(db, user_id)  # user 존재 확인
    profile = _get_profile_or_404(db, user_id)
    return APIResponse(data=profile, message="프로필을 조회했습니다.")


@router.post(
    "/{user_id}/profile",
    response_model=APIResponse[UserProfileRead],
    status_code=status.HTTP_201_CREATED,
    summary="프로필 생성",
)
def create_user_profile(
    user_id: int,
    payload: UserProfileCreate,
    db: Session = Depends(get_db),
) -> APIResponse[UserProfileRead]:
    """회원 프로필을 생성한다. 이미 프로필이 존재하면 409 에러를 반환한다."""
    _get_user_or_404(db, user_id)  # user 존재 확인

    # 중복 프로필 체크
    existing = select(UserProfile).where(
        UserProfile.user_id == user_id,
        UserProfile.deleted_at.is_(None),
    )
    if db.scalar(existing) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="이미 프로필이 존재합니다.",
        )

    profile = UserProfile(
        user_id=user_id,
        user_name=payload.user_name,
        phone_number=payload.phone_number,
        birth_date=payload.birth_date,
        gender_code=payload.gender_code,
        created_by=payload.created_by,
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)

    return APIResponse(data=profile, message="프로필을 생성했습니다.")


@router.put(
    "/{user_id}/profile",
    response_model=APIResponse[UserProfileRead],
    summary="프로필 수정",
)
def update_user_profile(
    user_id: int,
    payload: UserProfileUpdate,
    db: Session = Depends(get_db),
) -> APIResponse[UserProfileRead]:
    """회원 프로필을 수정한다."""
    _get_user_or_404(db, user_id)  # user 존재 확인
    profile = _get_profile_or_404(db, user_id)

    update_data = payload.model_dump(exclude_unset=True)
    for field_name, field_value in update_data.items():
        setattr(profile, field_name, field_value)

    if update_data:
        profile.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)

    db.add(profile)
    db.commit()
    db.refresh(profile)

    return APIResponse(data=profile, message="프로필을 수정했습니다.")


@router.delete(
    "/{user_id}/profile",
    response_model=APIResponse[dict[str, int]],
    summary="프로필 삭제",
)
def delete_user_profile(
    user_id: int,
    db: Session = Depends(get_db),
) -> APIResponse[dict[str, int]]:
    """회원 프로필을 소프트 삭제한다."""
    _get_user_or_404(db, user_id)  # user 존재 확인
    profile = _get_profile_or_404(db, user_id)

    profile.deleted_at = datetime.now(timezone.utc).replace(tzinfo=None)
    db.add(profile)
    db.commit()

    return APIResponse(data={"user_id": user_id}, message="프로필을 삭제했습니다.")


# ──────────────────────────────────────────────
# UserAddress CRUD
# ──────────────────────────────────────────────


@router.get(
    "/{user_id}/addresses",
    response_model=APIResponse[list[UserAddressRead]],
    summary="배송지 목록 조회",
)
def list_user_addresses(
    user_id: int,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> APIResponse[list[UserAddressRead]]:
    """회원의 배송지 목록을 조회한다."""
    _get_user_or_404(db, user_id)  # user 존재 확인

    stmt = (
        select(UserAddress)
        .where(UserAddress.user_id == user_id)
        .where(UserAddress.deleted_at.is_(None))
        .offset(skip)
        .limit(limit)
        .order_by(UserAddress.is_default_address.desc(), UserAddress.id)
    )
    addresses = list(db.scalars(stmt).all())
    return APIResponse(data=addresses, message="배송지 목록을 조회했습니다.")


@router.get(
    "/{user_id}/addresses/{address_id}",
    response_model=APIResponse[UserAddressRead],
    summary="배송지 상세 조회",
)
def get_user_address(
    user_id: int,
    address_id: int,
    db: Session = Depends(get_db),
) -> APIResponse[UserAddressRead]:
    """회원 배송지 상세 정보를 조회한다."""
    _get_user_or_404(db, user_id)  # user 존재 확인
    address = _get_address_or_404(db, address_id, user_id)
    return APIResponse(data=address, message="배송지 정보를 조회했습니다.")


@router.post(
    "/{user_id}/addresses",
    response_model=APIResponse[UserAddressRead],
    status_code=status.HTTP_201_CREATED,
    summary="배송지 생성",
)
def create_user_address(
    user_id: int,
    payload: UserAddressCreate,
    db: Session = Depends(get_db),
) -> APIResponse[UserAddressRead]:
    """회원 배송지를 생성한다."""
    _get_user_or_404(db, user_id)  # user 존재 확인

    # 기본 배송지 처리
    if payload.is_default_address:
        _unset_default_address(db, user_id)

    address = UserAddress(
        user_id=user_id,
        address_name=payload.address_name,
        recipient_name=payload.recipient_name,
        recipient_phone=payload.recipient_phone,
        postal_code=payload.postal_code,
        address_line1=payload.address_line1,
        address_line2=payload.address_line2,
        is_default_address=payload.is_default_address,
        created_by=payload.created_by,
    )
    db.add(address)
    db.commit()
    db.refresh(address)

    return APIResponse(data=address, message="배송지를 생성했습니다.")


@router.put(
    "/{user_id}/addresses/{address_id}",
    response_model=APIResponse[UserAddressRead],
    summary="배송지 수정",
)
def update_user_address(
    user_id: int,
    address_id: int,
    payload: UserAddressUpdate,
    db: Session = Depends(get_db),
) -> APIResponse[UserAddressRead]:
    """회원 배송지 정보를 수정한다."""
    _get_user_or_404(db, user_id)  # user 존재 확인
    address = _get_address_or_404(db, address_id, user_id)

    # 기본 배송지 변경 처리
    if payload.is_default_address is True:
        _unset_default_address(db, user_id, exclude_id=address_id)

    update_data = payload.model_dump(exclude_unset=True)
    for field_name, field_value in update_data.items():
        setattr(address, field_name, field_value)

    if update_data:
        address.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)

    db.add(address)
    db.commit()
    db.refresh(address)

    return APIResponse(data=address, message="배송지를 수정했습니다.")


@router.delete(
    "/{user_id}/addresses/{address_id}",
    response_model=APIResponse[dict[str, int]],
    summary="배송지 삭제",
)
def delete_user_address(
    user_id: int,
    address_id: int,
    db: Session = Depends(get_db),
) -> APIResponse[dict[str, int]]:
    """회원 배송지를 소프트 삭제한다."""
    _get_user_or_404(db, user_id)  # user 존재 확인
    address = _get_address_or_404(db, address_id, user_id)

    address.deleted_at = datetime.now(timezone.utc).replace(tzinfo=None)
    db.add(address)
    db.commit()

    return APIResponse(data={"address_id": address_id}, message="배송지를 삭제했습니다.")


# ──────────────────────────────────────────────
# UserRole CRUD
# ──────────────────────────────────────────────


@role_router.get("", response_model=APIResponse[list[UserRoleRead]], summary="역할 목록 조회")
def list_roles(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> APIResponse[list[UserRoleRead]]:
    """역할 목록을 조회한다."""
    stmt = select(UserRole).offset(skip).limit(limit).order_by(UserRole.id)
    roles = list(db.scalars(stmt).all())
    return APIResponse(data=roles, message="역할 목록을 조회했습니다.")


@role_router.get(
    "/{role_id}",
    response_model=APIResponse[UserRoleRead],
    summary="역할 상세 조회",
)
def get_role(
    role_id: int,
    db: Session = Depends(get_db),
) -> APIResponse[UserRoleRead]:
    """역할 상세 정보를 조회한다."""
    role = _get_role_or_404(db, role_id)
    return APIResponse(data=role, message="역할 정보를 조회했습니다.")


@role_router.post(
    "",
    response_model=APIResponse[UserRoleRead],
    status_code=status.HTTP_201_CREATED,
    summary="역할 생성",
)
def create_role(
    payload: UserRoleCreate,
    db: Session = Depends(get_db),
) -> APIResponse[UserRoleRead]:
    """새로운 역할을 생성한다."""
    role = UserRole(role_name=payload.role_name)
    db.add(role)
    db.commit()
    db.refresh(role)
    return APIResponse(data=role, message="역할을 생성했습니다.")


@role_router.put(
    "/{role_id}",
    response_model=APIResponse[UserRoleRead],
    summary="역할 수정",
)
def update_role(
    role_id: int,
    payload: UserRoleUpdate,
    db: Session = Depends(get_db),
) -> APIResponse[UserRoleRead]:
    """역할 정보를 수정한다."""
    role = _get_role_or_404(db, role_id)

    update_data = payload.model_dump(exclude_unset=True)
    for field_name, field_value in update_data.items():
        setattr(role, field_name, field_value)

    db.add(role)
    db.commit()
    db.refresh(role)
    return APIResponse(data=role, message="역할을 수정했습니다.")


@role_router.delete(
    "/{role_id}",
    response_model=APIResponse[dict[str, int]],
    summary="역할 삭제",
)
def delete_role(
    role_id: int,
    db: Session = Depends(get_db),
) -> APIResponse[dict[str, int]]:
    """역할을 삭제한다."""
    role = _get_role_or_404(db, role_id)
    db.delete(role)
    db.commit()
    return APIResponse(data={"role_id": role_id}, message="역할을 삭제했습니다.")


# ──────────────────────────────────────────────
# User-Role Assignment (UserRoleMap)
# ──────────────────────────────────────────────


@router.post(
    "/{user_id}/roles",
    response_model=APIResponse[dict[str, int]],
    summary="사용자 역할 할당",
)
def assign_role_to_user(
    user_id: int,
    payload: dict[str, int],
    db: Session = Depends(get_db),
) -> APIResponse[dict[str, int]]:
    """사용자에게 역할을 할당한다."""
    _get_user_or_404(db, user_id)  # user 존재 확인

    role_id = payload.get("role_id")
    if role_id is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="role_id가 필요합니다.",
        )

    _get_role_or_404(db, role_id)  # role 존재 확인

    # 중복 할당 체크
    existing = db.get(UserRoleMap, (user_id, role_id))
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="이미 할당된 역할입니다.",
        )

    mapping = UserRoleMap(user_id=user_id, role_id=role_id)
    db.add(mapping)
    db.commit()

    return APIResponse(
        data={"user_id": user_id, "role_id": role_id},
        message="역할을 할당했습니다.",
    )


@router.delete(
    "/{user_id}/roles/{role_id}",
    response_model=APIResponse[dict[str, int]],
    summary="사용자 역할 해제",
)
def remove_role_from_user(
    user_id: int,
    role_id: int,
    db: Session = Depends(get_db),
) -> APIResponse[dict[str, int]]:
    """사용자의 역할을 해제한다."""
    _get_user_or_404(db, user_id)  # user 존재 확인

    mapping = db.get(UserRoleMap, (user_id, role_id))
    if mapping is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="할당된 역할을 찾을 수 없습니다.",
        )

    db.delete(mapping)
    db.commit()

    return APIResponse(
        data={"user_id": user_id, "role_id": role_id},
        message="역할을 해제했습니다.",
    )


__all__ = ["router", "role_router"]
