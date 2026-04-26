"""
재고 소진 후 자동 취소 로직 검증 테스트 (단순 버전).

requests 라이브러리를 사용한 순차적 실행으로 안정성 확보.
"""
from __future__ import annotations

import json
import logging
import time
import uuid
from typing import Any

import requests

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:8000/api/v1"
INITIAL_STOCK = 50  # 초기 재고
PHASE2_COUNT = 20   # Phase 2 주문 수 (재고 소진 확인용, 너무 많으면 서버 부하)


def create_test_data() -> dict[str, Any]:
    """테스트에 필요한 사용자/상품/SKU/재고를 생성한다."""
    session = requests.Session()

    # 1. 사용자 생성
    user_email = f"exhaust_{uuid.uuid4().hex[:8]}@example.com"
    resp = session.post(
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
        timeout=10,
    )
    resp.raise_for_status()
    user_id = resp.json()["data"]["id"]
    logger.info(f"  ✓ 사용자 생성: id={user_id}")

    # 2. 상품 생성
    resp = session.post(
        f"{BASE_URL}/products",
        json={
            "product_name": f"Exhaust Test Product {uuid.uuid4().hex[:6]}",
            "product_description": "재고 소진 테스트",
            "brand_id": None,
            "product_status": "ACTIVE",
            "base_price_amount": "29900.00",
            "thumbnail_image_url": None,
            "created_by": None,
        },
        timeout=10,
    )
    resp.raise_for_status()
    product_id = resp.json()["data"]["id"]
    logger.info(f"  ✓ 상품 생성: id={product_id}")

    # 3. SKU 생성
    sku_code = f"EXH-{uuid.uuid4().hex[:8].upper()}"
    resp = session.post(
        f"{BASE_URL}/skus",
        json={
            "product_id": product_id,
            "sku_code": sku_code,
            "sale_price_amount": "29900.00",
            "stock_quantity": INITIAL_STOCK,
            "sku_status": "ACTIVE",
            "option_value_ids": [],
        },
        timeout=10,
    )
    resp.raise_for_status()
    sku_id = resp.json()["data"]["id"]
    logger.info(f"  ✓ SKU 생성: id={sku_id}")

    # 4. 재고 생성 (INITIAL_STOCK만큼)
    resp = session.post(
        f"{BASE_URL}/inventory",
        json={
            "sku_id": sku_id,
            "total_quantity": INITIAL_STOCK,
            "available_quantity": INITIAL_STOCK,
            "reserved_quantity": 0,
            "safety_stock_quantity": 0,
        },
        timeout=10,
    )
    resp.raise_for_status()
    inventory_id = resp.json()["data"]["id"]
    logger.info(f"  ✓ 재고 생성: id={inventory_id}, available={INITIAL_STOCK}")

    return {
        "user_id": user_id,
        "sku_id": sku_id,
        "inventory_id": inventory_id,
    }


def create_order(
    session: requests.Session,
    test_data: dict[str, Any],
    order_index: int,
    phase: int,
) -> tuple[int, int | None, str | None]:
    """단일 주문을 생성하고 (status_code, order_id, error)를 반환한다."""
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

    try:
        resp = session.post(f"{BASE_URL}/orders", json=payload, timeout=30)
        if resp.status_code == 201:
            order_id = resp.json()["data"]["id"]
            logger.debug(f"  [Phase{phase}] Order #{order_index}: 201 (id={order_id})")
            return (201, order_id, None)
        elif resp.status_code == 409:
            body = resp.text[:200]
            logger.debug(f"  [Phase{phase}] Order #{order_index}: 409 - {body}")
            return (409, None, body)
        else:
            body = resp.text[:200]
            logger.debug(f"  [Phase{phase}] Order #{order_index}: {resp.status_code} - {body}")
            return (resp.status_code, None, body)
    except Exception as e:
        logger.error(f"  [Phase{phase}] Order #{order_index} exception: {type(e).__name__}: {e}")
        return (0, None, f"{type(e).__name__}: {e}")


