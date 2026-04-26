from __future__ import annotations
from typing import Optional

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.dependencies import get_db
from app.models.inventory import (
    Inventory,
    InventoryAdjustment,
    InventoryReservation,
    InventoryTransaction,
)
from app.models.product import SKU
from app.schemas import APIResponse
from app.schemas.inventory import (
    InventoryAdjustmentCreate,
    InventoryAdjustmentRead,
    InventoryCreate,
    InventoryRead,
    InventoryReservationCreate,
    InventoryReservationRead,
    InventoryTransactionCreate,
    InventoryTransactionRead,
    InventoryUpdate,
)

router = APIRouter(prefix="/inventory", tags=["Inventory (재고)"])


def _inventory_query():
    return (
        select(Inventory)
        .options(
            selectinload(Inventory.sku),
            selectinload(Inventory.reservations),
            selectinload(Inventory.transactions),
        )
    )


def _get_inventory_or_404(db: Session, inventory_id: int) -> Inventory:
    statement = _inventory_query().where(Inventory.id == inventory_id)
    inventory = db.execute(statement).scalar_one_or_none()

    if inventory is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="재고를 찾을 수 없습니다.",
        )

    return inventory


@router.get("", response_model=APIResponse[list[InventoryRead]], summary="재고 목록 조회")
def list_inventory(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    sku_id: Optional[int] = Query(default=None, gt=0),
    db: Session = Depends(get_db),
) -> APIResponse[list[InventoryRead]]:
    """재고 목록을 SKU와 페이징 조건으로 조회한다."""
    statement = _inventory_query().offset(skip).limit(limit)

    if sku_id is not None:
        statement = statement.where(Inventory.sku_id == sku_id)

    inventory_list = db.execute(statement).scalars().unique().all()
    return APIResponse(data=inventory_list, message="재고 목록을 조회했습니다.")


@router.get("/{inventory_id}", response_model=APIResponse[InventoryRead], summary="재고 상세 조회")
def get_inventory(inventory_id: int, db: Session = Depends(get_db)) -> APIResponse[InventoryRead]:
    """재고 상세 정보를 조회한다."""
    inventory = _get_inventory_or_404(db, inventory_id)
    return APIResponse(data=inventory, message="재고 상세 정보를 조회했습니다.")


@router.post(
    "",
    response_model=APIResponse[InventoryRead],
    status_code=status.HTTP_201_CREATED,
    summary="재고 생성",
)
def create_inventory(payload: InventoryCreate, db: Session = Depends(get_db)) -> APIResponse[InventoryRead]:
    """재고 기본 정보를 생성한다."""
    # SKU 존재 여부 확인
    sku = db.execute(select(SKU).where(SKU.id == payload.sku_id)).scalar_one_or_none()
    if sku is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="해당 SKU를 찾을 수 없습니다.",
        )

    # 중복 재고 확인 (sku_id는 unique)
    existing = db.execute(select(Inventory).where(Inventory.sku_id == payload.sku_id)).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="이미 해당 SKU의 재고가 존재합니다.",
        )

    inventory = Inventory(
        sku_id=payload.sku_id,
        total_quantity=payload.total_quantity,
        available_quantity=payload.available_quantity,
        reserved_quantity=payload.reserved_quantity,
        safety_stock_quantity=payload.safety_stock_quantity,
        created_by=payload.created_by,
    )
    db.add(inventory)
    db.commit()
    db.refresh(inventory)

    created_inventory = _get_inventory_or_404(db, inventory.id)
    return APIResponse(data=created_inventory, message="재고를 생성했습니다.")


@router.put("/{inventory_id}", response_model=APIResponse[InventoryRead], summary="재고 수정")
def update_inventory(
    inventory_id: int,
    payload: InventoryUpdate,
    db: Session = Depends(get_db),
) -> APIResponse[InventoryRead]:
    """재고 기본 정보를 수정한다."""
    inventory = _get_inventory_or_404(db, inventory_id)

    update_data = payload.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="수정할 필드가 제공되지 않았습니다.",
        )

    for field, value in update_data.items():
        setattr(inventory, field, value)

    inventory.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(inventory)

    updated_inventory = _get_inventory_or_404(db, inventory.id)
    return APIResponse(data=updated_inventory, message="재고를 수정했습니다.")


