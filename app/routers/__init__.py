from fastapi import APIRouter

from app.routers.auth import router as auth_router
from app.routers.brand import router as brand_router
from app.routers.category import router as category_router
from app.routers.product import router as product_router
from app.routers.sku import router as sku_router
from app.routers.user import router as user_router, role_router
from app.routers.cart import router as cart_router
from app.routers.inventory import router as inventory_router
from app.routers.order import router as order_router
from app.routers.payment import router as payment_router
from app.routers.promotion import router as promotion_router
from app.routers.shipment import router as shipment_router
from app.routers.review import router as review_router
from app.routers.search import router as search_router
from app.routers.admin import router as admin_router

router = APIRouter(tags=["system"])


@router.get("/health", summary="헬스 체크")
def health_check() -> dict[str, str]:
    """서비스 상태를 반환한다."""
    return {"status": "ok"}


api_router = APIRouter()
api_router.include_router(router)
api_router.include_router(brand_router)
api_router.include_router(category_router)
api_router.include_router(product_router)
api_router.include_router(sku_router)
api_router.include_router(user_router)
api_router.include_router(cart_router)
api_router.include_router(order_router)
api_router.include_router(payment_router)
api_router.include_router(inventory_router)
api_router.include_router(shipment_router)
api_router.include_router(promotion_router)
api_router.include_router(review_router)
api_router.include_router(search_router)
api_router.include_router(admin_router)
api_router.include_router(auth_router)
api_router.include_router(role_router)


__all__ = [
    "api_router",
    "brand_router",
    "category_router",
    "product_router",
    "sku_router",
    "user_router",
    "cart_router",
    "inventory_router",
    "order_router",
    "payment_router",
    "promotion_router",
    "shipment_router",
    "review_router",
    "search_router",
    "admin_router",
    "role_router",
    "auth_router",
    "router",
]
