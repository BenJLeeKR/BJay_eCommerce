-- 확장된 DDL 문 (E-Commerce 시스템)
-- 참조: reference_docs/ 디렉토리의 원본 SQL 파일들
-- 생성일: 2026-04-23

-- 1. 스키마 생성
CREATE SCHEMA IF NOT EXISTS ecommerce;
CREATE SCHEMA IF NOT EXISTS meta;

SET search_path TO ecommerce, public;

-- 2. 메타 테이블 (데이터 카탈로그)
CREATE TABLE meta.meta_table (
    table_name VARCHAR(100) PRIMARY KEY,
    table_description TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE meta.meta_column (
    id BIGSERIAL PRIMARY KEY,
    table_name VARCHAR(100) NOT NULL,
    column_name VARCHAR(100) NOT NULL,
    data_type VARCHAR(50),
    is_nullable BOOLEAN,
    is_pk BOOLEAN,
    is_fk BOOLEAN,
    reference_table VARCHAR(100),
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE meta.meta_enum (
    enum_type VARCHAR(50),
    enum_value VARCHAR(50),
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (enum_type, enum_value)
);

-- 3. 도메인별 테이블 생성 (원본 SQL 파일에서 복사)
-- 아래는 주요 테이블 생성문의 요약본입니다.
-- 전체 정의는 reference_docs/*.sql 파일을 참조하십시오.

-- 3.1 Product 도메인
CREATE TABLE ecommerce.product (
    id BIGSERIAL PRIMARY KEY,
    product_name VARCHAR(255) NOT NULL,
    product_description TEXT,
    brand_id BIGINT,
    product_status VARCHAR(20) NOT NULL,
    base_price_amount NUMERIC(12,2) NOT NULL,
    thumbnail_image_url TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    created_by BIGINT,
    updated_at TIMESTAMP,
    updated_by BIGINT,
    deleted_at TIMESTAMP,
    deleted_by BIGINT
);

-- 나머지 Product 관련 테이블 (brand, category, sku 등)은 원본 파일 참조

-- 3.2 User 도메인
CREATE TABLE ecommerce.user_account (
    id BIGSERIAL PRIMARY KEY,
    user_email VARCHAR(255) NOT NULL UNIQUE,
    password_hash TEXT,
    user_status VARCHAR(20) NOT NULL,
    user_type VARCHAR(20) NOT NULL,
    is_email_verified BOOLEAN DEFAULT FALSE,
    last_login_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    created_by BIGINT,
    updated_at TIMESTAMP,
    updated_by BIGINT,
    deleted_at TIMESTAMP,
    deleted_by BIGINT
);

-- 나머지 User 관련 테이블은 원본 파일 참조

-- 4. 확장된 외래 키 제약 조건 (원본에 누락된 경우)
ALTER TABLE ecommerce.product ADD CONSTRAINT fk_product_brand 
    FOREIGN KEY (brand_id) REFERENCES ecommerce.brand(id) ON DELETE SET NULL;

ALTER TABLE ecommerce.cart ADD CONSTRAINT fk_cart_user 
    FOREIGN KEY (user_id) REFERENCES ecommerce.user_account(id) ON DELETE SET NULL;

ALTER TABLE ecommerce.order_header ADD CONSTRAINT fk_order_user 
    FOREIGN KEY (user_id) REFERENCES ecommerce.user_account(id) ON DELETE RESTRICT;

ALTER TABLE ecommerce.order_item ADD CONSTRAINT fk_order_item_order 
    FOREIGN KEY (order_id) REFERENCES ecommerce.order_header(id) ON DELETE CASCADE;

ALTER TABLE ecommerce.order_item ADD CONSTRAINT fk_order_item_sku 
    FOREIGN KEY (sku_id) REFERENCES ecommerce.sku(id) ON DELETE RESTRICT;

-- 5. 확장된 인덱스 (성능 최적화)
CREATE INDEX idx_product_brand_id ON ecommerce.product(brand_id);
CREATE INDEX idx_product_status ON ecommerce.product(product_status);
CREATE INDEX idx_sku_product_id ON ecommerce.sku(product_id);
CREATE INDEX idx_order_user_id ON ecommerce.order_header(user_id);
CREATE INDEX idx_order_status ON ecommerce.order_header(order_status);
CREATE INDEX idx_payment_order_id ON ecommerce.payment(order_id);
CREATE INDEX idx_inventory_sku_id ON ecommerce.inventory(sku_id);
CREATE INDEX idx_shipment_order_id ON ecommerce.shipment(order_id);

-- 6. 확장된 뷰 (편의성)
CREATE VIEW ecommerce.product_detail AS
SELECT 
    p.id,
    p.product_name,
    p.base_price_amount,
    b.brand_name,
    c.category_name,
    s.sku_code,
    s.sale_price_amount,
    s.stock_quantity
FROM ecommerce.product p
LEFT JOIN ecommerce.brand b ON p.brand_id = b.id
LEFT JOIN ecommerce.product_category_map pcm ON p.id = pcm.product_id
LEFT JOIN ecommerce.category c ON pcm.category_id = c.id
LEFT JOIN ecommerce.sku s ON p.id = s.product_id;

-- 7. 확장된 함수 (재고 관리)
CREATE OR REPLACE FUNCTION ecommerce.reserve_inventory(
    p_sku_id BIGINT,
    p_quantity INT,
    p_order_id BIGINT
) RETURNS BOOLEAN LANGUAGE plpgsql AS $$
DECLARE
    v_available INT;
BEGIN
    SELECT available_quantity INTO v_available
    FROM ecommerce.inventory WHERE sku_id = p_sku_id FOR UPDATE;
    
    IF v_available >= p_quantity THEN
        UPDATE ecommerce.inventory 
        SET available_quantity = available_quantity - p_quantity,
            reserved_quantity = reserved_quantity + p_quantity
        WHERE sku_id = p_sku_id;
        
        INSERT INTO ecommerce.inventory_reservation (sku_id, order_id, reserved_quantity, reservation_status)
        VALUES (p_sku_id, p_order_id, p_quantity, 'RESERVED');
        
        RETURN TRUE;
    ELSE
        RETURN FALSE;
    END IF;
END;
$$;

-- 8. 확장된 트리거 (자동 업데이트)
CREATE OR REPLACE FUNCTION ecommerce.update_product_review_summary()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    -- 리뷰 추가/수정/삭제 시 product_review_summary 갱신
    -- 구현 생략 (참조용)
    RETURN NEW;
END;
$$;

-- 9. 메타 데이터 삽입 (참조)
-- 원본 SQL 파일의 INSERT INTO meta.* 문을 여기에 포함시킬 수 있습니다.
-- 자세한 내용은 reference_docs/*.sql 파일을 참조하십시오.

-- 10. 마무리
COMMENT ON SCHEMA ecommerce IS 'E-Commerce 시스템의 주요 스키마';
COMMENT ON SCHEMA meta IS '메타데이터 및 데이터 카탈로그 스키마';

-- 확장된 DDL 생성 완료
-- 참고: 이 파일은 reference_docs/의 원본 SQL 파일을 기반으로 확장된 요소를 추가한 것입니다.
