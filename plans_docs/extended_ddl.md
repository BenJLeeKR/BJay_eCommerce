# 확장된 DDL 문 및 SQL 문

## 개요
이 문서는 `reference_docs/` 디렉토리에 있는 원본 SQL 파일들을 기반으로 확장된 DDL(Data Definition Language) 문을 제공합니다.  
확장된 부분은 **외래 키 제약 조건**, **추가 인덱스**, **편의 뷰**, **저장 함수**, **트리거** 등을 포함합니다.

## 1. 스키마 생성
```sql
CREATE SCHEMA IF NOT EXISTS ecommerce;
CREATE SCHEMA IF NOT EXISTS meta;

SET search_path TO ecommerce, public;
```

## 2. 메타 테이블 (데이터 카탈로그)
```sql
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
```

## 3. 도메인별 테이블 (요약)
원본 SQL 파일(`01.Products.sql` ~ `11.Admin.sql`)에 정의된 전체 테이블 생성문은 별도로 제공됩니다.  
아래는 각 도메인의 대표 테이블 생성 예시입니다.

### 3.1 Product 도메인
```sql
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
-- 나머지 테이블: brand, category, product_category_map, product_option, product_option_value, sku, sku_option_value_map, product_image
```

### 3.2 User 도메인
```sql
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
-- 나머지 테이블: user_profile, user_address, user_auth, user_login_history, user_role, user_role_map
```

### 3.3 Cart, Order, Payment, Inventory, Shipping, Promotion, Review, Search, Admin 도메인
각 도메인의 전체 테이블 정의는 원본 SQL 파일을 참조하십시오.

## 4. 확장된 외래 키 제약 조건
원본 DDL에 명시되지 않은 외래 키 관계를 추가합니다.

```sql
-- Product
ALTER TABLE ecommerce.product ADD CONSTRAINT fk_product_brand 
    FOREIGN KEY (brand_id) REFERENCES ecommerce.brand(id) ON DELETE SET NULL;

-- Cart
ALTER TABLE ecommerce.cart ADD CONSTRAINT fk_cart_user 
    FOREIGN KEY (user_id) REFERENCES ecommerce.user_account(id) ON DELETE SET NULL;

-- Order
ALTER TABLE ecommerce.order_header ADD CONSTRAINT fk_order_user 
    FOREIGN KEY (user_id) REFERENCES ecommerce.user_account(id) ON DELETE RESTRICT;

ALTER TABLE ecommerce.order_item ADD CONSTRAINT fk_order_item_order 
    FOREIGN KEY (order_id) REFERENCES ecommerce.order_header(id) ON DELETE CASCADE;

ALTER TABLE ecommerce.order_item ADD CONSTRAINT fk_order_item_sku 
    FOREIGN KEY (sku_id) REFERENCES ecommerce.sku(id) ON DELETE RESTRICT;

-- Payment
ALTER TABLE ecommerce.payment ADD CONSTRAINT fk_payment_order 
    FOREIGN KEY (order_id) REFERENCES ecommerce.order_header(id) ON DELETE CASCADE;

-- Inventory
ALTER TABLE ecommerce.inventory ADD CONSTRAINT fk_inventory_sku 
    FOREIGN KEY (sku_id) REFERENCES ecommerce.sku(id) ON DELETE CASCADE;

-- Shipment
ALTER TABLE ecommerce.shipment ADD CONSTRAINT fk_shipment_order 
    FOREIGN KEY (order_id) REFERENCES ecommerce.order_header(id) ON DELETE CASCADE;

-- Review
ALTER TABLE ecommerce.review ADD CONSTRAINT fk_review_product 
    FOREIGN KEY (product_id) REFERENCES ecommerce.product(id) ON DELETE CASCADE;

ALTER TABLE ecommerce.review ADD CONSTRAINT fk_review_user 
    FOREIGN KEY (user_id) REFERENCES ecommerce.user_account(id) ON DELETE SET NULL;
```

