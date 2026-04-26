from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.crud import CRUDBase
from app.models.admin import (
    AdminAccount,
    AdminAccountRoleMap,
    AdminActionLog,
    AdminAccessLog,
    AdminMenu,
    AdminPermission,
    AdminRole,
    AdminRolePermissionMap,
)
from app.schemas.admin import (
    AdminAccountCreate,
    AdminAccountUpdate,
    AdminActionLogCreate,
    AdminAccessLogCreate,
    AdminMenuCreate,
    AdminMenuUpdate,
    AdminPermissionCreate,
    AdminPermissionUpdate,
    AdminRoleCreate,
    AdminRoleUpdate,
)


class AdminAccountCRUD(CRUDBase[AdminAccount]):
    """관리자 계정 CRUD (soft delete 적용)."""

    def create(self, db: Session, obj_in: AdminAccountCreate) -> AdminAccount:
        """관리자 계정을 생성한다."""
        obj_data = obj_in.model_dump()
        db_obj = AdminAccount(**obj_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get(self, db: Session, object_id: int) -> Optional[AdminAccount]:
        """관리자 계정을 id로 조회한다. (soft delete 제외)"""
        stmt = (
            select(AdminAccount)
            .where(AdminAccount.id == object_id)
            .where(AdminAccount.deleted_at.is_(None))
        )
        return db.scalar(stmt)

    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> list[AdminAccount]:
        """관리자 계정 목록을 조회한다. (soft delete 제외)"""
        stmt = (
            select(AdminAccount)
            .where(AdminAccount.deleted_at.is_(None))
            .offset(skip)
            .limit(limit)
            .order_by(AdminAccount.id)
        )
        return list(db.scalars(stmt))

    def update(
        self, db: Session, db_obj: AdminAccount, obj_in: AdminAccountUpdate
    ) -> AdminAccount:
        """관리자 계정을 수정한다."""
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, object_id: int) -> AdminAccount:
        """관리자 계정을 soft delete 처리한다."""
        stmt = (
            select(AdminAccount)
            .where(AdminAccount.id == object_id)
            .where(AdminAccount.deleted_at.is_(None))
        )
        db_obj = db.scalar(stmt)
        if db_obj:
            db_obj.deleted_at = datetime.now()
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)
        return db_obj

    def get_by_email(self, db: Session, email: str) -> Optional[AdminAccount]:
        """관리자 이메일로 계정을 조회한다. (soft delete 제외)"""
        stmt = (
            select(AdminAccount)
            .where(AdminAccount.admin_email == email)
            .where(AdminAccount.deleted_at.is_(None))
        )
        return db.scalar(stmt)

    def get_by_status(
        self, db: Session, status: str, *, skip: int = 0, limit: int = 100
    ) -> list[AdminAccount]:
        """관리자 계정을 상태별로 조회한다. (soft delete 제외)"""
        stmt = (
            select(AdminAccount)
            .where(AdminAccount.admin_status == status)
            .where(AdminAccount.deleted_at.is_(None))
            .offset(skip)
            .limit(limit)
            .order_by(AdminAccount.id)
        )
        return list(db.scalars(stmt))

    def authenticate(
        self, db: Session, email: str, password_hash: str
    ) -> Optional[AdminAccount]:
        """관리자 인증을 처리한다."""
        stmt = (
            select(AdminAccount)
            .where(AdminAccount.admin_email == email)
            .where(AdminAccount.password_hash == password_hash)
            .where(AdminAccount.deleted_at.is_(None))
        )
        return db.scalar(stmt)

    def update_last_login(self, db: Session, admin_id: int) -> Optional[AdminAccount]:
        """관리자 마지막 로그인 시간을 갱신한다."""
        stmt = (
            select(AdminAccount)
            .where(AdminAccount.id == admin_id)
            .where(AdminAccount.deleted_at.is_(None))
        )
        db_obj = db.scalar(stmt)
        if db_obj:
            db_obj.last_login_at = datetime.now()
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)
        return db_obj


