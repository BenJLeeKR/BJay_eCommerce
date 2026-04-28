from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.orm import Session, selectinload

from app.crud import CRUDBase
from app.models.cart import Cart, CartCoupon, CartItem, CartItemOptionSnapshot
from app.schemas.cart import (
    CartCreate,
    CartCouponCreate,
    CartCouponNestedCreate,
    CartCouponRead,
    CartItemCreate,
    CartItemNestedCreate,
    CartItemOptionSnapshotCreate,
    CartItemOptionSnapshotNestedCreate,
    CartItemOptionSnapshotRead,
    CartItemRead,
    CartItemUpdate,
    CartUpdate,
)


class CartCRUD(CRUDBase[Cart]):
    """장바구니 CRUD 연산을 담당한다."""

    def __init__(self) -> None:
        super().__init__(Cart)

    def create(
        self,
        db: Session,
        obj_in: CartCreate,
        *,
        session_id: Optional[str] = None,
    ) -> Cart:
        """장바구니를 생성한다."""
        create_data = obj_in.model_dump(exclude_unset=True)
        if session_id is not None:
            create_data["session_id"] = session_id
        db_obj = Cart(**create_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def create_with_items(
        self,
        db: Session,
        obj_in: CartCreate,
        *,
        session_id: Optional[str] = None,
    ) -> Cart:
        """장바구니와 함께 items(옵션 스냅샷 포함), coupons를 한 트랜잭션에 생성한다."""
        # 1. Cart 기본 정보 생성
        create_data = obj_in.model_dump(exclude={"items", "coupons"}, exclude_unset=True)
        if session_id is not None:
            create_data["session_id"] = session_id
        cart = Cart(**create_data)
        db.add(cart)
        db.flush()  # cart.id 확보

        # 2. items → cart_item + cart_item_option_snapshot INSERT
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        for item_in in obj_in.items:
            cart_item = CartItem(
                cart_id=cart.id,
                sku_id=item_in.sku_id,
                quantity=item_in.quantity,
                unit_price_amount=item_in.unit_price_amount,
                total_price_amount=item_in.total_price_amount,
                is_selected=item_in.is_selected,
                added_at=item_in.added_at or now,
                created_by=item_in.created_by,
            )
            db.add(cart_item)
            db.flush()  # cart_item.id 확보

            # 2-1. option_snapshots → cart_item_option_snapshot INSERT
            for snap_in in item_in.option_snapshots:
                snapshot = CartItemOptionSnapshot(
                    cart_item_id=cart_item.id,
                    option_name=snap_in.option_name,
                    option_value=snap_in.option_value,
                )
                db.add(snapshot)

        # 3. coupons → cart_coupon INSERT
        for coupon_in in obj_in.coupons:
            coupon = CartCoupon(
                cart_id=cart.id,
                coupon_id=coupon_in.coupon_id,
                discount_amount=coupon_in.discount_amount,
            )
            db.add(coupon)

        db.commit()
        db.refresh(cart)
        return cart

    def get(self, db: Session, object_id: int) -> Optional[Cart]:
        """장바구니를 ID로 조회한다."""
        return db.get(Cart, object_id)

    def get_with_relations(self, db: Session, cart_id: int) -> Optional[Cart]:
        """장바구니를 관계( items, coupons, option_snapshots )와 함께 조회한다."""
        stmt = (
            select(Cart)
            .options(
                selectinload(Cart.items).selectinload(CartItem.option_snapshots),
                selectinload(Cart.coupons),
            )
            .where(Cart.id == cart_id, Cart.deleted_at.is_(None))
        )
        return db.execute(stmt).scalar_one_or_none()

    def get_by_user_id(
        self,
        db: Session,
        user_id: int,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Cart]:
        """장바구니 목록을 사용자 ID로 조회한다."""
        stmt = (
            select(Cart)
            .where(Cart.user_id == user_id)
            .where(Cart.deleted_at.is_(None))
            .offset(skip)
            .limit(limit)
            .order_by(Cart.id)
        )
        return list(db.scalars(stmt).all())

    def get_by_session_id(
        self,
        db: Session,
        session_id: str,
    ) -> Optional[Cart]:
        """장바구니를 세션 ID로 조회한다."""
        stmt = (
            select(Cart)
            .where(Cart.session_id == session_id)
            .where(Cart.deleted_at.is_(None))
        )
        return db.scalar(stmt)

    def get_multi(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Cart]:
        """장바구니 목록을 페이징하여 조회한다."""
        stmt = (
            select(Cart)
            .where(Cart.deleted_at.is_(None))
            .offset(skip)
            .limit(limit)
            .order_by(Cart.id)
        )
        return list(db.scalars(stmt).all())

    def get_multi_with_relations(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
        user_id: Optional[int] = None,
        session_id: Optional[str] = None,
        cart_status: Optional[str] = None,
    ) -> tuple[list[Cart], int]:
        """장바구니 목록을 관계( items, coupons, option_snapshots )와 함께 조건별로 조회한다.

        Returns:
            (아이템 목록, 전체 개수) 튜플
        """
        base_where = [Cart.deleted_at.is_(None)]

        if user_id is not None:
            base_where.append(Cart.user_id == user_id)
        if session_id is not None:
            base_where.append(Cart.session_id == session_id)
        if cart_status is not None:
            base_where.append(Cart.cart_status == cart_status)

        # 전체 개수 조회
        count_stmt = select(func.count()).select_from(Cart).where(*base_where)
        total_count = db.execute(count_stmt).scalar_one()

        # 목록 조회
        stmt = (
            select(Cart)
            .options(
                selectinload(Cart.items).selectinload(CartItem.option_snapshots),
                selectinload(Cart.coupons),
            )
            .where(*base_where)
            .offset(skip)
            .limit(limit)
            .order_by(Cart.id)
        )

        items = list(db.execute(stmt).scalars().unique().all())
        return items, total_count

    def update(
        self,
        db: Session,
        db_obj: Cart,
        obj_in: CartUpdate,
    ) -> Cart:
        """장바구니 정보를 수정한다."""
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, object_id: int) -> Optional[Cart]:
        """장바구니를 소프트 삭제한다."""
        db_obj = db.get(Cart, object_id)
        if db_obj is None:
            return None
        from datetime import datetime, timezone

        db_obj.deleted_at = datetime.now(timezone.utc)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj


