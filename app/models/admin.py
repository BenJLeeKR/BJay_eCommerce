from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.config import settings
from app.database import Base


class AdminAccount(Base):
    """관리자 계정 정보를 저장한다."""

    __tablename__ = "admin_account"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    admin_email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    admin_status: Mapped[str] = mapped_column(String(20), nullable=False)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    deleted_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)

    roles: Mapped[list[AdminRole]] = relationship(
        secondary=lambda: AdminAccountRoleMap.__table__,
        back_populates="admins",
    )
    action_logs: Mapped[list[AdminActionLog]] = relationship(back_populates="admin")
    access_logs: Mapped[list[AdminAccessLog]] = relationship(back_populates="admin")


class AdminRole(Base):
    """관리자 역할 정의를 저장한다."""

    __tablename__ = "admin_role"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    role_name: Mapped[str] = mapped_column(String(100), nullable=False)
    role_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())

    admins: Mapped[list[AdminAccount]] = relationship(
        secondary=lambda: AdminAccountRoleMap.__table__,
        back_populates="roles",
    )
    permissions: Mapped[list[AdminPermission]] = relationship(
        secondary=lambda: AdminRolePermissionMap.__table__,
        back_populates="roles",
    )


class AdminPermission(Base):
    """권한 정의를 저장한다."""

    __tablename__ = "admin_permission"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    permission_code: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    permission_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    resource_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    action_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())

    roles: Mapped[list[AdminRole]] = relationship(
        secondary=lambda: AdminRolePermissionMap.__table__,
        back_populates="permissions",
    )


class AdminRolePermissionMap(Base):
    """역할과 권한의 다대다 매핑 테이블."""

    __tablename__ = "admin_role_permission_map"

    role_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(f"{settings.DB_SCHEMA}.admin_role.id"),
        primary_key=True,
    )
    permission_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(f"{settings.DB_SCHEMA}.admin_permission.id"),
        primary_key=True,
    )

    role: Mapped[AdminRole] = relationship(overlaps="permissions,roles")
    permission: Mapped[AdminPermission] = relationship(overlaps="permissions,roles")


class AdminAccountRoleMap(Base):
    """관리자 계정과 역할의 다대다 매핑 테이블."""

    __tablename__ = "admin_account_role_map"

    admin_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(f"{settings.DB_SCHEMA}.admin_account.id"),
        primary_key=True,
    )
    role_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(f"{settings.DB_SCHEMA}.admin_role.id"),
        primary_key=True,
    )

    admin: Mapped[AdminAccount] = relationship(overlaps="admins,roles")
    role: Mapped[AdminRole] = relationship(overlaps="admins,roles")


class AdminMenu(Base):
    """관리자 메뉴 계층 구조를 저장한다."""

    __tablename__ = "admin_menu"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    parent_menu_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey(f"{settings.DB_SCHEMA}.admin_menu.id"),
        nullable=True,
    )
    menu_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    menu_path: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    sort_order: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())

    parent: Mapped[Optional[AdminMenu]] = relationship(remote_side=[id], back_populates="children")
    children: Mapped[list[AdminMenu]] = relationship(back_populates="parent")


class AdminActionLog(Base):
    """관리자 작업 로그를 저장한다."""

    __tablename__ = "admin_action_log"
    __table_args__ = (Index("idx_admin_action_log_admin_id", "admin_id"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    admin_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(f"{settings.DB_SCHEMA}.admin_account.id"),
        nullable=False,
    )
    action_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    target_table: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    target_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    action_data: Mapped[Optional[dict]] = mapped_column(type_=Text, nullable=True)  # JSONB 대신 Text로 임시 처리
    ip_address: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())

    admin: Mapped[AdminAccount] = relationship(back_populates="action_logs")


class AdminAccessLog(Base):
    """관리자 접속 로그를 저장한다."""

    __tablename__ = "admin_access_log"
    __table_args__ = (Index("idx_admin_access_log_admin_id", "admin_id"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    admin_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey(f"{settings.DB_SCHEMA}.admin_account.id"),
        nullable=True,
    )
    login_result: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    accessed_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())

    admin: Mapped[Optional[AdminAccount]] = relationship(back_populates="access_logs")