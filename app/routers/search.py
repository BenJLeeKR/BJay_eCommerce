from __future__ import annotations
from enum import Enum
from typing import Optional

from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.models.search import SearchAutocomplete, SearchKeyword, SearchProductIndex, SearchSynonym
from app.schemas import APIResponse, PagedResult
from app.schemas.search import (
    SearchAutocompleteCreate,
    SearchAutocompleteRead,
    SearchAutocompleteUpdate,
    SearchKeywordCreate,
    SearchKeywordRead,
    SearchKeywordUpdate,
    SearchProductIndexCreate,
    SearchProductIndexRead,
    SearchProductIndexUpdate,
    SearchSynonymCreate,
    SearchSynonymRead,
    SearchSynonymUpdate,
)

router = APIRouter(prefix="/search", tags=["Search (검색)"])


class SearchSortBy(str, Enum):
    """상품 검색 정렬 기준.

    - ``newest``: 최신 등록순
    - ``price_asc``: 가격 낮은순
    - ``price_desc``: 가격 높은순
    - ``rating_desc``: 평점 높은순
    - ``review_desc``: 리뷰 많은순
    """

    newest = "newest"
    price_asc = "price_asc"
    price_desc = "price_desc"
    rating_desc = "rating_desc"
    review_desc = "review_desc"


