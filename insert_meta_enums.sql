-- ============================================================
-- meta.meta_enum INSERT SQL
-- 
-- 모든 ecommerce 스키마의 유효한 enum 값을 meta.meta_enum
-- 테이블에 추가합니다.
--
-- 생성일: 2026-04-25
-- ============================================================

-- ============================================================
-- 그룹 A: reference_docs에 명시적 INSERT 구문이 있는 enum 타입
-- ============================================================

-- 1. user_status (02.Users.sql)
INSERT INTO meta.meta_enum (enum_type, enum_value, description) VALUES
('user_status', 'ACTIVE', '정상'),
('user_status', 'SUSPENDED', '정지'),
('user_status', 'DELETED', '삭제');

-- 2. user_type (02.Users.sql)
INSERT INTO meta.meta_enum (enum_type, enum_value, description) VALUES
('user_type', 'NORMAL', '일반회원'),
('user_type', 'ADMIN', '관리자'),
('user_type', 'SELLER', '판매자');

-- 3. auth_provider (02.Users.sql)
INSERT INTO meta.meta_enum (enum_type, enum_value, description) VALUES
('auth_provider', 'LOCAL', '일반로그인'),
('auth_provider', 'GOOGLE', '구글'),
('auth_provider', 'KAKAO', '카카오');

-- 4. cart_status (03.Cart.sql)
INSERT INTO meta.meta_enum (enum_type, enum_value, description) VALUES
('cart_status', 'ACTIVE', '사용중'),
('cart_status', 'ORDERED', '주문완료'),
('cart_status', 'ABANDONED', '미사용');

-- 5. order_status (04.Order.sql)
INSERT INTO meta.meta_enum (enum_type, enum_value, description) VALUES
('order_status', 'CREATED', '주문생성'),
('order_status', 'PAID', '결제완료'),
('order_status', 'SHIPPING', '배송준비중'),
('order_status', 'SHIPPED', '배송중'),
('order_status', 'DELIVERED', '배송완료'),
('order_status', 'COMPLETED', '완료'),
('order_status', 'CANCELLED', '취소'),
('order_status', 'REFUNDED', '환불'),
('order_status', 'PAYMENT_PENDING', '결제대기');

-- 6. payment_status (04.Order.sql + 05.Payment.sql + order_payment DEFAULT 'PENDING')
INSERT INTO meta.meta_enum (enum_type, enum_value, description) VALUES
('payment_status', 'PENDING', '결제대기'),
('payment_status', 'READY', '결제준비'),
('payment_status', 'SUCCESS', '결제성공'),
('payment_status', 'FAIL', '결제실패'),
('payment_status', 'CANCEL', '결제취소'),
('payment_status', 'REFUNDED', '환불');

-- 7. shipment_status (04.Order.sql + 07.Shipment.sql)
INSERT INTO meta.meta_enum (enum_type, enum_value, description) VALUES
('shipment_status', 'READY', '배송준비'),
('shipment_status', 'PACKING', '포장중'),
('shipment_status', 'SHIPPED', '배송중'),
('shipment_status', 'DELIVERED', '배송완료'),
('shipment_status', 'RETURNED', '반품'),
('shipment_status', 'CANCELLED', '취소');

-- 8. transaction_type (05.Payment.sql)
INSERT INTO meta.meta_enum (enum_type, enum_value, description) VALUES
('transaction_type', 'AUTHORIZE', '승인'),
('transaction_type', 'CAPTURE', '매입'),
('transaction_type', 'CANCEL', '취소'),
('transaction_type', 'REFUND', '환불');

-- 9. transaction_status (05.Payment.sql)
INSERT INTO meta.meta_enum (enum_type, enum_value, description) VALUES
('transaction_status', 'SUCCESS', '성공'),
('transaction_status', 'FAIL', '실패');

-- 10. refund_status (05.Payment.sql)
INSERT INTO meta.meta_enum (enum_type, enum_value, description) VALUES
('refund_status', 'REQUESTED', '환불요청'),
('refund_status', 'SUCCESS', '환불완료'),
('refund_status', 'FAIL', '환불실패');

