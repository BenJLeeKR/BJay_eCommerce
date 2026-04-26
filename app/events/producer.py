from __future__ import annotations

import asyncio
import json
import logging
from typing import Optional

from aiokafka import AIOKafkaProducer
from pydantic import BaseModel

from app.core.config import settings

logger = logging.getLogger(__name__)

# Kafka 토픽 상수
TOPIC_ORDER_CREATED = "OrderCreated"
TOPIC_INVENTORY_UPDATED = "InventoryUpdated"
TOPIC_PAYMENT_COMPLETED = "PaymentCompleted"
TOPIC_SHIPMENT_CREATED = "ShipmentCreated"
TOPIC_PRODUCT_INDEX_UPDATED = "ProductIndexUpdated"

_producer: Optional[AIOKafkaProducer] = None
_producer_lock = asyncio.Lock()
_producer_ready = asyncio.Event()


async def get_producer() -> AIOKafkaProducer:
    """Kafka Producer 싱글톤 인스턴스를 반환한다."""
    global _producer
    if _producer is None:
        async with _producer_lock:
            # Double-checked locking: Lock 획득 후 다시 확인
            if _producer is None:
                if not settings.KAFKA_BOOTSTRAP_SERVERS:
                    raise RuntimeError(
                        "KAFKA_BOOTSTRAP_SERVERS not set, cannot create producer"
                    )
                _producer = AIOKafkaProducer(
                    bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                    value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
                    key_serializer=lambda k: str(k).encode("utf-8"),
                    request_timeout_ms=5000,
                )
                await _producer.start()
                _producer_ready.set()
                logger.info("Kafka producer started: %s", settings.KAFKA_BOOTSTRAP_SERVERS)
    else:
        # Producer가 완전히 초기화될 때까지 대기
        await _producer_ready.wait()
    return _producer


async def publish_event(
    topic: str,
    key: str,
    event: BaseModel,
) -> bool:
    """Kafka 토픽에 이벤트를 발행한다.

    Args:
        topic: Kafka 토픽 이름
        key: 메시지 키 (일반적으로 order_id 또는 sku_id)
        event: 발행할 Pydantic 이벤트 모델

    Returns:
        발행 성공 여부. 실패 시 로그만 남기고 False 반환.
        (DB 트랜잭션은 유지 — Outbox Pattern 도입 전 과도기적 접근)
    """
    try:
        producer = await get_producer()
        await producer.send(
            topic=topic,
            key=key,
            value=event.model_dump(mode="json"),
        )
        logger.info("Event published: topic=%s key=%s event=%s", topic, key, event.event_name)
        return True
    except Exception as exc:
        logger.error(
            "Failed to publish event: topic=%s key=%s error=%s",
            topic,
            key,
            exc,
        )
        return False


async def stop_producer() -> None:
    """Producer를 정리한다."""
    global _producer
    if _producer is not None:
        await _producer.stop()
        _producer = None
        logger.info("Kafka producer stopped")


__all__ = [
    "TOPIC_ORDER_CREATED",
    "TOPIC_INVENTORY_UPDATED",
    "TOPIC_PAYMENT_COMPLETED",
    "TOPIC_SHIPMENT_CREATED",
    "TOPIC_PRODUCT_INDEX_UPDATED",
    "get_producer",
    "publish_event",
    "stop_producer",
]
