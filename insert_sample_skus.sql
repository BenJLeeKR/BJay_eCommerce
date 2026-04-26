-- ============================================================
-- Sample SKU data INSERT (Swagger UI 장바구니 생성 테스트용)
-- ============================================================
-- 주의: 이 스크립트는 기존 데이터를 중복 생성하지 않도록
--       sku_code 기준으로 존재 여부를 체크합니다.
-- ============================================================

INSERT INTO ecommerce.sku (product_id, sku_code, sale_price_amount, stock_quantity, sku_status, created_at, created_by)
SELECT 2, 'ASUS-ROG-G14-32GB', 1890000.00, 50, 'ACTIVE', NOW(), 1
WHERE NOT EXISTS (SELECT 1 FROM ecommerce.sku WHERE sku_code = 'ASUS-ROG-G14-32GB');

INSERT INTO ecommerce.sku (product_id, sku_code, sale_price_amount, stock_quantity, sku_status, created_at, created_by)
SELECT 3, 'SONY-WH1000XM5-BLK', 450000.00, 100, 'ACTIVE', NOW(), 1
WHERE NOT EXISTS (SELECT 1 FROM ecommerce.sku WHERE sku_code = 'SONY-WH1000XM5-BLK');


-- ============================================================
-- SKU-OptionValue 매핑 데이터 INSERT (기존 SKU 소급 적용)
-- ============================================================
-- sku_code 기준으로 SKU ID를 찾아 sku_option_value_map에 INSERT
-- WHERE NOT EXISTS 로 중복 방지
-- ============================================================

-- -------------------------------------------------------
-- Product 2: 에이수스 ROG 제피러스 G14 - 램 용량 (option_id=1)
-- -------------------------------------------------------
-- SKU 1: ASUS-ROG-G14-16GB → 16GB (option_value_id=1)
INSERT INTO ecommerce.sku_option_value_map (sku_id, option_value_id)
SELECT s.id, 1 FROM ecommerce.sku s
WHERE s.sku_code = 'ASUS-ROG-G14-16GB'
  AND NOT EXISTS (SELECT 1 FROM ecommerce.sku_option_value_map WHERE sku_id = s.id AND option_value_id = 1);

-- SKU 2: ASUS-ROG-G14-32GB → 32GB (option_value_id=2)
INSERT INTO ecommerce.sku_option_value_map (sku_id, option_value_id)
SELECT s.id, 2 FROM ecommerce.sku s
WHERE s.sku_code = 'ASUS-ROG-G14-32GB'
  AND NOT EXISTS (SELECT 1 FROM ecommerce.sku_option_value_map WHERE sku_id = s.id AND option_value_id = 2);

-- -------------------------------------------------------
-- Product 3: 소니 WH-1000XM5 - 색상 (option_id=2)
-- -------------------------------------------------------
-- SKU 3: SONY-WH1000XM5-SIL → 플래티넘 실버 (option_value_id=3)
INSERT INTO ecommerce.sku_option_value_map (sku_id, option_value_id)
SELECT s.id, 3 FROM ecommerce.sku s
WHERE s.sku_code = 'SONY-WH1000XM5-SIL'
  AND NOT EXISTS (SELECT 1 FROM ecommerce.sku_option_value_map WHERE sku_id = s.id AND option_value_id = 3);

-- SKU 4: SONY-WH1000XM5-BLK → 블랙 (option_value_id=4)
INSERT INTO ecommerce.sku_option_value_map (sku_id, option_value_id)
SELECT s.id, 4 FROM ecommerce.sku s
WHERE s.sku_code = 'SONY-WH1000XM5-BLK'
  AND NOT EXISTS (SELECT 1 FROM ecommerce.sku_option_value_map WHERE sku_id = s.id AND option_value_id = 4);

-- -------------------------------------------------------
-- Product 4: 로지텍 G Pro X TKL - 스위치 타입 (option_id=3)
-- -------------------------------------------------------
-- SKU 5: LOGITECH-GPROX-BROWN → GX 브라운(갈축) (option_value_id=5)
INSERT INTO ecommerce.sku_option_value_map (sku_id, option_value_id)
SELECT s.id, 5 FROM ecommerce.sku s
WHERE s.sku_code = 'LOGITECH-GPROX-BROWN'
  AND NOT EXISTS (SELECT 1 FROM ecommerce.sku_option_value_map WHERE sku_id = s.id AND option_value_id = 5);

-- SKU 6: LOGITECH-GPROX-RED → GX 레드(적축) (option_value_id=6)
INSERT INTO ecommerce.sku_option_value_map (sku_id, option_value_id)
SELECT s.id, 6 FROM ecommerce.sku s
WHERE s.sku_code = 'LOGITECH-GPROX-RED'
  AND NOT EXISTS (SELECT 1 FROM ecommerce.sku_option_value_map WHERE sku_id = s.id AND option_value_id = 6);

