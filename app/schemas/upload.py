"""
업로드(Upload) API 스키마.

Phase 2에서 Presigned URL 기반 이미지 업로드가 구현될 예정입니다.
현재는 프론트엔드와의 인터페이스 계약만 정의합니다.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import Field

from app.schemas import ORMBaseSchema


class PresignedUrlRequest(ORMBaseSchema):
    """Presigned URL 발급 요청.

    클라이언트가 업로드할 파일의 정보를 서버에 전달합니다.
    """

    file_name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="업로드할 파일명 (확장자 포함, 예: product_001.jpg)",
    )
    content_type: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="파일 MIME 타입 (예: image/jpeg, image/png)",
    )
    file_size: int = Field(
        ...,
        gt=0,
        le=10 * 1024 * 1024,  # 10MB
        description="파일 크기 (bytes, 최대 10MB)",
    )
    upload_category: str = Field(
        default="product",
        max_length=50,
        description="업로드 카테고리 (product, review, profile, banner 등)",
    )


class PresignedUrlResponse(ORMBaseSchema):
    """Presigned URL 발급 응답.

    클라이언트는 이 URL로 직접 파일을 업로드합니다.
    """

    upload_url: str = Field(..., description="파일 업로드를 위한 Presigned URL (PUT 요청)")
    file_url: str = Field(..., description="업로드 완료 후 파일에 접근할 수 있는 CDN/스토리지 URL")
    expires_at: datetime = Field(..., description="Presigned URL 만료 시간")


class FileUploadCompleteRequest(ORMBaseSchema):
    """업로드 완료 콜백 요청.

    클라이언트가 Presigned URL로 업로드를 완료한 후,
    서버에 업로드 완료를 알리고 파일 참조를 생성합니다.
    """

    file_url: str = Field(..., max_length=500, description="업로드된 파일의 URL")
    original_file_name: str = Field(..., max_length=255, description="원본 파일명")
    content_type: str = Field(..., max_length=100, description="파일 MIME 타입")
    file_size: int = Field(..., gt=0, description="파일 크기 (bytes)")
    upload_category: str = Field(..., max_length=50, description="업로드 카테고리")
    entity_type: Optional[str] = Field(
        default=None,
        max_length=50,
        description="연관 엔티티 타입 (product, review 등)",
    )
    entity_id: Optional[int] = Field(default=None, gt=0, description="연관 엔티티 ID")


class FileUploadRead(ORMBaseSchema):
    """업로드된 파일 정보 조회 응답."""

    id: int = Field(..., description="파일 ID")
    file_url: str = Field(..., description="파일 접근 URL")
    original_file_name: str = Field(..., description="원본 파일명")
    content_type: str = Field(..., description="파일 MIME 타입")
    file_size: int = Field(..., description="파일 크기 (bytes)")
    upload_category: str = Field(..., description="업로드 카테고리")
    entity_type: Optional[str] = Field(default=None, description="연관 엔티티 타입")
    entity_id: Optional[int] = Field(default=None, description="연관 엔티티 ID")
    created_at: datetime = Field(..., description="업로드 일시")
