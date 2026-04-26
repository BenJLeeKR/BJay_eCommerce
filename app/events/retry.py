from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, Optional

logger = logging.getLogger(__name__)

# In-Memory 멱등성 키 저장소 (실제 환경에서는 Redis 권장)
_idempotency_store: dict[str, datetime] = {}

RETRY_TOPIC_SUFFIX = ".retry"
DLQ_TOPIC_SUFFIX = ".dlq"
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 5
IDEMPOTENCY_TTL_SECONDS = 3600  # 1시간


def is_duplicate(event_id: str) -> bool:
    """멱등성 키 기반 중복 이벤트 체크.

    동일한 event_id가 이미 처리된 적이 있으면 True 반환.
    In-Memory 저장소이므로 Consumer 재시작 시 초기화됨.
    (향후 Redis 도입 필요)

    Args:
        event_id: 멱등성 키 (일반적으로 "topic:key:occurred_at" 조합)

    Returns:
        중복이면 True, 처음 보는 이벤트면 False
    """
    if event_id in _idempotency_store:
        logger.warning("Duplicate event detected: event_id=%s", event_id)
        return True

    # TTL 만료된 키 정리 (간단한 방식)
    _cleanup_expired()

    _idempotency_store[event_id] = datetime.utcnow()
    return False


def _cleanup_expired() -> None:
    """TTL이 만료된 멱등성 키를 정리한다."""
    now = datetime.utcnow()
    expired_keys = [
        key
        for key, timestamp in _idempotency_store.items()
        if (now - timestamp).total_seconds() > IDEMPOTENCY_TTL_SECONDS
    ]
    for key in expired_keys:
        del _idempotency_store[key]
    if expired_keys:
        logger.debug("Cleaned up %d expired idempotency keys", len(expired_keys))


async def publish_to_dlq(
    topic: str,
    message: dict[str, Any],
    error: str,
) -> None:
    """실패한 메시지를 DLQ(Dead Letter Queue) 토픽으로 발행한다.

    Args:
        topic: 원본 토픽 이름
        message: 원본 메시지 내용
        error: 실패 원인
    """
    dlq_message = {
        "original_topic": topic,
        "original_message": message,
        "error": error,
        "failed_at": datetime.utcnow().isoformat(),
    }
    dlq_topic = f"{topic}{DLQ_TOPIC_SUFFIX}"
    # TODO: DLQ Producer 발행 로직 (현재는 로깅만)
    logger.warning(
        "Message sent to DLQ: topic=%s dlq_topic=%s error=%s",
        topic,
        dlq_topic,
        error,
    )


__all__ = [
    "is_duplicate",
    "publish_to_dlq",
    "MAX_RETRIES",
    "RETRY_DELAY_SECONDS",
]
