# SKU 관련 Swagger 테스트 데이터

## 현재 DB 데이터 현황

### Product (10개)
| ID | 상품명 | 브랜드 | 가격 | 옵션 |
|----|--------|--------|------|------|
| 2 | 에이수스 ROG 제피러스 G14 | 에이수스 | 1,890,000 | 램 용량 (16GB / 32GB) |
| 3 | 소니 WH-1000XM5 | 소니 | 450,000 | 색상 (플래티넘 실버 / 블랙) |
| 4 | 로지텍 G Pro X TKL | 로지텍 | 169,000 | 스위치 타입 (갈축 / 적축) |
| 5 | 델 울트라샤프 U2723QE | 델 | 820,000 | 없음 |
| 6 | 레이저 바이퍼 V2 Pro | 레이저 | 199,000 | 색상 (화이트 / 블랙) |
| 7 | 아이패드 프로 11형 (M4) | 애플 | 1,499,000 | 용량 (256GB / 512GB) |
| 8 | 갤럭시 워치7 44mm | 삼성전자 | 389,000 | 연결 방식 (Bluetooth / LTE) |
| 9 | 삼성전자 T7 Shield 2TB | 삼성전자 | 245,000 | 없음 |
| 10 | 마샬 엠버튼 II | 마샬 | 259,000 | 색상 (Black and Brass / Cream) |
| 11 | 로지텍 C922 Pro Stream | 로지텍 | 129,000 | 없음 |

### Brand (8개)
| ID | 브랜드명 |
|----|----------|
| 1 | 에이수스 |
| 2 | 소니 |
| 3 | 로지텍 |
| 4 | 델 |
| 5 | 레이저 |
| 6 | 애플 |
| 7 | 삼성전자 |
| 8 | 마샬 |

### ProductOption (7개)
| ID | 상품 ID | 옵션명 | 옵션값 (ID: 값) |
|----|---------|--------|-----------------|
| 1 | 2 | 램 용량 | 1: 16GB, 2: 32GB |
| 2 | 3 | 색상 | 3: 플래티넘 실버, 4: 블랙 |
| 3 | 4 | 스위치 타입 | 5: GX 브라운(갈축), 6: GX 레드(적축) |
| 4 | 6 | 색상 | 7: 화이트, 8: 블랙 |
| 5 | 7 | 용량 | 9: 256GB, 10: 512GB |
| 6 | 8 | 연결 방식 | 11: Bluetooth, 12: LTE |
| 7 | 10 | 색상 | 13: Black and Brass, 14: Cream |

---

## 1. SKU 생성 API (`POST /api/v1/skus`)

### Payload 구조
```json
{
  "product_id": [상품 ID],
  "sku_code": "[고유 SKU 코드]",
  "sale_price_amount": [판매가],
  "stock_quantity": [초기 재고],
  "sku_status": "ACTIVE",
  "created_by": 1
}
```

### 1-A: 에이수스 ROG 제피러스 G14 (product_id=2) — 램 용량 16GB

```json
{
  "product_id": 2,
  "sku_code": "ASUS-ROG-G14-16GB",
  "sale_price_amount": 1690000.00,
  "stock_quantity": 30,
  "sku_status": "ACTIVE",
  "created_by": 1
}
```

### 1-B: 에이수스 ROG 제피러스 G14 (product_id=2) — 램 용량 32GB

```json
{
  "product_id": 2,
  "sku_code": "ASUS-ROG-G14-32GB",
  "sale_price_amount": 1890000.00,
  "stock_quantity": 50,
  "sku_status": "ACTIVE",
  "created_by": 1
}
```

### 2-A: 소니 WH-1000XM5 (product_id=3) — 플래티넘 실버

```json
{
  "product_id": 3,
  "sku_code": "SONY-WH1000XM5-SIL",
  "sale_price_amount": 450000.00,
  "stock_quantity": 100,
  "sku_status": "ACTIVE",
  "created_by": 1
}
```

### 2-B: 소니 WH-1000XM5 (product_id=3) — 블랙

```json
{
  "product_id": 3,
  "sku_code": "SONY-WH1000XM5-BLK",
  "sale_price_amount": 450000.00,
  "stock_quantity": 80,
  "sku_status": "ACTIVE",
  "created_by": 1
}
```

