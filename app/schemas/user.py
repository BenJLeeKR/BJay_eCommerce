from __future__ import annotations
from typing import Optional

from datetime import date, datetime

from pydantic import Field

from app.schemas import ORMBaseSchema, TimestampSchema


class UserProfileRead(TimestampSchema):
    """회원 프로필 응답 스키마."""

    id: int
    user_id: int
    user_name: Optional[str] = None
    phone_number: Optional[str] = None
    birth_date: Optional[date] = None
    gender_code: Optional[str] = None
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[int] = None


class UserProfileCreate(ORMBaseSchema):
    """회원 프로필 생성 요청 스키마.

    ``user_id``는 URL 경로에서 전달되므로 body에서 생략 가능.
    """

    user_id: Optional[int] = Field(default=None, description="회원 ID (URL 경로에서 전달)")
    user_name: Optional[str] = Field(default=None, max_length=100, description="회원 이름")
    phone_number: Optional[str] = Field(default=None, max_length=50, description="전화번호")
    birth_date: Optional[date] = Field(default=None, description="생년월일")
    gender_code: Optional[str] = Field(default=None, max_length=10, description="성별 코드")
    created_by: Optional[int] = Field(default=None, description="생성자 ID")


class UserProfileUpdate(ORMBaseSchema):
    """회원 프로필 수정 요청 스키마."""

    user_name: Optional[str] = Field(default=None, max_length=100, description="회원 이름")
    phone_number: Optional[str] = Field(default=None, max_length=50, description="전화번호")
    birth_date: Optional[date] = Field(default=None, description="생년월일")
    gender_code: Optional[str] = Field(default=None, max_length=10, description="성별 코드")
    updated_by: Optional[int] = Field(default=None, description="수정자 ID")


class UserAddressRead(TimestampSchema):
    """회원 배송지 응답 스키마."""

    id: int
    user_id: int
    address_name: Optional[str] = None
    recipient_name: Optional[str] = None
    recipient_phone: Optional[str] = None
    postal_code: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    is_default_address: Optional[bool] = None
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[int] = None


class UserAddressCreate(ORMBaseSchema):
    """회원 배송지 생성 요청 스키마.

    ``user_id``는 URL 경로에서 전달되므로 body에서 생략 가능.
    """

    user_id: Optional[int] = Field(default=None, description="회원 ID (URL 경로에서 전달)")
    address_name: Optional[str] = Field(default=None, max_length=100, description="배송지명")
    recipient_name: Optional[str] = Field(default=None, max_length=100, description="수령인")
    recipient_phone: Optional[str] = Field(default=None, max_length=50, description="수령인 전화번호")
    postal_code: Optional[str] = Field(default=None, max_length=20, description="우편번호")
    address_line1: Optional[str] = Field(default=None, max_length=255, description="기본 주소")
    address_line2: Optional[str] = Field(default=None, max_length=255, description="상세 주소")
    is_default_address: Optional[bool] = Field(default=False, description="기본 배송지 여부")
    created_by: Optional[int] = Field(default=None, description="생성자 ID")


class UserAddressUpdate(ORMBaseSchema):
    """회원 배송지 수정 요청 스키마."""

    address_name: Optional[str] = Field(default=None, max_length=100, description="배송지명")
    recipient_name: Optional[str] = Field(default=None, max_length=100, description="수령인")
    recipient_phone: Optional[str] = Field(default=None, max_length=50, description="수령인 전화번호")
    postal_code: Optional[str] = Field(default=None, max_length=20, description="우편번호")
    address_line1: Optional[str] = Field(default=None, max_length=255, description="기본 주소")
    address_line2: Optional[str] = Field(default=None, max_length=255, description="상세 주소")
    is_default_address: Optional[bool] = Field(default=None, description="기본 배송지 여부")
    updated_by: Optional[int] = Field(default=None, description="수정자 ID")


class UserAuthRead(TimestampSchema):
    """회원 인증 응답 스키마."""

    id: int
    user_id: int
    auth_provider: str
    provider_user_id: Optional[str] = None
    refresh_token: Optional[str] = None
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[int] = None


class UserLoginHistoryRead(ORMBaseSchema):
    """회원 로그인 이력 응답 스키마."""

    id: int
    user_id: int
    login_at: Optional[datetime] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    login_result: Optional[str] = None
    created_at: Optional[datetime] = None


class UserLoginHistoryCreate(ORMBaseSchema):
    """회원 로그인 이력 생성 요청 스키마."""

    user_id: int = Field(..., description="회원 ID")
    login_at: Optional[datetime] = Field(default=None, description="로그인 시각")
    ip_address: Optional[str] = Field(default=None, max_length=50, description="IP 주소")
    user_agent: Optional[str] = Field(default=None, description="User-Agent")
    login_result: Optional[str] = Field(default=None, max_length=20, description="로그인 결과 (SUCCESS/FAILURE)")


class UserRoleRead(ORMBaseSchema):
    """회원 역할 응답 스키마."""

    id: int
    role_name: str
    created_at: Optional[datetime] = None


class UserRoleCreate(ORMBaseSchema):
    """회원 역할 생성 요청 스키마."""

    role_name: str = Field(..., max_length=50, description="역할명")


class UserRoleUpdate(ORMBaseSchema):
    """회원 역할 수정 요청 스키마."""

    role_name: Optional[str] = Field(default=None, max_length=50, description="역할명")


class UserRoleMapCreate(ORMBaseSchema):
    """회원-역할 매핑 생성 요청 스키마."""

    user_id: int = Field(..., description="회원 ID")
    role_id: int = Field(..., description="역할 ID")


class UserAccountBase(ORMBaseSchema):
    """회원 계정 공통 입력 스키마."""

    user_email: str = Field(..., max_length=255)
    password_hash: Optional[str] = None
    user_status: str = Field(..., max_length=20)
    user_type: str = Field(..., max_length=20)
    is_email_verified: Optional[bool] = False
    last_login_at: Optional[datetime] = None


class UserAccountCreate(UserAccountBase):
    """회원 계정 생성 요청 스키마."""

    created_by: Optional[int] = None


class UserAccountUpdate(ORMBaseSchema):
    """회원 계정 수정 요청 스키마."""

    user_email: Optional[str] = Field(default=None, max_length=255)
    password_hash: Optional[str] = None
    user_status: Optional[str] = Field(default=None, max_length=20)
    user_type: Optional[str] = Field(default=None, max_length=20)
    is_email_verified: Optional[bool] = None
    last_login_at: Optional[datetime] = None
    updated_by: Optional[int] = None


class UserAccountRead(UserAccountBase, TimestampSchema):
    """회원 계정 상세 응답 스키마."""

    id: int
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[int] = None
    profile: Optional[UserProfileRead] = None
    addresses: list[UserAddressRead] = Field(default_factory=list)
    auth_methods: list[UserAuthRead] = Field(default_factory=list)
    login_histories: list[UserLoginHistoryRead] = Field(default_factory=list)
    roles: list[UserRoleRead] = Field(default_factory=list)


__all__ = [
    "UserAccountBase",
    "UserAccountCreate",
    "UserAccountRead",
    "UserAccountUpdate",
    "UserAddressCreate",
    "UserAddressRead",
    "UserAddressUpdate",
    "UserAuthRead",
    "UserLoginHistoryCreate",
    "UserLoginHistoryRead",
    "UserProfileCreate",
    "UserProfileRead",
    "UserProfileUpdate",
    "UserRoleCreate",
    "UserRoleRead",
    "UserRoleUpdate",
    "UserRoleMapCreate",
]
