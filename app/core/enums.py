from __future__ import annotations


class OrderStatus:
    """주문 상태 상수.

    모든 값은 meta.meta_enum 테이블의 order_status 타입과 동기화되어야 함.
    """

    CREATED = "CREATED"  # 주문 생성, 결제 대기
    PAYMENT_PENDING = "PAYMENT_PENDING"  # 결제 진행 중
    PAID = "PAID"  # 결제 완료
    SHIPPING = "SHIPPING"  # 배송 준비 중
    SHIPPED = "SHIPPED"  # 배송 중
    DELIVERED = "DELIVERED"  # 배송 완료
    COMPLETED = "COMPLETED"  # 구매 확정
    CANCELLED = "CANCELLED"  # 주문 취소
    REFUNDED = "REFUNDED"  # 환불 완료

    # 유효 상태 전이 맵: 현재 상태 → 가능한 다음 상태 목록
    TRANSITIONS: dict[str, list[str]] = {
        CREATED: [PAYMENT_PENDING, CANCELLED],
        PAYMENT_PENDING: [PAID, CANCELLED],
        PAID: [SHIPPING, CANCELLED],
        SHIPPING: [SHIPPED, CANCELLED],
        SHIPPED: [DELIVERED],
        DELIVERED: [COMPLETED, REFUNDED],
        COMPLETED: [],
        CANCELLED: [],
        REFUNDED: [],
    }

    @classmethod
    def is_valid_transition(cls, current: str, next_status: str) -> bool:
        return next_status in cls.TRANSITIONS.get(current, [])


class PaymentStatus:
    """결제 상태 상수.

    모든 값은 meta.meta_enum 테이블의 payment_status 타입과 동기화되어야 함.
    """

    PENDING = "PENDING"
    READY = "READY"
    SUCCESS = "SUCCESS"
    FAIL = "FAIL"
    CANCEL = "CANCEL"
    REFUNDED = "REFUNDED"


class ShipmentStatus:
    """배송 상태 상수.

    모든 값은 meta.meta_enum 테이블의 shipment_status 타입과 동기화되어야 함.
    """

    READY = "READY"
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
