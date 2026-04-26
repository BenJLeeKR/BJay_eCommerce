from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.config import settings
from app.database import Base


class Review(Base):
    """상품 리뷰 정보를 저장한다."""

    __tablename__ = "review"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(f"{settings.DB_SCHEMA}.product.id"),
        nullable=False,
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(f"{settings.DB_SCHEMA}.user_account.id"),
        nullable=False,
    )
    order_item_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(f"{settings.DB_SCHEMA}.order_item.id"),
        nullable=False,
    )
    review_title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    review_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    review_status: Mapped[str] = mapped_column(String(30), nullable=False)
    is_verified_purchase: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    like_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    comment_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    deleted_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)

    product: Mapped["Product"] = relationship(back_populates="reviews")
    user: Mapped["UserAccount"] = relationship(back_populates="reviews")
    order_item: Mapped["OrderItem"] = relationship(back_populates="review")
    ratings: Mapped[list["ReviewRating"]] = relationship(
        back_populates="review",
        cascade="all, delete-orphan",
    )
    images: Mapped[list["ReviewImage"]] = relationship(
        back_populates="review",
        cascade="all, delete-orphan",
    )
    likes: Mapped[list["ReviewLike"]] = relationship(
        back_populates="review",
        cascade="all, delete-orphan",
    )
    reports: Mapped[list["ReviewReport"]] = relationship(
        back_populates="review",
        cascade="all, delete-orphan",
    )
    comments: Mapped[list["ReviewComment"]] = relationship(
        back_populates="review",
        cascade="all, delete-orphan",
    )


class ReviewRating(Base):
    """리뷰 평점 정보를 저장한다."""

    __tablename__ = "review_rating"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    review_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(f"{settings.DB_SCHEMA}.review.id"),
        nullable=False,
    )
    rating_score: Mapped[int] = mapped_column(Integer, nullable=False)
    rating_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())

    review: Mapped["Review"] = relationship(back_populates="ratings")


class ReviewImage(Base):
    """리뷰 이미지를 저장한다."""

    __tablename__ = "review_image"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    review_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(f"{settings.DB_SCHEMA}.review.id"),
        nullable=False,
    )
    image_url: Mapped[str] = mapped_column(Text, nullable=False)
    sort_order: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())

    review: Mapped["Review"] = relationship(back_populates="images")


class ReviewLike(Base):
    """리뷰 좋아요 정보를 저장한다."""

    __tablename__ = "review_like"

    review_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(f"{settings.DB_SCHEMA}.review.id"),
        primary_key=True,
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(f"{settings.DB_SCHEMA}.user_account.id"),
        primary_key=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())

    review: Mapped["Review"] = relationship(back_populates="likes")
    user: Mapped["UserAccount"] = relationship(back_populates="review_likes")


class ReviewReport(Base):
    """리뷰 신고 정보를 저장한다."""

    __tablename__ = "review_report"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    review_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(f"{settings.DB_SCHEMA}.review.id"),
        nullable=False,
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(f"{settings.DB_SCHEMA}.user_account.id"),
        nullable=False,
    )
    report_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    report_status: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())

    review: Mapped["Review"] = relationship(back_populates="reports")
    user: Mapped["UserAccount"] = relationship(back_populates="review_reports")


class ReviewComment(Base):
    """리뷰 댓글 정보를 저장한다."""

    __tablename__ = "review_comment"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    review_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(f"{settings.DB_SCHEMA}.review.id"),
        nullable=False,
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(f"{settings.DB_SCHEMA}.user_account.id"),
        nullable=False,
    )
    comment_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())

    review: Mapped["Review"] = relationship(back_populates="comments")
    user: Mapped["UserAccount"] = relationship(back_populates="review_comments")


class ProductReviewSummary(Base):
    """상품별 리뷰 집계 정보를 저장한다."""

    __tablename__ = "product_review_summary"

    product_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(f"{settings.DB_SCHEMA}.product.id"),
        primary_key=True,
    )
    average_rating: Mapped[Optional[float]] = mapped_column(Numeric(3, 2), nullable=True)
    total_review_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    rating_1_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    rating_2_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    rating_3_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    rating_4_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    rating_5_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())

    product: Mapped["Product"] = relationship(back_populates="review_summary")