class AdminRoleCRUD(CRUDBase[AdminRole]):
    """관리자 역할 CRUD."""

    def create(self, db: Session, obj_in: AdminRoleCreate) -> AdminRole:
        """관리자 역할을 생성한다."""
        obj_data = obj_in.model_dump()
        db_obj = AdminRole(**obj_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get(self, db: Session, object_id: int) -> Optional[AdminRole]:
        """관리자 역할을 id로 조회한다."""
        stmt = select(AdminRole).where(AdminRole.id == object_id)
        return db.scalar(stmt)

    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> list[AdminRole]:
        """관리자 역할 목록을 조회한다."""
        stmt = (
            select(AdminRole)
            .offset(skip)
            .limit(limit)
            .order_by(AdminRole.id)
        )
        return list(db.scalars(stmt))

    def update(
        self, db: Session, db_obj: AdminRole, obj_in: AdminRoleUpdate
    ) -> AdminRole:
        """관리자 역할을 수정한다."""
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, object_id: int) -> AdminRole:
        """관리자 역할을 삭제한다."""
        stmt = select(AdminRole).where(AdminRole.id == object_id)
        db_obj = db.scalar(stmt)
        if db_obj:
            db.delete(db_obj)
            db.commit()
        return db_obj

    def get_by_name(self, db: Session, role_name: str) -> Optional[AdminRole]:
        """역할 이름으로 조회한다."""
        stmt = select(AdminRole).where(AdminRole.role_name == role_name)
        return db.scalar(stmt)


class AdminPermissionCRUD(CRUDBase[AdminPermission]):
    """관리자 권한 CRUD."""

    def create(self, db: Session, obj_in: AdminPermissionCreate) -> AdminPermission:
        """관리자 권한을 생성한다."""
        obj_data = obj_in.model_dump()
        db_obj = AdminPermission(**obj_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get(self, db: Session, object_id: int) -> Optional[AdminPermission]:
        """관리자 권한을 id로 조회한다."""
        stmt = select(AdminPermission).where(AdminPermission.id == object_id)
        return db.scalar(stmt)

    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> list[AdminPermission]:
        """관리자 권한 목록을 조회한다."""
        stmt = (
            select(AdminPermission)
            .offset(skip)
            .limit(limit)
            .order_by(AdminPermission.id)
        )
        return list(db.scalars(stmt))

    def update(
        self, db: Session, db_obj: AdminPermission, obj_in: AdminPermissionUpdate
    ) -> AdminPermission:
        """관리자 권한을 수정한다."""
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, object_id: int) -> AdminPermission:
        """관리자 권한을 삭제한다."""
        stmt = select(AdminPermission).where(AdminPermission.id == object_id)
        db_obj = db.scalar(stmt)
        if db_obj:
            db.delete(db_obj)
            db.commit()
        return db_obj

    def get_by_code(self, db: Session, permission_code: str) -> Optional[AdminPermission]:
        """권한 코드로 조회한다."""
        stmt = select(AdminPermission).where(
            AdminPermission.permission_code == permission_code
        )
        return db.scalar(stmt)

    def get_by_resource(
        self, db: Session, resource_type: str
    ) -> list[AdminPermission]:
        """리소스 타입별 권한 목록을 조회한다."""
        stmt = (
            select(AdminPermission)
            .where(AdminPermission.resource_type == resource_type)
            .order_by(AdminPermission.id)
        )
        return list(db.scalars(stmt))


