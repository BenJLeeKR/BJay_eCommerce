from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class OrderItemEvent(BaseModel):
    """주문 상품 이벤트 데이터."""

    sku_id: int
    product_name: str
    quantity: int
    unit_price_amount: int


class OrderCreatedEvent(BaseModel):
    """주문 생성 이벤트 (§4 OrderCreated).

    설계 문서의 이벤트 스펙:
    {
      "order_id": number,
      "user_id": number
    }
    """

    event_name: str = "OrderCreated"
    event_version: str = "1.0"
    occurred_at: datetime = Field(default_factory=datetime.utcnow)

    order_id: int
    user_id: int
    total_pay_amount: int
    order_status: str = "PENDING"
    items: list[OrderItemEvent]


class InventoryUpdatedEvent(BaseModel):
    """재고 변동 이벤트."""

    event_name: str = "InventoryUpdated"
    event_version: str = "1.0"
    occurred_at: datetime = Field(default_factory=datetime.utcnow)

    sku_id: int
    available_quantity: int
    reserved_quantity: int
    order_id: int


class PaymentCompletedEvent(BaseModel):
    """결제 완료 이벤트.

    설계 문서의 이벤트 스펙:
    {
      "order_id": number,
      "status": "SUCCESS"
    }
    """

    event_name: str = "PaymentCompleted"
    event_version: str = "1.0"
    occurred_at: datetime = Field(default_factory=datetime.utcnow)

    order_id: int
    payment_id: int
    status: str  # "SUCCESS" | "FAIL"


class ShipmentCreatedEvent(BaseModel):
    """배송 생성 이벤트."""

    event_name: str = "ShipmentCreated"
    event_version: str = "1.0"
    occurred_at: datetime = Field(default_factory=datetime.utcnow)

    shipment_id: int
    order_id: int
    warehouse_id: int


class ProductIndexUpdatedEvent(BaseModel):
    """상품 검색 인덱스 업데이트 이벤트.

    DB → Kafka → Elasticsearch 파이프라인용.
    Product 생성/수정 시 발행되어 Search 인덱스를 갱신한다.
    """

    event_name: str = "ProductIndexUpdated"
    event_version: str = "1.0"
    occurred_at: datetime = Field(default_factory=datetime.utcnow)

    product_id: int
    product_name: Optional[str] = None
    product_description: Optional[str] = None
    category_ids: Optional[list[int]] = None
    brand_name: Optional[str] = None
    price_amount: Optional[Decimal] = None
    is_active: Optional[bool] = None


__all__ = [
    "OrderItemEvent",
    "OrderCreatedEvent",
    "InventoryUpdatedEvent",
    "PaymentCompletedEvent",
    "ShipmentCreatedEvent",
    "ProductIndexUpdatedEvent",
]