@router.delete("/{inventory_id}", response_model=APIResponse[None], summary="재고 삭제")
def delete_inventory(inventory_id: int, db: Session = Depends(get_db)) -> APIResponse[None]:
    """재고를 삭제한다."""
    inventory = _get_inventory_or_404(db, inventory_id)

    db.delete(inventory)
    db.commit()

    return APIResponse(data=None, message="재고를 삭제했습니다.")


# ---------- 재고 조정 (InventoryAdjustment) ----------


@router.get(
    "/adjustments",
    response_model=APIResponse[list[InventoryAdjustmentRead]],
    summary="재고 조정 이력 목록 조회",
)
def list_inventory_adjustments(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    sku_id: Optional[int] = Query(default=None, gt=0),
    db: Session = Depends(get_db),
) -> APIResponse[list[InventoryAdjustmentRead]]:
    """재고 조정 이력 목록을 SKU 조건으로 조회한다."""
    statement = select(InventoryAdjustment).options(selectinload(InventoryAdjustment.inventory))

    if sku_id is not None:
        statement = statement.where(InventoryAdjustment.sku_id == sku_id)

    statement = statement.offset(skip).limit(limit)
    adjustments = db.execute(statement).scalars().unique().all()
    return APIResponse(data=adjustments, message="재고 조정 이력 목록을 조회했습니다.")


@router.get(
    "/adjustments/{adjustment_id}",
    response_model=APIResponse[InventoryAdjustmentRead],
    summary="재고 조정 이력 상세 조회",
)
def get_inventory_adjustment(
    adjustment_id: int,
    db: Session = Depends(get_db),
) -> APIResponse[InventoryAdjustmentRead]:
    """재고 조정 이력 상세 정보를 조회한다."""
    statement = (
        select(InventoryAdjustment)
        .options(selectinload(InventoryAdjustment.inventory))
        .where(InventoryAdjustment.id == adjustment_id)
    )
    adjustment = db.execute(statement).scalar_one_or_none()

    if adjustment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="재고 조정 이력을 찾을 수 없습니다.",
        )

    return APIResponse(data=adjustment, message="재고 조정 이력 상세 정보를 조회했습니다.")


@router.post(
    "/adjustments",
    response_model=APIResponse[InventoryAdjustmentRead],
    status_code=status.HTTP_201_CREATED,
    summary="재고 조정 생성",
)
def create_inventory_adjustment(
    payload: InventoryAdjustmentCreate,
    db: Session = Depends(get_db),
) -> APIResponse[InventoryAdjustmentRead]:
    """재고 조정 이력을 생성하고 Inventory 수량을 함께 업데이트한다."""
    # SKU 및 재고 확인
    inventory = db.execute(select(Inventory).where(Inventory.sku_id == payload.sku_id)).scalar_one_or_none()
    if inventory is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="해당 SKU의 재고를 찾을 수 없습니다.",
        )

    # 재고 조정 생성
    adjustment = InventoryAdjustment(
        sku_id=payload.sku_id,
        adjustment_quantity=payload.adjustment_quantity,
        adjustment_reason=payload.adjustment_reason,
        created_by=payload.created_by,
    )
    db.add(adjustment)

    # Inventory 수량 업데이트
    inventory.total_quantity += payload.adjustment_quantity
    inventory.available_quantity += payload.adjustment_quantity
    inventory.updated_at = datetime.now(timezone.utc)

    # InventoryTransaction 기록
    transaction = InventoryTransaction(
        sku_id=payload.sku_id,
        transaction_type="IN" if payload.adjustment_quantity >= 0 else "OUT",
        quantity=abs(payload.adjustment_quantity),
        reference_type="ADJUSTMENT",
        reference_id=adjustment.id,
    )
    db.add(transaction)

    db.commit()
    db.refresh(adjustment)

    statement = (
        select(InventoryAdjustment)
        .options(selectinload(InventoryAdjustment.inventory))
        .where(InventoryAdjustment.id == adjustment.id)
    )
    created_adjustment = db.execute(statement).scalar_one_or_none()

    return APIResponse(data=created_adjustment, message="재고 조정 이력을 생성했습니다.")


