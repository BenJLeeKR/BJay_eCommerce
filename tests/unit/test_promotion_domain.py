from datetime import datetime, timezone
from decimal import Decimal

from app.models.promotion import Promotion, Coupon, CouponIssue, CouponUsage, PromotionCondition, PromotionTarget
from app.routers.promotion import router
from app.schemas.promotion import PromotionCreate, PromotionUpdate


def test_promotion_table_and_indexes_are_defined() -> None:
    """프로모션 모델의 핵심 테이블 메타데이터가 정의되어야 한다."""
    index_names = {index.name for index in Promotion.__table__.indexes}

    assert Promotion.__tablename__ == "promotion"
    assert Promotion.__table__.c.promotion_name.nullable is False
    assert Promotion.__table__.c.promotion_type.nullable is False
    assert Promotion.__table__.c.discount_type.nullable is False
    assert Promotion.__table__.c.discount_value.nullable is False
    assert Promotion.__table__.c.start_at.nullable is False
    assert Promotion.__table__.c.end_at.nullable is False


def test_coupon_table_and_indexes_are_defined() -> None:
    """쿠폰 모델의 핵심 제약 조건과 인덱스가 정의되어야 한다."""
    index_names = {index.name for index in Coupon.__table__.indexes}

    assert Coupon.__tablename__ == "coupon"
    assert "idx_coupon_promotion_id" in index_names
    assert Coupon.__table__.c.coupon_code.unique is True
    assert Coupon.__table__.c.issued_quantity.nullable is False
    assert Coupon.__table__.c.per_user_limit.nullable is False


def test_coupon_issue_table_and_indexes_are_defined() -> None:
    """쿠폰 발급 모델의 핵심 인덱스가 정의되어야 한다."""
    index_names = {index.name for index in CouponIssue.__table__.indexes}

    assert CouponIssue.__tablename__ == "coupon_issue"
    assert "idx_coupon_issue_coupon_id" in index_names
    assert "idx_coupon_issue_user_id" in index_names
    assert CouponIssue.__table__.c.coupon_id.nullable is False
    assert CouponIssue.__table__.c.user_id.nullable is False
    assert CouponIssue.__table__.c.is_used.nullable is False


def test_coupon_usage_table_and_indexes_are_defined() -> None:
    """쿠폰 사용 모델의 핵심 인덱스가 정의되어야 한다."""
    index_names = {index.name for index in CouponUsage.__table__.indexes}

    assert CouponUsage.__tablename__ == "coupon_usage"
    assert "idx_coupon_usage_coupon_issue_id" in index_names
    assert "idx_coupon_usage_order_id" in index_names
    assert CouponUsage.__table__.c.coupon_issue_id.nullable is False
    assert CouponUsage.__table__.c.order_id.nullable is False
    assert CouponUsage.__table__.c.discount_amount.nullable is False


def test_promotion_create_schema_validates_required_fields() -> None:
    """프로모션 생성 스키마가 핵심 필드를 검증해야 한다."""
    payload = PromotionCreate(
        promotion_name="신규 가입 할인",
        promotion_type="COUPON",
        discount_type="RATE",
        discount_value=Decimal("10.00"),
        max_discount_amount=Decimal("5000.00"),
        start_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        end_at=datetime(2026, 12, 31, tzinfo=timezone.utc),
        is_active=True,
        priority=1,
        created_by=100,
    )

    assert payload.promotion_name == "신규 가입 할인"
    assert payload.promotion_type == "COUPON"
    assert payload.discount_type == "RATE"
    assert payload.discount_value == Decimal("10.00")
    assert payload.max_discount_amount == Decimal("5000.00")
    assert payload.is_active is True
    assert payload.priority == 1


def test_promotion_update_schema_supports_partial_update() -> None:
    """프로모션 수정 스키마는 부분 업데이트를 지원해야 한다."""
    payload = PromotionUpdate(is_active=False, updated_by=200)

    assert payload.model_dump(exclude_unset=True) == {
        "is_active": False,
        "updated_by": 200,
    }


def test_promotion_router_registers_expected_routes() -> None:
    """프로모션 라우터에 CRUD 엔드포인트가 등록되어야 한다."""
    route_map = {(tuple(sorted(route.methods)), route.path) for route in router.routes}

    assert (("GET",), "/promotions") in route_map
    assert (("GET",), "/promotions/{promotion_id}") in route_map
    assert (("POST",), "/promotions") in route_map
    assert (("PUT",), "/promotions/{promotion_id}") in route_map
    assert (("DELETE",), "/promotions/{promotion_id}") in route_map


def test_promotion_condition_table_defined() -> None:
    """프로모션 조건 테이블이 정의되어야 한다."""
    assert PromotionCondition.__tablename__ == "promotion_condition"
    assert PromotionCondition.__table__.c.promotion_id.nullable is False
    assert PromotionCondition.__table__.c.condition_type.nullable is False


def test_promotion_target_table_defined() -> None:
    """프로모션 대상 테이블이 정의되어야 한다."""
    assert PromotionTarget.__tablename__ == "promotion_target"
    assert PromotionTarget.__table__.c.promotion_id.nullable is False
    assert PromotionTarget.__table__.c.target_type.nullable is False