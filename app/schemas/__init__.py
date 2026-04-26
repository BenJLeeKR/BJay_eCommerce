from __future__ import annotations
from typing import Optional

from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict

SchemaType = TypeVar("SchemaType")


class ORMBaseSchema(BaseModel):
    """ORM 객체 변환을 지원하는 공통 스키마 베이스 클래스."""

    model_config = ConfigDict(from_attributes=True)


class TimestampSchema(ORMBaseSchema):
    """생성/수정 시각 필드를 공통으로 제공한다."""

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class APIResponse(ORMBaseSchema, Generic[SchemaType]):
    """표준 API 응답 포맷을 제공한다."""

    success: bool = True
    message: str = "요청이 성공했습니다."
    data: Optional[SchemaType] = None


from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
)
from app.schemas.search import (
    SearchProductIndexRead,
    SearchProductIndexCreate,
    SearchProductIndexUpdate,
    SearchKeywordRead,
    SearchKeywordCreate,
    SearchKeywordUpdate,
    SearchAutocompleteRead,
    SearchAutocompleteCreate,
    SearchAutocompleteUpdate,
    SearchSynonymRead,
    SearchSynonymCreate,
    SearchSynonymUpdate,
)
from app.schemas.admin import (
    AdminAccountBase,
    AdminAccountCreate,
    AdminAccountRead,
    AdminAccountUpdate,
    AdminRoleBase,
    AdminRoleCreate,
    AdminRoleRead,
    AdminRoleReadWithPermissions,
    AdminRoleUpdate,
    AdminPermissionBase,
    AdminPermissionCreate,
    AdminPermissionRead,
    AdminPermissionUpdate,
    AdminMenuBase,
    AdminMenuCreate,
    AdminMenuRead,
    AdminMenuUpdate,
    AdminActionLogBase,
    AdminActionLogCreate,
    AdminActionLogRead,
    AdminAccessLogBase,
    AdminAccessLogCreate,
    AdminAccessLogRead,
)

__all__ = [
    "APIResponse",
    "ORMBaseSchema",
    "TimestampSchema",
    "SearchProductIndexRead",
    "SearchProductIndexCreate",
    "SearchProductIndexUpdate",
    "SearchKeywordRead",
    "SearchKeywordCreate",
    "SearchKeywordUpdate",
    "SearchAutocompleteRead",
    "SearchAutocompleteCreate",
    "SearchAutocompleteUpdate",
    "SearchSynonymRead",
    "SearchSynonymCreate",
    "SearchSynonymUpdate",
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
    "LoginRequest",
    "LoginResponse",
]
