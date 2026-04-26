from __future__ import annotations
from typing import Optional

from datetime import datetime
from decimal import Decimal

from pydantic import Field

from app.schemas import ORMBaseSchema, TimestampSchema


class ReviewRatingRead(TimestampSchema):
    """리뷰 평점 응답 스키마."""

    id: int
    review_id: int
    rating_score: int
    rating_type: Optional[str] = None


class ReviewImageRead(TimestampSchema):
    """리뷰 이미지 응답 스키마."""

    id: int
    review_id: int
    image_url: str
    sort_order: Optional[int] = None


class ReviewLikeRead(TimestampSchema):
    """리뷰 좋아요 응답 스키마."""

    review_id: int
    user_id: int


class ReviewReportRead(TimestampSchema):
    """리뷰 신고 응답 스키마."""

    id: int
    review_id: int
    user_id: int
    report_reason: Optional[str] = None
    report_status: Optional[str] = None


class ReviewCommentRead(TimestampSchema):
    """리뷰 댓글 응답 스키마."""

    id: int
    review_id: int
    user_id: int
    comment_content: Optional[str] = None


class ProductReviewSummaryRead(TimestampSchema):
    """상품 리뷰 집계 응답 스키마."""

    product_id: int
    average_rating: Optional[Decimal] = None
    total_review_count: Optional[int] = None
    rating_1_count: int = 0
    rating_2_count: int = 0
    rating_3_count: int = 0
    rating_4_count: int = 0
    rating_5_count: int = 0


class ReviewBase(ORMBaseSchema):
    """리뷰 공통 입력 스키마."""

    product_id: int
    user_id: int
    order_item_id: int
    review_title: Optional[str] = Field(default=None, max_length=255)
    review_content: Optional[str] = None
    review_status: str = Field(..., max_length=30)
    is_verified_purchase: bool = True
    like_count: int = 0
    comment_count: int = 0


class ReviewCreate(ReviewBase):
    """리뷰 생성 요청 스키마."""

    created_by: Optional[int] = None


class ReviewUpdate(ORMBaseSchema):
    """리뷰 수정 요청 스키마."""

    review_title: Optional[str] = Field(default=None, max_length=255)
    review_content: Optional[str] = None
    review_status: Optional[str] = Field(default=None, max_length=30)
    is_verified_purchase: Optional[bool] = None
    like_count: Optional[int] = None
    comment_count: Optional[int] = None
    updated_by: Optional[int] = None


class ReviewRead(ReviewBase, TimestampSchema):
    """리뷰 상세 응답 스키마."""

    id: int
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[int] = None
    ratings: list[ReviewRatingRead] = Field(default_factory=list)
    images: list[ReviewImageRead] = Field(default_factory=list)
    likes: list[ReviewLikeRead] = Field(default_factory=list)
    reports: list[ReviewReportRead] = Field(default_factory=list)
    comments: list[ReviewCommentRead] = Field(default_factory=list)


__all__ = [
    "ReviewRatingRead",
    "ReviewImageRead",
    "ReviewLikeRead",
    "ReviewReportRead",
    "ReviewCommentRead",
    "ProductReviewSummaryRead",
    "ReviewBase",
    "ReviewCreate",
    "ReviewUpdate",
    "ReviewRead",
]