@router.delete(
    "/adjustments/{adjustment_id}",
    response_model=APIResponse[dict[str, int]],
    summary="재고 조정 이력 삭제",
)
def delete_inventory_adjustment(
    adjustment_id: int,
    db: Session = Depends(get_db),
) -> APIResponse[dict[str, int]]:
    """재고 조정 이력을 삭제한다."""
    adjustment = db.execute(
        select(InventoryAdjustment).where(InventoryAdjustment.id == adjustment_id)
    ).scalar_one_or_none()

    if adjustment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="재고 조정 이력을 찾을 수 없습니다.",
        )

    db.delete(adjustment)
    db.commit()

    return APIResponse(data={"adjustment_id": adjustment_id}, message="재고 조정 이력을 삭제했습니다.")


# 재고 예약 관련 엔드포인트
@router.post(
    "/reservations",
    response_model=APIResponse[InventoryReservationRead],
    status_code=status.HTTP_201_CREATED,
    summary="재고 예약 생성",
)
def create_reservation(
    payload: InventoryReservationCreate,
    db: Session = Depends(get_db),
) -> APIResponse[InventoryReservationRead]:
    """재고 예약을 생성한다."""
    # SKU 및 재고 확인
    inventory = db.execute(select(Inventory).where(Inventory.sku_id == payload.sku_id)).scalar_one_or_none()
    if inventory is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="해당 SKU의 재고를 찾을 수 없습니다.",
        )

    # 가용 수량 검증
    if inventory.available_quantity < payload.reserved_quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="가용 수량이 부족합니다.",
        )

    # 예약 생성
    reservation = InventoryReservation(
        sku_id=payload.sku_id,
        order_id=payload.order_id,
        reserved_quantity=payload.reserved_quantity,
        reservation_status=payload.reservation_status,
        expired_at=payload.expired_at,
    )
    db.add(reservation)

    # 재고 수량 업데이트
    inventory.available_quantity -= payload.reserved_quantity
    inventory.reserved_quantity += payload.reserved_quantity
    inventory.updated_at = datetime.now(timezone.utc)

    # InventoryTransaction 기록
    transaction = InventoryTransaction(
        sku_id=payload.sku_id,
        transaction_type="RESERVE",
        quantity=payload.reserved_quantity,
        reference_type="RESERVATION",
        reference_id=reservation.id,
    )
    db.add(transaction)

    db.commit()
    db.refresh(reservation)

    # 응답 생성
    statement = (
        select(InventoryReservation)
        .options(selectinload(InventoryReservation.inventory), selectinload(InventoryReservation.order))
        .where(InventoryReservation.id == reservation.id)
    )
    created_reservation = db.execute(statement).scalar_one_or_none()

    return APIResponse(data=created_reservation, message="재고 예약을 생성했습니다.")


@router.get(
    "/reservations/{reservation_id}",
    response_model=APIResponse[InventoryReservationRead],
    summary="재고 예약 상세 조회",
)
def get_reservation(reservation_id: int, db: Session = Depends(get_db)) -> APIResponse[InventoryReservationRead]:
    """재고 예약 상세 정보를 조회한다."""
    statement = (
        select(InventoryReservation)
        .options(selectinload(InventoryReservation.inventory), selectinload(InventoryReservation.order))
        .where(InventoryReservation.id == reservation_id)
    )
    reservation = db.execute(statement).scalar_one_or_none()

    if reservation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="재고 예약을 찾을 수 없습니다.",
        )

    return APIResponse(data=reservation, message="재고 예약 상세 정보를 조회했습니다.")


# 재고 변동 이력 조회
@router.get(
    "/transactions",
    response_model=APIResponse[list[InventoryTransactionRead]],
    summary="재고 변동 이력 조회",
)
def list_transactions(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    sku_id: Optional[int] = Query(default=None, gt=0),
    db: Session = Depends(get_db),
) -> APIResponse[list[InventoryTransactionRead]]:
    """재고 변동 이력을 조회한다."""
    statement = select(InventoryTransaction).options(selectinload(InventoryTransaction.inventory))

    if sku_id is not None:
        statement = statement.where(InventoryTransaction.sku_id == sku_id)

    statement = statement.offset(skip).limit(limit)
    transactions = db.execute(statement).scalars().unique().all()

    return APIResponse(data=transactions, message="재고 변동 이력을 조회했습니다.")