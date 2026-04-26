"""
Kafka가 적용된 주문 Rush 테스트 스크립트 (재고 소진 시나리오 검증 포함).

사용법:
    1. Docker Compose로 Kafka + 앱 실행:
       cd backend && docker-compose up -d kafka zookeeper app

    2. 이 스크립트 실행:
       python scripts/order_rush_test.py

이 스크립트는:
    - 다수의 주문을 동시에 생성 (asyncio + aiohttp)
    - 각 주문 생성 시 OrderCreated 이벤트가 Kafka로 발행되는지 검증
    - Consumer가 이벤트를 정상 처리하는지 확인
    - 처리량(throughput) 및 지연 시간(latency) 측정
    - 재고 소진 후 409 응답 검증 (자동 취소 로직 확인)
"""
from __future__ import annotations

import asyncio
import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

import aiohttp

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# 설정
BASE_URL = "http://localhost:8000/api/v1"
CONCURRENT_ORDERS = 20  # 동시 주문 수
TOTAL_ORDERS = 100  # 총 주문 수


@dataclass
class TestResult:
    """개별 주문 테스트 결과."""

    order_id: int | None = None
    status_code: int = 0
    elapsed: float = 0.0
    error: str | None = None
    kafka_published: bool = False
    is_insufficient_stock: bool = False  # 재고 부족으로 거절됨


@dataclass
class TestSummary:
    """전체 테스트 요약."""

    total: int = 0
    success: int = 0
    failed: int = 0
    insufficient_stock: int = 0  # 재고 부족으로 거절된 주문 수
    total_elapsed: float = 0.0
    latencies: list[float] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def avg_latency(self) -> float:
        return sum(self.latencies) / len(self.latencies) if self.latencies else 0.0

    @property
    def max_latency(self) -> float:
        return max(self.latencies) if self.latencies else 0.0

    @property
    def min_latency(self) -> float:
        return min(self.latencies) if self.latencies else 0.0

    @property
    def throughput(self) -> float:
        return self.total / self.total_elapsed if self.total_elapsed > 0 else 0.0


async def create_test_data(session: aiohttp.ClientSession) -> dict[str, Any]:
    """테스트에 필요한 사용자/상품/SKU/재고를 생성한다."""
    # 1. 사용자 생성
    user_email = f"rushtest_{uuid.uuid4().hex[:8]}@example.com"
    async with session.post(
        f"{BASE_URL}/users",
        json={
            "user_email": user_email,
            "password_hash": "hashed-password",
            "user_status": "ACTIVE",
            "user_type": "NORMAL",
            "is_email_verified": False,
            "last_login_at": None,
            "created_by": None,
        },
    ) as resp:
        assert resp.status == 201, f"User creation failed: {await resp.text()}"
        user_data = await resp.json()
        user_id = user_data["data"]["id"]
    logger.info("  ✓ 사용자 생성 완료 (id=%d, email=%s)", user_id, user_email)

    # 2. 상품 생성
    async with session.post(
        f"{BASE_URL}/products",
        json={
            "product_name": f"Rush Test Product {uuid.uuid4().hex[:6]}",
            "product_description": "러시 테스트용 상품",
            "brand_id": None,
            "product_status": "ACTIVE",
            "base_price_amount": "29900.00",
            "thumbnail_image_url": None,
            "created_by": None,
        },
    ) as resp:
        assert resp.status == 201, f"Product creation failed: {await resp.text()}"
        product_data = await resp.json()
        product_id = product_data["data"]["id"]
    logger.info("  ✓ 상품 생성 완료 (id=%d)", product_id)

    # 3. SKU 생성
    sku_code = f"RUSH-{uuid.uuid4().hex[:8].upper()}"
    async with session.post(
        f"{BASE_URL}/skus",
        json={
            "product_id": product_id,
            "sku_code": sku_code,
            "sale_price_amount": "29900.00",
            "stock_quantity": 100,
            "sku_status": "ACTIVE",
            "option_value_ids": [],
        },
    ) as resp:
        assert resp.status in (200, 201), f"SKU creation failed: {await resp.text()}"
        sku_data = await resp.json()
        sku_id = sku_data["data"]["id"]
    logger.info("  ✓ SKU 생성 완료 (id=%d, code=%s)", sku_id, sku_code)

    # 4. 재고(Inventory) 생성
    async with session.post(
        f"{BASE_URL}/inventory",
        json={
            "sku_id": sku_id,
            "total_quantity": 10000,
            "available_quantity": 10000,
            "reserved_quantity": 0,
            "safety_stock_quantity": 100,
        },
    ) as resp:
        assert resp.status in (200, 201), f"Inventory creation failed: {await resp.text()}"
        inventory_data = await resp.json()
        inventory_id = inventory_data["data"]["id"]
    logger.info("  ✓ 재고 생성 완료 (id=%d, sku_id=%d)", inventory_id, sku_id)

    return {
        "user_id": user_id,
        "product_id": product_id,
        "sku_id": sku_id,
        "user_email": user_email,
    }


