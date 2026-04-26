# 🛒 E-Commerce API

**FastAPI 기반의 확장 가능한 이커머스 백엔드 시스템**  
SQLAlchemy 2.0 ORM과 PostgreSQL을 중심으로 11개 도메인(상품, 회원, 장바구니, 주문, 결제, 재고, 배송, 프로모션, 리뷰, 검색, 관리자)을 완전한 RESTful API로 제공합니다.

---

## 🚀 기술 스택

| 계층 | 기술 |
|------|------|
| **웹 프레임워크** | [FastAPI](https://fastapi.tiangolo.com/) 0.115 |
| **ORM** | [SQLAlchemy](https://www.sqlalchemy.org/) 2.0 (비동기 미사용, sync ORM) |
| **스키마/검증** | [Pydantic](https://docs.pydantic.dev/) v2 + [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) |
| **데이터베이스** | PostgreSQL 15 |
| **인증** | JWT ([python-jose](https://github.com/mpdavis/python-jose) + [passlib](https://passlib.readthedocs.io/) bcrypt) |
| **캐시** | Redis 7 |
| **메시지 브로커** | Apache Kafka (Confluent 7.6) |
| **검색 엔진** | Elasticsearch 8.13 |
| **컨테이너** | Docker + Docker Compose |
| **테스트** | pytest, HTTPX (TestClient) |

---

## 📁 디렉토리 구조

```
workspace/
├── app/
│   ├── __init__.py
│   ├── main.py                  # FastAPI 애플리케이션 진입점
│   ├── database.py              # SQLAlchemy 엔진, 세션 팩토리, Base
│   ├── dependencies.py          # 공통 의존성 (get_db, get_current_user)
│   ├── core/
│   │   ├── config.py            # Pydantic Settings (환경 변수 관리)
│   │   ├── exceptions.py        # 공통 예외 클래스 및 핸들러
│   │   └── security.py          # JWT 생성/검증, bcrypt 해싱
│   ├── models/                  # SQLAlchemy ORM 모델 (11개 도메인)
│   │   ├── product.py
│   │   ├── user.py
│   │   ├── cart.py
│   │   ├── order.py
│   │   ├── payment.py
│   │   ├── inventory.py
│   │   ├── shipment.py
│   │   ├── promotion.py
│   │   ├── review.py
│   │   ├── search.py
│   │   └── admin.py
│   ├── schemas/                 # Pydantic 요청/응답 스키마
│   │   ├── __init__.py          # 공통 APIResponse, ORMBaseSchema
│   │   └── (도메인별 스키마)
│   ├── routers/                 # API 엔드포인트 (prefix + tags)
│   │   ├── __init__.py          # api_router 집계 + /health
│   │   └── (도메인별 라우터)
│   ├── crud/                    # 데이터 접근 계층 (선택적 사용)
│   └── utils/                   # 유틸리티 함수
├── tests/
│   ├── conftest.py              # 통합 테스트 Fixture (PostgreSQL TestContainer)
│   ├── unit/                    # 단위 테스트 (도메인별 + core)
│   │   ├── test_product_domain.py
│   │   ├── test_user_domain.py
│   │   ├── test_cart_domain.py
│   │   ├── test_order_domain.py
│   │   ├── test_payment_domain.py
│   │   ├── test_inventory_domain.py
│   │   ├── test_shipment_domain.py
│   │   ├── test_promotion_domain.py
│   │   ├── test_review_domain.py
│   │   ├── test_search_domain.py
│   │   ├── test_admin_domain.py
│   │   └── core/
│   │       ├── test_config.py
│   │       ├── test_database.py
│   │       ├── test_dependencies.py
│   │       ├── test_exceptions.py
│   │       ├── test_main.py
│   │       ├── test_security.py
│   │       └── test_utils.py
│   └── integration/             # 통합 테스트 (HTTP API)
│       ├── test_product_api.py
│       ├── test_user_api.py
│       ├── test_cart_api.py
│       └── test_order_api.py
├── .env                         # 환경 변수
├── Dockerfile                   # 애플리케이션 컨테이너 이미지
├── docker-compose.yml           # 전체 인프라 구성
└── requirements.txt             # Python 의존성
```

---

## 🛠️ 설치 및 실행 가이드

### 1. 사전 요구 사항

- Python 3.11+
- Docker & Docker Compose (권장)
- PostgreSQL 15 (로컬 실행 시)

### 2. 로컬 개발 환경 (가상환경)

```bash
# 저장소 클론
git clone <repository-url>
cd workspace

# 가상환경 생성 및 활성화
python3.11 -m venv venv
source venv/bin/activate

# 의존성 설치
pip install --upgrade pip
pip install -r requirements.txt

# 환경 변수 설정
cp .env .env.local
# .env.local 파일을 편집하여 POSTGRES_SERVER=localhost 등으로 변경
```

### 3. Docker Compose 실행 (권장)

```bash
cd workspace

# 전체 인프라 + 애플리케이션 실행
docker compose up -d

# 로그 확인
docker compose logs -f app
```

실행되는 서비스:

| 서비스 | 포트 | 비고 |
|--------|------|------|
| `app` (FastAPI) | `8000` | 메인 애플리케이션 |
| `postgres` | `5432` | PostgreSQL 15 |
| `redis` | `6379` | Redis 7 |
| `kafka` | `9092` | Apache Kafka |
| `elasticsearch` | `9200` | Elasticsearch 8.13 |

### 4. API 문서 확인

서비스 실행 후 브라우저에서 접속:

- **Swagger UI**: [`http://localhost:8000/docs`](http://localhost:8000/docs)
- **ReDoc**: [`http://localhost:8000/redoc`](http://localhost:8000/redoc)
- **OpenAPI JSON**: [`http://localhost:8000/api/v1/openapi.json`](http://localhost:8000/api/v1/openapi.json)

### 5. 환경 변수 (.env)

| 변수명 | 기본값 | 설명 |
|--------|--------|------|
| `PROJECT_NAME` | `E-Commerce API` | 프로젝트명 |
| `APP_VERSION` | `0.1.0` | 애플리케이션 버전 |
| `DEBUG` | `true` | 디버그 모드 |
| `API_V1_PREFIX` | `/api/v1` | API 버전 prefix |
| `DB_SCHEMA` | `ecommerce` | PostgreSQL 스키마 |
| `POSTGRES_SERVER` | `postgres` | DB 호스트 |
| `POSTGRES_PORT` | `5432` | DB 포트 |
| `POSTGRES_USER` | `postgres` | DB 사용자 |
| `POSTGRES_PASSWORD` | `your-password` | DB 비밀번호 |
| `POSTGRES_DB` | `ecommerce` | DB 이름 |
| `SECRET_KEY` | `change-this-secret-key` | JWT 서명 키 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | JWT 만료 시간 |
| `REDIS_URL` | `redis://redis:6379/0` | Redis 연결 문자열 |
| `KAFKA_BOOTSTRAP_SERVERS` | `kafka:9092` | Kafka 브로커 |
| `ELASTICSEARCH_URL` | `http://elasticsearch:9200` | Elasticsearch URL |

---

## 📖 API 명세

모든 엔드포인트는 [`/api/v1`](workspace/app/core/config.py:20) prefix 아래에 위치합니다.

### 🔹 시스템

| Method | URL | 설명 |
|--------|-----|------|
| `GET` | `/api/v1/health` | 헬스 체크 |

### 🔹 상품 (Products)

| Method | URL | 설명 |
|--------|-----|------|
| `GET` | `/api/v1/products` | 상품 목록 조회 (페이징, 상태 필터) |
| `GET` | `/api/v1/products/{product_id}` | 상품 상세 조회 |
| `POST` | `/api/v1/products` | 상품 생성 |
| `PUT` | `/api/v1/products/{product_id}` | 상품 수정 |
| `DELETE` | `/api/v1/products/{product_id}` | 상품 소프트 삭제 |

### 🔹 회원 (Users)

| Method | URL | 설명 |
|--------|-----|------|
| `GET` | `/api/v1/users` | 회원 목록 조회 (페이징, 상태/타입 필터) |
| `GET` | `/api/v1/users/{user_id}` | 회원 상세 조회 |
| `POST` | `/api/v1/users` | 회원 생성 |
| `PUT` | `/api/v1/users/{user_id}` | 회원 수정 |
| `DELETE` | `/api/v1/users/{user_id}` | 회원 소프트 삭제 |

### 🔹 장바구니 (Carts)

| Method | URL | 설명 |
|--------|-----|------|
| `GET` | `/api/v1/carts` | 장바구니 목록 조회 |
| `GET` | `/api/v1/carts/{cart_id}` | 장바구니 상세 조회 |
| `POST` | `/api/v1/carts` | 장바구니 생성 |
| `PUT` | `/api/v1/carts/{cart_id}` | 장바구니 수정 |
| `DELETE` | `/api/v1/carts/{cart_id}` | 장바구니 소프트 삭제 |
| `GET` | `/api/v1/carts/{cart_id}/items` | 장바구니 상품 목록 조회 |
| `POST` | `/api/v1/carts/{cart_id}/items` | 장바구니 상품 추가 |
| `PUT` | `/api/v1/carts/{cart_id}/items/{item_id}` | 장바구니 상품 수정 |
| `DELETE` | `/api/v1/carts/{cart_id}/items/{item_id}` | 장바구니 상품 삭제 |

### 🔹 주문 (Orders)

| Method | URL | 설명 |
|--------|-----|------|
| `GET` | `/api/v1/orders` | 주문 목록 조회 (사용자/상태 필터) |
| `GET` | `/api/v1/orders/{order_id}` | 주문 상세 조회 |
| `POST` | `/api/v1/orders` | 주문 생성 (상품 + 상태 이력 포함) |
| `PUT` | `/api/v1/orders/{order_id}` | 주문 수정 (상태 변경 시 이력 기록) |
| `DELETE` | `/api/v1/orders/{order_id}` | 주문 소프트 삭제 |

### 🔹 결제 (Payments)

| Method | URL | 설명 |
|--------|-----|------|
| `GET` | `/api/v1/payments` | 결제 목록 조회 (상태/주문 필터) |
| `GET` | `/api/v1/payments/{payment_id}` | 결제 상세 조회 |
| `POST` | `/api/v1/payments` | 결제 생성 |
| `PUT` | `/api/v1/payments/{payment_id}` | 결제 수정 |
| `DELETE` | `/api/v1/payments/{payment_id}` | 결제 소프트 삭제 |

### 🔹 재고 (Inventory)

| Method | URL | 설명 |
|--------|-----|------|
| `GET` | `/api/v1/inventory` | 재고 목록 조회 (SKU 필터) |
| `GET` | `/api/v1/inventory/{inventory_id}` | 재고 상세 조회 |
| `POST` | `/api/v1/inventory` | 재고 생성 (SKU 중복 검사) |
| `PUT` | `/api/v1/inventory/{inventory_id}` | 재고 수정 |
| `DELETE` | `/api/v1/inventory/{inventory_id}` | 재고 삭제 |
| `POST` | `/api/v1/inventory/reservations` | 재고 예약 생성 (가용 수량 검증) |
| `GET` | `/api/v1/inventory/reservations/{reservation_id}` | 재고 예약 상세 조회 |
| `GET` | `/api/v1/inventory/transactions` | 재고 변동 이력 조회 |

### 🔹 배송 (Shipments)

| Method | URL | 설명 |
|--------|-----|------|
| `GET` | `/api/v1/shipments` | 배송 목록 조회 |
| `GET` | `/api/v1/shipments/{shipment_id}` | 배송 상세 조회 |
| `POST` | `/api/v1/shipments` | 배송 생성 |
| `PUT` | `/api/v1/shipments/{shipment_id}` | 배송 수정 |
| `DELETE` | `/api/v1/shipments/{shipment_id}` | 배송 소프트 삭제 |
| `GET` | `/api/v1/shipments/{shipment_id}/items` | 배송 상품 목록 조회 |
| `POST` | `/api/v1/shipments/{shipment_id}/items` | 배송 상품 생성 |
| `PUT` | `/api/v1/shipments/{shipment_id}/items/{item_id}` | 배송 상품 수정 |
| `DELETE` | `/api/v1/shipments/{shipment_id}/items/{item_id}` | 배송 상품 소프트 삭제 |
| `GET` | `/api/v1/warehouses` | 창고 목록 조회 |
| `GET` | `/api/v1/warehouses/{warehouse_id}` | 창고 상세 조회 |
| `POST` | `/api/v1/warehouses` | 창고 생성 |
| `PUT` | `/api/v1/warehouses/{warehouse_id}` | 창고 수정 |

### 🔹 프로모션 (Promotions)

| Method | URL | 설명 |
|--------|-----|------|
| `GET` | `/api/v1/promotions` | 프로모션 목록 조회 (활성/타입 필터) |
| `GET` | `/api/v1/promotions/{promotion_id}` | 프로모션 상세 조회 |
| `POST` | `/api/v1/promotions` | 프로모션 생성 |
| `PUT` | `/api/v1/promotions/{promotion_id}` | 프로모션 수정 |
| `DELETE` | `/api/v1/promotions/{promotion_id}` | 프로모션 소프트 삭제 |

### 🔹 리뷰 (Reviews)

| Method | URL | 설명 |
|--------|-----|------|
| `GET` | `/api/v1/reviews` | 리뷰 목록 조회 (상품/사용자/상태 필터) |
| `GET` | `/api/v1/reviews/{review_id}` | 리뷰 상세 조회 |
| `POST` | `/api/v1/reviews` | 리뷰 생성 |
| `PUT` | `/api/v1/reviews/{review_id}` | 리뷰 수정 |
| `DELETE` | `/api/v1/reviews/{review_id}` | 리뷰 논리 삭제 |

### 🔹 검색 (Search)

| Method | URL | 설명 |
|--------|-----|------|
| `GET` | `/api/v1/search/products` | 검색 인덱스 목록 조회 |
| `GET` | `/api/v1/search/products/{product_id}` | 검색 인덱스 상세 조회 |
| `POST` | `/api/v1/search/products` | 검색 인덱스 생성 |
| `PUT` | `/api/v1/search/products/{product_id}` | 검색 인덱스 수정 |
| `DELETE` | `/api/v1/search/products/{product_id}` | 검색 인덱스 삭제 |
| `GET` | `/api/v1/search/keywords` | 검색 키워드 목록 조회 |
| `GET` | `/api/v1/search/keywords/{keyword}` | 검색 키워드 상세 조회 |
| `POST` | `/api/v1/search/keywords` | 검색 키워드 생성 |
| `PUT` | `/api/v1/search/keywords/{keyword}` | 검색 키워드 수정 |
| `DELETE` | `/api/v1/search/keywords/{keyword}` | 검색 키워드 삭제 |
| `GET` | `/api/v1/search/autocomplete` | 자동완성 목록 조회 |
| `GET` | `/api/v1/search/autocomplete/{id}` | 자동완성 상세 조회 |
| `POST` | `/api/v1/search/autocomplete` | 자동완성 생성 |
| `PUT` | `/api/v1/search/autocomplete/{id}` | 자동완성 수정 |
| `DELETE` | `/api/v1/search/autocomplete/{id}` | 자동완성 삭제 |
| `GET` | `/api/v1/search/synonyms` | 동의어 목록 조회 |
| `GET` | `/api/v1/search/synonyms/{id}` | 동의어 상세 조회 |
| `POST` | `/api/v1/search/synonyms` | 동의어 생성 |
| `PUT` | `/api/v1/search/synonyms/{id}` | 동의어 수정 |
| `DELETE` | `/api/v1/search/synonyms/{id}` | 동의어 삭제 |

### 🔹 관리자 (Admin)

| Method | URL | 설명 |
|--------|-----|------|
| `GET` | `/api/v1/admin/accounts` | 관리자 계정 목록 조회 |
| `GET` | `/api/v1/admin/accounts/{admin_id}` | 관리자 계정 상세 조회 |
| `POST` | `/api/v1/admin/accounts` | 관리자 계정 생성 |
| `PUT` | `/api/v1/admin/accounts/{admin_id}` | 관리자 계정 수정 |
| `DELETE` | `/api/v1/admin/accounts/{admin_id}` | 관리자 계정 소프트 삭제 |
| `GET` | `/api/v1/admin/roles` | 관리자 역할 목록 조회 |
| `GET` | `/api/v1/admin/permissions` | 권한 목록 조회 |

---

## 🧪 테스트 실행

### 단위 테스트 (Unit Tests)

```bash
cd workspace

# 전체 단위 테스트 실행
pytest tests/unit/ -v

# 특정 도메인 테스트
pytest tests/unit/test_product_domain.py -v
pytest tests/unit/test_user_domain.py -v

# Core 모듈 테스트
pytest tests/unit/core/ -v
```

### 통합 테스트 (Integration Tests)

통합 테스트는 실제 PostgreSQL 데이터베이스(`ecommerce_test`)가 필요합니다.  
Docker Compose로 PostgreSQL을 먼저 실행한 후 테스트를 수행하세요.

```bash
# PostgreSQL 컨테이너 실행
docker compose up -d postgres

# 통합 테스트 실행
pytest tests/integration/ -v

# 특정 API 테스트
pytest tests/integration/test_product_api.py -v
pytest tests/integration/test_user_api.py -v
pytest tests/integration/test_cart_api.py -v
pytest tests/integration/test_order_api.py -v
```

### 테스트 커버리지 확인

```bash
pytest --cov=app tests/ -v
```

---

## 🏗️ 아키텍처 개요

이 프로젝트는 **레이어드 아키텍처(Layered Architecture)** 를 따릅니다.

```
┌─────────────────────────────────────────────┐
│              Routers (API 계층)              │
│  요청/응답 처리, 입력 검증, HTTP 상태 코드    │
├─────────────────────────────────────────────┤
│              Schemas (검증 계층)              │
│  Pydantic 모델: 요청 바디 검증, 응답 직렬화   │
├─────────────────────────────────────────────┤
│              Models (ORM 계층)               │
│  SQLAlchemy 2.0: 테이블 매핑, 관계 정의      │
├─────────────────────────────────────────────┤
│              Database (영속성 계층)           │
│  엔진/세션 관리, Connection Pooling          │
└─────────────────────────────────────────────┘
```

- **Routers** → `app/routers/` — HTTP 엔드포인트 정의, 의존성 주입
- **Schemas** → `app/schemas/` — Pydantic v2 기반 요청/응답 스키마
- **Models** → `app/models/` — SQLAlchemy 2.0 ORM 모델
- **Core** → `app/core/` — 설정, 보안, 예외 처리 공통 모듈
- **Tests** → `tests/unit/` + `tests/integration/` — 단위/통합 테스트 분리

### 공통 응답 포맷

모든 API는 [`APIResponse[T]`](workspace/app/schemas/__init__.py:25) 제네릭 래퍼로 응답합니다.

```json
{
  "success": true,
  "message": "요청이 성공했습니다.",
  "data": { ... }
}
```

### 예외 처리

- [`ApplicationException`](workspace/app/core/exceptions.py:5) — 커스텀 예외 베이스 클래스
- [`ResourceNotFoundException`](workspace/app/core/exceptions.py:14) — 404 응답
- 전역 예외 핸들러가 등록되어 있어 처리되지 않은 예외도 일관된 JSON 포맷으로 응답

### 인증

- JWT 기반 인증 ([`get_current_user`](workspace/app/dependencies.py:21) 의존성)
- bcrypt 비밀번호 해싱 ([`security.py`](workspace/app/core/security.py))
- Bearer 토큰 방식 (`HTTPBearer`)

---

## 📄 라이선스

이 프로젝트는 학습 및 참고 용도로 제공됩니다.