### 3-A: 로지텍 G Pro X TKL (product_id=4) — 갈축

```json
{
  "product_id": 4,
  "sku_code": "LOGITECH-GPROX-BROWN",
  "sale_price_amount": 169000.00,
  "stock_quantity": 60,
  "sku_status": "ACTIVE",
  "created_by": 1
}
```

### 3-B: 로지텍 G Pro X TKL (product_id=4) — 적축

```json
{
  "product_id": 4,
  "sku_code": "LOGITECH-GPROX-RED",
  "sale_price_amount": 169000.00,
  "stock_quantity": 45,
  "sku_status": "ACTIVE",
  "created_by": 1
}
```

### 4: 델 울트라샤프 U2723QE (product_id=5) — 옵션 없음

```json
{
  "product_id": 5,
  "sku_code": "DELL-U2723QE-BASE",
  "sale_price_amount": 820000.00,
  "stock_quantity": 25,
  "sku_status": "ACTIVE",
  "created_by": 1
}
```

### 5-A: 레이저 바이퍼 V2 Pro (product_id=6) — 화이트

```json
{
  "product_id": 6,
  "sku_code": "RAZER-VIPER-WHITE",
  "sale_price_amount": 199000.00,
  "stock_quantity": 70,
  "sku_status": "ACTIVE",
  "created_by": 1
}
```

### 5-B: 레이저 바이퍼 V2 Pro (product_id=6) — 블랙

```json
{
  "product_id": 6,
  "sku_code": "RAZER-VIPER-BLACK",
  "sale_price_amount": 199000.00,
  "stock_quantity": 65,
  "sku_status": "ACTIVE",
  "created_by": 1
}
```

### 6-A: 아이패드 프로 11형 M4 (product_id=7) — 256GB

```json
{
  "product_id": 7,
  "sku_code": "IPAD-PRO-M4-256GB",
  "sale_price_amount": 1499000.00,
  "stock_quantity": 40,
  "sku_status": "ACTIVE",
  "created_by": 1
}
```

### 6-B: 아이패드 프로 11형 M4 (product_id=7) — 512GB

```json
{
  "product_id": 7,
  "sku_code": "IPAD-PRO-M4-512GB",
  "sale_price_amount": 1799000.00,
  "stock_quantity": 35,
  "sku_status": "ACTIVE",
  "created_by": 1
}
```

### 7-A: 갤럭시 워치7 44mm (product_id=8) — Bluetooth

```json
{
  "product_id": 8,
  "sku_code": "GALAXY-WATCH7-BT",
  "sale_price_amount": 389000.00,
  "stock_quantity": 90,
  "sku_status": "ACTIVE",
  "created_by": 1
}
```

### 7-B: 갤럭시 워치7 44mm (product_id=8) — LTE

```json
{
  "product_id": 8,
  "sku_code": "GALAXY-WATCH7-LTE",
  "sale_price_amount": 459000.00,
  "stock_quantity": 40,
  "sku_status": "ACTIVE",
  "created_by": 1
}
```

### 8: 삼성전자 T7 Shield 2TB (product_id=9) — 옵션 없음

```json
{
  "product_id": 9,
  "sku_code": "SAMSUNG-T7-2TB",
  "sale_price_amount": 245000.00,
  "stock_quantity": 55,
  "sku_status": "ACTIVE",
  "created_by": 1
}
```

### 9-A: 마샬 엠버튼 II (product_id=10) — Black and Brass

```json
{
  "product_id": 10,
  "sku_code": "MARSHALL-EMBERTON-BLK",
  "sale_price_amount": 259000.00,
  "stock_quantity": 50,
  "sku_status": "ACTIVE",
  "created_by": 1
}
```

### 9-B: 마샬 엠버튼 II (product_id=10) — Cream

```json
{
  "product_id": 10,
  "sku_code": "MARSHALL-EMBERTON-CRM",
  "sale_price_amount": 259000.00,
  "stock_quantity": 35,
  "sku_status": "ACTIVE",
  "created_by": 1
}
```