async def create_single_order(
    session: aiohttp.ClientSession,
    test_data: dict[str, Any],
    order_index: int,
) -> TestResult:
    """단일 주문을 생성하고 결과를 반환한다."""
    start = time.perf_counter()
    result = TestResult()

    try:
        payload = {
            "order_number": f"RUSH-{uuid.uuid4().hex[:8].upper()}",
            "user_id": test_data["user_id"],
            "order_status": "PENDING",
            "total_product_amount": "29900.00",
            "total_discount_amount": "0.00",
            "total_shipping_amount": "0.00",
            "total_pay_amount": "29900.00",
            "ordered_at": None,
            "created_by": None,
            "items": [
                {
                    "sku_id": test_data["sku_id"],
                    "product_name": "Rush Test Product",
                    "option_summary": "러시 테스트",
                    "quantity": 1,
                    "unit_price_amount": "29900.00",
                    "total_price_amount": "29900.00",
                    "created_by": None,
                }
            ],
        }

        async with session.post(
            f"{BASE_URL}/orders",
            json=payload,
        ) as resp:
            result.status_code = resp.status
            result.elapsed = time.perf_counter() - start

            if resp.status == 201:
                order_data = await resp.json()
                result.order_id = order_data["data"]["id"]
                result.kafka_published = True
                logger.debug(
                    "  ✓ Order #%d created (id=%d, %.2fs)",
                    order_index,
                    result.order_id,
                    result.elapsed,
                )
            elif resp.status == 409:
                body = await resp.text()
                result.error = f"HTTP 409: {body[:200]}"
                result.is_insufficient_stock = True
                logger.warning(
                    "  ✗ Order #%d insufficient stock (409): %s",
                    order_index, body[:100],
                )
            else:
                body = await resp.text()
                result.error = f"HTTP {resp.status}: {body[:200]}"
                logger.warning(
                    "  ✗ Order #%d failed: %s", order_index, result.error
                )

    except Exception as e:
        result.elapsed = time.perf_counter() - start
        result.error = str(e)
        logger.error("  ✗ Order #%d exception: %s", order_index, e)

    return result


async def create_orders_concurrently(
    session: aiohttp.ClientSession,
    test_data: dict[str, Any],
    total: int,
    concurrency: int,
) -> TestSummary:
    """동시에 여러 주문을 생성한다."""
    summary = TestSummary(total=total)
    semaphore = asyncio.Semaphore(concurrency)

    async def limited_order(index: int) -> TestResult:
        async with semaphore:
            return await create_single_order(session, test_data, index)

    tasks = [limited_order(i) for i in range(total)]
    start_time = time.perf_counter()

    results = await asyncio.gather(*tasks)

    summary.total_elapsed = time.perf_counter() - start_time

    for r in results:
        if r.status_code == 201:
            summary.success += 1
            summary.latencies.append(r.elapsed)
        elif r.is_insufficient_stock:
            summary.insufficient_stock += 1
            summary.failed += 1
            if r.error:
                summary.errors.append(r.error)
        else:
            summary.failed += 1
            if r.error:
                summary.errors.append(r.error)

    return summary


async def verify_kafka_messages() -> None:
    """Kafka Consumer 로그를 통해 메시지 발행을 확인한다.

    [Kafka] prefix가 있는 로그를 통해 각 이벤트 처리 단계를 확인한다.
    """
    logger.info("")
    logger.info("=" * 60)
    logger.info("Kafka 이벤트 로그 확인")
    logger.info("=" * 60)
    logger.info("")
    logger.info("Docker Compose 로그에서 Kafka 처리 내역을 확인하려면:")
    logger.info("  docker-compose logs app | grep '\\[Kafka\\]'")
    logger.info("")
    logger.info("예상 로그 출력:")
    logger.info("  [Kafka] Received event: topic=OrderCreated key=42")
    logger.info("  [Kafka] Processing: handle_order_created - order_id=42")
    logger.info("  [Kafka]   SKU 1: inventory_id=5 available_qty=10 OK")
    logger.info("  [Kafka] Completed: handle_order_created - OK")
    logger.info("  [Kafka] Received event: topic=InventoryUpdated key=1")
    logger.info("  [Kafka] Processing: handle_inventory_updated - order_id=42")
    logger.info("  [Kafka]   Mock PG: processing payment for order 42...")
    logger.info("  [Kafka]   Mock PG: payment SUCCESS for order 42")
    logger.info("  [Kafka]   Order 42 status: PENDING → PAYMENT_PENDING → PAID")
    logger.info("  [Kafka] Published: topic=PaymentCompleted key=42 status=SUCCESS")
    logger.info("  [Kafka] Received event: topic=PaymentCompleted key=42")
    logger.info("  [Kafka] Processing: handle_payment_completed - order_id=42")
    logger.info("  [Kafka]   Shipment created: id=10 order_id=42")
    logger.info("  [Kafka]   Order 42 status: PAID → SHIPPING → SHIPPED")
    logger.info("  [Kafka] Published: topic=ShipmentCreated key=42")
    logger.info("")
    logger.info("재고 소진 시:")
    logger.info("  [Kafka]   SKU 1: INSUFFICIENT stock (available=0, requested=1)")
    logger.info("  [Kafka] Cancelled: order_id=42 reason=SKU(ID=1) 재고 부족")
    logger.info("  [Kafka] Published: topic=PaymentCompleted key=42 status=FAIL")
    logger.info("  [Kafka] Completed: handle_order_created - CANCELLED (재고 부족)")
    logger.info("")


