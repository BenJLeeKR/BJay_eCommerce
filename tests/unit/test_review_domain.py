from decimal import Decimal

from app.models.review import Review, ReviewRating, ReviewImage, ReviewLike, ReviewReport, ReviewComment, ProductReviewSummary
from app.routers.review import router
from app.schemas.review import ReviewCreate, ReviewUpdate


def test_review_table_and_columns_are_defined() -> None:
    """리뷰 모델의 핵심 테이블 메타데이터가 정의되어야 한다."""
    assert Review.__tablename__ == "review"
    assert Review.__table__.c.product_id.nullable is False
    assert Review.__table__.c.user_id.nullable is False
    assert Review.__table__.c.order_item_id.nullable is False
    assert Review.__table__.c.review_status.nullable is False
    assert Review.__table__.c.is_verified_purchase.nullable is False
    assert Review.__table__.c.like_count.nullable is False
    assert Review.__table__.c.comment_count.nullable is False


def test_review_rating_table_and_columns_are_defined() -> None:
    """리뷰 평점 모델의 핵심 컬럼이 정의되어야 한다."""
    assert ReviewRating.__tablename__ == "review_rating"
    assert ReviewRating.__table__.c.review_id.nullable is False
    assert ReviewRating.__table__.c.rating_score.nullable is False


def test_review_image_table_and_columns_are_defined() -> None:
    """리뷰 이미지 모델의 핵심 컬럼이 정의되어야 한다."""
    assert ReviewImage.__tablename__ == "review_image"
    assert ReviewImage.__table__.c.review_id.nullable is False
    assert ReviewImage.__table__.c.image_url.nullable is False


def test_review_like_table_and_primary_key() -> None:
    """리뷰 좋아요 모델의 복합 기본 키가 정의되어야 한다."""
    assert ReviewLike.__tablename__ == "review_like"
    primary_key_columns = {col.name for col in ReviewLike.__table__.primary_key.columns}
    assert primary_key_columns == {"review_id", "user_id"}


def test_review_report_table_and_columns_are_defined() -> None:
    """리뷰 신고 모델의 핵심 컬럼이 정의되어야 한다."""
    assert ReviewReport.__tablename__ == "review_report"
    assert ReviewReport.__table__.c.review_id.nullable is False
    assert ReviewReport.__table__.c.user_id.nullable is False


def test_review_comment_table_and_columns_are_defined() -> None:
    """리뷰 댓글 모델의 핵심 컬럼이 정의되어야 한다."""
    assert ReviewComment.__tablename__ == "review_comment"
    assert ReviewComment.__table__.c.review_id.nullable is False
    assert ReviewComment.__table__.c.user_id.nullable is False


def test_product_review_summary_table_and_columns_are_defined() -> None:
    """상품 리뷰 집계 모델의 핵심 컬럼이 정의되어야 한다."""
    assert ProductReviewSummary.__tablename__ == "product_review_summary"
    assert ProductReviewSummary.__table__.c.product_id.nullable is False
    assert ProductReviewSummary.__table__.c.average_rating.nullable is True
    assert ProductReviewSummary.__table__.c.total_review_count.nullable is True


def test_review_create_schema_validates_required_fields() -> None:
    """리뷰 생성 스키마가 핵심 필드를 검증해야 한다."""
    payload = ReviewCreate(
        product_id=1,
        user_id=2,
        order_item_id=3,
        review_title="좋은 상품",
        review_content="만족스러운 구매입니다.",
        review_status="ACTIVE",
        is_verified_purchase=True,
        like_count=0,
        comment_count=0,
        created_by=100,
    )

    assert payload.product_id == 1
    assert payload.user_id == 2
    assert payload.review_status == "ACTIVE"
    assert payload.is_verified_purchase is True


def test_review_update_schema_supports_partial_update() -> None:
    """리뷰 수정 스키마는 부분 업데이트를 지원해야 한다."""
    payload = ReviewUpdate(review_status="HIDDEN", updated_by=200)

    assert payload.model_dump(exclude_unset=True) == {
        "review_status": "HIDDEN",
        "updated_by": 200,
    }


def test_review_router_registers_expected_routes() -> None:
    """리뷰 라우터에 CRUD 엔드포인트가 등록되어야 한다."""
    route_map = {(tuple(sorted(route.methods)), route.path) for route in router.routes}

    assert (("GET",), "/reviews") in route_map
    assert (("GET",), "/reviews/{review_id}") in route_map
    assert (("POST",), "/reviews") in route_map
    assert (("PUT",), "/reviews/{review_id}") in route_map
    assert (("DELETE",), "/reviews/{review_id}") in route_map