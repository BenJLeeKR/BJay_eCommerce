from __future__ import annotations

import logging
from typing import Any, Optional

from elasticsearch import Elasticsearch

from app.core.config import settings
from app.database import SessionLocal
from app.models.search import SearchProductIndex

logger = logging.getLogger(__name__)

_es_client: Optional[Elasticsearch] = None

ES_INDEX_NAME = "products"

# Elasticsearch 인덱스 매핑 정의
ES_INDEX_MAPPINGS: dict[str, Any] = {
    "mappings": {
        "properties": {
            "product_id": {"type": "long"},
            "product_name": {
                "type": "text",
                "fields": {"keyword": {"type": "keyword"}},
            },
            "product_description": {"type": "text"},
            "category_ids": {"type": "long"},
            "brand_name": {"type": "keyword"},
            "price_amount": {"type": "double"},
            "average_rating": {"type": "double"},
            "review_count": {"type": "integer"},
            "stock_quantity": {"type": "integer"},
            "is_active": {"type": "boolean"},
            "search_keywords": {"type": "text"},
            "updated_at": {"type": "date"},
        }
    }
}


def get_es_client() -> Elasticsearch:
    """Elasticsearch 클라이언트 싱글톤을 반환한다."""
    global _es_client
    if _es_client is None:
        _es_client = Elasticsearch(settings.ELASTICSEARCH_URL)
        logger.info("Elasticsearch client created: %s", settings.ELASTICSEARCH_URL)
    return _es_client


def ensure_index_exists() -> None:
    """ES 인덱스가 없으면 생성한다."""
    es = get_es_client()
    if not es.indices.exists(index=ES_INDEX_NAME):
        es.indices.create(index=ES_INDEX_NAME, body=ES_INDEX_MAPPINGS)
        logger.info("ES index created: %s", ES_INDEX_NAME)
    else:
        logger.debug("ES index already exists: %s", ES_INDEX_NAME)


async def index_product(product_id: int) -> bool:
    """SearchProductIndex DB 레코드를 Elasticsearch에 인덱싱한다.

    Args:
        product_id: 인덱싱할 상품 ID

    Returns:
        성공 시 True, 실패 시 False
    """
    es = get_es_client()
    db = SessionLocal()
    try:
        index = db.query(SearchProductIndex).filter(
            SearchProductIndex.product_id == product_id
        ).first()
        if index is None:
            logger.warning(
                "SearchProductIndex not found: product_id=%s", product_id
            )
            return False

        doc = {
            "product_id": index.product_id,
            "product_name": index.product_name,
            "product_description": index.product_description,
            "category_ids": index.category_ids,
            "brand_name": index.brand_name,
            "price_amount": float(index.price_amount) if index.price_amount else None,
            "average_rating": (
                float(index.average_rating) if index.average_rating else None
            ),
            "review_count": index.review_count,
            "stock_quantity": index.stock_quantity,
            "is_active": index.is_active,
            "search_keywords": index.search_keywords,
            "updated_at": (
                index.updated_at.isoformat() if index.updated_at else None
            ),
        }

        es.index(index=ES_INDEX_NAME, id=product_id, body=doc)
        logger.info("ES indexed: product_id=%s", product_id)
        return True
    except Exception as exc:
        logger.error(
            "ES index failed: product_id=%s error=%s", product_id, exc
        )
        return False
    finally:
        db.close()


async def delete_product(product_id: int) -> bool:
    """Elasticsearch에서 상품 문서를 삭제한다.

    Args:
        product_id: 삭제할 상품 ID

    Returns:
        성공 시 True, 실패 시 False
    """
    es = get_es_client()
    try:
        es.delete(index=ES_INDEX_NAME, id=product_id, ignore=[404])
        logger.info("ES deleted: product_id=%s", product_id)
        return True
    except Exception as exc:
        logger.error(
            "ES delete failed: product_id=%s error=%s", product_id, exc
        )
        return False


__all__ = [
    "get_es_client",
    "ensure_index_exists",
    "index_product",
    "delete_product",
]