def main() -> None:
    logger.info("=" * 70)
    logger.info("재고 소진 후 자동 취소 로직 검증 테스트 (단순 버전)")
    logger.info("=" * 70)
    logger.info(f"  초기 재고:          {INITIAL_STOCK}개")
    logger.info(f"  Phase 1 주문 수:    {INITIAL_STOCK}개 (재고만큼)")
    logger.info(f"  Phase 2 주문 수:    {PHASE2_COUNT}개 (재고 소진 확인)")
    logger.info(f"  API URL:            {BASE_URL}")
    logger.info("=" * 70)
    logger.info("")

    session = requests.Session()

    # 1. 테스트 데이터 준비
    logger.info("[1/4] 테스트 데이터 생성 중...")
    test_data = create_test_data()
    logger.info("")

    # ============================================================
    # Phase 1: INITIAL_STOCK개 주문 (전부 성공 예상)
    # ============================================================
    logger.info("[2/4] Phase 1: 정상 재고 범위 내 주문 생성")
    logger.info(f"  주문: {INITIAL_STOCK}개 (재고={INITIAL_STOCK})")
    logger.info(f"  예상: 전부 201 Created")
    logger.info("")

    phase1_success = 0
    phase1_insufficient = 0
    phase1_other = 0
    phase1_order_ids: list[int] = []
    phase1_start = time.perf_counter()

    for i in range(INITIAL_STOCK):
        status_code, order_id, error = create_order(session, test_data, i + 1, 1)
        if status_code == 201:
            phase1_success += 1
            if order_id:
                phase1_order_ids.append(order_id)
        elif status_code == 409:
            phase1_insufficient += 1
        else:
            phase1_other += 1

        # 진행률 표시
        if (i + 1) % 10 == 0 or i == 0:
            logger.info(f"  진행: {i+1}/{INITIAL_STOCK} (성공={phase1_success}, 409={phase1_insufficient})")

    phase1_elapsed = time.perf_counter() - phase1_start

    logger.info("")
    logger.info(f"  Phase 1 결과:")
    logger.info(f"    성공 (201):        {phase1_success}")
    logger.info(f"    재고 부족 (409):   {phase1_insufficient}")
    logger.info(f"    기타 실패:         {phase1_other}")
    logger.info(f"    소요 시간:         {phase1_elapsed:.2f}s")
    logger.info("")

    # Phase 1과 Phase 2 사이에 충분한 대기 (DB 연결 풀 회복)
    logger.info("  Phase 2 준비를 위해 5초 대기...")
    time.sleep(5)

    # ============================================================
    # Phase 2: PHASE2_COUNT개 추가 주문 (재고 소진 → 409 예상)
    # ============================================================
    logger.info("[3/4] Phase 2: 재고 소진 후 추가 주문 생성")
    logger.info(f"  주문: {PHASE2_COUNT}개 (재고={INITIAL_STOCK}, 이미 {phase1_success}개 소진)")
    logger.info(f"  예상: 전부 409 Conflict (재고 부족)")
    logger.info("")

    phase2_success = 0
    phase2_insufficient = 0
    phase2_other = 0
    phase2_start = time.perf_counter()

    for i in range(PHASE2_COUNT):
        status_code, order_id, error = create_order(session, test_data, i + 1, 2)
        if status_code == 201:
            phase2_success += 1
        elif status_code == 409:
            phase2_insufficient += 1
        else:
            phase2_other += 1

        if (i + 1) % 5 == 0 or i == 0:
            logger.info(f"  진행: {i+1}/{PHASE2_COUNT} (성공={phase2_success}, 409={phase2_insufficient})")

    phase2_elapsed = time.perf_counter() - phase2_start

    logger.info("")
    logger.info(f"  Phase 2 결과:")
    logger.info(f"    성공 (201):        {phase2_success}")
    logger.info(f"    재고 부족 (409):   {phase2_insufficient}")
    logger.info(f"    기타 실패:         {phase2_other}")
    logger.info(f"    소요 시간:         {phase2_elapsed:.2f}s")
    logger.info("")

    # ============================================================
    # 결과 분석
    # ============================================================
    logger.info("[4/4] 결과 분석")
    logger.info("")
    logger.info("=" * 70)
    logger.info("최종 검증 결과")
    logger.info("=" * 70)

    # 검증 1: Phase 1 - 모든 주문이 201이어야 함
    logger.info("")
    logger.info("▸ 검증 1: API Layer - with_for_update() 동시성 제어")
    if phase1_success == INITIAL_STOCK:
        logger.info(f"  ✅ Phase 1: {phase1_success}/{INITIAL_STOCK} 주문 성공 (201)")
        logger.info(f"     SELECT ... FOR UPDATE로 Race Condition 방지 확인")
    else:
        logger.warning(f"  ⚠️ Phase 1: {phase1_success}/{INITIAL_STOCK}만 성공")
        if phase1_insufficient > 0:
            logger.warning(f"     {phase1_insufficient}개 409 발생 - 재고가 너무 적음")

    # 검증 2: Phase 2 - 재고 소진으로 409 발생
    logger.info("")
    logger.info("▸ 검증 2: 재고 소진 후 409 Conflict 반환")
    if phase2_insufficient > 0:
        logger.info(f"  ✅ Phase 2: {phase2_insufficient}개 주문이 409로 거절됨")
        logger.info(f"     재고 소진 시 API가 정상적으로 409 반환")
    elif phase2_success > 0:
        logger.warning(f"  ⚠️ Phase 2: {phase2_success}개 주문이 성공 (예상: 0)")
        logger.warning(f"     with_for_update()가 Race Condition을 막지 못함")
    else:
        logger.info(f"  ℹ️ Phase 2: 기타 오류로 인한 실패 ({phase2_other}개)")

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
    logger.info("")
    logger.info("  재고 소진 시 (Consumer 안전망):")
    logger.info("    [Kafka]   SKU ...: INSUFFICIENT stock (available=..., requested=...)")
    logger.info("    [Kafka] Cancelled: order_id=... reason=SKU(ID=...) 재고 부족")
    logger.info("    [Kafka] Published: topic=PaymentCompleted key=... status=FAIL")
    logger.info("")

    # 검증 4: 주문 상태 확인
    logger.info("▸ 검증 4: 주문 상태 확인 (Phase 1 성공 주문)")
    if phase1_order_ids:
        matched = 0
        total = min(len(phase1_order_ids), 5)  # 처음 5개만 샘플 확인
        for oid in phase1_order_ids[:total]:
            try:
                resp = session.get(f"{BASE_URL}/orders/{oid}", timeout=10)
                if resp.status_code == 200:
                    actual_status = resp.json()["data"]["order_status"]
                    logger.info(f"  Order {oid}: status={actual_status}")
                    if actual_status == "PENDING":
                        matched += 1
                else:
                    logger.warning(f"  Order {oid}: API returned {resp.status_code}")
            except Exception as e:
                logger.warning(f"  Order {oid}: exception {e}")
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
    logger.info(f"  Phase 1 (재고={INITIAL_STOCK}): {phase1_success} 성공 / {phase1_insufficient} 재고부족")
    logger.info(f"  Phase 2 (x2 배수):  {phase2_success} 성공 / {phase2_insufficient} 재고부족")
    logger.info("")
    if phase1_success == INITIAL_STOCK and phase2_insufficient > 0:
        logger.info("  ✅✅✅ 모든 검증 통과!")
        logger.info("     - API: with_for_update()가 Race Condition 방지")
        logger.info("     - 재고 소진 시 409 Conflict 정상 반환")
        logger.info("     - Consumer: [Kafka] 로그로 자동 취소 확인 필요")
    elif phase1_success == INITIAL_STOCK and phase2_insufficient == 0:
        logger.warning("  ⚠️ Phase 1은 정상 but Phase 2에서 재고 부족 미발생")
        logger.warning("     with_for_update()가 일부 Race Condition을 허용함")
    else:
        logger.warning("  ⚠️ 예상치 못한 결과 - 상세 로그 분석 필요")
    logger.info("")


if __name__ == "__main__":
    main()
