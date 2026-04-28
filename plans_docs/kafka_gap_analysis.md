# Kafka 적용 Gap 분석

## 설계 문서 vs 현재 구현

### 설계 문서(`reference_docs/coding_convention.md`)가 명시하는 Kafka 요구사항

| 항목 | 설계 요구사항 | 현재 구현 상태 |
|------|--------------|---------------|
| **기술 스택** (§1.2) | MQ: Kafka | ❌ 미적용 |
| **시스템 구성** (§1.1) | Client → ... → App → DB / Redis / Kafka / Elasticsearch | ❌ Kafka 빠짐 |
| **Search** (§2.10) | DB → Kafka → Elasticsearch (역정규화) | ❌ 직접 DB 쿼리 |
| **이벤트 스펙** (§4) | `OrderCreated`, `PaymentCompleted` JSON 스펙 정의 | ❌ 미구현 |
| **Kafka 토픽** (§7) | `OrderCreated`, `PaymentCompleted`, `InventoryUpdated`, `ShipmentCreated` | ❌ 토픽 미생성 |
| **장애 대응** (§8) | Retry + DLQ, Idempotency, Circuit Breaker | ❌ 미구현 |

### 현재 주문 생성 흐름 (동기식)

```
Client → POST /api/v1/orders
  → OrderHeader/OrderItem DB INSERT
  → InventoryReservation DB INSERT
  → Response 반환 (200 OK)
```

### 설계에서 요구하는 이벤트 기반 흐름

```
Client → POST /api/v1/orders
  → OrderHeader/OrderItem DB INSERT
  → Kafka: OrderCreated (event 발행)
  → Response 반환 (202 Accepted)
  
[Consumer] OrderCreated 수신
  → Inventory 서비스: 재고 예약
  → Kafka: InventoryUpdated (event 발행)
  
[Consumer] InventoryUpdated 수신  
  → Payment 서비스: 결제 요청
  → Kafka: PaymentCompleted (event 발행)

[Consumer] PaymentCompleted 수신
  → Shipment 서비스: 배송 생성
  → Kafka: ShipmentCreated (event 발행)
```

## 적용 안된 원인 분석

### 1. 인프라는 준비됨
- `docker-compose.yml`에 **Kafka 컨테이너** 정의됨
- `config.py`에 `KAFKA_BOOTSTRAP_SERVERS` 환경변수 설정됨

### 2. 런타임 의존성 누락
- `requirements.txt`에 **Kafka 클라이언트 라이브러리 없음**
  - 필요: `aiokafka` 또는 `confluent-kafka`

### 3. 애플리케이션 코드 누락
- Kafka **Producer 계층** 없음 (이벤트 발행 코드)
- Kafka **Consumer 계층** 없음 (이벤트 구독 코드)
- Kafka **설정/유틸리티 모듈** 없음
- **이벤트 스키마** 정의 없음
- **재시도/데드레터 큐/멱등성** 로직 없음

### 4. 현재 구현이 동기식 REST에 집중됨
- DB CRUD 중심 구현 완료 (Model, Schema, Router, CRUD)
- 테스트 269개 통과
- 이벤트 기반 아키텍처는 아직 개발되지 않은 상태

## 적용을 위한 필요 작업

| 단계 | 작업 | 상세 |
|------|------|------|
| 1 | Kafka 클라이언트 추가 | `aiokafka` 또는 `confluent-kafka`를 requirements.txt에 추가 |
| 2 | Kafka 설정 모듈 | Producer/Consumer 팩토리, 시리얼라이저 |
| 3 | 이벤트 스키마 | 각 토픽별 Pydantic 이벤트 모델 정의 |
| 4 | Producer 계층 | OrderCreated, PaymentCompleted, InventoryUpdated, ShipmentCreated 발행 |
| 5 | Consumer 계층 | 각 이벤트 구독 및 핸들러 (order → inventory → payment → shipment) |
| 6 | 재시도/DLQ | 실패 시 재시도 로직 및 데드레터 큐 |
| 7 | 멱등성 보장 | 멱등성 키 기반 중복 이벤트 처리 |
| 8 | 트랜잭셔널 아웃박스 | DB 트랜잭션과 Kafka 발행 간 원자성 보장 |