# SearchProductIndex endpoints
@router.get("/products", response_model=APIResponse[PagedResult[SearchProductIndexRead]], summary="상품 검색")
def list_search_products(
    q: Optional[str] = Query(default=None, min_length=1, max_length=255, description="검색어"),
    category_id: Optional[list[int]] = Query(default=None, description="카테고리 ID (다중 선택)"),
    brand_name: Optional[list[str]] = Query(default=None, description="브랜드명 (다중 선택)"),
    min_price: Optional[Decimal] = Query(default=None, ge=0, description="최소 가격"),
    max_price: Optional[Decimal] = Query(default=None, ge=0, description="최대 가격"),
    min_rating: Optional[Decimal] = Query(default=None, ge=0, le=5, description="최소 평점"),
    is_active: Optional[bool] = Query(default=None, description="활성 상태"),
    in_stock_only: bool = Query(default=False, description="재고 있는 상품만"),
    sort_by: Optional[SearchSortBy] = Query(default=SearchSortBy.newest, description="정렬 기준"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> APIResponse[PagedResult[SearchProductIndexRead]]:
    """상품 검색 인덱스를 다양한 필터와 정렬 조건으로 조회한다.

    프론트엔드 필터 UI와 연동하여 가격대, 브랜드, 평점, 재고 여부 등을
    쿼리 파라미터로 전달할 수 있다.
    """
    statement = select(SearchProductIndex)

    # ── 검색어 ──
    if q is not None:
        like_pattern = f"%{q}%"
        statement = statement.where(
            SearchProductIndex.product_name.ilike(like_pattern)
            | SearchProductIndex.product_description.ilike(like_pattern)
            | SearchProductIndex.search_keywords.ilike(like_pattern)
        )

    # ── 카테고리 ──
    if category_id:
        # category_ids는 JSON 배열이므로 배열 교차 검색
        for cid in category_id:
            statement = statement.where(
                SearchProductIndex.category_ids.any(cid)
            )

    # ── 브랜드 ──
    if brand_name:
        statement = statement.where(SearchProductIndex.brand_name.in_(brand_name))

    # ── 가격 범위 ──
    if min_price is not None:
        statement = statement.where(SearchProductIndex.price_amount >= min_price)
    if max_price is not None:
        statement = statement.where(SearchProductIndex.price_amount <= max_price)

    # ── 평점 ──
    if min_rating is not None:
        statement = statement.where(SearchProductIndex.average_rating >= min_rating)

    # ── 활성 상태 ──
    if is_active is not None:
        statement = statement.where(SearchProductIndex.is_active == is_active)

    # ── 재고 필터 ──
    if in_stock_only:
        statement = statement.where(
            SearchProductIndex.stock_quantity.is_(None)
            | (SearchProductIndex.stock_quantity > 0)
        )

    # ── 정렬 ──
    sort_map = {
        SearchSortBy.newest: SearchProductIndex.updated_at.desc(),
        SearchSortBy.price_asc: SearchProductIndex.price_amount.asc(),
        SearchSortBy.price_desc: SearchProductIndex.price_amount.desc(),
        SearchSortBy.rating_desc: SearchProductIndex.average_rating.desc(),
        SearchSortBy.review_desc: SearchProductIndex.review_count.desc(),
    }
    order_col = sort_map.get(sort_by, SearchProductIndex.updated_at.desc())
    statement = statement.order_by(order_col)

    # ── 전체 개수 ──
    count_stmt = select(func.count()).select_from(statement.subquery())
    total_count = db.scalar(count_stmt) or 0

    # ── 페이지네이션 ──
    statement = statement.offset(skip).limit(limit)
    products = db.execute(statement).scalars().all()

    return APIResponse(
        data=PagedResult(
            items=products,
            total_count=total_count,
            skip=skip,
            limit=limit,
        ),
        message="상품 검색 결과를 조회했습니다.",
    )


@router.get("/products/{product_id}", response_model=APIResponse[SearchProductIndexRead], summary="검색 인덱스 상세 조회")
def get_search_product(product_id: int, db: Session = Depends(get_db)) -> APIResponse[SearchProductIndexRead]:
    """검색 인덱스 상세 정보를 조회한다."""
    product = db.get(SearchProductIndex, product_id)
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="검색 인덱스를 찾을 수 없습니다.",
        )
    return APIResponse(data=product, message="검색 인덱스 상세 정보를 조회했습니다.")


@router.post(
    "/products",
    response_model=APIResponse[SearchProductIndexRead],
    status_code=status.HTTP_201_CREATED,
    summary="검색 인덱스 생성",
)
def create_search_product(
    payload: SearchProductIndexCreate,
    db: Session = Depends(get_db),
) -> APIResponse[SearchProductIndexRead]:
    """검색 인덱스 데이터를 생성한다."""
    product = SearchProductIndex(**payload.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    return APIResponse(data=product, message="검색 인덱스를 생성했습니다.")


@router.put("/products/{product_id}", response_model=APIResponse[SearchProductIndexRead], summary="검색 인덱스 수정")
def update_search_product(
    product_id: int,
    payload: SearchProductIndexUpdate,
    db: Session = Depends(get_db),
) -> APIResponse[SearchProductIndexRead]:
    """검색 인덱스 데이터를 수정한다."""
    product = db.get(SearchProductIndex, product_id)
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="검색 인덱스를 찾을 수 없습니다.",
        )

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(product, field, value)

    db.commit()
    db.refresh(product)
    return APIResponse(data=product, message="검색 인덱스를 수정했습니다.")


@router.delete("/products/{product_id}", response_model=APIResponse[None], summary="검색 인덱스 삭제")
def delete_search_product(product_id: int, db: Session = Depends(get_db)) -> APIResponse[None]:
    """검색 인덱스 데이터를 삭제한다."""
    product = db.get(SearchProductIndex, product_id)
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="검색 인덱스를 찾을 수 없습니다.",
        )

    db.delete(product)
    db.commit()
    return APIResponse(data=None, message="검색 인덱스를 삭제했습니다.")


# SearchKeyword endpoints
@router.get("/keywords", response_model=APIResponse[list[SearchKeywordRead]], summary="검색 키워드 목록 조회")
def list_search_keywords(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> APIResponse[list[SearchKeywordRead]]:
    """검색 키워드 목록을 페이징 조건으로 조회한다."""
    statement = select(SearchKeyword).offset(skip).limit(limit)
    keywords = db.execute(statement).scalars().all()
    return APIResponse(data=keywords, message="검색 키워드 목록을 조회했습니다.")


@router.get("/keywords/{keyword}", response_model=APIResponse[SearchKeywordRead], summary="검색 키워드 상세 조회")
def get_search_keyword(keyword: str, db: Session = Depends(get_db)) -> APIResponse[SearchKeywordRead]:
    """검색 키워드 상세 정보를 조회한다."""
    keyword_obj = db.get(SearchKeyword, keyword)
    if keyword_obj is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="검색 키워드를 찾을 수 없습니다.",
        )
    return APIResponse(data=keyword_obj, message="검색 키워드 상세 정보를 조회했습니다.")