### 10: 로지텍 C922 Pro Stream (product_id=11) — 옵션 없음

```json
{
  "product_id": 11,
  "sku_code": "LOGITECH-C922-BASE",
  "sale_price_amount": 129000.00,
  "stock_quantity": 80,
  "sku_status": "ACTIVE",
  "created_by": 1
}
```

---

## 2. SKU 벌크 INSERT SQL

위 JSON을 개별적으로 Swagger에서 테스트하기 번거롭다면, 아래 SQL을 한 번에 실행하여 17개 SKU를 일괄 INSERT할 수 있습니다.

```sql
-- ============================================================
-- SKU 일괄 INSERT (17개) - sku_code 기준 중복 방지
-- ============================================================

-- Product 2: 에이수스 ROG 제피러스 G14
INSERT INTO ecommerce.sku (product_id, sku_code, sale_price_amount, stock_quantity, sku_status, created_at, created_by)
SELECT 2, 'ASUS-ROG-G14-16GB', 1690000.00, 30, 'ACTIVE', NOW(), 1
WHERE NOT EXISTS (SELECT 1 FROM ecommerce.sku WHERE sku_code = 'ASUS-ROG-G14-16GB');

INSERT INTO ecommerce.sku (product_id, sku_code, sale_price_amount, stock_quantity, sku_status, created_at, created_by)
SELECT 2, 'ASUS-ROG-G14-32GB', 1890000.00, 50, 'ACTIVE', NOW(), 1
WHERE NOT EXISTS (SELECT 1 FROM ecommerce.sku WHERE sku_code = 'ASUS-ROG-G14-32GB');

-- Product 3: 소니 WH-1000XM5
INSERT INTO ecommerce.sku (product_id, sku_code, sale_price_amount, stock_quantity, sku_status, created_at, created_by)
SELECT 3, 'SONY-WH1000XM5-SIL', 450000.00, 100, 'ACTIVE', NOW(), 1
WHERE NOT EXISTS (SELECT 1 FROM ecommerce.sku WHERE sku_code = 'SONY-WH1000XM5-SIL');

INSERT INTO ecommerce.sku (product_id, sku_code, sale_price_amount, stock_quantity, sku_status, created_at, created_by)
SELECT 3, 'SONY-WH1000XM5-BLK', 450000.00, 80, 'ACTIVE', NOW(), 1
WHERE NOT EXISTS (SELECT 1 FROM ecommerce.sku WHERE sku_code = 'SONY-WH1000XM5-BLK');

-- Product 4: 로지텍 G Pro X TKL
INSERT INTO ecommerce.sku (product_id, sku_code, sale_price_amount, stock_quantity, sku_status, created_at, created_by)
SELECT 4, 'LOGITECH-GPROX-BROWN', 169000.00, 60, 'ACTIVE', NOW(), 1
WHERE NOT EXISTS (SELECT 1 FROM ecommerce.sku WHERE sku_code = 'LOGITECH-GPROX-BROWN');

INSERT INTO ecommerce.sku (product_id, sku_code, sale_price_amount, stock_quantity, sku_status, created_at, created_by)
SELECT 4, 'LOGITECH-GPROX-RED', 169000.00, 45, 'ACTIVE', NOW(), 1
WHERE NOT EXISTS (SELECT 1 FROM ecommerce.sku WHERE sku_code = 'LOGITECH-GPROX-RED');

-- Product 5: 델 울트라샤프 U2723QE
INSERT INTO ecommerce.sku (product_id, sku_code, sale_price_amount, stock_quantity, sku_status, created_at, created_by)
SELECT 5, 'DELL-U2723QE-BASE', 820000.00, 25, 'ACTIVE', NOW(), 1
WHERE NOT EXISTS (SELECT 1 FROM ecommerce.sku WHERE sku_code = 'DELL-U2723QE-BASE');

-- Product 6: 레이저 바이퍼 V2 Pro
INSERT INTO ecommerce.sku (product_id, sku_code, sale_price_amount, stock_quantity, sku_status, created_at, created_by)
SELECT 6, 'RAZER-VIPER-WHITE', 199000.00, 70, 'ACTIVE', NOW(), 1
WHERE NOT EXISTS (SELECT 1 FROM ecommerce.sku WHERE sku_code = 'RAZER-VIPER-WHITE');

INSERT INTO ecommerce.sku (product_id, sku_code, sale_price_amount, stock_quantity, sku_status, created_at, created_by)
SELECT 6, 'RAZER-VIPER-BLACK', 199000.00, 65, 'ACTIVE', NOW(), 1
WHERE NOT EXISTS (SELECT 1 FROM ecommerce.sku WHERE sku_code = 'RAZER-VIPER-BLACK');

-- Product 7: 아이패드 프로 11형 M4
INSERT INTO ecommerce.sku (product_id, sku_code, sale_price_amount, stock_quantity, sku_status, created_at, created_by)
SELECT 7, 'IPAD-PRO-M4-256GB', 1499000.00, 40, 'ACTIVE', NOW(), 1
WHERE NOT EXISTS (SELECT 1 FROM ecommerce.sku WHERE sku_code = 'IPAD-PRO-M4-256GB');

INSERT INTO ecommerce.sku (product_id, sku_code, sale_price_amount, stock_quantity, sku_status, created_at, created_by)
SELECT 7, 'IPAD-PRO-M4-512GB', 1799000.00, 35, 'ACTIVE', NOW(), 1
WHERE NOT EXISTS (SELECT 1 FROM ecommerce.sku WHERE sku_code = 'IPAD-PRO-M4-512GB');

-- Product 8: 갤럭시 워치7 44mm
INSERT INTO ecommerce.sku (product_id, sku_code, sale_price_amount, stock_quantity, sku_status, created_at, created_by)
SELECT 8, 'GALAXY-WATCH7-BT', 389000.00, 90, 'ACTIVE', NOW(), 1
WHERE NOT EXISTS (SELECT 1 FROM ecommerce.sku WHERE sku_code = 'GALAXY-WATCH7-BT');

INSERT INTO ecommerce.sku (product_id, sku_code, sale_price_amount, stock_quantity, sku_status, created_at, created_by)
SELECT 8, 'GALAXY-WATCH7-LTE', 459000.00, 40, 'ACTIVE', NOW(), 1
WHERE NOT EXISTS (SELECT 1 FROM ecommerce.sku WHERE sku_code = 'GALAXY-WATCH7-LTE');

-- Product 9: 삼성전자 T7 Shield 2TB
INSERT INTO ecommerce.sku (product_id, sku_code, sale_price_amount, stock_quantity, sku_status, created_at, created_by)
SELECT 9, 'SAMSUNG-T7-2TB', 245000.00, 55, 'ACTIVE', NOW(), 1
WHERE NOT EXISTS (SELECT 1 FROM ecommerce.sku WHERE sku_code = 'SAMSUNG-T7-2TB');

-- Product 10: 마샬 엠버튼 II
INSERT INTO ecommerce.sku (product_id, sku_code, sale_price_amount, stock_quantity, sku_status, created_at, created_by)
SELECT 10, 'MARSHALL-EMBERTON-BLK', 259000.00, 50, 'ACTIVE', NOW(), 1
WHERE NOT EXISTS (SELECT 1 FROM ecommerce.sku WHERE sku_code = 'MARSHALL-EMBERTON-BLK');

INSERT INTO ecommerce.sku (product_id, sku_code, sale_price_amount, stock_quantity, sku_status, created_at, created_by)
SELECT 10, 'MARSHALL-EMBERTON-CRM', 259000.00, 35, 'ACTIVE', NOW(), 1
WHERE NOT EXISTS (SELECT 1 FROM ecommerce.sku WHERE sku_code = 'MARSHALL-EMBERTON-CRM');

-- Product 11: 로지텍 C922 Pro Stream
INSERT INTO ecommerce.sku (product_id, sku_code, sale_price_amount, stock_quantity, sku_status, created_at, created_by)
SELECT 11, 'LOGITECH-C922-BASE', 129000.00, 80, 'ACTIVE', NOW(), 1
WHERE NOT EXISTS (SELECT 1 FROM ecommerce.sku WHERE sku_code = 'LOGITECH-C922-BASE');
```

