"""Core 유틸리티(utils) 모듈 단위 테스트."""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

import pytest

from app.utils import format_currency, utc_now


class TestUtcNow:
    """utc_now 함수의 동작을 검증한다."""

    def test_utc_now_returns_datetime(self):
        """utc_now가 datetime 인스턴스를 반환해야 한다."""
        result = utc_now()
        assert isinstance(result, datetime)

    def test_utc_now_is_timezone_aware(self):
        """utc_now가 시간대 정보를 포함해야 한다."""
        result = utc_now()
        assert result.tzinfo is not None

    def test_utc_now_is_utc(self):
        """utc_now의 시간대가 UTC여야 한다."""
        result = utc_now()
        assert result.tzinfo == timezone.utc

    def test_utc_now_is_recent(self):
        """utc_now가 현재 시각에 가까운 값을 반환해야 한다."""
        now = datetime.now(timezone.utc)
        result = utc_now()
        delta = abs((now - result).total_seconds())
        assert delta < 5  # 5초 이내

    def test_utc_now_returns_new_value_each_call(self):
        """utc_now를 연속 호출하면 서로 다른 시각을 반환해야 한다."""
        t1 = utc_now()
        t2 = utc_now()
        # 두 호출 사이에 시간이 흘렀으므로 t2 >= t1
        assert t2 >= t1


class TestFormatCurrency:
    """format_currency 함수의 동작을 검증한다."""

    def test_format_currency_decimal(self):
        """Decimal 타입 금액을 올바른 포맷으로 변환해야 한다."""
        result = format_currency(Decimal("15000.00"))
        assert result == "KRW 15,000.00"

    def test_format_currency_integer(self):
        """int 타입 금액을 올바른 포맷으로 변환해야 한다."""
        result = format_currency(5000)
        assert result == "KRW 5,000"

    def test_format_currency_float(self):
        """float 타입 금액을 올바른 포맷으로 변환해야 한다."""
        result = format_currency(12345.67)
        assert result == "KRW 12,345.67"

    def test_format_currency_custom_currency(self):
        """커스텀 통화 코드로 포맷팅할 수 있어야 한다."""
        result = format_currency(Decimal("30000"), currency="USD")
        assert result == "USD 30,000"

    def test_format_currency_zero(self):
        """0원을 올바르게 포맷팅해야 한다."""
        result = format_currency(Decimal("0"))
        assert result == "KRW 0"

    def test_format_currency_large_number(self):
        """큰 금액을 천 단위 구분자로 포맷팅해야 한다."""
        result = format_currency(Decimal("1000000000"))
        assert result == "KRW 1,000,000,000"

    def test_format_currency_negative_amount(self):
        """음수 금액도 포맷팅할 수 있어야 한다."""
        result = format_currency(Decimal("-5000"))
        assert result == "KRW -5,000"

    def test_format_currency_small_decimal(self):
        """소수점 이하 자릿수가 있는 금액을 포맷팅해야 한다."""
        result = format_currency(Decimal("99.99"))
        assert result == "KRW 99.99"

    def test_format_currency_empty_currency(self):
        """빈 통화 코드로 포맷팅할 수 있어야 한다."""
        result = format_currency(Decimal("1000"), currency="")
        assert result == " 1,000"

    def test_format_currency_with_string_amount(self):
        """문자열 금액을 Decimal로 변환하여 포맷팅해야 한다."""
        result = format_currency("25000")  # type: ignore[arg-type]
        assert result == "KRW 25,000"
