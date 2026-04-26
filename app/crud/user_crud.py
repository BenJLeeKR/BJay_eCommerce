from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.crud import CRUDBase
from app.models.user import (
    UserAccount,
    UserAddress,
    UserAuth,
    UserLoginHistory,
    UserProfile,
    UserRole,
    UserRoleMap,
)
from app.schemas.user import (
    UserAccountCreate,
    UserAccountUpdate,
    UserAddressCreate,
    UserAddressRead,
    UserAddressUpdate,
    UserAuthRead,
    UserLoginHistoryCreate,
    UserLoginHistoryRead,
    UserProfileCreate,
    UserProfileRead,
    UserProfileUpdate,
    UserRoleCreate,
    UserRoleRead,
    UserRoleUpdate,
)


class UserAccountCRUD(CRUDBase[UserAccount]):
    """회원 계정 CRUD 연산을 담당한다."""

    def __init__(self) -> None:
        super().__init__(UserAccount)

    def create(self, db: Session, obj_in: UserAccountCreate) -> UserAccount:
        """회원 계정을 생성한다."""
        create_data = obj_in.model_dump(exclude_unset=True)
        db_obj = UserAccount(**create_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get(self, db: Session, object_id: int) -> Optional[UserAccount]:
        """회원 계정을 ID로 조회한다."""
        return db.get(UserAccount, object_id)

    def get_by_email(self, db: Session, email: str) -> Optional[UserAccount]:
        """회원 계정을 이메일로 조회한다."""
        stmt = select(UserAccount).where(UserAccount.user_email == email)
        return db.scalar(stmt)

    def get_multi(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[UserAccount]:
        """회원 계정 목록을 페이징하여 조회한다."""
        stmt = (
            select(UserAccount)
            .where(UserAccount.deleted_at.is_(None))
            .offset(skip)
            .limit(limit)
            .order_by(UserAccount.id)
        )
        return list(db.scalars(stmt).all())

    def update(
        self,
        db: Session,
        db_obj: UserAccount,
        obj_in: UserAccountUpdate,
    ) -> UserAccount:
        """회원 계정 정보를 수정한다."""
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, object_id: int) -> Optional[UserAccount]:
        """회원 계정을 소프트 삭제한다."""
        db_obj = db.get(UserAccount, object_id)
        if db_obj is None:
            return None
        from datetime import datetime, timezone

        db_obj.deleted_at = datetime.now(timezone.utc)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj


class UserProfileCRUD(CRUDBase[UserProfile]):
    """회원 프로필 CRUD 연산을 담당한다."""

    def __init__(self) -> None:
        super().__init__(UserProfile)

    def create(self, db: Session, obj_in: UserProfileCreate) -> UserProfile:
        """회원 프로필을 생성한다."""
        create_data = obj_in.model_dump(exclude_unset=True)
        db_obj = UserProfile(**create_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get(self, db: Session, object_id: int) -> Optional[UserProfile]:
        """회원 프로필을 ID로 조회한다."""
        return db.get(UserProfile, object_id)

    def get_by_user_id(self, db: Session, user_id: int) -> Optional[UserProfile]:
        """회원 프로필을 사용자 ID로 조회한다."""
        stmt = select(UserProfile).where(UserProfile.user_id == user_id)
        return db.scalar(stmt)

    def get_multi(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[UserProfile]:
        """회원 프로필 목록을 페이징하여 조회한다."""
        stmt = (
            select(UserProfile)
            .where(UserProfile.deleted_at.is_(None))
            .offset(skip)
            .limit(limit)
            .order_by(UserProfile.id)
        )
        return list(db.scalars(stmt).all())

    def update(
        self,
        db: Session,
        db_obj: UserProfile,
        obj_in: UserProfileUpdate,
    ) -> UserProfile:
        """회원 프로필 정보를 수정한다."""
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, object_id: int) -> Optional[UserProfile]:
        """회원 프로필을 소프트 삭제한다."""
        db_obj = db.get(UserProfile, object_id)
        if db_obj is None:
            return None
        from datetime import datetime, timezone

        db_obj.deleted_at = datetime.now(timezone.utc)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj


class UserAddressCRUD(CRUDBase[UserAddress]):
    """회원 배송지 CRUD 연산을 담당한다."""

    def __init__(self) -> None:
        super().__init__(UserAddress)

    def create(self, db: Session, obj_in: UserAddressCreate) -> UserAddress:
        """회원 배송지를 생성한다."""
        create_data = obj_in.model_dump(exclude_unset=True)
        db_obj = UserAddress(**create_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get(self, db: Session, object_id: int) -> Optional[UserAddress]:
        """회원 배송지를 ID로 조회한다."""
        return db.get(UserAddress, object_id)

    def get_by_user_id(
        self,
        db: Session,
        user_id: int,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[UserAddress]:
        """회원 배송지 목록을 사용자 ID로 조회한다."""
        stmt = (
            select(UserAddress)
            .where(UserAddress.user_id == user_id)
            .where(UserAddress.deleted_at.is_(None))
            .offset(skip)
            .limit(limit)
            .order_by(UserAddress.id)
        )
        return list(db.scalars(stmt).all())

    def get_default_by_user_id(
        self,
        db: Session,
        user_id: int,
    ) -> Optional[UserAddress]:
        """회원의 기본 배송지를 조회한다."""
        stmt = (
            select(UserAddress)
            .where(UserAddress.user_id == user_id)
            .where(UserAddress.is_default_address.is_(True))
            .where(UserAddress.deleted_at.is_(None))
        )
        return db.scalar(stmt)

    def get_multi(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[UserAddress]:
        """회원 배송지 목록을 페이징하여 조회한다."""
        stmt = (
            select(UserAddress)
            .where(UserAddress.deleted_at.is_(None))
            .offset(skip)
            .limit(limit)
            .order_by(UserAddress.id)
        )
        return list(db.scalars(stmt).all())

    def update(
        self,
        db: Session,
        db_obj: UserAddress,
        obj_in: UserAddressUpdate,
    ) -> UserAddress:
        """회원 배송지 정보를 수정한다."""
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, object_id: int) -> Optional[UserAddress]:
        """회원 배송지를 소프트 삭제한다."""
        db_obj = db.get(UserAddress, object_id)
        if db_obj is None:
            return None
        from datetime import datetime, timezone

        db_obj.deleted_at = datetime.now(timezone.utc)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj


class UserAuthCRUD(CRUDBase[UserAuth]):
    """회원 인증 수단 CRUD 연산을 담당한다."""

    def __init__(self) -> None:
        super().__init__(UserAuth)

    def create(self, db: Session, obj_in: UserAuthRead) -> UserAuth:
        """회원 인증 수단을 생성한다."""
        create_data = obj_in.model_dump(exclude_unset=True)
        db_obj = UserAuth(**create_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get(self, db: Session, object_id: int) -> Optional[UserAuth]:
        """회원 인증 수단을 ID로 조회한다."""
        return db.get(UserAuth, object_id)

    def get_by_user_id(
        self,
        db: Session,
        user_id: int,
    ) -> list[UserAuth]:
        """회원 인증 수단 목록을 사용자 ID로 조회한다."""
        stmt = (
            select(UserAuth)
            .where(UserAuth.user_id == user_id)
            .where(UserAuth.deleted_at.is_(None))
            .order_by(UserAuth.id)
        )
        return list(db.scalars(stmt).all())

    def get_multi(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[UserAuth]:
        """회원 인증 수단 목록을 페이징하여 조회한다."""
        stmt = (
            select(UserAuth)
            .where(UserAuth.deleted_at.is_(None))
            .offset(skip)
            .limit(limit)
            .order_by(UserAuth.id)
        )
        return list(db.scalars(stmt).all())

    def update(
        self,
        db: Session,
        db_obj: UserAuth,
        obj_in: UserAuthRead,
    ) -> UserAuth:
        """회원 인증 수단 정보를 수정한다."""
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, object_id: int) -> Optional[UserAuth]:
        """회원 인증 수단을 소프트 삭제한다."""
        db_obj = db.get(UserAuth, object_id)
        if db_obj is None:
            return None
        from datetime import datetime, timezone

        db_obj.deleted_at = datetime.now(timezone.utc)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj


class UserLoginHistoryCRUD(CRUDBase[UserLoginHistory]):
    """회원 로그인 이력 CRUD 연산을 담당한다."""

    def __init__(self) -> None:
        super().__init__(UserLoginHistory)

    def create(
        self,
        db: Session,
        obj_in: UserLoginHistoryCreate,
    ) -> UserLoginHistory:
        """회원 로그인 이력을 생성한다."""
        create_data = obj_in.model_dump(exclude_unset=True)
        db_obj = UserLoginHistory(**create_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get(self, db: Session, object_id: int) -> Optional[UserLoginHistory]:
        """회원 로그인 이력을 ID로 조회한다."""
        return db.get(UserLoginHistory, object_id)

    def get_by_user_id(
        self,
        db: Session,
        user_id: int,
        *,
        skip: int = 0,
        limit: int = 20,
    ) -> list[UserLoginHistory]:
        """회원 로그인 이력 목록을 사용자 ID로 조회한다."""
        stmt = (
            select(UserLoginHistory)
            .where(UserLoginHistory.user_id == user_id)
            .offset(skip)
            .limit(limit)
            .order_by(UserLoginHistory.login_at.desc())
        )
        return list(db.scalars(stmt).all())

    def get_multi(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[UserLoginHistory]:
        """회원 로그인 이력 목록을 페이징하여 조회한다."""
        stmt = (
            select(UserLoginHistory)
            .offset(skip)
            .limit(limit)
            .order_by(UserLoginHistory.id)
        )
        return list(db.scalars(stmt).all())

    def remove(self, db: Session, object_id: int) -> Optional[UserLoginHistory]:
        """회원 로그인 이력을 삭제한다."""
        db_obj = db.get(UserLoginHistory, object_id)
        if db_obj is None:
            return None
        db.delete(db_obj)
        db.commit()
        return db_obj


class UserRoleCRUD(CRUDBase[UserRole]):
    """회원 역할 CRUD 연산을 담당한다."""

    def __init__(self) -> None:
        super().__init__(UserRole)

    def create(self, db: Session, obj_in: UserRoleCreate) -> UserRole:
        """회원 역할을 생성한다."""
        create_data = obj_in.model_dump(exclude_unset=True)
        db_obj = UserRole(**create_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get(self, db: Session, object_id: int) -> Optional[UserRole]:
        """회원 역할을 ID로 조회한다."""
        return db.get(UserRole, object_id)

    def get_multi(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[UserRole]:
        """회원 역할 목록을 페이징하여 조회한다."""
        stmt = (
            select(UserRole)
            .offset(skip)
            .limit(limit)
            .order_by(UserRole.id)
        )
        return list(db.scalars(stmt).all())

    def update(
        self,
        db: Session,
        db_obj: UserRole,
        obj_in: UserRoleUpdate,
    ) -> UserRole:
        """회원 역할 정보를 수정한다."""
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, object_id: int) -> Optional[UserRole]:
        """회원 역할을 삭제한다."""
        db_obj = db.get(UserRole, object_id)
        if db_obj is None:
            return None
        db.delete(db_obj)
        db.commit()
        return db_obj


class UserRoleMapCRUD(CRUDBase[UserRoleMap]):
    """회원-역할 매핑 CRUD 연산을 담당한다."""

    def __init__(self) -> None:
        super().__init__(UserRoleMap)

    def create(self, db: Session, user_id: int, role_id: int) -> UserRoleMap:
        """회원과 역할을 매핑한다."""
        db_obj = UserRoleMap(user_id=user_id, role_id=role_id)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get(
        self,
        db: Session,
        user_id: int,
        role_id: int,
    ) -> Optional[UserRoleMap]:
        """회원-역할 매핑을 조회한다."""
        return db.get(UserRoleMap, (user_id, role_id))

    def get_by_user_id(
        self,
        db: Session,
        user_id: int,
    ) -> list[UserRoleMap]:
        """회원의 역할 매핑 목록을 조회한다."""
        stmt = select(UserRoleMap).where(UserRoleMap.user_id == user_id)
        return list(db.scalars(stmt).all())

    def remove(
        self,
        db: Session,
        user_id: int,
        role_id: int,
    ) -> Optional[UserRoleMap]:
        """회원-역할 매핑을 삭제한다."""
        db_obj = db.get(UserRoleMap, (user_id, role_id))
        if db_obj is None:
            return None
        db.delete(db_obj)
        db.commit()
        return db_obj


user_account_crud = UserAccountCRUD()
user_profile_crud = UserProfileCRUD()
user_address_crud = UserAddressCRUD()
user_auth_crud = UserAuthCRUD()
user_login_history_crud = UserLoginHistoryCRUD()
user_role_crud = UserRoleCRUD()
user_role_map_crud = UserRoleMapCRUD()


__all__ = [
    "UserAccountCRUD",
    "UserProfileCRUD",
    "UserAddressCRUD",
    "UserAuthCRUD",
    "UserLoginHistoryCRUD",
    "UserRoleCRUD",
    "UserRoleMapCRUD",
    "user_account_crud",
    "user_profile_crud",
    "user_address_crud",
    "user_auth_crud",
    "user_login_history_crud",
    "user_role_crud",
    "user_role_map_crud",
]