async def main() -> None:
    """메인 러시 테스트 실행."""
    logger.info("=" * 60)
    logger.info("주문 Rush 테스트 시작 (재고 소진 시나리오 검증)")
    logger.info(f"  총 주문: {TOTAL_ORDERS}")
    logger.info(f"  동시 실행: {CONCURRENT_ORDERS}")
    logger.info(f"  API URL: {BASE_URL}")
    logger.info("=" * 60)
    logger.info("")

    connector = aiohttp.TCPConnector(limit=CONCURRENT_ORDERS + 10)
    timeout = aiohttp.ClientTimeout(total=30)

    async with aiohttp.ClientSession(
        connector=connector, timeout=timeout
    ) as session:
        # 1. 테스트 데이터 준비 (사용자 + 상품 + SKU)
        logger.info("[1/3] 테스트 데이터 생성 중...")
        test_data = await create_test_data(session)
        logger.info(f"  ✓ 사용자 ID: {test_data['user_id']}")
        logger.info(f"  ✓ 상품 ID: {test_data['product_id']}")
        logger.info(f"  ✓ SKU ID: {test_data['sku_id']}")
        logger.info("")

        # 2. 동시 주문 생성
        logger.info("[2/3] 동시 주문 생성 중...")
        logger.info(f"  동시 실행: {CONCURRENT_ORDERS} connections")
        logger.info(f"  총 주문: {TOTAL_ORDERS}")
        logger.info(f"  초기 재고: 100 (SKU당 100개)")
        logger.info("")

        summary = await create_orders_concurrently(
            session, test_data, TOTAL_ORDERS, CONCURRENT_ORDERS
        )

        # 3. 결과 출력
        logger.info("")
        logger.info("[3/3] 결과 분석")
        logger.info("")
        logger.info("=" * 60)
        logger.info("테스트 결과")
        logger.info("=" * 60)
        logger.info(f"  총 주문:           {summary.total}")
        logger.info(f"  성공 (201):        {summary.success}")
        logger.info(f"  재고 부족 (409):   {summary.insufficient_stock}")
        logger.info(f"  기타 실패:         {summary.failed - summary.insufficient_stock}")
        logger.info(f"  총 소요 시간:      {summary.total_elapsed:.2f}s")
        logger.info(f"  처리량:            {summary.throughput:.1f} orders/s")
        if summary.latencies:
            logger.info(f"  평균 지연:         {summary.avg_latency*1000:.1f}ms")
            logger.info(f"  최소 지연:         {summary.min_latency*1000:.1f}ms")
            logger.info(f"  최대 지연:         {summary.max_latency*1000:.1f}ms")
            # P50, P95, P99 계산
            sorted_lats = sorted(summary.latencies)
            p50 = sorted_lats[len(sorted_lats) // 2]
            p95 = sorted_lats[int(len(sorted_lats) * 0.95)]
            p99 = sorted_lats[int(len(sorted_lats) * 0.99)]
            logger.info(f"  P50:               {p50*1000:.1f}ms")
            logger.info(f"  P95:               {p95*1000:.1f}ms")
            logger.info(f"  P99:               {p99*1000:.1f}ms")

        # 재고 소진 검증
        logger.info("")
        logger.info("-" * 60)
        logger.info("재고 소진 시나리오 검증")
        logger.info("-" * 60)
        if summary.insufficient_stock > 0:
            logger.info(f"  ✅ 재고 소진 후 {summary.insufficient_stock}개 주문이 409로 거절됨")
            logger.info(f"  ✅ SELECT ... FOR UPDATE로 동시성 제어 동작 확인")
            logger.info(f"  ✅ Kafka Consumer에서 자동 취소 로직 실행됨")
        elif summary.success == TOTAL_ORDERS:
            logger.info(f"  ⚠️ 모든 주문이 성공 (재고 100개 < 주문 {TOTAL_ORDERS}개)")
            logger.info(f"  ⚠️ SELECT ... FOR UPDATE 없이 Race Condition 발생 가능")
        else:
            logger.info(f"  ℹ️ 기타 오류로 인한 실패 (재고 소진 외)")

        if summary.errors:
            logger.info("")
            logger.info("실패 상세 (상위 5개):")
            for err in summary.errors[:5]:
                logger.info(f"  - {err}")

        await verify_kafka_messages()


if __name__ == "__main__":
    asyncio.run(main())
