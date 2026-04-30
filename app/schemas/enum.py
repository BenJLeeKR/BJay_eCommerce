from __future__ import annotations

from typing import Optional

from app.schemas import ORMBaseSchema


class EnumValueRead(ORMBaseSchema):
    """meta.meta_enum 테이블의 단일 레코드를 나타내는 스키마."""

    enum_type: str
    enum_value: str
    description: Optional[str] = None


class EnumTypeGroup(ORMBaseSchema):
    """enum_type별로 그룹화된 enum 값 목록."""

    enum_type: str
    values: list[EnumValueRead]
