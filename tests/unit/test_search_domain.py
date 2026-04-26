from decimal import Decimal

from app.models.search import SearchAutocomplete, SearchKeyword, SearchProductIndex, SearchSynonym
from app.routers.search import router
from app.schemas.search import (
    SearchAutocompleteCreate,
    SearchAutocompleteUpdate,
    SearchKeywordCreate,
    SearchKeywordUpdate,
    SearchProductIndexCreate,
    SearchProductIndexUpdate,
    SearchSynonymCreate,
    SearchSynonymUpdate,
)


def test_search_product_index_table_is_defined() -> None:
    """검색 인덱스 모델의 핵심 테이블 메타데이터가 정의되어야 한다."""
    assert SearchProductIndex.__tablename__ == "search_product_index"
    assert SearchProductIndex.__table__.c.product_id.primary_key is True
    assert SearchProductIndex.__table__.c.product_name.nullable is True
    assert SearchProductIndex.__table__.c.price_amount.nullable is True
    assert SearchProductIndex.__table__.c.updated_at.nullable is False


def test_search_keyword_table_is_defined() -> None:
    """검색 키워드 모델의 핵심 제약 조건이 정의되어야 한다."""
    assert SearchKeyword.__tablename__ == "search_keyword"
    assert SearchKeyword.__table__.c.keyword.primary_key is True
    assert SearchKeyword.__table__.c.search_count.nullable is False
    assert SearchKeyword.__table__.c.last_searched_at.nullable is True


def test_search_autocomplete_table_is_defined() -> None:
    """자동완성 모델의 핵심 테이블 메타데이터가 정의되어야 한다."""
    assert SearchAutocomplete.__tablename__ == "search_autocomplete"
    assert SearchAutocomplete.__table__.c.id.primary_key is True
    assert SearchAutocomplete.__table__.c.keyword.nullable is False
    assert SearchAutocomplete.__table__.c.weight.nullable is False
    assert SearchAutocomplete.__table__.c.created_at.nullable is False


def test_search_synonym_table_is_defined() -> None:
    """동의어 모델의 핵심 테이블 메타데이터가 정의되어야 한다."""
    assert SearchSynonym.__tablename__ == "search_synonym"
    assert SearchSynonym.__table__.c.id.primary_key is True
    assert SearchSynonym.__table__.c.keyword.nullable is False
    assert SearchSynonym.__table__.c.synonym.nullable is False
    assert SearchSynonym.__table__.c.created_at.nullable is False


def test_search_product_index_create_schema_validates_fields() -> None:
    """검색 인덱스 생성 스키마가 핵심 필드를 검증해야 한다."""
    payload = SearchProductIndexCreate(
        product_id=123,
        product_name="테스트 상품",
        product_description="설명",
        category_ids=[1, 2, 3],
        brand_name="테스트 브랜드",
        price_amount=Decimal("12900.00"),
        average_rating=Decimal("4.5"),
        review_count=100,
        stock_quantity=50,
        is_active=True,
        search_keywords="테스트,상품",
    )

    assert payload.product_id == 123
    assert payload.product_name == "테스트 상품"
    assert payload.price_amount == Decimal("12900.00")
    assert payload.average_rating == Decimal("4.5")
    assert payload.is_active is True


def test_search_product_index_update_schema_supports_partial_update() -> None:
    """검색 인덱스 수정 스키마는 부분 업데이트를 지원해야 한다."""
    payload = SearchProductIndexUpdate(
        product_name="수정된 상품명",
        is_active=False,
    )

    assert payload.model_dump(exclude_unset=True) == {
        "product_name": "수정된 상품명",
        "is_active": False,
    }


def test_search_keyword_create_schema_validates_fields() -> None:
    """검색 키워드 생성 스키마가 핵심 필드를 검증해야 한다."""
    payload = SearchKeywordCreate(
        keyword="테스트",
        search_count=5,
    )

    assert payload.keyword == "테스트"
    assert payload.search_count == 5


def test_search_keyword_update_schema_supports_partial_update() -> None:
    """검색 키워드 수정 스키마는 부분 업데이트를 지원해야 한다."""
    payload = SearchKeywordUpdate(
        search_count=10,
    )

    assert payload.model_dump(exclude_unset=True) == {
        "search_count": 10,
    }


def test_search_autocomplete_create_schema_validates_fields() -> None:
    """자동완성 생성 스키마가 핵심 필드를 검증해야 한다."""
    payload = SearchAutocompleteCreate(
        keyword="테스트",
        weight=5,
    )

    assert payload.keyword == "테스트"
    assert payload.weight == 5


def test_search_autocomplete_update_schema_supports_partial_update() -> None:
    """자동완성 수정 스키마는 부분 업데이트를 지원해야 한다."""
    payload = SearchAutocompleteUpdate(
        keyword="수정된키워드",
        weight=10,
    )

    assert payload.model_dump(exclude_unset=True) == {
        "keyword": "수정된키워드",
        "weight": 10,
    }


def test_search_synonym_create_schema_validates_fields() -> None:
    """동의어 생성 스키마가 핵심 필드를 검증해야 한다."""
    payload = SearchSynonymCreate(
        keyword="컴퓨터",
        synonym="노트북",
    )

    assert payload.keyword == "컴퓨터"
    assert payload.synonym == "노트북"


def test_search_synonym_update_schema_supports_partial_update() -> None:
    """동의어 수정 스키마는 부분 업데이트를 지원해야 한다."""
    payload = SearchSynonymUpdate(
        keyword="휴대폰",
        synonym="스마트폰",
    )

    assert payload.model_dump(exclude_unset=True) == {
        "keyword": "휴대폰",
        "synonym": "스마트폰",
    }


def test_search_router_registers_expected_routes() -> None:
    """검색 라우터에 CRUD 엔드포인트가 등록되어야 한다."""
    route_map = {(tuple(sorted(route.methods)), route.path) for route in router.routes}

    # SearchProductIndex routes
    assert (("GET",), "/search/products") in route_map
    assert (("GET",), "/search/products/{product_id}") in route_map
    assert (("POST",), "/search/products") in route_map
    assert (("PUT",), "/search/products/{product_id}") in route_map
    assert (("DELETE",), "/search/products/{product_id}") in route_map

    # SearchKeyword routes
    assert (("GET",), "/search/keywords") in route_map
    assert (("GET",), "/search/keywords/{keyword}") in route_map
    assert (("POST",), "/search/keywords") in route_map
    assert (("PUT",), "/search/keywords/{keyword}") in route_map
    assert (("DELETE",), "/search/keywords/{keyword}") in route_map

    # SearchAutocomplete routes
    assert (("GET",), "/search/autocomplete") in route_map
    assert (("GET",), "/search/autocomplete/{id}") in route_map
    assert (("POST",), "/search/autocomplete") in route_map
    assert (("PUT",), "/search/autocomplete/{id}") in route_map
    assert (("DELETE",), "/search/autocomplete/{id}") in route_map

    # SearchSynonym routes
    assert (("GET",), "/search/synonyms") in route_map
    assert (("GET",), "/search/synonyms/{id}") in route_map
    assert (("POST",), "/search/synonyms") in route_map
    assert (("PUT",), "/search/synonyms/{id}") in route_map
    assert (("DELETE",), "/search/synonyms/{id}") in route_map