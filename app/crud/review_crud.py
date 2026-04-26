from __future__ import annotations

from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.crud import CRUDBase
from app.models.review import (
    ProductReviewSummary,
    Review,
    ReviewComment,
    ReviewImage,
    ReviewLike,
    ReviewRating,
    ReviewReport,
)
from app.schemas.review import (
    ReviewCommentRead,
    ReviewCreate,
    ReviewImageRead,
    ReviewRatingRead,
    ReviewReportRead,
    ReviewUpdate,
)


class ReviewCRUD(CRUDBase[Review]):
    """리뷰 CRUD 연산을 담당한다."""

    def __init__(self) -> None:
        super().__init__(Review)

    def create(self, db: Session, obj_in: ReviewCreate) -> Review:
        """리뷰를 생성한다."""
        create_data = obj_in.model_dump(exclude_unset=True)
        db_obj = Review(**create_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get(self, db: Session, object_id: int) -> Optional[Review]:
        """리뷰를 ID로 조회한다."""
        return db.get(Review, object_id)

    def get_by_product_id(
        self,
        db: Session,
        product_id: int,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Review]:
        """상품의 리뷰 목록을 조회한다."""
        stmt = (
            select(Review)
            .where(Review.product_id == product_id)
            .where(Review.deleted_at.is_(None))
            .offset(skip)
            .limit(limit)
            .order_by(Review.created_at.desc())
        )
        return list(db.scalars(stmt).all())

    def get_by_user_id(
        self,
        db: Session,
        user_id: int,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Review]:
        """사용자의 리뷰 목록을 조회한다."""
        stmt = (
            select(Review)
            .where(Review.user_id == user_id)
            .where(Review.deleted_at.is_(None))
            .offset(skip)
            .limit(limit)
            .order_by(Review.created_at.desc())
        )
        return list(db.scalars(stmt).all())

    def get_by_status(
        self,
        db: Session,
        status: str,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Review]:
        """리뷰 목록을 상태별로 조회한다."""
        stmt = (
            select(Review)
            .where(Review.review_status == status)
            .where(Review.deleted_at.is_(None))
            .offset(skip)
            .limit(limit)
            .order_by(Review.id)
        )
        return list(db.scalars(stmt).all())

    def get_multi(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Review]:
        """리뷰 목록을 페이징하여 조회한다."""
        stmt = (
            select(Review)
            .where(Review.deleted_at.is_(None))
            .offset(skip)
            .limit(limit)
            .order_by(Review.id)
        )
        return list(db.scalars(stmt).all())

    def update(
        self,
        db: Session,
        db_obj: Review,
        obj_in: ReviewUpdate,
    ) -> Review:
        """리뷰를 수정한다."""
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, object_id: int) -> Optional[Review]:
        """리뷰를 소프트 삭제한다."""
        db_obj = db.get(Review, object_id)
        if db_obj is None:
            return None
        from datetime import datetime, timezone

        db_obj.deleted_at = datetime.now(timezone.utc)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj


class ReviewRatingCRUD(CRUDBase[ReviewRating]):
    """리뷰 평점 CRUD 연산을 담당한다."""

    def __init__(self) -> None:
        super().__init__(ReviewRating)

    def create(
        self,
        db: Session,
        obj_in: ReviewRatingRead,
    ) -> ReviewRating:
        """리뷰 평점을 생성한다."""
        create_data = obj_in.model_dump(exclude_unset=True)
        db_obj = ReviewRating(**create_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get(self, db: Session, object_id: int) -> Optional[ReviewRating]:
        """리뷰 평점을 ID로 조회한다."""
        return db.get(ReviewRating, object_id)

    def get_by_review_id(
        self,
        db: Session,
        review_id: int,
    ) -> list[ReviewRating]:
        """리뷰의 평점 목록을 조회한다."""
        stmt = (
            select(ReviewRating)
            .where(ReviewRating.review_id == review_id)
            .order_by(ReviewRating.id)
        )
        return list(db.scalars(stmt).all())

    def get_multi(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[ReviewRating]:
        """리뷰 평점 목록을 페이징하여 조회한다."""
        stmt = (
            select(ReviewRating)
            .offset(skip)
            .limit(limit)
            .order_by(ReviewRating.id)
        )
        return list(db.scalars(stmt).all())

    def remove(self, db: Session, object_id: int) -> Optional[ReviewRating]:
        """리뷰 평점을 삭제한다."""
        db_obj = db.get(ReviewRating, object_id)
        if db_obj is None:
            return None
        db.delete(db_obj)
        db.commit()
        return db_obj


class ReviewImageCRUD(CRUDBase[ReviewImage]):
    """리뷰 이미지 CRUD 연산을 담당한다."""

    def __init__(self) -> None:
        super().__init__(ReviewImage)

    def create(
        self,
        db: Session,
        obj_in: ReviewImageRead,
    ) -> ReviewImage:
        """리뷰 이미지를 생성한다."""
        create_data = obj_in.model_dump(exclude_unset=True)
        db_obj = ReviewImage(**create_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get(self, db: Session, object_id: int) -> Optional[ReviewImage]:
        """리뷰 이미지를 ID로 조회한다."""
        return db.get(ReviewImage, object_id)

    def get_by_review_id(
        self,
        db: Session,
        review_id: int,
    ) -> list[ReviewImage]:
        """리뷰의 이미지 목록을 조회한다."""
        stmt = (
            select(ReviewImage)
            .where(ReviewImage.review_id == review_id)
            .order_by(ReviewImage.sort_order)
        )
        return list(db.scalars(stmt).all())

    def get_multi(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[ReviewImage]:
        """리뷰 이미지 목록을 페이징하여 조회한다."""
        stmt = (
            select(ReviewImage)
            .offset(skip)
            .limit(limit)
            .order_by(ReviewImage.id)
        )
        return list(db.scalars(stmt).all())

    def remove(self, db: Session, object_id: int) -> Optional[ReviewImage]:
        """리뷰 이미지를 삭제한다."""
        db_obj = db.get(ReviewImage, object_id)
        if db_obj is None:
            return None
        db.delete(db_obj)
        db.commit()
        return db_obj


class ReviewLikeCRUD(CRUDBase[ReviewLike]):
    """리뷰 좋아요 CRUD 연산을 담당한다."""

    def __init__(self) -> None:
        super().__init__(ReviewLike)

    def create(
        self,
        db: Session,
        review_id: int,
        user_id: int,
    ) -> ReviewLike:
        """리뷰 좋아요를 생성한다."""
        db_obj = ReviewLike(review_id=review_id, user_id=user_id)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get(
        self,
        db: Session,
        review_id: int,
        user_id: int,
    ) -> Optional[ReviewLike]:
        """리뷰 좋아요를 조회한다."""
        return db.get(ReviewLike, (review_id, user_id))

    def get_by_review_id(
        self,
        db: Session,
        review_id: int,
    ) -> list[ReviewLike]:
        """리뷰의 좋아요 목록을 조회한다."""
        stmt = select(ReviewLike).where(ReviewLike.review_id == review_id)
        return list(db.scalars(stmt).all())

    def get_count_by_review_id(
        self,
        db: Session,
        review_id: int,
    ) -> int:
        """리뷰의 좋아요 개수를 조회한다."""
        stmt = (
            select(func.count())
            .select_from(ReviewLike)
            .where(ReviewLike.review_id == review_id)
        )
        result = db.execute(stmt).scalar()
        return result or 0

    def remove(
        self,
        db: Session,
        review_id: int,
        user_id: int,
    ) -> Optional[ReviewLike]:
        """리뷰 좋아요를 삭제한다."""
        db_obj = db.get(ReviewLike, (review_id, user_id))
        if db_obj is None:
            return None
        db.delete(db_obj)
        db.commit()
        return db_obj


class ReviewReportCRUD(CRUDBase[ReviewReport]):
    """리뷰 신고 CRUD 연산을 담당한다."""

    def __init__(self) -> None:
        super().__init__(ReviewReport)

    def create(
        self,
        db: Session,
        obj_in: ReviewReportRead,
    ) -> ReviewReport:
        """리뷰 신고를 생성한다."""
        create_data = obj_in.model_dump(exclude_unset=True)
        db_obj = ReviewReport(**create_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get(self, db: Session, object_id: int) -> Optional[ReviewReport]:
        """리뷰 신고를 ID로 조회한다."""
        return db.get(ReviewReport, object_id)

    def get_by_review_id(
        self,
        db: Session,
        review_id: int,
    ) -> list[ReviewReport]:
        """리뷰의 신고 목록을 조회한다."""
        stmt = (
            select(ReviewReport)
            .where(ReviewReport.review_id == review_id)
            .order_by(ReviewReport.id)
        )
        return list(db.scalars(stmt).all())

    def get_by_status(
        self,
        db: Session,
        status: str,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[ReviewReport]:
        """신고 목록을 상태별로 조회한다."""
        stmt = (
            select(ReviewReport)
            .where(ReviewReport.report_status == status)
            .offset(skip)
            .limit(limit)
            .order_by(ReviewReport.id)
        )
        return list(db.scalars(stmt).all())

    def get_multi(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[ReviewReport]:
        """리뷰 신고 목록을 페이징하여 조회한다."""
        stmt = (
            select(ReviewReport)
            .offset(skip)
            .limit(limit)
            .order_by(ReviewReport.id)
        )
        return list(db.scalars(stmt).all())

    def remove(self, db: Session, object_id: int) -> Optional[ReviewReport]:
        """리뷰 신고를 삭제한다."""
        db_obj = db.get(ReviewReport, object_id)
        if db_obj is None:
            return None
        db.delete(db_obj)
        db.commit()
        return db_obj


class ReviewCommentCRUD(CRUDBase[ReviewComment]):
    """리뷰 댓글 CRUD 연산을 담당한다."""

    def __init__(self) -> None:
        super().__init__(ReviewComment)

    def create(
        self,
        db: Session,
        obj_in: ReviewCommentRead,
    ) -> ReviewComment:
        """리뷰 댓글을 생성한다."""
        create_data = obj_in.model_dump(exclude_unset=True)
        db_obj = ReviewComment(**create_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get(self, db: Session, object_id: int) -> Optional[ReviewComment]:
        """리뷰 댓글을 ID로 조회한다."""
        return db.get(ReviewComment, object_id)

    def get_by_review_id(
        self,
        db: Session,
        review_id: int,
    ) -> list[ReviewComment]:
        """리뷰의 댓글 목록을 조회한다."""
        stmt = (
            select(ReviewComment)
            .where(ReviewComment.review_id == review_id)
            .order_by(ReviewComment.id)
        )
        return list(db.scalars(stmt).all())

    def get_multi(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[ReviewComment]:
        """리뷰 댓글 목록을 페이징하여 조회한다."""
        stmt = (
            select(ReviewComment)
            .offset(skip)
            .limit(limit)
            .order_by(ReviewComment.id)
        )
        return list(db.scalars(stmt).all())

    def remove(
        self,
        db: Session,
        object_id: int,
    ) -> Optional[ReviewComment]:
        """리뷰 댓글을 삭제한다."""
        db_obj = db.get(ReviewComment, object_id)
        if db_obj is None:
            return None
        db.delete(db_obj)
        db.commit()
        return db_obj


class ProductReviewSummaryCRUD(CRUDBase[ProductReviewSummary]):
    """상품 리뷰 집계 CRUD 연산을 담당한다."""

    def __init__(self) -> None:
        super().__init__(ProductReviewSummary)

    def create(
        self,
        db: Session,
        product_id: int,
    ) -> ProductReviewSummary:
        """상품 리뷰 집계를 생성한다."""
        db_obj = ProductReviewSummary(product_id=product_id)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get(
        self,
        db: Session,
        product_id: int,
    ) -> Optional[ProductReviewSummary]:
        """상품 리뷰 집계를 조회한다."""
        return db.get(ProductReviewSummary, product_id)

    def get_multi(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[ProductReviewSummary]:
        """상품 리뷰 집계 목록을 페이징하여 조회한다."""
        stmt = (
            select(ProductReviewSummary)
            .offset(skip)
            .limit(limit)
            .order_by(ProductReviewSummary.product_id)
        )
        return list(db.scalars(stmt).all())

    def update(
        self,
        db: Session,
        db_obj: ProductReviewSummary,
        obj_in: dict,
    ) -> ProductReviewSummary:
        """상품 리뷰 집계를 수정한다."""
        for field, value in obj_in.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(
        self,
        db: Session,
        product_id: int,
    ) -> Optional[ProductReviewSummary]:
        """상품 리뷰 집계를 삭제한다."""
        db_obj = db.get(ProductReviewSummary, product_id)
        if db_obj is None:
            return None
        db.delete(db_obj)
        db.commit()
        return db_obj


review_crud = ReviewCRUD()
review_rating_crud = ReviewRatingCRUD()
review_image_crud = ReviewImageCRUD()
review_like_crud = ReviewLikeCRUD()
review_report_crud = ReviewReportCRUD()
review_comment_crud = ReviewCommentCRUD()
product_review_summary_crud = ProductReviewSummaryCRUD()


__all__ = [
    "ReviewCRUD",
    "ReviewRatingCRUD",
    "ReviewImageCRUD",
    "ReviewLikeCRUD",
    "ReviewReportCRUD",
    "ReviewCommentCRUD",
    "ProductReviewSummaryCRUD",
    "review_crud",
    "review_rating_crud",
    "review_image_crud",
    "review_like_crud",
    "review_report_crud",
    "review_comment_crud",
    "product_review_summary_crud",
]