@router.post(
    "/keywords",
    response_model=APIResponse[SearchKeywordRead],
    status_code=status.HTTP_201_CREATED,
    summary="검색 키워드 생성",
)
def create_search_keyword(
    payload: SearchKeywordCreate,
    db: Session = Depends(get_db),
) -> APIResponse[SearchKeywordRead]:
    """검색 키워드 데이터를 생성한다."""
    keyword = SearchKeyword(**payload.model_dump())
    db.add(keyword)
    db.commit()
    db.refresh(keyword)
    return APIResponse(data=keyword, message="검색 키워드를 생성했습니다.")


@router.put("/keywords/{keyword}", response_model=APIResponse[SearchKeywordRead], summary="검색 키워드 수정")
def update_search_keyword(
    keyword: str,
    payload: SearchKeywordUpdate,
    db: Session = Depends(get_db),
) -> APIResponse[SearchKeywordRead]:
    """검색 키워드 데이터를 수정한다."""
    keyword_obj = db.get(SearchKeyword, keyword)
    if keyword_obj is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="검색 키워드를 찾을 수 없습니다.",
        )

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(keyword_obj, field, value)

    db.commit()
    db.refresh(keyword_obj)
    return APIResponse(data=keyword_obj, message="검색 키워드를 수정했습니다.")


@router.delete("/keywords/{keyword}", response_model=APIResponse[None], summary="검색 키워드 삭제")
def delete_search_keyword(keyword: str, db: Session = Depends(get_db)) -> APIResponse[None]:
    """검색 키워드 데이터를 삭제한다."""
    keyword_obj = db.get(SearchKeyword, keyword)
    if keyword_obj is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="검색 키워드를 찾을 수 없습니다.",
        )

    db.delete(keyword_obj)
    db.commit()
    return APIResponse(data=None, message="검색 키워드를 삭제했습니다.")


# SearchAutocomplete endpoints
@router.get("/autocomplete", response_model=APIResponse[list[SearchAutocompleteRead]], summary="자동완성 목록 조회")
def list_autocomplete(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> APIResponse[list[SearchAutocompleteRead]]:
    """자동완성 목록을 페이징 조건으로 조회한다."""
    statement = select(SearchAutocomplete).offset(skip).limit(limit)
    autocompletes = db.execute(statement).scalars().all()
    return APIResponse(data=autocompletes, message="자동완성 목록을 조회했습니다.")


@router.get("/autocomplete/{id}", response_model=APIResponse[SearchAutocompleteRead], summary="자동완성 상세 조회")
def get_autocomplete(id: int, db: Session = Depends(get_db)) -> APIResponse[SearchAutocompleteRead]:
    """자동완성 상세 정보를 조회한다."""
    autocomplete = db.get(SearchAutocomplete, id)
    if autocomplete is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="자동완성 데이터를 찾을 수 없습니다.",
        )
    return APIResponse(data=autocomplete, message="자동완성 상세 정보를 조회했습니다.")


@router.post(
    "/autocomplete",
    response_model=APIResponse[SearchAutocompleteRead],
    status_code=status.HTTP_201_CREATED,
    summary="자동완성 생성",
)
def create_autocomplete(
    payload: SearchAutocompleteCreate,
    db: Session = Depends(get_db),
) -> APIResponse[SearchAutocompleteRead]:
    """자동완성 데이터를 생성한다."""
    autocomplete = SearchAutocomplete(**payload.model_dump())
    db.add(autocomplete)
    db.commit()
    db.refresh(autocomplete)
    return APIResponse(data=autocomplete, message="자동완성 데이터를 생성했습니다.")


