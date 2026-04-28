from __future__ import annotations
from typing import Optional

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from sqlalchemy.orm import Session

from app.crud import (
    cart_crud,
    cart_item_crud,
    cart_item_option_snapshot_crud,
    cart_coupon_crud,
    sku_crud,
)
from app.dependencies import get_db, get_session_id
from app.models.cart import CartItem
from app.models.inventory import Inventory
from app.models.product import SKU
from app.schemas import APIResponse, PagedResult
from app.schemas.cart import (
    CartCreate,
    CartRead,
    CartUpdate,
    CartItemCreate,
    CartItemRead,
    CartItemUpdate,
    CartItemOptionSnapshotCreate,
    CartItemOptionSnapshotRead,
    CartCouponCreate,
    CartCouponRead,
)

router = APIRouter(tags=["Carts (장바구니)"])


def _get_cart_or_404(db: Session, cart_id: int) -> "Cart":
    """장바구니를 관계( items, coupons, option_snapshots )와 함께 조회하고 없으면 404."""
    cart = cart_crud.get_with_relations(db, cart_id)
    if cart is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="장바구니를 찾을 수 없습니다.",
        )
    return cart


def _validate_sku_for_cart(
    db: Session,
    sku_id: int,
    quantity: int,
) -> SKU:
    """장바구니 추가 전 SKU의 유효성, 상태, 재고를 검증한다."""
    sku = sku_crud.get(db, sku_id)
    if sku is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"SKU(ID={sku_id})를 찾을 수 없습니다.",
        )
    if sku.deleted_at is not None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"SKU(ID={sku_id})는 삭제된 상품입니다.",
        )
    if sku.sku_status != "ACTIVE":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"SKU(ID={sku_id})는 현재 판매 중인 상품이 아닙니다. (상태: {sku.sku_status})",
        )
    # 재고 검증: Inventory.available_quantity 기준
    inventory = db.query(Inventory).filter(Inventory.sku_id == sku_id).first()
    if inventory is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"SKU(ID={sku_id})의 재고 정보가 존재하지 않습니다.",
        )
    if inventory.available_quantity < quantity:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"SKU(ID={sku_id})의 재고가 부족합니다. (요청: {quantity}, 가용재고: {inventory.available_quantity})",
        )
    return sku


def _get_cart_item_or_404(db: Session, cart_item_id: int) -> CartItem:
    """장바구니 상품 항목을 옵션 스냅샷과 함께 조회하고 없으면 404."""
    cart_item = cart_item_crud.get_with_option_snapshots(db, cart_item_id)
    if cart_item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="장바구니 상품을 찾을 수 없습니다.",
        )
    return cart_item


@router.get("/carts", response_model=APIResponse[PagedResult[CartRead]], summary="장바구니 목록 조회")
def list_carts(
    request: Request,
    response: Response,
    skip: int = Query(default=0, ge=0, description="건너뛸 레코드 수"),
    limit: int = Query(default=20, ge=1, le=100, description="페이지당 최대 아이템 수"),
    user_id: Optional[int] = Query(default=None, description="회원 ID 필터"),
    cart_status: Optional[str] = Query(default=None, max_length=20, description="장바구니 상태 필터"),
    db: Session = Depends(get_db),
) -> APIResponse[PagedResult[CartRead]]:
    """장바구니 목록을 사용자/세션/상태 조건으로 조회한다."""
    session_id: Optional[str] = None
    if user_id is None:
        session_id = get_session_id(request, response)

    carts, total_count = cart_crud.get_multi_with_relations(
        db,
        skip=skip,
        limit=limit,
        user_id=user_id,
        session_id=session_id,
        cart_status=cart_status,
    )

    return APIResponse(
        data=PagedResult[CartRead](
            items=carts,
            total_count=total_count,
            skip=skip,
            limit=limit,
        ),
        message="장바구니 목록을 조회했습니다.",
    )


@router.get("/carts/{cart_id}", response_model=APIResponse[CartRead], summary="장바구니 상세 조회")
def get_cart(cart_id: int, db: Session = Depends(get_db)) -> APIResponse[CartRead]:
    """장바구니 상세 정보를 조회한다."""
    cart = _get_cart_or_404(db, cart_id)
    return APIResponse(data=cart, message="장바구니 상세 정보를 조회했습니다.")


