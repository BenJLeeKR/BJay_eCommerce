from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from sqlalchemy import BigInteger, Boolean, Date, DateTime, ForeignKey, PrimaryKeyConstraint, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.config import settings
from app.database import Base


class UserAccount(Base):
    """회원 계정 기본 정보를 저장한다."""

    __tablename__ = "user_account"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    password_hash: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    user_status: Mapped[str] = mapped_column(String(20), nullable=False)
    user_type: Mapped[str] = mapped_column(String(20), nullable=False)
    is_email_verified: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True, default=False, server_default="false")
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    deleted_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)

    profile: Mapped[Optional[UserProfile]] = relationship(back_populates="user", uselist=False)
    addresses: Mapped[list[UserAddress]] = relationship(back_populates="user", cascade="all, delete-orphan")
    auth_methods: Mapped[list[UserAuth]] = relationship(back_populates="user", cascade="all, delete-orphan")
    login_histories: Mapped[list[UserLoginHistory]] = relationship(back_populates="user", cascade="all, delete-orphan")
    roles: Mapped[list[UserRole]] = relationship(
        secondary=lambda: UserRoleMap.__table__,
        back_populates="users",
    )
    carts: Mapped[list["Cart"]] = relationship(back_populates="user")
    orders: Mapped[list["OrderHeader"]] = relationship(back_populates="user")
    reviews: Mapped[list["Review"]] = relationship(back_populates="user")
    review_likes: Mapped[list["ReviewLike"]] = relationship(back_populates="user")
    review_reports: Mapped[list["ReviewReport"]] = relationship(back_populates="user")
    review_comments: Mapped[list["ReviewComment"]] = relationship(back_populates="user")
    payment_methods: Mapped[list["PaymentMethod"]] = relationship(back_populates="user")


class UserProfile(Base):
    """회원 프로필 정보를 저장한다."""

    __tablename__ = "user_profile"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(f"{settings.DB_SCHEMA}.user_account.id"),
        nullable=False,
    )
    user_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    phone_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    birth_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    gender_code: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    deleted_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)

    user: Mapped[UserAccount] = relationship(back_populates="profile")


class UserAddress(Base):
    """회원 배송지 정보를 저장한다."""

    __tablename__ = "user_address"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(f"{settings.DB_SCHEMA}.user_account.id"),
        nullable=False,
    )
    address_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    recipient_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    recipient_phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    postal_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    address_line1: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    address_line2: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_default_address: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True, default=False, server_default="false")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    deleted_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)

    user: Mapped[UserAccount] = relationship(back_populates="addresses")


class UserAuth(Base):
    """회원 인증 수단 정보를 저장한다."""

    __tablename__ = "user_auth"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(f"{settings.DB_SCHEMA}.user_account.id"),
        nullable=False,
    )
    auth_provider: Mapped[str] = mapped_column(String(50), nullable=False)
    provider_user_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    refresh_token: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    deleted_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)

    user: Mapped[UserAccount] = relationship(back_populates="auth_methods")


class UserLoginHistory(Base):
    """회원 로그인 이력을 저장한다."""

    __tablename__ = "user_login_history"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(f"{settings.DB_SCHEMA}.user_account.id"),
        nullable=False,
    )
    login_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    ip_address: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    login_result: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())

    user: Mapped[UserAccount] = relationship(back_populates="login_histories")


class UserRole(Base):
    """회원 역할 정의를 저장한다."""

    __tablename__ = "user_role"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    role_name: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, server_default=func.now())

    users: Mapped[list[UserAccount]] = relationship(
        secondary=lambda: UserRoleMap.__table__,
        back_populates="roles",
    )


class UserRoleMap(Base):
    """회원과 역할의 다대다 매핑을 저장한다."""

    __tablename__ = "user_role_map"
    __table_args__ = (
        PrimaryKeyConstraint("user_id", "role_id"),
    )

    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(f"{settings.DB_SCHEMA}.user_account.id"),
        nullable=False,
    )
    role_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(f"{settings.DB_SCHEMA}.user_role.id"),
        nullable=False,
    )


__all__ = [
    "UserAccount",
    "UserAddress",
    "UserAuth",
    "UserLoginHistory",
    "UserProfile",
    "UserRole",
    "UserRoleMap",
]