-- -------------------------------------------------------
-- Product 5: 델 울트라샤프 U2723QE - 옵션 없음 → 매핑 생략
-- -------------------------------------------------------

-- -------------------------------------------------------
-- Product 6: 레이저 바이퍼 V2 Pro - 색상 (option_id=4)
-- -------------------------------------------------------
-- SKU 8: RAZER-VIPER-WHITE → 화이트 (option_value_id=7)
INSERT INTO ecommerce.sku_option_value_map (sku_id, option_value_id)
SELECT s.id, 7 FROM ecommerce.sku s
WHERE s.sku_code = 'RAZER-VIPER-WHITE'
  AND NOT EXISTS (SELECT 1 FROM ecommerce.sku_option_value_map WHERE sku_id = s.id AND option_value_id = 7);

-- SKU 9: RAZER-VIPER-BLACK → 블랙 (option_value_id=8)
INSERT INTO ecommerce.sku_option_value_map (sku_id, option_value_id)
SELECT s.id, 8 FROM ecommerce.sku s
WHERE s.sku_code = 'RAZER-VIPER-BLACK'
  AND NOT EXISTS (SELECT 1 FROM ecommerce.sku_option_value_map WHERE sku_id = s.id AND option_value_id = 8);

-- -------------------------------------------------------
-- Product 7: 아이패드 프로 11형 (M4) - 용량 (option_id=5)
-- -------------------------------------------------------
-- SKU 10: IPAD-PRO-M4-256GB → 256GB (option_value_id=9)
INSERT INTO ecommerce.sku_option_value_map (sku_id, option_value_id)
SELECT s.id, 9 FROM ecommerce.sku s
WHERE s.sku_code = 'IPAD-PRO-M4-256GB'
  AND NOT EXISTS (SELECT 1 FROM ecommerce.sku_option_value_map WHERE sku_id = s.id AND option_value_id = 9);

-- SKU 11: IPAD-PRO-M4-512GB → 512GB (option_value_id=10)
INSERT INTO ecommerce.sku_option_value_map (sku_id, option_value_id)
SELECT s.id, 10 FROM ecommerce.sku s
WHERE s.sku_code = 'IPAD-PRO-M4-512GB'
  AND NOT EXISTS (SELECT 1 FROM ecommerce.sku_option_value_map WHERE sku_id = s.id AND option_value_id = 10);

-- -------------------------------------------------------
-- Product 8: 갤럭시 워치7 44mm - 연결 방식 (option_id=6)
-- -------------------------------------------------------
-- SKU 12: GALAXY-WATCH7-BT → Bluetooth (option_value_id=11)
INSERT INTO ecommerce.sku_option_value_map (sku_id, option_value_id)
SELECT s.id, 11 FROM ecommerce.sku s
WHERE s.sku_code = 'GALAXY-WATCH7-BT'
  AND NOT EXISTS (SELECT 1 FROM ecommerce.sku_option_value_map WHERE sku_id = s.id AND option_value_id = 11);

-- SKU 13: GALAXY-WATCH7-LTE → LTE (option_value_id=12)
INSERT INTO ecommerce.sku_option_value_map (sku_id, option_value_id)
SELECT s.id, 12 FROM ecommerce.sku s
WHERE s.sku_code = 'GALAXY-WATCH7-LTE'
  AND NOT EXISTS (SELECT 1 FROM ecommerce.sku_option_value_map WHERE sku_id = s.id AND option_value_id = 12);

-- -------------------------------------------------------
-- Product 9: 삼성전자 T7 Shield 2TB - 옵션 없음 → 매핑 생략
-- -------------------------------------------------------

-- -------------------------------------------------------
-- Product 10: 마샬 엠버튼 II - 색상 (option_id=7)
-- -------------------------------------------------------
-- SKU 15: MARSHALL-EMBERTON-BLK → Black and Brass (option_value_id=13)
INSERT INTO ecommerce.sku_option_value_map (sku_id, option_value_id)
SELECT s.id, 13 FROM ecommerce.sku s
WHERE s.sku_code = 'MARSHALL-EMBERTON-BLK'
  AND NOT EXISTS (SELECT 1 FROM ecommerce.sku_option_value_map WHERE sku_id = s.id AND option_value_id = 13);

-- SKU 16: MARSHALL-EMBERTON-CRM → Cream (option_value_id=14)
INSERT INTO ecommerce.sku_option_value_map (sku_id, option_value_id)
SELECT s.id, 14 FROM ecommerce.sku s
WHERE s.sku_code = 'MARSHALL-EMBERTON-CRM'
  AND NOT EXISTS (SELECT 1 FROM ecommerce.sku_option_value_map WHERE sku_id = s.id AND option_value_id = 14);

-- -------------------------------------------------------
-- Product 11: 로지텍 C922 Pro Stream - 옵션 없음 → 매핑 생략
-- -------------------------------------------------------