---

## 3. SKU-OptionValue 매핑 INSERT SQL (SKU 생성 후 실행)

SKU 생성 후, 각 SKU를 해당 ProductOptionValue에 연결해야 합니다.
SKU ID는 INSERT 순서대로 1부터 시작한다고 가정합니다.
(실제 ID는 `SELECT id, sku_code FROM ecommerce.sku;` 로 확인 후 변경)

```sql
-- ============================================================
-- SKUOptionValueMap INSERT
-- SKU ID는 INSERT 순서에 따라 1~17로 가정
-- ============================================================

-- Product 2: 에이수스 ROG G14
-- SKU 1 (16GB) → OptionValue 1 (16GB)
INSERT INTO ecommerce.sku_option_value_map (sku_id, option_value_id)
SELECT s.id, pov.id FROM ecommerce.sku s, ecommerce.product_option_value pov
WHERE s.sku_code = 'ASUS-ROG-G14-16GB' AND pov.id = 1
AND NOT EXISTS (SELECT 1 FROM ecommerce.sku_option_value_map WHERE sku_id = s.id AND option_value_id = pov.id);

-- SKU 2 (32GB) → OptionValue 2 (32GB)
INSERT INTO ecommerce.sku_option_value_map (sku_id, option_value_id)
SELECT s.id, pov.id FROM ecommerce.sku s, ecommerce.product_option_value pov
WHERE s.sku_code = 'ASUS-ROG-G14-32GB' AND pov.id = 2
AND NOT EXISTS (SELECT 1 FROM ecommerce.sku_option_value_map WHERE sku_id = s.id AND option_value_id = pov.id);

-- Product 3: 소니 WH-1000XM5
-- SKU 3 (플래티넘 실버) → OptionValue 3
INSERT INTO ecommerce.sku_option_value_map (sku_id, option_value_id)
SELECT s.id, 3 FROM ecommerce.sku s WHERE s.sku_code = 'SONY-WH1000XM5-SIL'
AND NOT EXISTS (SELECT 1 FROM ecommerce.sku_option_value_map WHERE sku_id = s.id AND option_value_id = 3);

-- SKU 4 (블랙) → OptionValue 4
INSERT INTO ecommerce.sku_option_value_map (sku_id, option_value_id)
SELECT s.id, 4 FROM ecommerce.sku s WHERE s.sku_code = 'SONY-WH1000XM5-BLK'
AND NOT EXISTS (SELECT 1 FROM ecommerce.sku_option_value_map WHERE sku_id = s.id AND option_value_id = 4);

-- Product 4: 로지텍 G Pro X TKL
-- SKU 5 (갈축) → OptionValue 5
INSERT INTO ecommerce.sku_option_value_map (sku_id, option_value_id)
SELECT s.id, 5 FROM ecommerce.sku s WHERE s.sku_code = 'LOGITECH-GPROX-BROWN'
AND NOT EXISTS (SELECT 1 FROM ecommerce.sku_option_value_map WHERE sku_id = s.id AND option_value_id = 5);

-- SKU 6 (적축) → OptionValue 6
INSERT INTO ecommerce.sku_option_value_map (sku_id, option_value_id)
SELECT s.id, 6 FROM ecommerce.sku s WHERE s.sku_code = 'LOGITECH-GPROX-RED'
AND NOT EXISTS (SELECT 1 FROM ecommerce.sku_option_value_map WHERE sku_id = s.id AND option_value_id = 6);

-- Product 5: 델 울트라샤프 (옵션 없음 - 매핑 불필요)

-- Product 6: 레이저 바이퍼 V2 Pro
-- SKU 8 (화이트) → OptionValue 7
INSERT INTO ecommerce.sku_option_value_map (sku_id, option_value_id)
SELECT s.id, 7 FROM ecommerce.sku s WHERE s.sku_code = 'RAZER-VIPER-WHITE'
AND NOT EXISTS (SELECT 1 FROM ecommerce.sku_option_value_map WHERE sku_id = s.id AND option_value_id = 7);

-- SKU 9 (블랙) → OptionValue 8
INSERT INTO ecommerce.sku_option_value_map (sku_id, option_value_id)
SELECT s.id, 8 FROM ecommerce.sku s WHERE s.sku_code = 'RAZER-VIPER-BLACK'
AND NOT EXISTS (SELECT 1 FROM ecommerce.sku_option_value_map WHERE sku_id = s.id AND option_value_id = 8);

-- Product 7: 아이패드 프로 M4
-- SKU 10 (256GB) → OptionValue 9
INSERT INTO ecommerce.sku_option_value_map (sku_id, option_value_id)
SELECT s.id, 9 FROM ecommerce.sku s WHERE s.sku_code = 'IPAD-PRO-M4-256GB'
AND NOT EXISTS (SELECT 1 FROM ecommerce.sku_option_value_map WHERE sku_id = s.id AND option_value_id = 9);

-- SKU 11 (512GB) → OptionValue 10
INSERT INTO ecommerce.sku_option_value_map (sku_id, option_value_id)
SELECT s.id, 10 FROM ecommerce.sku s WHERE s.sku_code = 'IPAD-PRO-M4-512GB'
AND NOT EXISTS (SELECT 1 FROM ecommerce.sku_option_value_map WHERE sku_id = s.id AND option_value_id = 10);

-- Product 8: 갤럭시 워치7
-- SKU 12 (Bluetooth) → OptionValue 11
INSERT INTO ecommerce.sku_option_value_map (sku_id, option_value_id)
SELECT s.id, 11 FROM ecommerce.sku s WHERE s.sku_code = 'GALAXY-WATCH7-BT'
AND NOT EXISTS (SELECT 1 FROM ecommerce.sku_option_value_map WHERE sku_id = s.id AND option_value_id = 11);

-- SKU 13 (LTE) → OptionValue 12
INSERT INTO ecommerce.sku_option_value_map (sku_id, option_value_id)
SELECT s.id, 12 FROM ecommerce.sku s WHERE s.sku_code = 'GALAXY-WATCH7-LTE'
AND NOT EXISTS (SELECT 1 FROM ecommerce.sku_option_value_map WHERE sku_id = s.id AND option_value_id = 12);

-- Product 9: T7 Shield (옵션 없음 - 매핑 불필요)

-- Product 10: 마샬 엠버튼 II
-- SKU 15 (Black and Brass) → OptionValue 13
INSERT INTO ecommerce.sku_option_value_map (sku_id, option_value_id)
SELECT s.id, 13 FROM ecommerce.sku s WHERE s.sku_code = 'MARSHALL-EMBERTON-BLK'
AND NOT EXISTS (SELECT 1 FROM ecommerce.sku_option_value_map WHERE sku_id = s.id AND option_value_id = 13);

-- SKU 16 (Cream) → OptionValue 14
INSERT INTO ecommerce.sku_option_value_map (sku_id, option_value_id)
SELECT s.id, 14 FROM ecommerce.sku s WHERE s.sku_code = 'MARSHALL-EMBERTON-CRM'
AND NOT EXISTS (SELECT 1 FROM ecommerce.sku_option_value_map WHERE sku_id = s.id AND option_value_id = 14);

-- Product 11: 로지텍 C922 (옵션 없음 - 매핑 불필요)
```

---

## 4. 실행 순서 (권장)

1. **SKU INSERT 실행**: 위 SQL(섹션 2)을 psql 또는 DB 클라이언트에서 실행
   ```bash
   docker compose exec postgres psql -U postgres -d ecommerce -c "...SQL..."
   ```
   또는 Swagger UI에서 위 JSON(섹션 1)을 개별적으로 `POST /api/v1/skus`에 전송

2. **SKU ID 확인**:
   ```sql
   SELECT id, sku_code, product_id FROM ecommerce.sku ORDER BY id;
   ```

3. **SKUOptionValueMap INSERT 실행**: 위 SQL(섹션 3) 실행

4. **장바구니 생성 테스트**: [`backend/fix_data_swagger_payloads.md`](backend/fix_data_swagger_payloads.md)의 Cart Payload 2 사용
   - `sku_id`를 실제 DB에 INSERT된 ID로 변경

5. **재고(Inventory) 생성**: `POST /api/v1/inventory`로 각 SKU의 재고 정보 생성
