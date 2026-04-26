from __future__ import annotations
from datetime import datetime, timezone
from decimal import Decimal
from typing import Union


def utc_now() -> datetime:
    """UTC 기준 현재 시각을 반환한다."""
    return datetime.now(timezone.utc)


def format_currency(amount: Union[Decimal, int, float], currency: str = "KRW") -> str:
    """금액 값을 간단한 문자열 포맷으로 변환한다."""
    return f"{currency} {Decimal(str(amount)):,}"


__all__ = ["format_currency", "utc_now"]

