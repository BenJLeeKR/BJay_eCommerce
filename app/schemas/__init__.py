from __future__ import annotations
from typing import Optional

from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

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


class PagedResult(ORMBaseSchema, Generic[SchemaType]):
    """페이지네이션 응답을 위한 공통 래퍼.

    목록형 API에서 전체 아이템 개수(total_count)를 함께 반환하여
    프론트엔드가 페이지네이션 UI를 정확히 렌더링할 수 있도록 한다.

    사용 예:
        APIResponse[PagedResult[ProductRead]]
    """

    items: list[SchemaType] = Field(default_factory=list, description="현재 페이지의 아이템 목록")
    total_count: int = Field(default=0, ge=0, description="전체 아이템 개수")
    skip: int = Field(default=0, ge=0, description="건너뛴 레코드 수")
    limit: int = Field(default=20, ge=1, description="페이지당 최대 아이템 수")


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

from app.schemas.upload import (  # noqa: F401 — Phase 2 placeholder
    PresignedUrlRequest,
    PresignedUrlResponse,
    FileUploadCompleteRequest,
    FileUploadRead,
)

__all__ = [
    "APIResponse",
    "ORMBaseSchema",
    "TimestampSchema",
    "PagedResult",
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
    "PresignedUrlRequest",
    "PresignedUrlResponse",
    "FileUploadCompleteRequest",
    "FileUploadRead",
]
