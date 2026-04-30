from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db_session
from app.models.enum_meta import MetaEnum
from app.schemas import APIResponse
from app.schemas.enum import EnumTypeGroup, EnumValueRead

router = APIRouter(prefix="/enums", tags=["enums"])


@router.get(
    "",
    response_model=APIResponse[list[EnumTypeGroup]],
    summary="모든 enum 타입과 값 목록 조회",
    description="meta.meta_enum 테이블에서 모든 enum 타입별 유효한 값 목록을 반환한다. "
    "enum_type 쿼리 파라미터로 특정 타입만 필터링할 수 있다.",
)
def list_enums(
    enum_type: Optional[str] = Query(
        default=None,
        description="필터링할 enum 타입 (예: order_status, payment_status). 생략 시 전체 조회.",
    ),
    db: Session = Depends(get_db_session),
) -> APIResponse[list[EnumTypeGroup]]:
    """meta.meta_enum 테이블에서 enum 값을 조회한다.

    프론트엔드에서 드롭다운/셀렉트 박스의 옵션을 동적으로 렌더링할 때 사용한다.
    """
    query = select(MetaEnum).order_by(MetaEnum.enum_type, MetaEnum.enum_value)

    if enum_type:
        query = query.where(MetaEnum.enum_type == enum_type)

    rows = db.execute(query).scalars().all()

    # enum_type별로 그룹화
    grouped: dict[str, list[EnumValueRead]] = {}
    for row in rows:
        if row.enum_type not in grouped:
            grouped[row.enum_type] = []
        grouped[row.enum_type].append(
            EnumValueRead(
                enum_type=row.enum_type,
                enum_value=row.enum_value,
                description=row.description,
            )
        )

    result = [
        EnumTypeGroup(enum_type=etype, values=values)
        for etype, values in grouped.items()
    ]

    return APIResponse(
        data=result,
        message="enum 목록을 조회했습니다.",
    )
