# Frontend Blueprint — E-Commerce API

> **작성일**: 2026-04-24  
> **대상**: FastAPI 백엔드 (`/api/v1`)  
> **목적**: 프론트엔드 개발자가 백엔드 API를 기반으로 즉시 개발을 시작할 수 있도록 화면(페이지)과 기능을 정의합니다.

---

## 목차

1. [아키텍처 개요](#1-아키텍처-개요)
2. [페이지 목록](#2-페이지-목록)
3. [상세 페이지 명세](#3-상세-페이지-명세)
   - 3.1 [홈 / 랜딩 페이지](#31-홈--랜딩-페이지)
   - 3.2 [상품 목록 페이지](#32-상품-목록-페이지)
   - 3.3 [상품 상세 페이지](#33-상품-상세-페이지)
   - 3.4 [장바구니 페이지](#34-장바구니-페이지)
   - 3.5 [주문/결제 페이지](#35-주문결제-페이지)
   - 3.6 [주문 내역 페이지](#36-주문-내역-페이지)
   - 3.7 [주문 상세 페이지](#37-주문-상세-페이지)
   - 3.8 [배송 조회 페이지](#38-배송-조회-페이지)
   - 3.9 [리뷰 페이지](#39-리뷰-페이지)
   - 3.10 [마이페이지 (회원 정보)](#310-마이페이지-회원-정보)
   - 3.11 [로그인 / 회원가입](#311-로그인--회원가입)
   - 3.12 [검색 페이지](#312-검색-페이지)
   - 3.13 [관리자 대시보드](#313-관리자-대시보드)
   - 3.14 [관리자: 상품 관리](#314-관리자-상품-관리)
   - 3.15 [관리자: 주문 관리](#315-관리자-주문-관리)
   - 3.16 [관리자: 회원 관리](#316-관리자-회원-관리)
   - 3.17 [관리자: 프로모션 관리](#317-관리자-프로모션-관리)
   - 3.18 [관리자: 재고 관리](#318-관리자-재고-관리)
   - 3.19 [관리자: 배송 관리](#319-관리자-배송-관리)
   - 3.20 [관리자: 결제 관리](#320-관리자-결제-관리)
   - 3.21 [관리자: 리뷰 관리](#321-관리자-리뷰-관리)
   - 3.22 [관리자: 검색/동의어 관리](#322-관리자-검색동의어-관리)
   - 3.23 [관리자: 관리자 계정 관리](#323-관리자-관리자-계정-관리)
4. [공통 사항](#4-공통-사항)

---

## 1. 아키텍처 개요

```
[프론트엔드 SPA]  ─── HTTP ───>  [FastAPI Backend (/api/v1)]
                                      │
                                      ├── users         (회원)
                                      ├── products      (상품)
                                      ├── carts         (장바구니)
                                      ├── orders        (주문)
                                      ├── payments      (결제)
                                      ├── inventory     (재고)
                                      ├── shipments     (배송)
                                      ├── promotions    (프로모션)
                                      ├── reviews       (리뷰)
                                      ├── search        (검색)
                                      └── admin         (관리자)
```

- **Base URL**: `/api/v1`
- **인증 방식**: JWT Bearer Token (`Authorization: Bearer <token>`)
- **공통 응답 형식**: `APIResponse<T>` = `{ "data": T, "message": string }`
- **페이지네이션**: 모든 목록 조회는 `skip`(offset)과 `limit`(default 20, max 100) 쿼리 파라미터 사용

---

## 2. 페이지 목록

| # | 페이지 | URL path (제안) | 도메인 | 주요 기능 | 권한 |
|---|--------|-----------------|--------|-----------|------|
| 1 | 홈 / 랜딩 | `/` | Product, Search | 인기 상품 노출, 검색 | Public |
| 2 | 상품 목록 | `/products` | Product, Search | 상품 검색/필터/정렬 | Public |
| 3 | 상품 상세 | `/products/:id` | Product, Review | 상품 정보, 리뷰 조회 | Public |
| 4 | 장바구니 | `/cart` | Cart | 장바구니 CRUD, 쿠폰 적용 | User |
| 5 | 주문/결제 | `/order` | Order, Payment, Cart | 주문 생성, 결제 | User |
| 6 | 주문 내역 | `/orders` | Order | 주문 목록 조회 | User |
| 7 | 주문 상세 | `/orders/:id` | Order, Payment, Shipment | 주문 상태, 결제/배송 정보 | User |
| 8 | 배송 조회 | `/orders/:id/shipments` | Shipment | 배송 추적 | User |
| 9 | 리뷰 | `/products/:id/reviews` | Review | 리뷰 CRUD | User |
| 10 | 마이페이지 | `/mypage` | User | 회원 정보 수정 | User |
| 11 | 로그인/회원가입 | `/auth` | User (별도) | 인증 | Public |
| 12 | 검색 결과 | `/search` | Search | 통합 검색 | Public |
| 13 | 관리자 대시보드 | `/admin` | Admin, Order 등 | 통계 요약 | Admin |
| 14 | 관리자: 상품 관리 | `/admin/products` | Product, Inventory | 상품 CRUD, 재고 관리 | Admin |
| 15 | 관리자: 주문 관리 | `/admin/orders` | Order | 주문 상태 변경 | Admin |
| 16 | 관리자: 회원 관리 | `/admin/users` | User | 회원 목록/상세 | Admin |
| 17 | 관리자: 프로모션 관리 | `/admin/promotions` | Promotion | 프로모션/쿠폰 CRUD | Admin |
| 18 | 관리자: 재고 관리 | `/admin/inventory` | Inventory | 재고 CRUD, 예약 관리 | Admin |
| 19 | 관리자: 배송 관리 | `/admin/shipments` | Shipment, Warehouse | 배송 CRUD, 창고 관리 | Admin |
| 20 | 관리자: 결제 관리 | `/admin/payments` | Payment | 결제 목록/상세 | Admin |
| 21 | 관리자: 리뷰 관리 | `/admin/reviews` | Review | 리뷰 상태 관리 | Admin |
| 22 | 관리자: 검색/동의어 관리 | `/admin/search` | Search | 인덱스/동의어/자동완성 | Admin |
| 23 | 관리자: 관리자 계정 관리 | `/admin/accounts` | Admin | 관리자 계정/권한/역할 | Super Admin |

---

## 3. 상세 페이지 명세

### 3.1 홈 / 랜딩 페이지

| 항목 | 내용 |
|------|------|
| **URL (제안)** | `/` |
| **접근 권한** | Public |
| **주요 기능** | 헤더 검색바, 카테고리 네비게이션, 추천 상품 노출 |
| **호출 API** | `GET /api/v1/health` (상태 확인), `GET /api/v1/products?limit=8` (신규/추천 상품) |

### 3.2 상품 목록 페이지

| 항목 | 내용 |
|------|------|
| **URL (제안)** | `/products` |
| **접근 권한** | Public |
| **주요 기능** | - 상품 목록 조회 (페이징) <br>- 상품 상태(판매중/품절 등)별 필터 <br>- 상품명/키워드 검색 |
| **호출 API** | `GET /api/v1/products?skip=0&limit=20&product_status=active` <br>`GET /api/v1/search/products?is_active=true` (검색 인덱스) |
| **Request Params** | `skip`, `limit`, `product_status` |

### 3.3 상품 상세 페이지

| 항목 | 내용 |
|------|------|
| **URL (제안)** | `/products/:productId` |
| **접근 권한** | Public |
| **주요 기능** | - 상품 기본 정보 + 브랜드/카테고리/옵션/SKU <br>- 상품 이미지 <br>- 리뷰 목록 조회 <br>- 장바구니 담기 버튼 |
| **호출 API** | `GET /api/v1/products/{product_id}` <br>`GET /api/v1/reviews?product_id={product_id}&skip=0&limit=10` |
| **Request Params** | `product_id` (path) |

### 3.4 장바구니 페이지

| 항목 | 내용 |
|------|------|
| **URL (제안)** | `/cart` |
| **접근 권한** | User (JWT) |
| **주요 기능** | - 장바구니 목록 조회 <br>- 장바구니 상품 추가/수량 변경/삭제 <br>- 옵션 변경 <br>- 쿠폰 적용 <br>- 주문서로 이동 |
| **호출 API** | `GET /api/v1/carts?user_id={me}` <br>`GET /api/v1/carts/{cart_id}` <br>`POST /api/v1/carts` (생성) <br>`POST /api/v1/carts/{cart_id}/items` (상품 추가) <br>`PUT /api/v1/items/{cart_item_id}` (수량 변경) <br>`DELETE /api/v1/items/{cart_item_id}` (상품 삭제) <br>`POST /api/v1/carts/{cart_id}/coupons` (쿠폰 적용) |
| **주의사항** | 비회원 장바구니는 `session_id` 기반; 로그인 시 `user_id`로 전환 필요 |

### 3.5 주문/결제 페이지

| 항목 | 내용 |
|------|------|
| **URL (제안)** | `/order` |
| **접근 권한** | User (JWT) |
| **주요 기능** | - 주문서 작성 (배송지, 수량 확인) <br>- 주문 생성 <br>- 결제 정보 입력 <br>- 결제 생성 |
| **호출 API** | `POST /api/v1/orders` (주문 생성) <br>`POST /api/v1/payments` (결제 생성) |
| **Request Body** | `OrderCreate` (order_number, user_id, items[], 금액 정보 등) <br>`PaymentCreate` (order_id, payment_method, amount 등) |

### 3.6 주문 내역 페이지

| 항목 | 내용 |
|------|------|
| **URL (제안)** | `/orders` |
| **접근 권한** | User (JWT) |
| **주요 기능** | - 내 주문 목록 조회 <br>- 주문 상태(주문완료/결제완료/배송중 등)별 필터 |
| **호출 API** | `GET /api/v1/orders?user_id={me}&skip=0&limit=20&order_status={status}` |
| **Request Params** | `user_id`, `order_status`, `skip`, `limit` |

### 3.7 주문 상세 페이지

| 항목 | 내용 |
|------|------|
| **URL (제안)** | `/orders/:orderId` |
| **접근 권한** | User (JWT) |
| **주요 기능** | - 주문 상세 정보 (상품, 금액) <br>- 결제 상태/이력 <br>- 배송 상태/추적 <br>- 리뷰 작성 버튼 |
| **호출 API** | `GET /api/v1/orders/{order_id}` <br>`GET /api/v1/payments?order_id={order_id}` <br>`GET /api/v1/shipments?order_id={order_id}` |

### 3.8 배송 조회 페이지

| 항목 | 내용 |
|------|------|
| **URL (제안)** | `/orders/:orderId/shipments` |
| **접근 권한** | User (JWT) |
| **주요 기능** | - 배송 상태 확인 <br>- 배송 상품 목록 <br>- 배송 추적 이력 |
| **호출 API** | `GET /api/v1/shipments/{shipment_id}` <br>`GET /api/v1/shipments/{shipment_id}/items` |

### 3.9 리뷰 페이지

| 항목 | 내용 |
|------|------|
| **URL (제안)** | `/products/:productId/reviews` / `/mypage/reviews` |
| **접근 권한** | User (JWT) |
| **주요 기능** | - 리뷰 목록 조회 (상품별/사용자별) <br>- 리뷰 작성/수정/삭제 <br>- 리뷰 상태(승인/대기/반려) |
| **호출 API** | `GET /api/v1/reviews?product_id={id}&skip=0&limit=20` <br>`POST /api/v1/reviews` (생성) <br>`PUT /api/v1/reviews/{review_id}` (수정) <br>`DELETE /api/v1/reviews/{review_id}` (삭제) |

### 3.10 마이페이지 (회원 정보)

| 항목 | 내용 |
|------|------|
| **URL (제안)** | `/mypage` |
| **접근 권한** | User (JWT) |
| **주요 기능** | - 내 정보 조회/수정 <br>- 계정 삭제 (회원 탈퇴) |
| **호출 API** | `GET /api/v1/users/{user_id}` <br>`PUT /api/v1/users/{user_id}` <br>`DELETE /api/v1/users/{user_id}` |

### 3.11 로그인 / 회원가입

| 항목 | 내용 |
|------|------|
| **URL (제안)** | `/auth/login`, `/auth/register` |
| **접근 권한** | Public |
| **주요 기능** | - 회원가입 <br>- 로그인 (JWT 발급) - 현재 API에 미구현 |
| **호출 API** | `POST /api/v1/users` (회원가입) <br>→ **로그인 엔드포인트는 별도 구현 필요** (`POST /api/v1/auth/login`) |
| **비고** | 현재 백엔드에는 JWT 검증(`get_current_user`)은 있지만 로그인/토큰 발급 엔드포인트는 구현되지 않음. 커스텀 로그인 API 추가 필요 |

### 3.12 검색 페이지

| 항목 | 내용 |
|------|------|
| **URL (제안)** | `/search` |
| **접근 권한** | Public |
| **주요 기능** | - 상품 검색 (키워드) <br>- 검색 인덱스 기반 결과 <br>- 자동완성 제안 |
| **호출 API** | `GET /api/v1/search/products?is_active=true` <br>`GET /api/v1/search/keywords` (인기 검색어) <br>`GET /api/v1/search/autocomplete` (자동완성) <br>`GET /api/v1/search/synonyms` (동의어) |

### 3.13 관리자 대시보드

| 항목 | 내용 |
|------|------|
| **URL (제안)** | `/admin` |
| **접근 권한** | Admin (JWT + Admin 권한) |
| **주요 기능** | - 주요 지표 요약 (주문 수, 매출, 가입자 수 등) <br>- 각 관리 메뉴로의 네비게이션 |
| **호출 API** | `GET /api/v1/health` <br>`GET /api/v1/orders?limit=5` (최근 주문) <br>`GET /api/v1/users?limit=5` (최근 가입자) |

### 3.14 관리자: 상품 관리

| 항목 | 내용 |
|------|------|
| **URL (제안)** | `/admin/products` |
| **접근 권한** | Admin |
| **주요 기능** | - 상품 CRUD <br>- 상품 상태 변경 <br>- 재고 현황 확인 |
| **호출 API** | `GET /api/v1/products?skip=0&limit=20` <br>`GET /api/v1/products/{product_id}` <br>`POST /api/v1/products` (생성) <br>`PUT /api/v1/products/{product_id}` (수정) <br>`DELETE /api/v1/products/{product_id}` (삭제) <br>`GET /api/v1/inventory?sku_id={sku_id}` (재고) |

### 3.15 관리자: 주문 관리

| 항목 | 내용 |
|------|------|
| **URL (제안)** | `/admin/orders` |
| **접근 권한** | Admin |
| **주요 기능** | - 전체 주문 목록 조회 <br>- 주문 상태 변경 (발주확인→결제확인→배송중→배송완료) |
| **호출 API** | `GET /api/v1/orders?skip=0&limit=20&order_status={status}` <br>`GET /api/v1/orders/{order_id}` <br>`PUT /api/v1/orders/{order_id}` (상태 변경) |

### 3.16 관리자: 회원 관리

| 항목 | 내용 |
|------|------|
| **URL (제안)** | `/admin/users` |
| **접근 권한** | Admin |
| **주요 기능** | - 회원 목록/상세 조회 <br>- 회원 상태 변경 <br>- 회원 계정 삭제 |
| **호출 API** | `GET /api/v1/users?skip=0&limit=20&user_status={status}` <br>`GET /api/v1/users/{user_id}` <br>`PUT /api/v1/users/{user_id}` <br>`DELETE /api/v1/users/{user_id}` |

### 3.17 관리자: 프로모션 관리

| 항목 | 내용 |
|------|------|
| **URL (제안)** | `/admin/promotions` |
| **접근 권한** | Admin |
| **주요 기능** | - 프로모션 CRUD <br>- 프로모션 활성/비활성 토글 <br>- 쿠폰 발행 내역 |
| **호출 API** | `GET /api/v1/promotions?skip=0&limit=20&is_active=true` <br>`GET /api/v1/promotions/{promotion_id}` <br>`POST /api/v1/promotions` <br>`PUT /api/v1/promotions/{promotion_id}` <br>`DELETE /api/v1/promotions/{promotion_id}` |

### 3.18 관리자: 재고 관리

| 항목 | 내용 |
|------|------|
| **URL (제안)** | `/admin/inventory` |
| **접근 권한** | Admin |
| **주요 기능** | - 재고 목록/상세 조회 <br>- 재고 수량 변경 <br>- 재고 예약 현황 <br>- 재고 변동 이력 |
| **호출 API** | `GET /api/v1/inventory?skip=0&limit=20&sku_id={id}` <br>`GET /api/v1/inventory/{inventory_id}` <br>`PUT /api/v1/inventory/{inventory_id}` <br>`POST /api/v1/inventory` <br>`DELETE /api/v1/inventory/{inventory_id}` <br>`GET /api/v1/inventory/reservations/{reservation_id}` <br>`POST /api/v1/inventory/reservations` <br>`GET /api/v1/inventory/transactions?sku_id={id}` |

### 3.19 관리자: 배송 관리

| 항목 | 내용 |
|------|------|
| **URL (제안)** | `/admin/shipments` |
| **접근 권한** | Admin |
| **주요 기능** | - 배송 목록/상세 조회 <br>- 배송 상태 변경 <br>- 배송 상품 관리 <br>- 창고(Warehouse) CRUD |
| **호출 API** | `GET /api/v1/shipments?skip=0&limit=20&shipment_status={status}` <br>`GET /api/v1/shipments/{shipment_id}` <br>`POST /api/v1/shipments` <br>`PUT /api/v1/shipments/{shipment_id}` <br>`DELETE /api/v1/shipments/{shipment_id}` <br>`GET /api/v1/shipments/{id}/items` <br>`GET /api/v1/warehouses` / `POST /api/v1/warehouses` / `PUT /api/v1/warehouses/{id}` / `DELETE /api/v1/warehouses/{id}` |

### 3.20 관리자: 결제 관리

| 항목 | 내용 |
|------|------|
| **URL (제안)** | `/admin/payments` |
| **접근 권한** | Admin |
| **주요 기능** | - 결제 목록/상세 조회 <br>- 결제 상태 관리 <br>- 결제 취소/환불 (트랜잭션 이력) |
| **호출 API** | `GET /api/v1/payments?skip=0&limit=20&payment_status={status}&order_id={id}` <br>`GET /api/v1/payments/{payment_id}` <br>`PUT /api/v1/payments/{payment_id}` <br>`DELETE /api/v1/payments/{payment_id}` |

### 3.21 관리자: 리뷰 관리

| 항목 | 내용 |
|------|------|
| **URL (제안)** | `/admin/reviews` |
| **접근 권한** | Admin |
| **주요 기능** | - 전체 리뷰 목록 조회 <br>- 리뷰 상태(승인/반려/대기) 관리 |
| **호출 API** | `GET /api/v1/reviews?skip=0&limit=20&review_status={status}` <br>`GET /api/v1/reviews/{review_id}` <br>`PUT /api/v1/reviews/{review_id}` <br>`DELETE /api/v1/reviews/{review_id}` |

### 3.22 관리자: 검색/동의어 관리

| 항목 | 내용 |
|------|------|
| **URL (제안)** | `/admin/search` |
| **접근 권한** | Admin |
| **주요 기능** | - 검색 인덱스 상품 CRUD <br>- 검색 키워드 관리 <br>- 자동완성 데이터 관리 <br>- 동의어(Synonym) 관리 |
| **호출 API** | `GET/POST/PUT/DELETE /api/v1/search/products/{id}` <br>`GET/POST/PUT/DELETE /api/v1/search/keywords/{keyword}` <br>`GET/POST/PUT/DELETE /api/v1/search/autocomplete/{id}` <br>`GET/POST/PUT/DELETE /api/v1/search/synonyms/{id}` |

### 3.23 관리자: 관리자 계정 관리

| 항목 | 내용 |
|------|------|
| **URL (제안)** | `/admin/accounts` |
| **접근 권한** | Super Admin |
| **주요 기능** | - 관리자 계정 CRUD <br>- 관리자 역할(Role) 목록 조회 <br>- 권한(Permission) 목록 조회 |
| **호출 API** | `GET /api/v1/admin/accounts?skip=0&limit=20&admin_status={status}` <br>`GET /api/v1/admin/accounts/{admin_id}` <br>`POST /api/v1/admin/accounts` <br>`PUT /api/v1/admin/accounts/{admin_id}` <br>`DELETE /api/v1/admin/accounts/{admin_id}` <br>`GET /api/v1/admin/roles` <br>`GET /api/v1/admin/permissions` |

---

## 4. 공통 사항

### 4.1 인증 흐름

```
[프론트엔드]                      [백엔드]
    |                                |
    |-- POST /api/v1/auth/login ---->|  ← (TODO: 백엔드에 추가 필요)
    |<--- { access_token, ... } -----|
    |                                |
    |-- GET /api/v1/xxx -------------|
    |   Authorization: Bearer <token> |
    |<--- { data, message } ---------|
```

> **⚠️ 주의**: 현재 백엔드에는 JWT 검증(`dependencies.get_current_user`) 로직은 있지만, 로그인하여 토큰을 발급하는 엔드포인트는 구현되어 있지 않습니다. 프론트엔드 개발 전에 `POST /api/v1/auth/login` 엔드포인트의 추가 구현이 필요합니다.

### 4.2 공통 응답 형식

```typescript
interface APIResponse<T> {
  data: T;
  message: string;
}
```

- 성공: HTTP 200 (목록/조회/수정), 201 (생성)
- 실패: HTTP 4xx (클라이언트 오류), 5xx (서버 오류)
- 페이지네이션: `skip`(offset) + `limit`(count), 응답에 total_count는 별도로 없음

### 4.3 추천 기술 스택 (프론트엔드)

| 영역 | 제안 |
|------|------|
| Framework | React 18+ / Next.js 14+ (App Router) |
| 언어 | TypeScript (strict mode) |
| HTTP 클라이언트 | axios / ky |
| 상태 관리 | React Query (TanStack Query) + Zustand |
| 폼 관리 | React Hook Form + Zod (스키마 검증) |
| UI 라이브러리 | Tailwind CSS + shadcn/ui (권장) |
| API 타입 생성 | openapi-typescript (openapi.json → TypeScript 타입 자동 생성) |

### 4.4 API 타입 자동 생성 (권장 사항)

`openapi.json` 파일을 기반으로 `openapi-typescript`를 사용하여 TypeScript 타입을 자동 생성할 수 있습니다.

```bash
npx openapi-typescript ./openapi.json -o ./src/types/api.ts
```

이렇게 생성된 타입을 사용하면 백엔드 API 응답과 요청 바디에 대한 타입 안정성을 확보할 수 있습니다.

---

## 부록: 전체 API 엔드포인트 맵

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/v1/health` | 헬스 체크 |
| GET/POST/PUT/DELETE | `/api/v1/users[/{user_id}]` | 회원 CRUD |
| GET/POST/PUT/DELETE | `/api/v1/products[/{product_id}]` | 상품 CRUD |
| GET/POST/PUT/DELETE | `/api/v1/carts[/{cart_id}]` | 장바구니 CRUD |
| GET/POST/PUT/DELETE | `/api/v1/carts/{cart_id}/items[/{item_id}]` | 장바구니 상품 |
| POST | `/api/v1/items/{cart_item_id}/option-snapshots` | 옵션 스냅샷 추가 |
| POST | `/api/v1/carts/{cart_id}/coupons` | 쿠폰 적용 |
| GET/POST/PUT/DELETE | `/api/v1/orders[/{order_id}]` | 주문 CRUD |
| GET/POST/PUT/DELETE | `/api/v1/payments[/{payment_id}]` | 결제 CRUD |
| GET/POST/PUT/DELETE | `/api/v1/inventory[/{inventory_id}]` | 재고 CRUD |
| POST | `/api/v1/inventory/reservations` | 재고 예약 생성 |
| GET | `/api/v1/inventory/reservations/{id}` | 예약 상세 |
| GET | `/api/v1/inventory/transactions` | 변동 이력 |
| GET/POST/PUT/DELETE | `/api/v1/shipments[/{shipment_id}]` | 배송 CRUD |
| GET/POST/PUT/DELETE | `/api/v1/shipments/{id}/items[/{item_id}]` | 배송 상품 |
| GET/POST/PUT/DELETE | `/api/v1/warehouses[/{warehouse_id}]` | 창고 CRUD |
| GET/POST/PUT/DELETE | `/api/v1/promotions[/{promotion_id}]` | 프로모션 CRUD |
| GET/POST/PUT/DELETE | `/api/v1/reviews[/{review_id}]` | 리뷰 CRUD |
| GET/POST/PUT/DELETE | `/api/v1/search/products[/{product_id}]` | 검색 인덱스 CRUD |
| GET/POST/PUT/DELETE | `/api/v1/search/keywords[/{keyword}]` | 키워드 CRUD |
| GET/POST/PUT/DELETE | `/api/v1/search/autocomplete[/{id}]` | 자동완성 CRUD |
| GET/POST/PUT/DELETE | `/api/v1/search/synonyms[/{id}]` | 동의어 CRUD |
| GET/POST/PUT/DELETE | `/api/v1/admin/accounts[/{admin_id}]` | 관리자 계정 CRUD |
| GET | `/api/v1/admin/roles` | 역할 목록 |
| GET | `/api/v1/admin/permissions` | 권한 목록 |
