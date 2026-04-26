from __future__ import annotations
from typing import Optional

from datetime import datetime

from pydantic import Field

from app.schemas import ORMBaseSchema, TimestampSchema


class AdminRoleRead(ORMBaseSchema):
    """관리자 역할 응답 스키마."""

    id: int
    role_name: str
    role_description: Optional[str] = None
    created_at: Optional[datetime] = None


class AdminPermissionRead(ORMBaseSchema):
    """권한 정의 응답 스키마."""

    id: int
    permission_code: str
    permission_name: Optional[str] = None
    resource_type: Optional[str] = None
    action_type: Optional[str] = None
    created_at: Optional[datetime] = None


class AdminMenuRead(TimestampSchema):
    """관리자 메뉴 응답 스키마."""

    id: int
    parent_menu_id: Optional[int] = None
    menu_name: Optional[str] = None
    menu_path: Optional[str] = None
    sort_order: Optional[int] = None
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[int] = None


class AdminActionLogRead(ORMBaseSchema):
    """관리자 작업 로그 응답 스키마."""

    id: int
    admin_id: int
    action_type: Optional[str] = None
    target_table: Optional[str] = None
    target_id: Optional[int] = None
    action_data: Optional[dict] = None
    ip_address: Optional[str] = None
    created_at: Optional[datetime] = None


class AdminAccessLogRead(ORMBaseSchema):
    """관리자 접속 로그 응답 스키마."""

    id: int
    admin_id: Optional[int] = None
    login_result: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    accessed_at: Optional[datetime] = None


class AdminAccountBase(ORMBaseSchema):
    """관리자 계정 공통 입력 스키마."""

    admin_email: str = Field(..., max_length=255)
    password_hash: str = Field(...)
    admin_status: str = Field(..., max_length=20)
    last_login_at: Optional[datetime] = None


class AdminAccountCreate(AdminAccountBase):
    """관리자 계정 생성 요청 스키마."""

    created_by: Optional[int] = None


class AdminAccountUpdate(ORMBaseSchema):
    """관리자 계정 수정 요청 스키마."""

    admin_email: Optional[str] = Field(default=None, max_length=255)
    password_hash: Optional[str] = None
    admin_status: Optional[str] = Field(default=None, max_length=20)
    last_login_at: Optional[datetime] = None
    updated_by: Optional[int] = None


class AdminAccountRead(AdminAccountBase, TimestampSchema):
    """관리자 계정 상세 응답 스키마."""

    id: int
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[int] = None
    roles: list[AdminRoleRead] = Field(default_factory=list)
    action_logs: list[AdminActionLogRead] = Field(default_factory=list)
    access_logs: list[AdminAccessLogRead] = Field(default_factory=list)


class AdminRoleBase(ORMBaseSchema):
    """관리자 역할 공통 입력 스키마."""

    role_name: str = Field(..., max_length=100)
    role_description: Optional[str] = None


class AdminRoleCreate(AdminRoleBase):
    """관리자 역할 생성 요청 스키마."""

    pass


class AdminRoleUpdate(ORMBaseSchema):
    """관리자 역할 수정 요청 스키마."""

    role_name: Optional[str] = Field(default=None, max_length=100)
    role_description: Optional[str] = None


class AdminRoleReadWithPermissions(AdminRoleRead):
    """권한 목록을 포함한 관리자 역할 응답 스키마."""

    permissions: list[AdminPermissionRead] = Field(default_factory=list)


class AdminPermissionBase(ORMBaseSchema):
    """권한 정의 공통 입력 스키마."""

    permission_code: str = Field(..., max_length=100)
    permission_name: Optional[str] = Field(default=None, max_length=255)
    resource_type: Optional[str] = Field(default=None, max_length=50)
    action_type: Optional[str] = Field(default=None, max_length=50)


class AdminPermissionCreate(AdminPermissionBase):
    """권한 정의 생성 요청 스키마."""

    pass


class AdminPermissionUpdate(ORMBaseSchema):
    """권한 정의 수정 요청 스키마."""

    permission_code: Optional[str] = Field(default=None, max_length=100)
    permission_name: Optional[str] = Field(default=None, max_length=255)
    resource_type: Optional[str] = Field(default=None, max_length=50)
    action_type: Optional[str] = Field(default=None, max_length=50)


class AdminMenuBase(ORMBaseSchema):
    """관리자 메뉴 공통 입력 스키마."""

    parent_menu_id: Optional[int] = None
    menu_name: Optional[str] = Field(default=None, max_length=255)
    menu_path: Optional[str] = Field(default=None, max_length=255)
    sort_order: Optional[int] = None


class AdminMenuCreate(AdminMenuBase):
    """관리자 메뉴 생성 요청 스키마."""

    created_by: Optional[int] = None


class AdminMenuUpdate(ORMBaseSchema):
    """관리자 메뉴 수정 요청 스키마."""

    parent_menu_id: Optional[int] = None
    menu_name: Optional[str] = Field(default=None, max_length=255)
    menu_path: Optional[str] = Field(default=None, max_length=255)
    sort_order: Optional[int] = None
    updated_by: Optional[int] = None


class AdminActionLogBase(ORMBaseSchema):
    """관리자 작업 로그 공통 입력 스키마."""

    admin_id: int
    action_type: Optional[str] = Field(default=None, max_length=50)
    target_table: Optional[str] = Field(default=None, max_length=100)
    target_id: Optional[int] = None
    action_data: Optional[dict] = None
    ip_address: Optional[str] = Field(default=None, max_length=50)


class AdminActionLogCreate(AdminActionLogBase):
    """관리자 작업 로그 생성 요청 스키마."""

    pass


class AdminAccessLogBase(ORMBaseSchema):
    """관리자 접속 로그 공통 입력 스키마."""

    admin_id: Optional[int] = None
    login_result: Optional[str] = Field(default=None, max_length=20)
    ip_address: Optional[str] = Field(default=None, max_length=50)
    user_agent: Optional[str] = None


class AdminAccessLogCreate(AdminAccessLogBase):
    """관리자 접속 로그 생성 요청 스키마."""

    pass


__all__ = [
    "AdminAccountBase",
    "AdminAccountCreate",
    "AdminAccountRead",
    "AdminAccountUpdate",
    "AdminRoleBase",
    "AdminRoleCreate",
    "AdminRoleRead",
    "AdminRoleReadWithPermissions",
    "AdminRoleUpdate",
    "AdminPermissionBase",
    "AdminPermissionCreate",
    "AdminPermissionRead",
    "AdminPermissionUpdate",
    "AdminMenuBase",
    "AdminMenuCreate",
    "AdminMenuRead",
    "AdminMenuUpdate",
    "AdminActionLogBase",
    "AdminActionLogCreate",
    "AdminActionLogRead",
    "AdminAccessLogBase",
    "AdminAccessLogCreate",
    "AdminAccessLogRead",
]