class AdminRolePermissionMapCRUD(CRUDBase[AdminRolePermissionMap]):
    """역할-권한 매핑 CRUD (복합키)."""

    def create(
        self, db: Session, role_id: int, permission_id: int
    ) -> AdminRolePermissionMap:
        """역할-권한 매핑을 생성한다."""
        db_obj = AdminRolePermissionMap(
            role_id=role_id, permission_id=permission_id
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get(self, db: Session, role_id: int, permission_id: int) -> Optional[AdminRolePermissionMap]:
        """역할-권한 매핑을 복합키로 조회한다."""
        stmt = (
            select(AdminRolePermissionMap)
            .where(AdminRolePermissionMap.role_id == role_id)
            .where(AdminRolePermissionMap.permission_id == permission_id)
        )
        return db.scalar(stmt)

    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> list[AdminRolePermissionMap]:
        """역할-권한 매핑 목록을 조회한다."""
        stmt = (
            select(AdminRolePermissionMap)
            .offset(skip)
            .limit(limit)
            .order_by(AdminRolePermissionMap.role_id)
        )
        return list(db.scalars(stmt))

    def remove(self, db: Session, role_id: int, permission_id: int) -> AdminRolePermissionMap:
        """역할-권한 매핑을 삭제한다."""
        stmt = (
            select(AdminRolePermissionMap)
            .where(AdminRolePermissionMap.role_id == role_id)
            .where(AdminRolePermissionMap.permission_id == permission_id)
        )
        db_obj = db.scalar(stmt)
        if db_obj:
            db.delete(db_obj)
            db.commit()
        return db_obj

    def get_by_role_id(
        self, db: Session, role_id: int
    ) -> list[AdminRolePermissionMap]:
        """역할 ID로 매핑 목록을 조회한다."""
        stmt = (
            select(AdminRolePermissionMap)
            .where(AdminRolePermissionMap.role_id == role_id)
        )
        return list(db.scalars(stmt))

    def get_by_permission_id(
        self, db: Session, permission_id: int
    ) -> list[AdminRolePermissionMap]:
        """권한 ID로 매핑 목록을 조회한다."""
        stmt = (
            select(AdminRolePermissionMap)
            .where(AdminRolePermissionMap.permission_id == permission_id)
        )
        return list(db.scalars(stmt))


class AdminAccountRoleMapCRUD(CRUDBase[AdminAccountRoleMap]):
    """계정-역할 매핑 CRUD (복합키)."""

    def create(
        self, db: Session, admin_id: int, role_id: int
    ) -> AdminAccountRoleMap:
        """계정-역할 매핑을 생성한다."""
        db_obj = AdminAccountRoleMap(admin_id=admin_id, role_id=role_id)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get(self, db: Session, admin_id: int, role_id: int) -> Optional[AdminAccountRoleMap]:
        """계정-역할 매핑을 복합키로 조회한다."""
        stmt = (
            select(AdminAccountRoleMap)
            .where(AdminAccountRoleMap.admin_id == admin_id)
            .where(AdminAccountRoleMap.role_id == role_id)
        )
        return db.scalar(stmt)

    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> list[AdminAccountRoleMap]:
        """계정-역할 매핑 목록을 조회한다."""
        stmt = (
            select(AdminAccountRoleMap)
            .offset(skip)
            .limit(limit)
            .order_by(AdminAccountRoleMap.admin_id)
        )
        return list(db.scalars(stmt))

    def remove(self, db: Session, admin_id: int, role_id: int) -> AdminAccountRoleMap:
        """계정-역할 매핑을 삭제한다."""
        stmt = (
            select(AdminAccountRoleMap)
            .where(AdminAccountRoleMap.admin_id == admin_id)
            .where(AdminAccountRoleMap.role_id == role_id)
        )
        db_obj = db.scalar(stmt)
        if db_obj:
            db.delete(db_obj)
            db.commit()
        return db_obj

    def get_by_admin_id(
        self, db: Session, admin_id: int
    ) -> list[AdminAccountRoleMap]:
        """관리자 ID로 매핑 목록을 조회한다."""
        stmt = (
            select(AdminAccountRoleMap)
            .where(AdminAccountRoleMap.admin_id == admin_id)
        )
        return list(db.scalars(stmt))

    def get_by_role_id(
        self, db: Session, role_id: int
    ) -> list[AdminAccountRoleMap]:
        """역할 ID로 매핑 목록을 조회한다."""
        stmt = (
            select(AdminAccountRoleMap)
            .where(AdminAccountRoleMap.role_id == role_id)
        )
        return list(db.scalars(stmt))


class AdminMenuCRUD(CRUDBase[AdminMenu]):
    """관리자 메뉴 CRUD."""

    def create(self, db: Session, obj_in: AdminMenuCreate) -> AdminMenu:
        """관리자 메뉴를 생성한다."""
        obj_data = obj_in.model_dump()
        db_obj = AdminMenu(**obj_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get(self, db: Session, object_id: int) -> Optional[AdminMenu]:
        """관리자 메뉴를 id로 조회한다."""
        stmt = select(AdminMenu).where(AdminMenu.id == object_id)
        return db.scalar(stmt)

    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> list[AdminMenu]:
        """관리자 메뉴 목록을 조회한다."""
        stmt = (
            select(AdminMenu)
            .offset(skip)
            .limit(limit)
            .order_by(AdminMenu.sort_order)
        )
        return list(db.scalars(stmt))

    def update(
        self, db: Session, db_obj: AdminMenu, obj_in: AdminMenuUpdate
    ) -> AdminMenu:
        """관리자 메뉴를 수정한다."""
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, object_id: int) -> AdminMenu:
        """관리자 메뉴를 삭제한다."""
        stmt = select(AdminMenu).where(AdminMenu.id == object_id)
        db_obj = db.scalar(stmt)
        if db_obj:
            db.delete(db_obj)
            db.commit()
        return db_obj

    def get_root_menus(self, db: Session) -> list[AdminMenu]:
        """최상위 메뉴 목록을 조회한다."""
        stmt = (
            select(AdminMenu)
            .where(AdminMenu.parent_menu_id.is_(None))
            .order_by(AdminMenu.sort_order)
        )
        return list(db.scalars(stmt))

    def get_children(
        self, db: Session, parent_id: int
    ) -> list[AdminMenu]:
        """부모 메뉴 ID로 하위 메뉴 목록을 조회한다."""
        stmt = (
            select(AdminMenu)
            .where(AdminMenu.parent_menu_id == parent_id)
            .order_by(AdminMenu.sort_order)
        )
        return list(db.scalars(stmt))


class AdminActionLogCRUD(CRUDBase[AdminActionLog]):
    """관리자 작업 로그 CRUD."""

    def create(self, db: Session, obj_in: AdminActionLogCreate) -> AdminActionLog:
        """관리자 작업 로그를 생성한다."""
        obj_data = obj_in.model_dump()
        db_obj = AdminActionLog(**obj_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get(self, db: Session, object_id: int) -> Optional[AdminActionLog]:
        """관리자 작업 로그를 id로 조회한다."""
        stmt = select(AdminActionLog).where(AdminActionLog.id == object_id)
        return db.scalar(stmt)

    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> list[AdminActionLog]:
        """관리자 작업 로그 목록을 조회한다."""
        stmt = (
            select(AdminActionLog)
            .offset(skip)
            .limit(limit)
            .order_by(AdminActionLog.created_at.desc())
        )
        return list(db.scalars(stmt))

    def get_by_admin_id(
        self, db: Session, admin_id: int, *, skip: int = 0, limit: int = 100
    ) -> list[AdminActionLog]:
        """관리자 ID로 작업 로그를 조회한다."""
        stmt = (
            select(AdminActionLog)
            .where(AdminActionLog.admin_id == admin_id)
            .offset(skip)
            .limit(limit)
            .order_by(AdminActionLog.created_at.desc())
        )
        return list(db.scalars(stmt))

    def get_by_action_type(
        self, db: Session, action_type: str, *, skip: int = 0, limit: int = 100
    ) -> list[AdminActionLog]:
        """작업 유형별 로그를 조회한다."""
        stmt = (
            select(AdminActionLog)
            .where(AdminActionLog.action_type == action_type)
            .offset(skip)
            .limit(limit)
            .order_by(AdminActionLog.created_at.desc())
        )
        return list(db.scalars(stmt))


class AdminAccessLogCRUD(CRUDBase[AdminAccessLog]):
    """관리자 접속 로그 CRUD."""

    def create(self, db: Session, obj_in: AdminAccessLogCreate) -> AdminAccessLog:
        """관리자 접속 로그를 생성한다."""
        obj_data = obj_in.model_dump()
        db_obj = AdminAccessLog(**obj_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get(self, db: Session, object_id: int) -> Optional[AdminAccessLog]:
        """관리자 접속 로그를 id로 조회한다."""
        stmt = select(AdminAccessLog).where(AdminAccessLog.id == object_id)
        return db.scalar(stmt)

    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> list[AdminAccessLog]:
        """관리자 접속 로그 목록을 조회한다."""
        stmt = (
            select(AdminAccessLog)
            .offset(skip)
            .limit(limit)
            .order_by(AdminAccessLog.accessed_at.desc())
        )
        return list(db.scalars(stmt))

    def get_by_admin_id(
        self, db: Session, admin_id: int, *, skip: int = 0, limit: int = 100
    ) -> list[AdminAccessLog]:
        """관리자 ID로 접속 로그를 조회한다."""
        stmt = (
            select(AdminAccessLog)
            .where(AdminAccessLog.admin_id == admin_id)
            .offset(skip)
            .limit(limit)
            .order_by(AdminAccessLog.accessed_at.desc())
        )
        return list(db.scalars(stmt))

    def get_recent_failures(
        self, db: Session, *, limit: int = 10
    ) -> list[AdminAccessLog]:
        """최근 실패한 접속 로그를 조회한다."""
        stmt = (
            select(AdminAccessLog)
            .where(AdminAccessLog.login_result == "FAIL")
            .order_by(AdminAccessLog.accessed_at.desc())
            .limit(limit)
        )
        return list(db.scalars(stmt))


# 모듈 레벨 싱글턴 인스턴스
admin_account_crud = AdminAccountCRUD(AdminAccount)
admin_role_crud = AdminRoleCRUD(AdminRole)
admin_permission_crud = AdminPermissionCRUD(AdminPermission)
admin_role_permission_map_crud = AdminRolePermissionMapCRUD(AdminRolePermissionMap)
admin_account_role_map_crud = AdminAccountRoleMapCRUD(AdminAccountRoleMap)
admin_menu_crud = AdminMenuCRUD(AdminMenu)
admin_action_log_crud = AdminActionLogCRUD(AdminActionLog)
admin_access_log_crud = AdminAccessLogCRUD(AdminAccessLog)