## 5. 확장된 인덱스 (성능 최적화)
```sql
-- Product
CREATE INDEX idx_product_brand_id ON ecommerce.product(brand_id);
CREATE INDEX idx_product_status ON ecommerce.product(product_status);
CREATE INDEX idx_sku_product_id ON ecommerce.sku(product_id);

-- Order
CREATE INDEX idx_order_user_id ON ecommerce.order_header(user_id);
CREATE INDEX idx_order_status ON ecommerce.order_header(order_status);
CREATE INDEX idx_order_item_order_id ON ecommerce.order_item(order_id);

-- Payment
CREATE INDEX idx_payment_order_id ON ecommerce.payment(order_id);
CREATE INDEX idx_payment_status ON ecommerce.payment(payment_status);

-- Inventory
CREATE INDEX idx_inventory_sku_id ON ecommerce.inventory(sku_id);
CREATE INDEX idx_inventory_reservation_sku ON ecommerce.inventory_reservation(sku_id);

-- Shipment
CREATE INDEX idx_shipment_order_id ON ecommerce.shipment(order_id);
CREATE INDEX idx_shipment_status ON ecommerce.shipment(shipment_status);

-- Search
CREATE INDEX idx_search_product_index_product_id ON ecommerce.search_product_index(product_id);
CREATE INDEX idx_search_keyword_keyword ON ecommerce.search_keyword(keyword);
```

## 6. 확장된 뷰 (편의성)
```sql
-- 상품 상세 정보 뷰
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

-- 주문 요약 뷰
CREATE VIEW ecommerce.order_summary AS
SELECT 
    o.id,
    o.order_number,
    u.user_email,
    o.order_status,
    o.total_pay_amount,
    o.ordered_at,
    COUNT(oi.id) AS item_count
FROM ecommerce.order_header o
JOIN ecommerce.user_account u ON o.user_id = u.id
LEFT JOIN ecommerce.order_item oi ON o.id = oi.order_id
GROUP BY o.id, u.user_email;
```

## 7. 확장된 함수 (비즈니스 로직)
```sql
-- 재고 예약 함수
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

-- 주문 총액 계산 함수
CREATE OR REPLACE FUNCTION ecommerce.calculate_order_total(p_order_id BIGINT)
RETURNS NUMERIC LANGUAGE plpgsql AS $$
DECLARE
    v_total NUMERIC;
BEGIN
    SELECT SUM(total_price_amount) INTO v_total
    FROM ecommerce.order_item
    WHERE order_id = p_order_id;
    
    RETURN COALESCE(v_total, 0);
END;
$$;
```

## 8. 확장된 트리거 (자동화)
```sql
-- 리뷰 평점 업데이트 트리거
CREATE OR REPLACE FUNCTION ecommerce.update_product_review_summary()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    -- 리뷰 추가/수정/삭제 시 product_review_summary 갱신
    -- 상세 구현은 생략
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_review_after_insert
AFTER INSERT ON ecommerce.review
FOR EACH ROW EXECUTE FUNCTION ecommerce.update_product_review_summary();

-- 재고 변동 이력 트리거
CREATE OR REPLACE FUNCTION ecommerce.log_inventory_transaction()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    INSERT INTO ecommerce.inventory_transaction (sku_id, transaction_type, quantity, reference_type, reference_id)
    VALUES (
        NEW.sku_id,
        CASE 
            WHEN NEW.available_quantity < OLD.available_quantity THEN 'OUT'
            WHEN NEW.available_quantity > OLD.available_quantity THEN 'IN'
            ELSE 'ADJUST'
        END,
        ABS(NEW.available_quantity - OLD.available_quantity),
        'SYSTEM',
        NULL
    );
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_inventory_after_update
AFTER UPDATE ON ecommerce.inventory
FOR EACH ROW EXECUTE FUNCTION ecommerce.log_inventory_transaction();
```

## 9. 메타 데이터 삽입 (예시)
원본 SQL 파일에 포함된 `INSERT INTO meta.*` 문은 그대로 사용할 수 있습니다.  
예시:

```sql
INSERT INTO meta.meta_table (table_name, table_description) VALUES
('product','상품'),
('brand','브랜드'),
('category','카테고리');
```

## 10. 전체 DDL 생성 스크립트
원본 11개 SQL 파일과 본 확장 DDL을 통합한 전체 스크립트를 생성하려면 다음 명령을 사용하십시오.

```bash
cat reference_docs/*.sql > full_schema.sql
```

그 후 본 문서의 4~8절에 있는 확장 문을 `full_schema.sql`에 추가합니다.

## 결론
이 확장 DDL은 프로덕션 환경에서의 데이터 무결성, 성능, 유지보수성을 향상시키기 위한 추가 요소를 포함합니다.  
실제 적용 시 테스트 환경에서 충분히 검증한 후 배포하시기 바랍니다.