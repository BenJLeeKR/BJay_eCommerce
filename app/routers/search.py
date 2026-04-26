from __future__ import annotations
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.models.search import SearchAutocomplete, SearchKeyword, SearchProductIndex, SearchSynonym
from app.schemas import APIResponse
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


# SearchProductIndex endpoints
@router.get("/products", response_model=APIResponse[list[SearchProductIndexRead]], summary="검색 인덱스 목록 조회")
def list_search_products(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
) -> APIResponse[list[SearchProductIndexRead]]:
    """검색 인덱스 목록을 페이징 조건으로 조회한다."""
    statement = select(SearchProductIndex).offset(skip).limit(limit)

    if is_active is not None:
        statement = statement.where(SearchProductIndex.is_active == is_active)

    products = db.execute(statement).scalars().all()
    return APIResponse(data=products, message="검색 인덱스 목록을 조회했습니다.")


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