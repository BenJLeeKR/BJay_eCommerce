-- ============================================================
-- Migration: warehouse_stock FK + 복합 인덱스 추가
-- 설계 문서(warehouse_design.md) 요구사항 반영
-- ============================================================

-- 1. warehouse_stock.warehouse_id → warehouse.id FK 추가
ALTER TABLE ecommerce.warehouse_stock
ADD CONSTRAINT fk_warehouse_stock_warehouse
FOREIGN KEY (warehouse_id) REFERENCES ecommerce.warehouse(id);

-- 2. 복합 인덱스 (warehouse_id, sku_id) 생성
CREATE INDEX IF NOT EXISTS ix_warehouse_stock_warehouse_sku
ON ecommerce.warehouse_stock (warehouse_id, sku_id);
