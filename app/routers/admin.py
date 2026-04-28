from __future__ import annotations
from typing import Optional

from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.orm import Session, selectinload

from app.dependencies import get_db, get_current_user_entity, require_user_types
from app.models.admin import AdminAccount, AdminRole, AdminPermission
from app.models.user import UserAccount
from app.models.order import OrderHeader
from app.models.payment import Payment
from app.models.shipment import Shipment
from app.models.inventory import Inventory
from app.models.promotion import Promotion
from app.schemas import APIResponse
from app.schemas.admin import (
    AdminAccountCreate,
    AdminAccountRead,
    AdminAccountUpdate,
    AdminRoleRead,
    AdminPermissionRead,
    AdminDashboardStats,
)

router = APIRouter(prefix="/admin", tags=["Admin (관리자)"])


def _admin_account_query():
    return (
        select(AdminAccount)
        .options(
            selectinload(AdminAccount.roles).selectinload(AdminRole.permissions),
            selectinload(AdminAccount.action_logs),
            selectinload(AdminAccount.access_logs),
        )
        .where(AdminAccount.deleted_at.is_(None))
    )


def _get_admin_account_or_404(db: Session, admin_id: int) -> AdminAccount:
    statement = _admin_account_query().where(AdminAccount.id == admin_id)
    admin = db.execute(statement).scalar_one_or_none()

    if admin is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="관리자 계정을 찾을 수 없습니다.",
        )

    return admin


@router.get("/accounts", response_model=APIResponse[list[AdminAccountRead]], summary="관리자 계정 목록 조회")
def list_admin_accounts(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    admin_status: Optional[str] = Query(default=None, max_length=20),
    db: Session = Depends(get_db),
) -> APIResponse[list[AdminAccountRead]]:
    """관리자 계정 목록을 상태와 페이징 조건으로 조회한다."""
    statement = _admin_account_query().offset(skip).limit(limit)

    if admin_status is not None:
        statement = statement.where(AdminAccount.admin_status == admin_status)

    accounts = db.execute(statement).scalars().unique().all()
    return APIResponse(data=accounts, message="관리자 계정 목록을 조회했습니다.")


@router.get("/accounts/{admin_id}", response_model=APIResponse[AdminAccountRead], summary="관리자 계정 상세 조회")
def get_admin_account(admin_id: int, db: Session = Depends(get_db)) -> APIResponse[AdminAccountRead]:
    """관리자 계정 상세 정보를 조회한다."""
    account = _get_admin_account_or_404(db, admin_id)
    return APIResponse(data=account, message="관리자 계정 상세 정보를 조회했습니다.")


@router.post(
    "/accounts",
    response_model=APIResponse[AdminAccountRead],
    status_code=status.HTTP_201_CREATED,
    summary="관리자 계정 생성",
)
def create_admin_account(payload: AdminAccountCreate, db: Session = Depends(get_db)) -> APIResponse[AdminAccountRead]:
    """관리자 계정을 생성한다."""
    account = AdminAccount(
        admin_email=payload.admin_email,
        password_hash=payload.password_hash,
        admin_status=payload.admin_status,
        last_login_at=payload.last_login_at,
        created_by=payload.created_by,
    )
    db.add(account)
    db.commit()
    db.refresh(account)

    created_account = _get_admin_account_or_404(db, account.id)
    return APIResponse(data=created_account, message="관리자 계정을 생성했습니다.")


@router.put("/accounts/{admin_id}", response_model=APIResponse[AdminAccountRead], summary="관리자 계정 수정")
def update_admin_account(
    admin_id: int,
    payload: AdminAccountUpdate,
    db: Session = Depends(get_db),
) -> APIResponse[AdminAccountRead]:
    """관리자 계정 정보를 수정한다."""
    account = _get_admin_account_or_404(db, admin_id)
    update_data = payload.model_dump(exclude_unset=True)

    for field_name, field_value in update_data.items():
        setattr(account, field_name, field_value)

    if update_data:
        account.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)

    db.add(account)
    db.commit()
    db.refresh(account)

    updated_account = _get_admin_account_or_404(db, admin_id)
    return APIResponse(data=updated_account, message="관리자 계정을 수정했습니다.")


