from decimal import Decimal

from app.models.payment import Payment, PaymentTransaction, PaymentMethod, PaymentRefund, PaymentLog
from app.routers.payment import router
from app.schemas.payment import PaymentCreate, PaymentUpdate


def test_payment_table_and_indexes_are_defined() -> None:
    """결제 모델의 핵심 테이블 메타데이터가 정의되어야 한다."""
    index_names = {index.name for index in Payment.__table__.indexes}

    assert Payment.__tablename__ == "payment"
    assert "idx_payment_order_id" in index_names
    assert "idx_payment_status" in index_names
    assert Payment.__table__.c.order_id.nullable is False
    assert Payment.__table__.c.payment_amount.nullable is False
    assert Payment.__table__.c.payment_status.nullable is False


def test_payment_transaction_table_and_indexes_are_defined() -> None:
    """결제 트랜잭션 모델의 핵심 제약 조건과 인덱스가 정의되어야 한다."""
    index_names = {index.name for index in PaymentTransaction.__table__.indexes}

    assert PaymentTransaction.__tablename__ == "payment_transaction"
    assert "idx_payment_transaction_payment_id" in index_names
    assert "idx_payment_transaction_pg_transaction_id" in index_names
    assert PaymentTransaction.__table__.c.payment_id.nullable is False
    assert PaymentTransaction.__table__.c.transaction_type.nullable is False


def test_payment_method_table_and_indexes_are_defined() -> None:
    """결제 수단 모델의 핵심 제약 조건과 인덱스가 정의되어야 한다."""
    index_names = {index.name for index in PaymentMethod.__table__.indexes}

    assert PaymentMethod.__tablename__ == "payment_method"
    assert "idx_payment_method_user_id" in index_names
    assert "idx_payment_method_is_default" in index_names
    assert PaymentMethod.__table__.c.user_id.nullable is False
    assert PaymentMethod.__table__.c.payment_method_code.nullable is False


def test_payment_refund_table_and_indexes_are_defined() -> None:
    """결제 환불 모델의 핵심 제약 조건과 인덱스가 정의되어야 한다."""
    index_names = {index.name for index in PaymentRefund.__table__.indexes}

    assert PaymentRefund.__tablename__ == "payment_refund"
    assert "idx_payment_refund_payment_id" in index_names
    assert "idx_payment_refund_status" in index_names
    assert PaymentRefund.__table__.c.payment_id.nullable is False
    assert PaymentRefund.__table__.c.refund_amount.nullable is False


def test_payment_log_table_and_indexes_are_defined() -> None:
    """결제 로그 모델의 핵심 제약 조건과 인덱스가 정의되어야 한다."""
    index_names = {index.name for index in PaymentLog.__table__.indexes}

    assert PaymentLog.__tablename__ == "payment_log"
    assert "idx_payment_log_payment_id" in index_names
    assert PaymentLog.__table__.c.payment_id.nullable is True


def test_payment_create_schema_validates_required_fields() -> None:
    """결제 생성 스키마가 핵심 필드를 검증해야 한다."""
    payload = PaymentCreate(
        order_id=1001,
        payment_status="READY",
        payment_amount=Decimal("12900.00"),
        paid_amount=Decimal("0.00"),
        currency_code="KRW",
        payment_method_code="CARD",
        idempotency_key="unique_key_123",
        created_by=100,
    )

    assert payload.order_id == 1001
    assert payload.payment_amount == Decimal("12900.00")
    assert payload.payment_status == "READY"
    assert payload.idempotency_key == "unique_key_123"


def test_payment_update_schema_supports_partial_update() -> None:
    """결제 수정 스키마는 부분 업데이트를 지원해야 한다."""
    payload = PaymentUpdate(payment_status="SUCCESS", paid_amount=Decimal("12900.00"), updated_by=200)

    assert payload.model_dump(exclude_unset=True) == {
        "payment_status": "SUCCESS",
        "paid_amount": Decimal("12900.00"),
        "updated_by": 200,
    }


def test_payment_router_registers_expected_routes() -> None:
    """결제 라우터에 CRUD 엔드포인트가 등록되어야 한다."""
    route_map = {(tuple(sorted(route.methods)), route.path) for route in router.routes}

    assert (("GET",), "/payments") in route_map
    assert (("GET",), "/payments/{payment_id}") in route_map
    assert (("POST",), "/payments") in route_map
    assert (("PUT",), "/payments/{payment_id}") in route_map
    assert (("DELETE",), "/payments/{payment_id}") in route_map