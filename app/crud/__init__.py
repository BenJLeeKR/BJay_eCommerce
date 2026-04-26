from typing import Any, Generic, Optional, TypeVar

from sqlalchemy.orm import Session

from app.database import Base

ModelType = TypeVar("ModelType", bound=Base)


class CRUDBase(Generic[ModelType]):
    """도메인 CRUD 구현에서 재사용할 수 있는 최소 공통 베이스 클래스."""

    def __init__(self, model: type[ModelType]):
        self.model = model

    def get(self, db: Session, object_id: Any) -> Optional[ModelType]:
        """기본 키 기준으로 단일 객체를 조회한다."""
        return db.get(self.model, object_id)


# User Domain
from app.crud.user_crud import (
    UserAccountCRUD,
    UserProfileCRUD,
    UserAddressCRUD,
    UserAuthCRUD,
    UserLoginHistoryCRUD,
    UserRoleCRUD,
    UserRoleMapCRUD,
    user_account_crud,
    user_profile_crud,
    user_address_crud,
    user_auth_crud,
    user_login_history_crud,
    user_role_crud,
    user_role_map_crud,
)

# Product Domain
from app.crud.product_crud import (
    BrandCRUD,
    CategoryCRUD,
    ProductCRUD,
    ProductCategoryMapCRUD,
    ProductOptionCRUD,
    ProductOptionValueCRUD,
    SKUCRUD,
    SKUOptionValueMapCRUD,
    ProductImageCRUD,
    brand_crud,
    category_crud,
    product_crud,
    product_category_map_crud,
    product_option_crud,
    product_option_value_crud,
    sku_crud,
    sku_option_value_map_crud,
    product_image_crud,
)

# Cart Domain
from app.crud.cart_crud import (
    CartCRUD,
    CartItemCRUD,
    CartItemOptionSnapshotCRUD,
    CartCouponCRUD,
    cart_crud,
    cart_item_crud,
    cart_item_option_snapshot_crud,
    cart_coupon_crud,
)

# Order Domain
from app.crud.order_crud import (
    OrderHeaderCRUD,
    OrderItemCRUD,
    OrderStatusHistoryCRUD,
    OrderPaymentCRUD,
    OrderShipmentCRUD,
    OrderAddressSnapshotCRUD,
    OrderCouponCRUD,
    order_header_crud,
    order_item_crud,
    order_status_history_crud,
    order_payment_crud,
    order_shipment_crud,
    order_address_snapshot_crud,
    order_coupon_crud,
)

# Payment Domain
from app.crud.payment_crud import (
    PaymentCRUD,
    PaymentTransactionCRUD,
    PaymentMethodCRUD,
    PaymentRefundCRUD,
    PaymentLogCRUD,
    payment_crud,
    payment_transaction_crud,
    payment_method_crud,
    payment_refund_crud,
    payment_log_crud,
)

# Inventory Domain
from app.crud.inventory_crud import (
    InventoryCRUD,
    InventoryReservationCRUD,
    InventoryTransactionCRUD,
    WarehouseStockCRUD,
    InventoryAdjustmentCRUD,
    inventory_crud,
    inventory_reservation_crud,
    inventory_transaction_crud,
    warehouse_stock_crud,
    inventory_adjustment_crud,
)

# Shipment Domain
from app.crud.shipment_crud import (
    ShipmentCRUD,
    ShipmentItemCRUD,
    ShipmentTrackingCRUD,
    ShipmentStatusHistoryCRUD,
    WarehouseCRUD,
    ShipmentPackageCRUD,
    shipment_crud,
    shipment_item_crud,
    shipment_tracking_crud,
    shipment_status_history_crud,
    warehouse_crud,
    shipment_package_crud,
)

# Promotion Domain
from app.crud.promotion_crud import (
    PromotionCRUD,
    PromotionConditionCRUD,
    PromotionTargetCRUD,
    CouponCRUD,
    CouponIssueCRUD,
    CouponUsageCRUD,
    promotion_crud,
    promotion_condition_crud,
    promotion_target_crud,
    coupon_crud,
    coupon_issue_crud,
    coupon_usage_crud,
)

# Review Domain
from app.crud.review_crud import (
    ReviewCRUD,
    ReviewRatingCRUD,
    ReviewImageCRUD,
    ReviewLikeCRUD,
    ReviewReportCRUD,
    ReviewCommentCRUD,
    ProductReviewSummaryCRUD,
    review_crud,
    review_rating_crud,
    review_image_crud,
    review_like_crud,
    review_report_crud,
    review_comment_crud,
    product_review_summary_crud,
)

# Search Domain
from app.crud.search_crud import (
    SearchProductIndexCRUD,
    SearchKeywordCRUD,
    SearchAutocompleteCRUD,
    SearchSynonymCRUD,
    search_product_index_crud,
    search_keyword_crud,
    search_autocomplete_crud,
    search_synonym_crud,
)

