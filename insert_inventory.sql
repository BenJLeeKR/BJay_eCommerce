-- ============================================================
-- Inventory 통합 개선 Plan - Phase 1: 초기 데이터 INSERT
-- ============================================================
-- 실행 전 확인: 모든 SKU에 대해 Inventory가 비어있는 상태여야 함
-- SELECT COUNT(*) FROM ecommerce.inventory; -- 0 이어야 함
-- ============================================================

-- Step 1: Inventory 기본 데이터 INSERT
-- 각 SKU의 stock_quantity 값을 기준으로 Inventory 레코드를 생성
INSERT INTO ecommerce.inventory (sku_id, total_quantity, available_quantity, reserved_quantity, safety_stock_quantity, created_by)
SELECT
    s.id,
    s.stock_quantity,
    s.stock_quantity,
    0,
    10,
    1
FROM ecommerce.sku s
WHERE NOT EXISTS (SELECT 1 FROM ecommerce.inventory i WHERE i.sku_id = s.id);

-- Step 2: WarehouseStock 초기 데이터 INSERT
-- 단일 가상 창고(warehouse_id=1)에 모든 재고 할당
INSERT INTO ecommerce.warehouse_stock (warehouse_id, sku_id, stock_quantity)
SELECT 1, s.id, s.stock_quantity
FROM ecommerce.sku s
WHERE NOT EXISTS (SELECT 1 FROM ecommerce.warehouse_stock ws WHERE ws.sku_id = s.id);

-- ============================================================
-- 결과 확인
-- ============================================================
-- SELECT s.sku_code, s.stock_quantity, i.total_quantity, i.available_quantity, ws.stock_quantity
-- FROM ecommerce.sku s
-- LEFT JOIN ecommerce.inventory i ON i.sku_id = s.id
-- LEFT JOIN ecommerce.warehouse_stock ws ON ws.sku_id = s.id AND ws.warehouse_id = 1
-- ORDER BY s.id;