@router.delete(
    "/accounts/{admin_id}",
    response_model=APIResponse[dict[str, int]],
    summary="관리자 계정 삭제",
)
def delete_admin_account(admin_id: int, db: Session = Depends(get_db)) -> APIResponse[dict[str, int]]:
    """관리자 계정을 소프트 삭제한다."""
    account = _get_admin_account_or_404(db, admin_id)
    account.deleted_at = datetime.now(timezone.utc).replace(tzinfo=None)
    db.add(account)
    db.commit()
    db.refresh(account)

    return APIResponse(data={"admin_id": admin_id}, message="관리자 계정을 삭제했습니다.")


@router.get("/roles", response_model=APIResponse[list[AdminRoleRead]], summary="관리자 역할 목록 조회")
def list_admin_roles(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> APIResponse[list[AdminRoleRead]]:
    """관리자 역할 목록을 페이징하여 조회한다."""
    statement = select(AdminRole).offset(skip).limit(limit)
    roles = db.execute(statement).scalars().all()
    return APIResponse(data=roles, message="관리자 역할 목록을 조회했습니다.")


@router.get("/permissions", response_model=APIResponse[list[AdminPermissionRead]], summary="권한 목록 조회")
def list_admin_permissions(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> APIResponse[list[AdminPermissionRead]]:
    """권한 목록을 페이징하여 조회한다."""
    statement = select(AdminPermission).offset(skip).limit(limit)
    permissions = db.execute(statement).scalars().all()
    return APIResponse(data=permissions, message="권한 목록을 조회했습니다.")


@router.get(
    "/dashboard/stats",
    response_model=APIResponse[AdminDashboardStats],
    summary="관리자 대시보드 통계",
)
def get_dashboard_stats(
    _: None = Depends(require_user_types("ADMIN")),
    db: Session = Depends(get_db),
) -> APIResponse[AdminDashboardStats]:
    """관리자 대시보드 위젯 구성을 위한 집계 통계를 반환한다.

    ADMIN 권한이 필요하며, 프론트엔드 대시보드 페이지에서
    매출 현황, 신규 가입자, 배송 대기, 재고 부족 등의 위젯을
    렌더링하는 데 사용된다.
    """
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    # 오늘 매출 (결제 완료 금액 합계)
    today_sales = (
        db.execute(
            select(func.coalesce(func.sum(Payment.paid_amount), 0)).where(
                Payment.approved_at >= today_start,
                Payment.payment_status == "APPROVED",
                Payment.deleted_at.is_(None),
            )
        ).scalar()
        or 0
    )

    # 오늘 결제 완료 주문 수
    today_paid_orders = (
        db.execute(
            select(func.count(Payment.id)).where(
                Payment.approved_at >= today_start,
                Payment.payment_status == "APPROVED",
                Payment.deleted_at.is_(None),
            )
        ).scalar()
        or 0
    )

    # 배송 대기 건수
    pending_shipments = (
        db.execute(
            select(func.count(Shipment.id)).where(
                Shipment.shipment_status == "PENDING",
                Shipment.deleted_at.is_(None),
            )
        ).scalar()
        or 0
    )

    # 재고 부족 SKU 수 (available_quantity < 5)
    low_stock_sku_count = (
        db.execute(
            select(func.count(Inventory.id)).where(
                Inventory.available_quantity < 5,
                Inventory.deleted_at.is_(None),
            )
        ).scalar()
        or 0
    )

    # 오늘 신규 가입자 수
    new_users_today = (
        db.execute(
            select(func.count(UserAccount.id)).where(
                UserAccount.created_at >= today_start,
                UserAccount.deleted_at.is_(None),
            )
        ).scalar()
        or 0
    )

    # 진행 중인 프로모션 수
    active_promotions = (
        db.execute(
            select(func.count(Promotion.id)).where(
                Promotion.is_active.is_(True),
                Promotion.start_at <= now,
                Promotion.end_at >= now,
                Promotion.deleted_at.is_(None),
            )
        ).scalar()
        or 0
    )

    stats = AdminDashboardStats(
        today_sales_amount=float(today_sales),
        today_paid_orders=today_paid_orders,
        pending_shipments=pending_shipments,
        low_stock_sku_count=low_stock_sku_count,
        new_users_today=new_users_today,
        active_promotions=active_promotions,
    )

    return APIResponse(data=stats, message="관리자 대시보드 통계를 조회했습니다.")


__all__ = ["router"]