# Admin Domain
from app.crud.admin_crud import (
    AdminAccountCRUD,
    AdminRoleCRUD,
    AdminPermissionCRUD,
    AdminRolePermissionMapCRUD,
    AdminAccountRoleMapCRUD,
    AdminMenuCRUD,
    AdminActionLogCRUD,
    AdminAccessLogCRUD,
    admin_account_crud,
    admin_role_crud,
    admin_permission_crud,
    admin_role_permission_map_crud,
    admin_account_role_map_crud,
    admin_menu_crud,
    admin_action_log_crud,
    admin_access_log_crud,
)

__all__ = [
    "CRUDBase",
    # User
    "UserAccountCRUD",
    "UserProfileCRUD",
    "UserAddressCRUD",
    "UserAuthCRUD",
    "UserLoginHistoryCRUD",
    "UserRoleCRUD",
    "UserRoleMapCRUD",
    "user_account_crud",
    "user_profile_crud",
    "user_address_crud",
    "user_auth_crud",
    "user_login_history_crud",
    "user_role_crud",
    "user_role_map_crud",
    # Product
    "BrandCRUD",
    "CategoryCRUD",
    "ProductCRUD",
    "ProductCategoryMapCRUD",
    "ProductOptionCRUD",
    "ProductOptionValueCRUD",
    "SKUCRUD",
    "SKUOptionValueMapCRUD",
    "ProductImageCRUD",
    "brand_crud",
    "category_crud",
    "product_crud",
    "product_category_map_crud",
    "product_option_crud",
    "product_option_value_crud",
    "sku_crud",
    "sku_option_value_map_crud",
    "product_image_crud",
    # Cart
    "CartCRUD",
    "CartItemCRUD",
    "CartItemOptionSnapshotCRUD",
    "CartCouponCRUD",
    "cart_crud",
    "cart_item_crud",
    "cart_item_option_snapshot_crud",
    "cart_coupon_crud",
    # Order
    "OrderHeaderCRUD",
    "OrderItemCRUD",
    "OrderStatusHistoryCRUD",
    "OrderPaymentCRUD",
    "OrderShipmentCRUD",
    "OrderAddressSnapshotCRUD",
    "OrderCouponCRUD",
    "order_header_crud",
    "order_item_crud",
    "order_status_history_crud",
    "order_payment_crud",
    "order_shipment_crud",
    "order_address_snapshot_crud",
    "order_coupon_crud",
    # Payment
    "PaymentCRUD",
    "PaymentTransactionCRUD",
    "PaymentMethodCRUD",
    "PaymentRefundCRUD",
    "PaymentLogCRUD",
    "payment_crud",
    "payment_transaction_crud",
    "payment_method_crud",
    "payment_refund_crud",
    "payment_log_crud",
    # Inventory
    "InventoryCRUD",
    "InventoryReservationCRUD",
    "InventoryTransactionCRUD",
    "WarehouseStockCRUD",
    "InventoryAdjustmentCRUD",
    "inventory_crud",
    "inventory_reservation_crud",
    "inventory_transaction_crud",
    "warehouse_stock_crud",
    "inventory_adjustment_crud",
    # Shipment
    "ShipmentCRUD",
    "ShipmentItemCRUD",
    "ShipmentTrackingCRUD",
    "ShipmentStatusHistoryCRUD",
    "WarehouseCRUD",
    "ShipmentPackageCRUD",
    "shipment_crud",
    "shipment_item_crud",
    "shipment_tracking_crud",
    "shipment_status_history_crud",
    "warehouse_crud",
    "shipment_package_crud",
    # Promotion
    "PromotionCRUD",
    "PromotionConditionCRUD",
    "PromotionTargetCRUD",
    "CouponCRUD",
    "CouponIssueCRUD",
    "CouponUsageCRUD",
    "promotion_crud",
    "promotion_condition_crud",
    "promotion_target_crud",
    "coupon_crud",
    "coupon_issue_crud",
    "coupon_usage_crud",
    # Review
    "ReviewCRUD",
    "ReviewRatingCRUD",
    "ReviewImageCRUD",
    "ReviewLikeCRUD",
    "ReviewReportCRUD",
    "ReviewCommentCRUD",
    "ProductReviewSummaryCRUD",
    "review_crud",
    "review_rating_crud",
    "review_image_crud",
    "review_like_crud",
    "review_report_crud",
    "review_comment_crud",
    "product_review_summary_crud",
    # Search
    "SearchProductIndexCRUD",
    "SearchKeywordCRUD",
    "SearchAutocompleteCRUD",
    "SearchSynonymCRUD",
    "search_product_index_crud",
    "search_keyword_crud",
    "search_autocomplete_crud",
    "search_synonym_crud",
    # Admin
    "AdminAccountCRUD",
    "AdminRoleCRUD",
    "AdminPermissionCRUD",
    "AdminRolePermissionMapCRUD",
    "AdminAccountRoleMapCRUD",
    "AdminMenuCRUD",
    "AdminActionLogCRUD",
    "AdminAccessLogCRUD",
    "admin_account_crud",
    "admin_role_crud",
    "admin_permission_crud",
    "admin_role_permission_map_crud",
    "admin_account_role_map_crud",
    "admin_menu_crud",
    "admin_action_log_crud",
    "admin_access_log_crud",
]