@router.put("/autocomplete/{id}", response_model=APIResponse[SearchAutocompleteRead], summary="자동완성 수정")
def update_autocomplete(
    id: int,
    payload: SearchAutocompleteUpdate,
    db: Session = Depends(get_db),
) -> APIResponse[SearchAutocompleteRead]:
    """자동완성 데이터를 수정한다."""
    autocomplete = db.get(SearchAutocomplete, id)
    if autocomplete is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="자동완성 데이터를 찾을 수 없습니다.",
        )

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(autocomplete, field, value)

    db.commit()
    db.refresh(autocomplete)
    return APIResponse(data=autocomplete, message="자동완성 데이터를 수정했습니다.")


@router.delete("/autocomplete/{id}", response_model=APIResponse[None], summary="자동완성 삭제")
def delete_autocomplete(id: int, db: Session = Depends(get_db)) -> APIResponse[None]:
    """자동완성 데이터를 삭제한다."""
    autocomplete = db.get(SearchAutocomplete, id)
    if autocomplete is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="자동완성 데이터를 찾을 수 없습니다.",
        )

    db.delete(autocomplete)
    db.commit()
    return APIResponse(data=None, message="자동완성 데이터를 삭제했습니다.")


# SearchSynonym endpoints
@router.get("/synonyms", response_model=APIResponse[list[SearchSynonymRead]], summary="동의어 목록 조회")
def list_synonyms(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> APIResponse[list[SearchSynonymRead]]:
    """동의어 목록을 페이징 조건으로 조회한다."""
    statement = select(SearchSynonym).offset(skip).limit(limit)
    synonyms = db.execute(statement).scalars().all()
    return APIResponse(data=synonyms, message="동의어 목록을 조회했습니다.")


@router.get("/synonyms/{id}", response_model=APIResponse[SearchSynonymRead], summary="동의어 상세 조회")
def get_synonym(id: int, db: Session = Depends(get_db)) -> APIResponse[SearchSynonymRead]:
    """동의어 상세 정보를 조회한다."""
    synonym = db.get(SearchSynonym, id)
    if synonym is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="동의어 데이터를 찾을 수 없습니다.",
        )
    return APIResponse(data=synonym, message="동의어 상세 정보를 조회했습니다.")


@router.post(
    "/synonyms",
    response_model=APIResponse[SearchSynonymRead],
    status_code=status.HTTP_201_CREATED,
    summary="동의어 생성",
)
def create_synonym(
    payload: SearchSynonymCreate,
    db: Session = Depends(get_db),
) -> APIResponse[SearchSynonymRead]:
    """동의어 데이터를 생성한다."""
    synonym = SearchSynonym(**payload.model_dump())
    db.add(synonym)
    db.commit()
    db.refresh(synonym)
    return APIResponse(data=synonym, message="동의어 데이터를 생성했습니다.")


@router.put("/synonyms/{id}", response_model=APIResponse[SearchSynonymRead], summary="동의어 수정")
def update_synonym(
    id: int,
    payload: SearchSynonymUpdate,
    db: Session = Depends(get_db),
) -> APIResponse[SearchSynonymRead]:
    """동의어 데이터를 수정한다."""
    synonym = db.get(SearchSynonym, id)
    if synonym is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="동의어 데이터를 찾을 수 없습니다.",
        )

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(synonym, field, value)

    db.commit()
    db.refresh(synonym)
    return APIResponse(data=synonym, message="동의어 데이터를 수정했습니다.")


@router.delete("/synonyms/{id}", response_model=APIResponse[None], summary="동의어 삭제")
def delete_synonym(id: int, db: Session = Depends(get_db)) -> APIResponse[None]:
    """동의어 데이터를 삭제한다."""
    synonym = db.get(SearchSynonym, id)
    if synonym is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="동의어 데이터를 찾을 수 없습니다.",
        )

    db.delete(synonym)
    db.commit()
    return APIResponse(data=None, message="동의어 데이터를 삭제했습니다.")