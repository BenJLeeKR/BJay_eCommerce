-- ============================================================
-- E-Commerce System 초기화 스크립트
-- PostgreSQL docker-entrypoint-initdb.d 에서 자동 실행
-- ============================================================

-- 1. 스키마 생성
CREATE SCHEMA IF NOT EXISTS ecommerce;

-- 2. Product 도메인
CREATE TABLE IF NOT EXISTS ecommerce.product (
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

CREATE TABLE IF NOT EXISTS ecommerce.brand (
    id BIGSERIAL PRIMARY KEY,
    brand_name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    created_by BIGINT,
    updated_at TIMESTAMP,
    updated_by BIGINT,
    deleted_at TIMESTAMP,
    deleted_by BIGINT
);

CREATE TABLE IF NOT EXISTS ecommerce.category (
    id BIGSERIAL PRIMARY KEY,
    parent_category_id BIGINT,
    category_name VARCHAR(255) NOT NULL,
    category_depth INT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    created_by BIGINT,
    updated_at TIMESTAMP,
    updated_by BIGINT,
    deleted_at TIMESTAMP,
    deleted_by BIGINT
);

CREATE TABLE IF NOT EXISTS ecommerce.product_category_map (
    product_id BIGINT NOT NULL,
    category_id BIGINT NOT NULL,
    PRIMARY KEY (product_id, category_id)
);

CREATE TABLE IF NOT EXISTS ecommerce.product_option (
    id BIGSERIAL PRIMARY KEY,
    product_id BIGINT NOT NULL,
    option_name VARCHAR(100) NOT NULL,
    sort_order INT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    created_by BIGINT,
    updated_at TIMESTAMP,
    updated_by BIGINT,
    deleted_at TIMESTAMP,
    deleted_by BIGINT
);

CREATE TABLE IF NOT EXISTS ecommerce.product_option_value (
    id BIGSERIAL PRIMARY KEY,
    option_id BIGINT NOT NULL,
    option_value VARCHAR(100) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    created_by BIGINT,
    updated_at TIMESTAMP,
    updated_by BIGINT,
    deleted_at TIMESTAMP,
    deleted_by BIGINT
);

CREATE TABLE IF NOT EXISTS ecommerce.sku (
    id BIGSERIAL PRIMARY KEY,
    product_id BIGINT NOT NULL,
    sku_code VARCHAR(100) NOT NULL UNIQUE,
    sale_price_amount NUMERIC(12,2) NOT NULL,
    stock_quantity INT NOT NULL DEFAULT 0,
    sku_status VARCHAR(20) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    created_by BIGINT,
    updated_at TIMESTAMP,
    updated_by BIGINT,
    deleted_at TIMESTAMP,
    deleted_by BIGINT
);

CREATE TABLE IF NOT EXISTS ecommerce.sku_option_value_map (
    sku_id BIGINT NOT NULL,
    option_value_id BIGINT NOT NULL,
    PRIMARY KEY (sku_id, option_value_id)
);

CREATE TABLE IF NOT EXISTS ecommerce.product_image (
    id BIGSERIAL PRIMARY KEY,
    product_id BIGINT NOT NULL,
    image_url TEXT NOT NULL,
    is_main_image BOOLEAN DEFAULT FALSE,
    sort_order INT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    created_by BIGINT,
    updated_at TIMESTAMP,
    updated_by BIGINT,
    deleted_at TIMESTAMP,
    deleted_by BIGINT
);

-- 3. User 도메인
CREATE TABLE IF NOT EXISTS ecommerce.user_account (
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

CREATE TABLE IF NOT EXISTS ecommerce.user_profile (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    user_name VARCHAR(100),
    phone_number VARCHAR(50),
    birth_date DATE,
    gender_code VARCHAR(10),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    created_by BIGINT,
    updated_at TIMESTAMP,
    updated_by BIGINT,
    deleted_at TIMESTAMP,
    deleted_by BIGINT
);

CREATE TABLE IF NOT EXISTS ecommerce.user_address (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    address_name VARCHAR(100),
    recipient_name VARCHAR(100),
    recipient_phone VARCHAR(50),
    postal_code VARCHAR(20),
    address_line1 VARCHAR(255),
    address_line2 VARCHAR(255),
    is_default_address BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    created_by BIGINT,
    updated_at TIMESTAMP,
    updated_by BIGINT,
    deleted_at TIMESTAMP,
    deleted_by BIGINT
);

CREATE TABLE IF NOT EXISTS ecommerce.user_auth (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    auth_provider VARCHAR(50) NOT NULL,
    provider_user_id VARCHAR(255),
    refresh_token TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    created_by BIGINT,
    updated_at TIMESTAMP,
    updated_by BIGINT,
    deleted_at TIMESTAMP,
    deleted_by BIGINT
);

CREATE TABLE IF NOT EXISTS ecommerce.user_login_history (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    login_at TIMESTAMP NOT NULL DEFAULT NOW(),
    ip_address VARCHAR(50),
    user_agent TEXT,
    login_result VARCHAR(20),
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ecommerce.user_role (
    id BIGSERIAL PRIMARY KEY,
    role_name VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ecommerce.user_role_map (
    user_id BIGINT NOT NULL,
    role_id BIGINT NOT NULL,
    PRIMARY KEY (user_id, role_id)
);

-- 4. Cart 도메인
CREATE TABLE IF NOT EXISTS ecommerce.cart (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT,
    session_id VARCHAR(255),
    cart_status VARCHAR(20) NOT NULL,
    last_added_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    created_by BIGINT,
    updated_at TIMESTAMP,
    updated_by BIGINT,
    deleted_at TIMESTAMP,
    deleted_by BIGINT
);

CREATE TABLE IF NOT EXISTS ecommerce.cart_item (
    id BIGSERIAL PRIMARY KEY,
    cart_id BIGINT NOT NULL,
    sku_id BIGINT NOT NULL,
    quantity INT NOT NULL,
    unit_price_amount NUMERIC(12,2) NOT NULL,
    total_price_amount NUMERIC(12,2) NOT NULL,
    is_selected BOOLEAN DEFAULT TRUE,
    added_at TIMESTAMP NOT NULL DEFAULT NOW(),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    created_by BIGINT,
    updated_at TIMESTAMP,
    updated_by BIGINT,
    deleted_at TIMESTAMP,
    deleted_by BIGINT
);

CREATE TABLE IF NOT EXISTS ecommerce.cart_item_option_snapshot (
    id BIGSERIAL PRIMARY KEY,
    cart_item_id BIGINT NOT NULL,
    option_name VARCHAR(100),
    option_value VARCHAR(100),
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ecommerce.cart_coupon (
    id BIGSERIAL PRIMARY KEY,
    cart_id BIGINT NOT NULL,
    coupon_id BIGINT NOT NULL,
    discount_amount NUMERIC(12,2),
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- 5. Order 도메인
CREATE TABLE IF NOT EXISTS ecommerce.order_header (
    id BIGSERIAL PRIMARY KEY,
    order_number VARCHAR(50) NOT NULL UNIQUE,
    user_id BIGINT NOT NULL,
    order_status VARCHAR(30) NOT NULL,
    total_product_amount NUMERIC(12,2) NOT NULL,
    total_discount_amount NUMERIC(12,2) DEFAULT 0,
    total_shipping_amount NUMERIC(12,2) DEFAULT 0,
    total_pay_amount NUMERIC(12,2) NOT NULL,
    ordered_at TIMESTAMP NOT NULL DEFAULT NOW(),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    created_by BIGINT,
    updated_at TIMESTAMP,
    updated_by BIGINT,
    deleted_at TIMESTAMP,
    deleted_by BIGINT
);

CREATE TABLE IF NOT EXISTS ecommerce.order_item (
    id BIGSERIAL PRIMARY KEY,
    order_id BIGINT NOT NULL,
    sku_id BIGINT NOT NULL,
    product_name VARCHAR(255) NOT NULL,
    option_summary TEXT,
    quantity INT NOT NULL,
    unit_price_amount NUMERIC(12,2) NOT NULL,
    total_price_amount NUMERIC(12,2) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    created_by BIGINT,
    updated_at TIMESTAMP,
    updated_by BIGINT,
    deleted_at TIMESTAMP,
    deleted_by BIGINT
);

CREATE TABLE IF NOT EXISTS ecommerce.order_status_history (
    id BIGSERIAL PRIMARY KEY,
    order_id BIGINT NOT NULL,
    order_status VARCHAR(30) NOT NULL,
    changed_at TIMESTAMP NOT NULL DEFAULT NOW(),
    changed_by BIGINT,
    change_reason TEXT
);

CREATE TABLE IF NOT EXISTS ecommerce.order_payment (
    id BIGSERIAL PRIMARY KEY,
    order_id BIGINT NOT NULL,
    payment_method VARCHAR(50),
    payment_status VARCHAR(30) DEFAULT 'PENDING' NOT NULL,
    pg_transaction_id VARCHAR(100),
    paid_amount NUMERIC(12,2) NOT NULL,
    paid_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ecommerce.order_shipment (
    id BIGSERIAL PRIMARY KEY,
    order_id BIGINT NOT NULL,
    shipment_status VARCHAR(30) NOT NULL,
    courier_name VARCHAR(100),
    tracking_number VARCHAR(100),
    shipped_at TIMESTAMP,
    delivered_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ecommerce.order_address_snapshot (
    id BIGSERIAL PRIMARY KEY,
    order_id BIGINT NOT NULL,
    recipient_name VARCHAR(100),
    recipient_phone VARCHAR(50),
    postal_code VARCHAR(20),
    address_line1 VARCHAR(255),
    address_line2 VARCHAR(255),
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ecommerce.order_coupon (
    id BIGSERIAL PRIMARY KEY,
    order_id BIGINT NOT NULL,
    coupon_id BIGINT NOT NULL,
    discount_amount NUMERIC(12,2),
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- 6. Payment 도메인
CREATE TABLE IF NOT EXISTS ecommerce.payment (
    id BIGSERIAL PRIMARY KEY,
    order_id BIGINT NOT NULL,
    payment_status VARCHAR(30) NOT NULL,
    payment_amount NUMERIC(12,2) NOT NULL,
    paid_amount NUMERIC(12,2) DEFAULT 0,
    currency_code VARCHAR(10) DEFAULT 'KRW',
    payment_method_code VARCHAR(50),
    idempotency_key VARCHAR(255) UNIQUE,
    requested_at TIMESTAMP NOT NULL DEFAULT NOW(),
    approved_at TIMESTAMP,
    cancelled_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    created_by BIGINT,
    updated_at TIMESTAMP,
    updated_by BIGINT,
    deleted_at TIMESTAMP,
    deleted_by BIGINT
);

CREATE TABLE IF NOT EXISTS ecommerce.payment_transaction (
    id BIGSERIAL PRIMARY KEY,
    payment_id BIGINT NOT NULL,
    transaction_type VARCHAR(30) NOT NULL,
    transaction_status VARCHAR(30) NOT NULL,
    transaction_amount NUMERIC(12,2) NOT NULL,
    pg_provider VARCHAR(50),
    pg_transaction_id VARCHAR(255),
    pg_response_raw JSONB,
    requested_at TIMESTAMP NOT NULL DEFAULT NOW(),
    responded_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ecommerce.payment_method (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    payment_method_code VARCHAR(50) NOT NULL,
    card_token VARCHAR(255),
    card_last4 VARCHAR(10),
    is_default BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP,
    deleted_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ecommerce.payment_refund (
    id BIGSERIAL PRIMARY KEY,
    payment_id BIGINT NOT NULL,
    refund_amount NUMERIC(12,2) NOT NULL,
    refund_reason TEXT,
    refund_status VARCHAR(30) NOT NULL,
    requested_at TIMESTAMP NOT NULL DEFAULT NOW(),
    processed_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ecommerce.payment_log (
    id BIGSERIAL PRIMARY KEY,
    payment_id BIGINT,
    log_type VARCHAR(50),
    log_message TEXT,
    log_data JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- 7. Inventory 도메인
CREATE TABLE IF NOT EXISTS ecommerce.inventory (
    id BIGSERIAL PRIMARY KEY,
    sku_id BIGINT NOT NULL UNIQUE,
    total_quantity INT NOT NULL,
    available_quantity INT NOT NULL,
    reserved_quantity INT NOT NULL,
    safety_stock_quantity INT DEFAULT 0,
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    created_by BIGINT
);

CREATE TABLE IF NOT EXISTS ecommerce.inventory_reservation (
    id BIGSERIAL PRIMARY KEY,
    sku_id BIGINT NOT NULL,
    order_id BIGINT NOT NULL,
    reserved_quantity INT NOT NULL,
    reservation_status VARCHAR(30) NOT NULL,
    expired_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ecommerce.inventory_transaction (
    id BIGSERIAL PRIMARY KEY,
    sku_id BIGINT NOT NULL,
    transaction_type VARCHAR(50) NOT NULL,
    quantity INT NOT NULL,
    reference_type VARCHAR(50),
    reference_id BIGINT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ecommerce.warehouse_stock (
    id BIGSERIAL PRIMARY KEY,
    warehouse_id BIGINT NOT NULL,
    sku_id BIGINT NOT NULL,
    stock_quantity INT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ecommerce.inventory_adjustment (
    id BIGSERIAL PRIMARY KEY,
    sku_id BIGINT NOT NULL,
    adjustment_quantity INT NOT NULL,
    adjustment_reason TEXT,
    created_by BIGINT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- 8. Shipment 도메인
CREATE TABLE IF NOT EXISTS ecommerce.shipment (
    id BIGSERIAL PRIMARY KEY,
    order_id BIGINT NOT NULL,
    shipment_status VARCHAR(30) NOT NULL,
    shipment_type VARCHAR(30),
    total_shipping_amount NUMERIC(12,2) DEFAULT 0,
    shipped_at TIMESTAMP,
    delivered_at TIMESTAMP,
    warehouse_id BIGINT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    created_by BIGINT,
    updated_at TIMESTAMP,
    updated_by BIGINT,
    deleted_at TIMESTAMP,
    deleted_by BIGINT
);

CREATE TABLE IF NOT EXISTS ecommerce.shipment_item (
    id BIGSERIAL PRIMARY KEY,
    shipment_id BIGINT NOT NULL,
    order_item_id BIGINT NOT NULL,
    sku_id BIGINT NOT NULL,
    shipped_quantity INT NOT NULL,
    delivered_quantity INT DEFAULT 0,
    shipment_item_status VARCHAR(30),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    created_by BIGINT,
    updated_at TIMESTAMP,
    updated_by BIGINT,
    deleted_at TIMESTAMP,
    deleted_by BIGINT
);

CREATE TABLE IF NOT EXISTS ecommerce.shipment_tracking (
    id BIGSERIAL PRIMARY KEY,
    shipment_id BIGINT NOT NULL,
    courier_code VARCHAR(50),
    tracking_number VARCHAR(100),
    tracking_status VARCHAR(50),
    last_tracked_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ecommerce.shipment_status_history (
    id BIGSERIAL PRIMARY KEY,
    shipment_id BIGINT NOT NULL,
    shipment_status VARCHAR(30) NOT NULL,
    changed_at TIMESTAMP NOT NULL DEFAULT NOW(),
    changed_by BIGINT,
    change_reason TEXT
);

CREATE TABLE IF NOT EXISTS ecommerce.warehouse (
    id BIGSERIAL PRIMARY KEY,
    warehouse_name VARCHAR(255) NOT NULL,
    postal_code VARCHAR(20),
    address_line1 VARCHAR(255),
    address_line2 VARCHAR(255),
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ecommerce.shipment_package (
    id BIGSERIAL PRIMARY KEY,
    shipment_id BIGINT NOT NULL,
    package_weight NUMERIC(10,2),
    package_volume NUMERIC(10,2),
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- 9. Promotion 도메인
CREATE TABLE IF NOT EXISTS ecommerce.promotion (
    id BIGSERIAL PRIMARY KEY,
    promotion_name VARCHAR(255) NOT NULL,
    promotion_type VARCHAR(50) NOT NULL,
    discount_type VARCHAR(50) NOT NULL,
    discount_value NUMERIC(12,2) NOT NULL,
    max_discount_amount NUMERIC(12,2),
    start_at TIMESTAMP NOT NULL,
    end_at TIMESTAMP NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    priority INT DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    created_by BIGINT,
    updated_at TIMESTAMP,
    updated_by BIGINT,
    deleted_at TIMESTAMP,
    deleted_by BIGINT
);

CREATE TABLE IF NOT EXISTS ecommerce.promotion_condition (
    id BIGSERIAL PRIMARY KEY,
    promotion_id BIGINT NOT NULL,
    condition_type VARCHAR(50) NOT NULL,
    condition_value JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ecommerce.promotion_target (
    id BIGSERIAL PRIMARY KEY,
    promotion_id BIGINT NOT NULL,
    target_type VARCHAR(50) NOT NULL,
    target_id BIGINT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ecommerce.coupon (
    id BIGSERIAL PRIMARY KEY,
    promotion_id BIGINT NOT NULL,
    coupon_code VARCHAR(100) UNIQUE,
    total_quantity INT,
    issued_quantity INT DEFAULT 0,
    per_user_limit INT DEFAULT 1,
    valid_from TIMESTAMP,
    valid_to TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    created_by BIGINT,
    deleted_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ecommerce.coupon_issue (
    id BIGSERIAL PRIMARY KEY,
    coupon_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    issued_at TIMESTAMP NOT NULL DEFAULT NOW(),
    expire_at TIMESTAMP,
    is_used BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ecommerce.coupon_usage (
    id BIGSERIAL PRIMARY KEY,
    coupon_issue_id BIGINT NOT NULL,
    order_id BIGINT NOT NULL,
    discount_amount NUMERIC(12,2),
    used_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- 10. Review 도메인
CREATE TABLE IF NOT EXISTS ecommerce.review (
    id BIGSERIAL PRIMARY KEY,
    product_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    order_item_id BIGINT NOT NULL,
    review_title VARCHAR(255),
    review_content TEXT,
    review_status VARCHAR(30) NOT NULL,
    is_verified_purchase BOOLEAN DEFAULT TRUE,
    like_count INT DEFAULT 0,
    comment_count INT DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    created_by BIGINT,
    updated_at TIMESTAMP,
    updated_by BIGINT,
    deleted_at TIMESTAMP,
    deleted_by BIGINT
);

CREATE TABLE IF NOT EXISTS ecommerce.review_rating (
    id BIGSERIAL PRIMARY KEY,
    review_id BIGINT NOT NULL,
    rating_score INT NOT NULL,
    rating_type VARCHAR(50),
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ecommerce.review_image (
    id BIGSERIAL PRIMARY KEY,
    review_id BIGINT NOT NULL,
    image_url TEXT NOT NULL,
    sort_order INT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ecommerce.review_like (
    review_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    PRIMARY KEY (review_id, user_id)
);

CREATE TABLE IF NOT EXISTS ecommerce.review_report (
    id BIGSERIAL PRIMARY KEY,
    review_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    report_reason VARCHAR(255),
    report_status VARCHAR(30),
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ecommerce.review_comment (
    id BIGSERIAL PRIMARY KEY,
    review_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    comment_content TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ecommerce.product_review_summary (
    product_id BIGINT PRIMARY KEY,
    average_rating NUMERIC(3,2),
    total_review_count INT,
    rating_1_count INT DEFAULT 0,
    rating_2_count INT DEFAULT 0,
    rating_3_count INT DEFAULT 0,
    rating_4_count INT DEFAULT 0,
    rating_5_count INT DEFAULT 0,
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- 11. Search 도메인
CREATE TABLE IF NOT EXISTS ecommerce.search_product_index (
    product_id BIGINT PRIMARY KEY,
    product_name VARCHAR(255),
    product_description TEXT,
    category_ids BIGINT[],
    brand_name VARCHAR(255),
    price_amount NUMERIC(12,2),
    average_rating NUMERIC(3,2),
    review_count INT,
    stock_quantity INT,
    is_active BOOLEAN,
    search_keywords TEXT,
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ecommerce.search_keyword (
    keyword VARCHAR(255) PRIMARY KEY,
    search_count INT DEFAULT 0,
    last_searched_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ecommerce.search_autocomplete (
    id BIGSERIAL PRIMARY KEY,
    keyword VARCHAR(255),
    weight INT DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ecommerce.search_synonym (
    id BIGSERIAL PRIMARY KEY,
    keyword VARCHAR(255),
    synonym VARCHAR(255),
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- 12. Admin 도메인
CREATE TABLE IF NOT EXISTS ecommerce.admin_account (
    id BIGSERIAL PRIMARY KEY,
    admin_email VARCHAR(255) NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    admin_status VARCHAR(20) NOT NULL,
    last_login_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    created_by BIGINT,
    updated_at TIMESTAMP,
    updated_by BIGINT,
    deleted_at TIMESTAMP,
    deleted_by BIGINT
);

CREATE TABLE IF NOT EXISTS ecommerce.admin_role (
    id BIGSERIAL PRIMARY KEY,
    role_name VARCHAR(100) NOT NULL,
    role_description TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ecommerce.admin_permission (
    id BIGSERIAL PRIMARY KEY,
    permission_code VARCHAR(100) NOT NULL UNIQUE,
    permission_name VARCHAR(255),
    resource_type VARCHAR(50),
    action_type VARCHAR(50),
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ecommerce.admin_role_permission_map (
    role_id BIGINT NOT NULL,
    permission_id BIGINT NOT NULL,
    PRIMARY KEY (role_id, permission_id)
);

CREATE TABLE IF NOT EXISTS ecommerce.admin_account_role_map (
    admin_id BIGINT NOT NULL,
    role_id BIGINT NOT NULL,
    PRIMARY KEY (admin_id, role_id)
);

CREATE TABLE IF NOT EXISTS ecommerce.admin_menu (
    id BIGSERIAL PRIMARY KEY,
    parent_menu_id BIGINT,
    menu_name VARCHAR(255),
    menu_path VARCHAR(255),
    sort_order INT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ecommerce.admin_action_log (
    id BIGSERIAL PRIMARY KEY,
    admin_id BIGINT NOT NULL,
    action_type VARCHAR(50),
    target_table VARCHAR(100),
    target_id BIGINT,
    action_data JSONB,
    ip_address VARCHAR(50),
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ecommerce.admin_access_log (
    id BIGSERIAL PRIMARY KEY,
    admin_id BIGINT,
    login_result VARCHAR(20),
    ip_address VARCHAR(50),
    user_agent TEXT,
    accessed_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- 13. 외래키 제약조건
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

ALTER TABLE ecommerce.payment ADD CONSTRAINT fk_payment_order
    FOREIGN KEY (order_id) REFERENCES ecommerce.order_header(id) ON DELETE RESTRICT;

ALTER TABLE ecommerce.inventory ADD CONSTRAINT fk_inventory_sku
    FOREIGN KEY (sku_id) REFERENCES ecommerce.sku(id) ON DELETE CASCADE;

ALTER TABLE ecommerce.shipment ADD CONSTRAINT fk_shipment_order
    FOREIGN KEY (order_id) REFERENCES ecommerce.order_header(id) ON DELETE RESTRICT;

-- 14. 인덱스
CREATE INDEX IF NOT EXISTS idx_product_brand_id ON ecommerce.product(brand_id);
CREATE INDEX IF NOT EXISTS idx_product_status ON ecommerce.product(product_status);
CREATE INDEX IF NOT EXISTS idx_sku_product_id ON ecommerce.sku(product_id);
CREATE INDEX IF NOT EXISTS idx_cart_user_id ON ecommerce.cart(user_id);
CREATE INDEX IF NOT EXISTS idx_cart_session_id ON ecommerce.cart(session_id);
CREATE INDEX IF NOT EXISTS idx_cart_item_cart_id ON ecommerce.cart_item(cart_id);
CREATE UNIQUE INDEX IF NOT EXISTS uq_cart_item ON ecommerce.cart_item(cart_id, sku_id);
CREATE INDEX IF NOT EXISTS idx_order_user_id ON ecommerce.order_header(user_id);
CREATE INDEX IF NOT EXISTS idx_order_status ON ecommerce.order_header(order_status);
CREATE INDEX IF NOT EXISTS idx_payment_order_id ON ecommerce.payment(order_id);
CREATE INDEX IF NOT EXISTS idx_inventory_sku_id ON ecommerce.inventory(sku_id);
CREATE INDEX IF NOT EXISTS idx_shipment_order_id ON ecommerce.shipment(order_id);