-- 11. reservation_status (06.Inventory.sql)
INSERT INTO meta.meta_enum (enum_type, enum_value, description) VALUES
('reservation_status', 'RESERVED', '예약'),
('reservation_status', 'CONFIRMED', '확정'),
('reservation_status', 'RELEASED', '해제');

-- 12. inventory_transaction_type (06.Inventory.sql)
INSERT INTO meta.meta_enum (enum_type, enum_value, description) VALUES
('inventory_transaction_type', 'IN', '입고'),
('inventory_transaction_type', 'OUT', '출고'),
('inventory_transaction_type', 'RESERVE', '예약'),
('inventory_transaction_type', 'RELEASE', '해제');

-- 13. shipment_item_status (07.Shipment.sql)
INSERT INTO meta.meta_enum (enum_type, enum_value, description) VALUES
('shipment_item_status', 'READY', '준비'),
('shipment_item_status', 'SHIPPED', '출고'),
('shipment_item_status', 'DELIVERED', '완료');

-- 14. shipment_type (07.Shipment.sql)
INSERT INTO meta.meta_enum (enum_type, enum_value, description) VALUES
('shipment_type', 'NORMAL', '일반배송'),
('shipment_type', 'EXPRESS', '빠른배송'),
('shipment_type', 'SAME_DAY', '당일배송');

-- 15. promotion_type (08.Promotion.sql)
INSERT INTO meta.meta_enum (enum_type, enum_value, description) VALUES
('promotion_type', 'COUPON', '쿠폰형'),
('promotion_type', 'AUTO', '자동적용');

-- 16. discount_type (08.Promotion.sql)
INSERT INTO meta.meta_enum (enum_type, enum_value, description) VALUES
('discount_type', 'RATE', '비율할인'),
('discount_type', 'FIXED', '정액할인');

-- 17. target_type (08.Promotion.sql)
INSERT INTO meta.meta_enum (enum_type, enum_value, description) VALUES
('target_type', 'ALL', '전체'),
('target_type', 'PRODUCT', '상품'),
('target_type', 'CATEGORY', '카테고리');

-- 18. review_status (09.Review.sql)
INSERT INTO meta.meta_enum (enum_type, enum_value, description) VALUES
('review_status', 'ACTIVE', '노출'),
('review_status', 'HIDDEN', '숨김'),
('review_status', 'DELETED', '삭제'),
('review_status', 'PENDING', '검토중');

-- 19. report_status (09.Review.sql)
INSERT INTO meta.meta_enum (enum_type, enum_value, description) VALUES
('report_status', 'PENDING', '대기'),
('report_status', 'RESOLVED', '처리완료');

-- 20. admin_status (11.Admin.sql)
INSERT INTO meta.meta_enum (enum_type, enum_value, description) VALUES
('admin_status', 'ACTIVE', '활성'),
('admin_status', 'INACTIVE', '비활성'),
('admin_status', 'LOCKED', '잠김');

-- 21. action_type (11.Admin.sql)
INSERT INTO meta.meta_enum (enum_type, enum_value, description) VALUES
('action_type', 'CREATE', '생성'),
('action_type', 'UPDATE', '수정'),
('action_type', 'DELETE', '삭제'),
('action_type', 'LOGIN', '로그인');

-- 22. resource_type (11.Admin.sql)
INSERT INTO meta.meta_enum (enum_type, enum_value, description) VALUES
('resource_type', 'MENU', '메뉴'),
('resource_type', 'API', 'API'),
('resource_type', 'BUTTON', '버튼');

-- 23. permission_action (11.Admin.sql)
INSERT INTO meta.meta_enum (enum_type, enum_value, description) VALUES
('permission_action', 'READ', '조회'),
('permission_action', 'WRITE', '쓰기'),
('permission_action', 'DELETE', '삭제'),
('permission_action', 'APPROVE', '승인');


-- ============================================================
-- 그룹 B: 컬럼 코멘트에만 정의되고 INSERT 누락된 enum 타입
-- ============================================================