@router.post(
    "/carts",
    response_model=APIResponse[CartRead],
    status_code=status.HTTP_201_CREATED,
    summary="장바구니 생성 (상품/쿠폰 포함)",
)
def create_cart(
    payload: CartCreate,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> APIResponse[CartRead]:
    """장바구니를 생성한다. items와 coupons를 함께 전달하여 한 번에 생성할 수 있다."""
    # SKU 검증: 모든 item의 sku_id가 유효한지 사전 확인
    for item_in in payload.items:
        _validate_sku_for_cart(db, item_in.sku_id, item_in.quantity)

    session_id = get_session_id(request, response)
    cart = cart_crud.create_with_items(db, payload, session_id=session_id)
    created_cart = _get_cart_or_404(db, cart.id)
    return APIResponse(data=created_cart, message="장바구니를 생성했습니다.")


@router.put("/carts/{cart_id}", response_model=APIResponse[CartRead], summary="장바구니 수정")
def update_cart(
    cart_id: int,
    payload: CartUpdate,
    db: Session = Depends(get_db),
) -> APIResponse[CartRead]:
    """장바구니 기본 정보를 수정한다."""
    cart = _get_cart_or_404(db, cart_id)
    update_data = payload.model_dump(exclude_unset=True)
    if update_data:
        cart.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
    cart_crud.update(db, cart, payload)
    updated_cart = _get_cart_or_404(db, cart_id)
    return APIResponse(data=updated_cart, message="장바구니를 수정했습니다.")


@router.delete(
    "/carts/{cart_id}",
    response_model=APIResponse[dict[str, int]],
    summary="장바구니 삭제",
)
def delete_cart(cart_id: int, db: Session = Depends(get_db)) -> APIResponse[dict[str, int]]:
    """장바구니를 소프트 삭제한다."""
    cart = _get_cart_or_404(db, cart_id)
    cart_crud.remove(db, cart_id)
    return APIResponse(data={"cart_id": cart_id}, message="장바구니를 삭제했습니다.")


@router.get(
    "/carts/{cart_id}/items",
    response_model=APIResponse[list[CartItemRead]],
    summary="장바구니 상품 목록 조회",
)
def list_cart_items(
    cart_id: int,
    db: Session = Depends(get_db),
) -> APIResponse[list[CartItemRead]]:
    """특정 장바구니에 담긴 상품 목록을 조회한다."""
    cart = _get_cart_or_404(db, cart_id)
    return APIResponse(data=cart.items, message="장바구니 상품 목록을 조회했습니다.")


@router.post(
    "/carts/{cart_id}/items",
    response_model=APIResponse[CartItemRead],
    status_code=status.HTTP_201_CREATED,
    summary="장바구니 상품 추가",
)
def add_cart_item(
    cart_id: int,
    payload: CartItemCreate,
    db: Session = Depends(get_db),
) -> APIResponse[CartItemRead]:
    """장바구니에 상품을 추가한다."""
    cart = _get_cart_or_404(db, cart_id)

    # 중복 SKU 검사
    existing = cart_item_crud.get_by_cart_and_sku(db, cart_id, payload.sku_id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="이미 동일한 상품이 장바구니에 존재합니다.",
        )

    cart_item = cart_item_crud.create(db, payload)
    loaded_item = _get_cart_item_or_404(db, cart_item.id)
    return APIResponse(data=loaded_item, message="장바구니에 상품을 추가했습니다.")


@router.put(
    "/items/{cart_item_id}",
    response_model=APIResponse[CartItemRead],
    summary="장바구니 상품 수정",
)
def update_cart_item(
    cart_item_id: int,
    payload: CartItemUpdate,
    db: Session = Depends(get_db),
) -> APIResponse[CartItemRead]:
    """장바구니 상품 정보를 수정한다."""
    cart_item = _get_cart_item_or_404(db, cart_item_id)
    update_data = payload.model_dump(exclude_unset=True)
    if update_data:
        cart_item.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
    cart_item_crud.update(db, cart_item, payload)
    updated_item = _get_cart_item_or_404(db, cart_item_id)
    return APIResponse(data=updated_item, message="장바구니 상품을 수정했습니다.")


@router.delete(
    "/items/{cart_item_id}",
    response_model=APIResponse[dict[str, int]],
    summary="장바구니 상품 삭제",
)
def delete_cart_item(cart_item_id: int, db: Session = Depends(get_db)) -> APIResponse[dict[str, int]]:
    """장바구니 상품을 소프트 삭제한다."""
    cart_item = _get_cart_item_or_404(db, cart_item_id)
    cart_item_crud.remove(db, cart_item_id)
    return APIResponse(data={"cart_item_id": cart_item_id}, message="장바구니 상품을 삭제했습니다.")


@router.post(
    "/items/{cart_item_id}/option-snapshots",
    response_model=APIResponse[CartItemOptionSnapshotRead],
    status_code=status.HTTP_201_CREATED,
    summary="장바구니 상품 옵션 스냅샷 추가",
)
def add_cart_item_option_snapshot(
    cart_item_id: int,
    payload: CartItemOptionSnapshotCreate,
    db: Session = Depends(get_db),
) -> APIResponse[CartItemOptionSnapshotRead]:
    """장바구니 상품에 옵션 스냅샷을 추가한다."""
    cart_item = _get_cart_item_or_404(db, cart_item_id)

    snapshot = cart_item_option_snapshot_crud.create(db, payload)
    return APIResponse(data=snapshot, message="옵션 스냅샷을 추가했습니다.")


@router.post(
    "/carts/{cart_id}/coupons",
    response_model=APIResponse[CartCouponRead],
    status_code=status.HTTP_201_CREATED,
    summary="장바구니 쿠폰 적용",
)
def add_cart_coupon(
    cart_id: int,
    payload: CartCouponCreate,
    db: Session = Depends(get_db),
) -> APIResponse[CartCouponRead]:
    """장바구니에 쿠폰을 적용한다."""
    cart = _get_cart_or_404(db, cart_id)

    coupon = cart_coupon_crud.create(db, payload)
    return APIResponse(data=coupon, message="장바구니에 쿠폰을 적용했습니다.")


__all__ = ["router"]