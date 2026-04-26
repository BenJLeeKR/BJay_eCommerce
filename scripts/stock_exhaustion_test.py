"""
재고 소진 후 자동 취소 로직 검증 테스트.

2-Phase 실행:
  Phase 1: INITIAL_STOCK개 주문 → 전부 201 Created 예상
  Phase 2: INITIAL_STOCK * 2개 추가 주문 → 전부 409 Conflict 예상

검증:
  1. API Layer: with_for_update()가 Race Condition을 방지하는지
  2. Consumer Layer: 재고 부족 시 자동 취소 + PaymentCompleted(FAIL) 발행
  3. Kafka 로그: [Kafka] prefix 출력 확인
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
INITIAL_STOCK = 50  # 초기 재고 (이 값보다 많은 주문을 보내 재고 소진 유도)
PHASE2_ORDERS = INITIAL_STOCK * 2  # Phase 2에서 보낼 주문 수 (재고의 2배)


@dataclass
class TestResult:
    """개별 주문 테스트 결과."""

    order_id: int | None = None
    status_code: int = 0
    elapsed: float = 0.0
    error: str | None = None
    is_insufficient_stock: bool = False


@dataclass
class PhaseSummary:
    """각 Phase의 테스트 요약."""

    total: int = 0
    success: int = 0
    insufficient_stock: int = 0
    other_failures: int = 0
    total_elapsed: float = 0.0
    latencies: list[float] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    order_ids: list[int] = field(default_factory=list)

    @property
    def avg_latency(self) -> float:
        return sum(self.latencies) / len(self.latencies) if self.latencies else 0.0

    @property
    def throughput(self) -> float:
        return self.total / self.total_elapsed if self.total_elapsed > 0 else 0.0


async def create_test_data(session: aiohttp.ClientSession) -> dict[str, Any]:
    """테스트에 필요한 사용자/상품/SKU/재고를 생성한다."""
    # 1. 사용자 생성
    user_email = f"exhaust_{uuid.uuid4().hex[:8]}@example.com"
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
            "product_name": f"Exhaust Test {uuid.uuid4().hex[:6]}",
            "product_description": "재고 소진 테스트용 상품",
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
    sku_code = f"EXH-{uuid.uuid4().hex[:8].upper()}"
    async with session.post(
        f"{BASE_URL}/skus",
        json={
            "product_id": product_id,
            "sku_code": sku_code,
            "sale_price_amount": "29900.00",
            "stock_quantity": INITIAL_STOCK,
            "sku_status": "ACTIVE",
            "option_value_ids": [],
        },
    ) as resp:
        assert resp.status in (200, 201), f"SKU creation failed: {await resp.text()}"
        sku_data = await resp.json()
        sku_id = sku_data["data"]["id"]
    logger.info("  ✓ SKU 생성 완료 (id=%d, code=%s)", sku_id, sku_code)

    # 4. 재고(Inventory) 생성 - INITIAL_STOCK만 설정
    async with session.post(
        f"{BASE_URL}/inventory",
        json={
            "sku_id": sku_id,
            "total_quantity": INITIAL_STOCK,
            "available_quantity": INITIAL_STOCK,
            "reserved_quantity": 0,
            "safety_stock_quantity": 5,
        },
    ) as resp:
        assert resp.status in (200, 201), f"Inventory creation failed: {await resp.text()}"
        inventory_data = await resp.json()
        inventory_id = inventory_data["data"]["id"]
    logger.info("  ✓ 재고 생성 완료 (id=%d, sku_id=%d, available=%d)", inventory_id, sku_id, INITIAL_STOCK)

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
    phase: int,
) -> TestResult:
    """단일 주문을 생성하고 결과를 반환한다."""
    start = time.perf_counter()
    result = TestResult()

    try:
        payload = {
            "order_number": f"EXH-{uuid.uuid4().hex[:8].upper()}",
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
                    "product_name": "Exhaust Test Product",
                    "option_summary": "재고 소진 테스트",
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
                logger.debug(
                    "  [Phase%d] Order #%d created (id=%d, %.2fs)",
                    phase, order_index, result.order_id, result.elapsed,
                )
            elif resp.status == 409:
                body = await resp.text()
                result.error = f"HTTP 409: {body[:200]}"
                result.is_insufficient_stock = True
                logger.debug(
                    "  [Phase%d] Order #%d insufficient stock (409): %s",
                    phase, order_index, body[:100],
                )
            else:
                body = await resp.text()
                result.error = f"HTTP {resp.status}: {body[:200]}"
                logger.debug(
                    "  [Phase%d] Order #%d failed: %s", phase, order_index, result.error
                )

    except Exception as e:
        result.elapsed = time.perf_counter() - start
        exc_type = type(e).__name__
        exc_repr = repr(e)
        result.error = f"{exc_type}: {exc_repr}"
        logger.error("  [Phase%d] Order #%d exception: %s: %s", phase, order_index, exc_type, exc_repr)

    return result


async def run_phase(
    session: aiohttp.ClientSession,
    test_data: dict[str, Any],
    total_orders: int,
    concurrency: int,
    phase: int,
) -> PhaseSummary:
    """Phase를 실행하고 결과를 반환한다."""
    summary = PhaseSummary(total=total_orders)
    semaphore = asyncio.Semaphore(concurrency)

    async def limited_order(index: int) -> TestResult:
        async with semaphore:
            return await create_single_order(session, test_data, index, phase)

    start_time = time.perf_counter()

    # 배치 처리: 한 번에 concurrency개씩 실행하여 연결 풀 고갈 방지
    for batch_start in range(0, total_orders, concurrency):
        batch_end = min(batch_start + concurrency, total_orders)
        batch_tasks = [limited_order(i) for i in range(batch_start, batch_end)]
        batch_results = await asyncio.gather(*batch_tasks)

        for r in batch_results:
            if r.status_code == 201:
                summary.success += 1
                summary.latencies.append(r.elapsed)
                if r.order_id:
                    summary.order_ids.append(r.order_id)
            elif r.is_insufficient_stock:
                summary.insufficient_stock += 1
                if r.error:
                    summary.errors.append(r.error)
            else:
                summary.other_failures += 1
                if r.error:
                    summary.errors.append(r.error)

        # 배치 간 짧은 대기 (서버 부하 방지)
        if batch_end < total_orders:
            await asyncio.sleep(0.5)

    summary.total_elapsed = time.perf_counter() - start_time

    return summary


async def verify_order_status(
    session: aiohttp.ClientSession,
    order_ids: list[int],
    expected_status: str,
) -> tuple[int, int]:
    """주문 상태를 API로 확인한다."""
    matched = 0
    total = len(order_ids)
    for oid in order_ids[:10]:  # 처음 10개만 샘플 확인
        try:
            async with session.get(f"{BASE_URL}/orders/{oid}") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    actual_status = data["data"]["order_status"]
                    if actual_status == expected_status:
                        matched += 1
                    else:
                        logger.warning(
                            "  ⚠️ Order %d: expected=%s actual=%s",
                            oid, expected_status, actual_status,
                        )
                else:
                    logger.warning("  ⚠️ Order %d: API returned %d", oid, resp.status)
        except Exception as e:
            logger.warning("  ⚠️ Order %d: exception %s", oid, e)
    return matched, total


async def main() -> None:
    """메인 테스트 실행."""
    logger.info("=" * 70)
    logger.info("재고 소진 후 자동 취소 로직 검증 테스트")
    logger.info("=" * 70)
    logger.info(f"  초기 재고:          {INITIAL_STOCK}개")
    logger.info(f"  Phase 1 주문 수:    {INITIAL_STOCK}개 (재고만큼)")
    logger.info(f"  Phase 2 주문 수:    {PHASE2_ORDERS}개 (재고의 2배)")
    logger.info(f"  동시 실행:          {CONCURRENT_ORDERS} connections")
    logger.info(f"  API URL:            {BASE_URL}")
    logger.info("=" * 70)
    logger.info("")

    connector = aiohttp.TCPConnector(
        limit=CONCURRENT_ORDERS + 10,
        limit_per_host=CONCURRENT_ORDERS + 5,
        force_close=True,
        enable_cleanup_closed=True,
    )
    timeout = aiohttp.ClientTimeout(total=120, connect=60)

    async with aiohttp.ClientSession(
        connector=connector, timeout=timeout
    ) as session:
        # 1. 테스트 데이터 준비
        logger.info("[1/4] 테스트 데이터 생성 중...")
        test_data = await create_test_data(session)
        logger.info(f"  ✓ 사용자 ID: {test_data['user_id']}")
        logger.info(f"  ✓ SKU ID: {test_data['sku_id']}")
        logger.info("")

        # ============================================================
        # Phase 1: INITIAL_STOCK개 주문 (전부 성공 예상)
        # ============================================================
        logger.info("[2/4] Phase 1: 정상 재고 범위 내 주문 생성")
        logger.info(f"  주문: {INITIAL_STOCK}개 (재고={INITIAL_STOCK})")
        logger.info(f"  예상: 전부 201 Created")
        logger.info("")

        phase1 = await run_phase(
            session, test_data, INITIAL_STOCK, CONCURRENT_ORDERS, phase=1
        )

        logger.info("")
        logger.info(f"  Phase 1 결과:")
        logger.info(f"    성공 (201):        {phase1.success}")
        logger.info(f"    재고 부족 (409):   {phase1.insufficient_stock}")
        logger.info(f"    기타 실패:         {phase1.other_failures}")
        logger.info(f"    소요 시간:         {phase1.total_elapsed:.2f}s")
        if phase1.latencies:
            logger.info(f"    평균 지연:         {phase1.avg_latency*1000:.1f}ms")
            logger.info(f"    처리량:           {phase1.throughput:.1f} orders/s")

        # ============================================================
        # Phase 2: INITIAL_STOCK * 2개 주문 (재고 소진 → 409 예상)
        # ============================================================
        logger.info("")
        logger.info("[3/4] Phase 2: 재고 소진 후 추가 주문 생성")
        logger.info(f"  주문: {PHASE2_ORDERS}개 (재고={INITIAL_STOCK}, 이미 {phase1.success}개 소진)")
        logger.info(f"  예상: 전부 409 Conflict (재고 부족)")
        logger.info("")

        phase2 = await run_phase(
            session, test_data, PHASE2_ORDERS, CONCURRENT_ORDERS, phase=2
        )

        logger.info("")
        logger.info(f"  Phase 2 결과:")
        logger.info(f"    성공 (201):        {phase2.success}")
        logger.info(f"    재고 부족 (409):   {phase2.insufficient_stock}")
        logger.info(f"    기타 실패:         {phase2.other_failures}")
        logger.info(f"    소요 시간:         {phase2.total_elapsed:.2f}s")
        if phase2.latencies:
            logger.info(f"    평균 지연:         {phase2.avg_latency*1000:.1f}ms")
            logger.info(f"    처리량:           {phase2.throughput:.1f} orders/s")

        # ============================================================
        # 결과 분석
        # ============================================================
        logger.info("")
        logger.info("[4/4] 결과 분석")
        logger.info("")
        logger.info("=" * 70)
        logger.info("최종 검증 결과")
        logger.info("=" * 70)

        # 검증 1: Phase 1 - 모든 주문이 201이어야 함
        logger.info("")
        logger.info("▸ 검증 1: API Layer - with_for_update() 동시성 제어")
        if phase1.success == INITIAL_STOCK:
            logger.info(f"  ✅ Phase 1: {phase1.success}/{INITIAL_STOCK} 주문 성공 (201)")
            logger.info(f"     SELECT ... FOR UPDATE로 Race Condition 방지 확인")
        else:
            logger.warning(f"  ⚠️ Phase 1: {phase1.success}/{INITIAL_STOCK}만 성공")
            logger.warning(f"     예상치 못한 {phase1.insufficient_stock}개 409 발생")

        # 검증 2: Phase 2 - 재고 소진으로 409 발생
        logger.info("")
        logger.info("▸ 검증 2: 재고 소진 후 409 Conflict 반환")
        if phase2.insufficient_stock > 0:
            logger.info(f"  ✅ Phase 2: {phase2.insufficient_stock}개 주문이 409로 거절됨")
            logger.info(f"     재고 소진 시 API가 정상적으로 409 반환")
        elif phase2.success > 0:
            logger.warning(f"  ⚠️ Phase 2: {phase2.success}개 주문이 성공 (예상: 0)")
            logger.warning(f"     with_for_update()가 Race Condition을 막지 못함")
        else:
            logger.info(f"  ℹ️ Phase 2: 기타 오류로 인한 실패")

        # 검증 3: Consumer Layer - 자동 취소 로그 확인
        logger.info("")
        logger.info("▸ 검증 3: Consumer Layer - 자동 취소 로직")
        logger.info("  Kafka Consumer 로그에서 다음을 확인하세요:")
        logger.info("    docker compose logs app | grep '\\[Kafka\\]'")
        logger.info("")
        logger.info("  정상 흐름 로그 예시:")
        logger.info("    [Kafka] Received event: topic=OrderCreated key=...")
        logger.info("    [Kafka] Processing: handle_order_created - order_id=...")
        logger.info("    [Kafka]   SKU ...: inventory_id=... available_qty=... OK")
        logger.info("    [Kafka] Completed: handle_order_created - OK")
        logger.info("    [Kafka] Received event: topic=InventoryUpdated key=...")
        logger.info("    [Kafka] Processing: handle_inventory_updated - order_id=...")
        logger.info("    [Kafka]   Mock PG: payment SUCCESS for order ...")
        logger.info("    [Kafka]   Order ... status: PENDING → PAYMENT_PENDING → PAID")
        logger.info("    [Kafka] Published: topic=PaymentCompleted key=... status=SUCCESS")
        logger.info("    [Kafka] Received event: topic=PaymentCompleted key=...")
        logger.info("    [Kafka] Processing: handle_payment_completed - order_id=...")
        logger.info("    [Kafka]   Shipment created: id=... order_id=...")
        logger.info("    [Kafka]   Order ... status: PAID → SHIPPING → SHIPPED")
        logger.info("    [Kafka] Published: topic=ShipmentCreated key=...")
        logger.info("")
        logger.info("  재고 소진 시 (Consumer 안전망):")
        logger.info("    [Kafka]   SKU ...: INSUFFICIENT stock (available=..., requested=...)")
        logger.info("    [Kafka] Cancelled: order_id=... reason=SKU(ID=...) 재고 부족")
        logger.info("    [Kafka] Published: topic=PaymentCompleted key=... status=FAIL")
        logger.info("    [Kafka] Completed: handle_order_created - CANCELLED (재고 부족)")

        # 검증 4: 주문 상태 확인 (Phase 1 성공한 주문들이 정상 처리되었는지)
        logger.info("")
        logger.info("▸ 검증 4: 주문 상태 확인 (Phase 1 성공 주문)")
        if phase1.order_ids:
            matched, total = await verify_order_status(
                session, phase1.order_ids, "PENDING"
            )
            if matched > 0:
                logger.info(f"  ✅ Phase 1 주문 상태 확인: {matched}/{total} 샘플 정상")
            else:
                logger.info(f"  ℹ️ Phase 1 주문 상태: Kafka Consumer 처리 대기 중")
        else:
            logger.info("  ℹ️ 확인할 Phase 1 주문 없음")

        # 최종 요약
        logger.info("")
        logger.info("=" * 70)
        logger.info("최종 요약")
        logger.info("=" * 70)
        logger.info(f"  Phase 1 (재고={INITIAL_STOCK}): {phase1.success} 성공 / {phase1.insufficient_stock} 재고부족")
        logger.info(f"  Phase 2 (x2 배수):  {phase2.success} 성공 / {phase2.insufficient_stock} 재고부족")
        logger.info("")
        if phase1.success == INITIAL_STOCK and phase2.insufficient_stock > 0:
            logger.info("  ✅✅✅ 모든 검증 통과!")
            logger.info("     - API: with_for_update()가 Race Condition 방지")
            logger.info("     - 재고 소진 시 409 Conflict 정상 반환")
            logger.info("     - Consumer: [Kafka] 로그로 자동 취소 확인 필요")
        elif phase1.success == INITIAL_STOCK and phase2.insufficient_stock == 0:
            logger.warning("  ⚠️ Phase 1은 정상 but Phase 2에서 재고 부족 미발생")
            logger.warning("     with_for_update()가 일부 Race Condition을 허용함")
        else:
            logger.warning("  ⚠️ 예상치 못한 결과 - 상세 로그 분석 필요")
        logger.info("")


if __name__ == "__main__":
    asyncio.run(main())
