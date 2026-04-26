from __future__ import annotations
from typing import Optional

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.dependencies import get_db
from app.models.payment import Payment, PaymentTransaction, PaymentRefund, PaymentLog
from app.schemas import APIResponse
from app.schemas.payment import PaymentCreate, PaymentRead, PaymentUpdate

router = APIRouter(prefix="/payments", tags=["Payments (결제)"])


def _payment_query():
    return (
        select(Payment)
        .options(
            selectinload(Payment.transactions),
            selectinload(Payment.refunds),
            selectinload(Payment.logs),
        )
        .where(Payment.deleted_at.is_(None))
    )


def _get_payment_or_404(db: Session, payment_id: int) -> Payment:
    statement = _payment_query().where(Payment.id == payment_id)
    payment = db.execute(statement).scalar_one_or_none()

    if payment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="결제를 찾을 수 없습니다.",
        )

    return payment


@router.get("", response_model=APIResponse[list[PaymentRead]], summary="결제 목록 조회")
def list_payments(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    payment_status: Optional[str] = Query(default=None, max_length=30),
    order_id: Optional[int] = Query(default=None, gt=0),
    db: Session = Depends(get_db),
) -> APIResponse[list[PaymentRead]]:
    """결제 목록을 상태, 주문 ID, 페이징 조건으로 조회한다."""
    statement = _payment_query().offset(skip).limit(limit)

    if payment_status is not None:
        statement = statement.where(Payment.payment_status == payment_status)
    if order_id is not None:
        statement = statement.where(Payment.order_id == order_id)

    payments = db.execute(statement).scalars().unique().all()
    return APIResponse(data=payments, message="결제 목록을 조회했습니다.")


@router.get("/{payment_id}", response_model=APIResponse[PaymentRead], summary="결제 상세 조회")
def get_payment(payment_id: int, db: Session = Depends(get_db)) -> APIResponse[PaymentRead]:
    """결제 상세 정보를 조회한다."""
    payment = _get_payment_or_404(db, payment_id)
    return APIResponse(data=payment, message="결제 상세 정보를 조회했습니다.")


@router.post(
    "",
    response_model=APIResponse[PaymentRead],
    status_code=status.HTTP_201_CREATED,
    summary="결제 생성",
)
def create_payment(payload: PaymentCreate, db: Session = Depends(get_db)) -> APIResponse[PaymentRead]:
    """결제 기본 정보를 생성한다."""
    payment = Payment(
        order_id=payload.order_id,
        payment_status=payload.payment_status,
        payment_amount=payload.payment_amount,
        paid_amount=payload.paid_amount,
        currency_code=payload.currency_code,
        payment_method_code=payload.payment_method_code,
        idempotency_key=payload.idempotency_key,
        created_by=payload.created_by,
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)

    created_payment = _get_payment_or_404(db, payment.id)
    return APIResponse(data=created_payment, message="결제를 생성했습니다.")


@router.put("/{payment_id}", response_model=APIResponse[PaymentRead], summary="결제 수정")
def update_payment(
    payment_id: int,
    payload: PaymentUpdate,
    db: Session = Depends(get_db),
) -> APIResponse[PaymentRead]:
    """결제 기본 정보를 수정한다."""
    payment = _get_payment_or_404(db, payment_id)
    update_data = payload.model_dump(exclude_unset=True)

    for field_name, field_value in update_data.items():
        setattr(payment, field_name, field_value)

    if update_data:
        payment.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)

    db.add(payment)
    db.commit()
    db.refresh(payment)

    updated_payment = _get_payment_or_404(db, payment_id)
    return APIResponse(data=updated_payment, message="결제를 수정했습니다.")


@router.delete(
    "/{payment_id}",
    response_model=APIResponse[dict[str, int]],
    summary="결제 삭제",
)
def delete_payment(payment_id: int, db: Session = Depends(get_db)) -> APIResponse[dict[str, int]]:
    """결제를 소프트 삭제한다."""
    payment = _get_payment_or_404(db, payment_id)
    payment.deleted_at = datetime.now(timezone.utc).replace(tzinfo=None)
    db.add(payment)
    db.commit()
    db.refresh(payment)

    return APIResponse(data={"payment_id": payment_id}, message="결제를 삭제했습니다.")


__all__ = ["router"]