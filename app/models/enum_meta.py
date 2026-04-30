from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class MetaEnum(Base):
    """meta.meta_enum 테이블에 대응하는 SQLAlchemy 모델.

    모든 ecommerce 스키마 테이블의 유효한 enum 값을 저장한다.
    이 테이블은 'meta' 스키마에 존재하며, 애플리케이션에서 동적으로
    enum 값을 조회할 때 사용된다.

    Note:
        이 테이블은 SQLAlchemy create_all()로 생성되지 않는다.
        (Base.metadata.schema가 'ecommerce'로 설정되어 있음)
        대신 insert_meta_enums.sql로 직접 생성/관리한다.
    """

    __tablename__ = "meta_enum"
    __table_args__ = {"schema": "meta"}

    enum_type: Mapped[str] = mapped_column(String(50), primary_key=True)
    enum_value: Mapped[str] = mapped_column(String(50), primary_key=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=func.now(), nullable=True
    )

    def __repr__(self) -> str:
        return f"<MetaEnum type={self.enum_type} value={self.enum_value}>"
