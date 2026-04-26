from __future__ import annotations


class OrderStatus:
    """주문 상태 상수."""

    PENDING = "PENDING"  # 주문 생성, 결제 대기
    PAYMENT_PENDING = "PAYMENT_PENDING"  # 결제 진행 중
    PAID = "PAID"  # 결제 완료
    SHIPPING = "SHIPPING"  # 배송 준비 중
    SHIPPED = "SHIPPED"  # 배송 중
    DELIVERED = "DELIVERED"  # 배송 완료
    COMPLETE = "COMPLETE"  # 구매 확정
    CANCELLED = "CANCELLED"  # 주문 취소
    REFUNDED = "REFUNDED"  # 환불 완료

    # 유효 상태 전이 맵: 현재 상태 → 가능한 다음 상태 목록
    TRANSITIONS: dict[str, list[str]] = {
        PENDING: [PAYMENT_PENDING, CANCELLED],
        PAYMENT_PENDING: [PAID, CANCELLED],
        PAID: [SHIPPING, CANCELLED],
        SHIPPING: [SHIPPED, CANCELLED],
        SHIPPED: [DELIVERED],
        DELIVERED: [COMPLETE, REFUNDED],
        COMPLETE: [],
        CANCELLED: [],
        REFUNDED: [],
    }

    @classmethod
    def is_valid_transition(cls, current: str, next_status: str) -> bool:
        return next_status in cls.TRANSITIONS.get(current, [])


class PaymentStatus:
    """결제 상태 상수."""

    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    SUCCESS = "SUCCESS"
    FAIL = "FAIL"
    CANCELLED = "CANCELLED"
    REFUNDED = "REFUNDED"


class ShipmentStatus:
    """배송 상태 상수."""

    PENDING = "PENDING"
    PACKING = "PACKING"
    SHIPPED = "SHIPPED"
    DELIVERED = "DELIVERED"
    RETURNED = "RETURNED"
    CANCELLED = "CANCELLED"


__all__ = [
    "OrderStatus",
    "PaymentStatus",
    "ShipmentStatus",
]