-- 24. login_result (02.Users.sql user_login_history.login_result / 11.Admin.sql admin_access_log.login_result)
INSERT INTO meta.meta_enum (enum_type, enum_value, description) VALUES
('login_result', 'SUCCESS', '성공'),
('login_result', 'FAIL', '실패');

-- 25. payment_method_code (05.Payment.sql payment.payment_method_code + payment_method.payment_method_code)
INSERT INTO meta.meta_enum (enum_type, enum_value, description) VALUES
('payment_method_code', 'CARD', '카드'),
('payment_method_code', 'KAKAO_PAY', '카카오페이'),
('payment_method_code', 'NAVER_PAY', '네이버페이'),
('payment_method_code', 'EASY_PAY', '간편결제');

-- 26. pg_provider (05.Payment.sql payment_transaction.pg_provider)
INSERT INTO meta.meta_enum (enum_type, enum_value, description) VALUES
('pg_provider', 'STRIPE', '스트라이프'),
('pg_provider', 'TOSS', '토스');

-- 27. log_type (05.Payment.sql payment_log.log_type)
INSERT INTO meta.meta_enum (enum_type, enum_value, description) VALUES
('log_type', 'REQUEST', '요청'),
('log_type', 'RESPONSE', '응답'),
('log_type', 'ERROR', '에러');

-- 28. reference_type (06.Inventory.sql inventory_transaction.reference_type)
INSERT INTO meta.meta_enum (enum_type, enum_value, description) VALUES
('reference_type', 'ORDER', '주문'),
('reference_type', 'ADMIN', '관리자');

-- 29. courier_code (07.Shipment.sql shipment_tracking.courier_code)
INSERT INTO meta.meta_enum (enum_type, enum_value, description) VALUES
('courier_code', 'CJ', 'CJ대한통운'),
('courier_code', 'LOGEN', '로젠택배'),
('courier_code', 'UPS', 'UPS');

-- 30. rating_type (09.Review.sql review_rating.rating_type)
INSERT INTO meta.meta_enum (enum_type, enum_value, description) VALUES
('rating_type', 'QUALITY', '품질'),
('rating_type', 'DELIVERY', '배송'),
('rating_type', 'PRICE', '가격');


-- ============================================================
-- 그룹 C: 코멘트/INSERT 모두 없어 추론한 enum 타입
-- [주의] 이 값들은 reference_docs에 명시되지 않았으며,
-- 일반적인 ecommerce 도메인 지식에 기반하여 추론한 값입니다.
-- 필요에 따라 수정/추가/삭제하세요.
-- ============================================================

-- 31. product_status (01.Products.sql product.product_status)
INSERT INTO meta.meta_enum (enum_type, enum_value, description) VALUES
('product_status', 'ACTIVE', '판매중'),
('product_status', 'INACTIVE', '판매중지'),
('product_status', 'DISCONTINUED', '단종');

-- 32. sku_status (01.Products.sql sku.sku_status)
INSERT INTO meta.meta_enum (enum_type, enum_value, description) VALUES
('sku_status', 'ACTIVE', '판매중'),
('sku_status', 'INACTIVE', '판매중지');

-- 33. gender_code (02.Users.sql user_profile.gender_code)
INSERT INTO meta.meta_enum (enum_type, enum_value, description) VALUES
('gender_code', 'M', '남성'),
('gender_code', 'F', '여성'),
('gender_code', 'NONE', '선택안함');

-- 34. condition_type (08.Promotion.sql promotion_condition.condition_type)
INSERT INTO meta.meta_enum (enum_type, enum_value, description) VALUES
('condition_type', 'MIN_AMOUNT', '최소주문금액'),
('condition_type', 'MIN_COUNT', '최소수량');

-- 35. tracking_status (07.Shipment.sql shipment_tracking.tracking_status)
INSERT INTO meta.meta_enum (enum_type, enum_value, description) VALUES
('tracking_status', 'COLLECTED', '집하'),
('tracking_status', 'IN_TRANSIT', '배송중'),
('tracking_status', 'OUT_FOR_DELIVERY', '배송출발'),
('tracking_status', 'DELIVERED', '배송완료'),
('tracking_status', 'FAILED', '배송실패');
