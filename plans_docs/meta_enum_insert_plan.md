# meta.enum INSERT SQL 생성 계획

## 개요
`meta.meta_enum` 테이블에 `ecommerce` 스키마의 모든 유효한 enum 값을 INSERT하는 SQL 문을 생성합니다.

## 분석 결과

### 1. reference_docs에 명시적 INSERT 구문이 있는 enum 타입 (24개 타입, ~55개 값)

| enum_type | enum_values | 출처 |
|-----------|------------|------|
| `user_status` | ACTIVE, SUSPENDED, DELETED | 02.Users.sql |
| `user_type` | NORMAL, ADMIN, SELLER | 02.Users.sql |
| `auth_provider` | LOCAL, GOOGLE, KAKAO | 02.Users.sql |
| `cart_status` | ACTIVE, ORDERED, ABANDONED | 03.Cart.sql |
| `order_status` | CREATED, PAID, SHIPPED, COMPLETED, CANCELLED | 04.Order.sql |
| `payment_status` | **READY, SUCCESS, FAIL, CANCEL, PENDING** | 04.Order.sql + 05.Payment.sql (+ PENDING은 order_payment DEFAULT) |
| `shipment_status` | READY, SHIPPED, DELIVERED, RETURNED | 04.Order.sql + 07.Shipment.sql |
| `transaction_type` | AUTHORIZE, CAPTURE, CANCEL, REFUND | 05.Payment.sql |
| `transaction_status` | SUCCESS, FAIL | 05.Payment.sql |
| `refund_status` | REQUESTED, SUCCESS, FAIL | 05.Payment.sql |
| `reservation_status` | RESERVED, CONFIRMED, RELEASED | 06.Inventory.sql |
| `inventory_transaction_type` | IN, OUT, RESERVE, RELEASE | 06.Inventory.sql |
| `shipment_item_status` | READY, SHIPPED, DELIVERED | 07.Shipment.sql |
| `shipment_type` | NORMAL, EXPRESS, SAME_DAY | 07.Shipment.sql |
| `promotion_type` | COUPON, AUTO | 08.Promotion.sql |
| `discount_type` | RATE, FIXED | 08.Promotion.sql |
| `target_type` | ALL, PRODUCT, CATEGORY | 08.Promotion.sql |
| `review_status` | ACTIVE, HIDDEN, DELETED, PENDING | 09.Review.sql |
| `report_status` | PENDING, RESOLVED | 09.Review.sql |
| `admin_status` | ACTIVE, INACTIVE, LOCKED | 11.Admin.sql |
| `action_type` | CREATE, UPDATE, DELETE, LOGIN | 11.Admin.sql |
| `resource_type` | MENU, API, BUTTON | 11.Admin.sql |
| `permission_action` | READ, WRITE, DELETE, APPROVE | 11.Admin.sql |

### 2. 컬럼 코멘트에만 정의된 enum 타입 (8개 타입) — INSERT 누락

| enum_type | enum_values | 출처 (컬럼 코멘트) |
|-----------|------------|-------------------|
| `login_result` | SUCCESS, FAIL | 02.Users.sql user_login_history.login_result |
| `payment_method_code` | CARD, KAKAO_PAY, NAVER_PAY, EASY_PAY | 05.Payment.sql payment.payment_method_code / payment_method.payment_method_code |
| `pg_provider` | STRIPE, TOSS | 05.Payment.sql payment_transaction.pg_provider |
| `log_type` | REQUEST, RESPONSE, ERROR | 05.Payment.sql payment_log.log_type |
| `reference_type` | ORDER, ADMIN | 06.Inventory.sql inventory_transaction.reference_type |
| `courier_code` | CJ, LOGEN, UPS | 07.Shipment.sql shipment_tracking.courier_code |
| `rating_type` | QUALITY, DELIVERY, PRICE | 09.Review.sql review_rating.rating_type |

### 3. 컬럼 코멘트도 INSERT도 없는 enum 타입 (5개 타입) — 추론 필요

| enum_type | 예상 값 | 근거 |
|-----------|---------|------|
| `product_status` | ACTIVE, INACTIVE, DISCONTINUED | 일반적인 상품 상태 |
| `sku_status` | ACTIVE, INACTIVE | 일반적인 SKU 상태 |
| `gender_code` | M, F, NONE | 일반적인 성별 코드 |
| `condition_type` | MIN_AMOUNT, MIN_COUNT | 프로모션 조건 유형 |
| `tracking_status` | COLLECTED, IN_TRANSIT, OUT_FOR_DELIVERY, DELIVERED, FAILED | 일반적인 배송 추적 상태 |

## 중복 제거 및 병합

- `payment_status`: 04.Order.sql에는 READY/SUCCESS/FAIL/CANCEL, 04.Order.sql order_payment DEFAULT 'PENDING', 05.Payment.sql에도 동일 — **병합 후 PENDING 추가**
- `shipment_status`: 04.Order.sql에는 READY/SHIPPED/DELIVERED, 07.Shipment.sql에는 RETURNED 추가 — **병합**
- `login_result`: user_login_history와 admin_access_log 모두 SUCCESS/FAIL

## 파일 위치
생성된 SQL 파일: `backend/insert_meta_enums.sql`