class CartItemCRUD(CRUDBase[CartItem]):
    """장바구니 상품 항목 CRUD 연산을 담당한다."""

    def __init__(self) -> None:
        super().__init__(CartItem)

    def create(self, db: Session, obj_in: CartItemCreate) -> CartItem:
        """장바구니 상품 항목을 생성한다."""
        create_data = obj_in.model_dump(exclude_unset=True)
        db_obj = CartItem(**create_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get(self, db: Session, object_id: int) -> Optional[CartItem]:
        """장바구니 상품 항목을 ID로 조회한다."""
        return db.get(CartItem, object_id)

    def get_with_option_snapshots(self, db: Session, cart_item_id: int) -> Optional[CartItem]:
        """장바구니 상품 항목을 옵션 스냅샷과 함께 조회한다."""
        stmt = (
            select(CartItem)
            .options(selectinload(CartItem.option_snapshots))
            .where(CartItem.id == cart_item_id, CartItem.deleted_at.is_(None))
        )
        return db.execute(stmt).scalar_one_or_none()

    def get_by_cart_id(
        self,
        db: Session,
        cart_id: int,
    ) -> list[CartItem]:
        """장바구니의 상품 항목 목록을 조회한다."""
        stmt = (
            select(CartItem)
            .where(CartItem.cart_id == cart_id)
            .where(CartItem.deleted_at.is_(None))
            .order_by(CartItem.id)
        )
        return list(db.scalars(stmt).all())

    def get_by_cart_and_sku(
        self,
        db: Session,
        cart_id: int,
        sku_id: int,
    ) -> Optional[CartItem]:
        """장바구니에서 특정 SKU의 항목을 조회한다."""
        stmt = (
            select(CartItem)
            .where(CartItem.cart_id == cart_id)
            .where(CartItem.sku_id == sku_id)
            .where(CartItem.deleted_at.is_(None))
        )
        return db.scalar(stmt)

    def get_multi(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[CartItem]:
        """장바구니 상품 항목 목록을 페이징하여 조회한다."""
        stmt = (
            select(CartItem)
            .where(CartItem.deleted_at.is_(None))
            .offset(skip)
            .limit(limit)
            .order_by(CartItem.id)
        )
        return list(db.scalars(stmt).all())

    def update(
        self,
        db: Session,
        db_obj: CartItem,
        obj_in: CartItemUpdate,
    ) -> CartItem:
        """장바구니 상품 항목을 수정한다."""
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, object_id: int) -> Optional[CartItem]:
        """장바구니 상품 항목을 소프트 삭제한다."""
        db_obj = db.get(CartItem, object_id)
        if db_obj is None:
            return None
        from datetime import datetime, timezone

        db_obj.deleted_at = datetime.now(timezone.utc)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj


class CartItemOptionSnapshotCRUD(CRUDBase[CartItemOptionSnapshot]):
    """장바구니 옵션 스냅샷 CRUD 연산을 담당한다."""

    def __init__(self) -> None:
        super().__init__(CartItemOptionSnapshot)

    def create(
        self,
        db: Session,
        obj_in: CartItemOptionSnapshotCreate,
    ) -> CartItemOptionSnapshot:
        """장바구니 옵션 스냅샷을 생성한다."""
        create_data = obj_in.model_dump(exclude_unset=True)
        db_obj = CartItemOptionSnapshot(**create_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get(
        self,
        db: Session,
        object_id: int,
    ) -> Optional[CartItemOptionSnapshot]:
        """장바구니 옵션 스냅샷을 ID로 조회한다."""
        return db.get(CartItemOptionSnapshot, object_id)

    def get_by_cart_item_id(
        self,
        db: Session,
        cart_item_id: int,
    ) -> list[CartItemOptionSnapshot]:
        """장바구니 상품 항목의 옵션 스냅샷 목록을 조회한다."""
        stmt = (
            select(CartItemOptionSnapshot)
            .where(CartItemOptionSnapshot.cart_item_id == cart_item_id)
            .order_by(CartItemOptionSnapshot.id)
        )
        return list(db.scalars(stmt).all())

    def get_multi(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[CartItemOptionSnapshot]:
        """장바구니 옵션 스냅샷 목록을 페이징하여 조회한다."""
        stmt = (
            select(CartItemOptionSnapshot)
            .offset(skip)
            .limit(limit)
            .order_by(CartItemOptionSnapshot.id)
        )
        return list(db.scalars(stmt).all())

    def remove(
        self,
        db: Session,
        object_id: int,
    ) -> Optional[CartItemOptionSnapshot]:
        """장바구니 옵션 스냅샷을 삭제한다."""
        db_obj = db.get(CartItemOptionSnapshot, object_id)
        if db_obj is None:
            return None
        db.delete(db_obj)
        db.commit()
        return db_obj


class CartCouponCRUD(CRUDBase[CartCoupon]):
    """장바구니 쿠폰 CRUD 연산을 담당한다."""

    def __init__(self) -> None:
        super().__init__(CartCoupon)

    def create(self, db: Session, obj_in: CartCouponCreate) -> CartCoupon:
        """장바구니 쿠폰을 생성한다."""
        create_data = obj_in.model_dump(exclude_unset=True)
        db_obj = CartCoupon(**create_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get(self, db: Session, object_id: int) -> Optional[CartCoupon]:
        """장바구니 쿠폰을 ID로 조회한다."""
        return db.get(CartCoupon, object_id)

    def get_by_cart_id(
        self,
        db: Session,
        cart_id: int,
    ) -> list[CartCoupon]:
        """장바구니의 쿠폰 목록을 조회한다."""
        stmt = (
            select(CartCoupon)
            .where(CartCoupon.cart_id == cart_id)
            .order_by(CartCoupon.id)
        )
        return list(db.scalars(stmt).all())

    def get_multi(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[CartCoupon]:
        """장바구니 쿠폰 목록을 페이징하여 조회한다."""
        stmt = (
            select(CartCoupon)
            .offset(skip)
            .limit(limit)
            .order_by(CartCoupon.id)
        )
        return list(db.scalars(stmt).all())

    def remove(self, db: Session, object_id: int) -> Optional[CartCoupon]:
        """장바구니 쿠폰을 삭제한다."""
        db_obj = db.get(CartCoupon, object_id)
        if db_obj is None:
            return None
        db.delete(db_obj)
        db.commit()
        return db_obj


    def merge_guest_cart(
        self,
        db: Session,
        user_id: int,
        session_id: str,
    ) -> Optional[Cart]:
        """비회원(session_id) 장바구니를 회원(user_id) 장바구니로 병합한다.

        로그인 성공 시 호출된다. 병합 정책:
        1. session_id로 게스트 장바구니 조회
        2. user_id로 기존 회원 장바구니 조회
        3. 둘 다 존재하면 SKU 기준으로 아이템 병합 (동일 SKU는 수량 합산)
        4. 게스트 장바구니의 쿠폰은 유효한 경우에만 회원 장바구니로 이동
        5. 게스트 장바구니는 병합 완료 후 소프트 삭제

        Returns:
            병합 결과 활성화된 회원 장바구니. 병합 대상이 없으면 None.
        """
        guest_cart = self.get_by_session_id(db, session_id)
        if guest_cart is None:
            return None

        # 게스트 장바구니에 user_id가 이미 할당되어 있으면 중복 병합 방지
        if guest_cart.user_id is not None:
            return None

        # 회원 장바구니 조회 (ACTIVE 상태)
        member_cart = None
        member_carts = self.get_by_user_id(db, user_id, limit=1)
        if member_carts:
            member_cart = member_carts[0]

        now = datetime.now(timezone.utc).replace(tzinfo=None)

        if member_cart is None:
            # 회원 장바구니가 없으면 게스트 장바구니를 회원 것으로 전환
            guest_cart.user_id = user_id
            guest_cart.session_id = None
            guest_cart.updated_at = now
            db.add(guest_cart)
            db.commit()
            db.refresh(guest_cart)
            return guest_cart

        # 회원 장바구니가 있으면 아이템 병합
        guest_items = (
            db.execute(
                select(CartItem)
                .options(selectinload(CartItem.option_snapshots))
                .where(CartItem.cart_id == guest_cart.id, CartItem.deleted_at.is_(None))
            )
            .scalars()
            .unique()
            .all()
        )

        for guest_item in guest_items:
            # 동일 SKU 확인
            existing_item = (
                db.execute(
                    select(CartItem).where(
                        CartItem.cart_id == member_cart.id,
                        CartItem.sku_id == guest_item.sku_id,
                        CartItem.deleted_at.is_(None),
                    )
                )
                .scalars()
                .first()
            )

            if existing_item is not None:
                # 동일 SKU: 수량 합산
                existing_item.quantity += guest_item.quantity
                existing_item.total_price_amount = (
                    existing_item.unit_price_amount * existing_item.quantity
                )
                existing_item.updated_at = now
                db.add(existing_item)
                # 게스트 아이템은 소프트 삭제
                guest_item.deleted_at = now
                db.add(guest_item)
            else:
                # 새 SKU: 게스트 아이템을 회원 장바구니로 재할당
                guest_item.cart_id = member_cart.id
                guest_item.updated_at = now
                db.add(guest_item)

        # 게스트 장바구니 쿠폰을 회원 장바구니로 이동
        guest_coupons = (
            db.execute(
                select(CartCoupon).where(CartCoupon.cart_id == guest_cart.id)
            )
            .scalars()
            .all()
        )
        for coupon in guest_coupons:
            # 동일 쿠폰이 이미 회원 장바구니에 있는지 확인
            existing_coupon = (
                db.execute(
                    select(CartCoupon).where(
                        CartCoupon.cart_id == member_cart.id,
                        CartCoupon.coupon_id == coupon.coupon_id,
                    )
                )
                .scalars()
                .first()
            )
            if existing_coupon is None:
                coupon.cart_id = member_cart.id
                db.add(coupon)
            else:
                db.delete(coupon)

        # 게스트 장바구니 소프트 삭제
        guest_cart.deleted_at = now
        guest_cart.updated_at = now
        db.add(guest_cart)

        member_cart.updated_at = now
        db.add(member_cart)
        db.commit()
        db.refresh(member_cart)
        return member_cart


cart_crud = CartCRUD()
cart_item_crud = CartItemCRUD()
cart_item_option_snapshot_crud = CartItemOptionSnapshotCRUD()
cart_coupon_crud = CartCouponCRUD()


__all__ = [
    "CartCRUD",
    "CartItemCRUD",
    "CartItemOptionSnapshotCRUD",
    "CartCouponCRUD",
    "cart_crud",
    "cart_item_crud",
    "cart_item_option_snapshot_crud",
    "cart_coupon_crud",
]
