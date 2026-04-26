from __future__ import annotations

from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.crud import CRUDBase
from app.models.search import SearchAutocomplete, SearchKeyword, SearchProductIndex, SearchSynonym
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


class SearchProductIndexCRUD(CRUDBase[SearchProductIndex]):
    """검색 인덱스 CRUD."""

    def create(self, db: Session, obj_in: SearchProductIndexCreate) -> SearchProductIndex:
        """검색 인덱스를 생성한다."""
        obj_data = obj_in.model_dump()
        db_obj = SearchProductIndex(**obj_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get(self, db: Session, object_id: int) -> Optional[SearchProductIndex]:
        """검색 인덱스를 product_id로 조회한다."""
        stmt = select(SearchProductIndex).where(SearchProductIndex.product_id == object_id)
        return db.scalar(stmt)

    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> list[SearchProductIndex]:
        """검색 인덱스 목록을 조회한다."""
        stmt = (
            select(SearchProductIndex)
            .offset(skip)
            .limit(limit)
            .order_by(SearchProductIndex.product_id)
        )
        return list(db.scalars(stmt))

    def update(
        self, db: Session, db_obj: SearchProductIndex, obj_in: SearchProductIndexUpdate
    ) -> SearchProductIndex:
        """검색 인덱스를 수정한다."""
        update_data = obj_in.model_dump(exclude_unset=True)
        update_data["updated_at"] = func.now()
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, object_id: int) -> SearchProductIndex:
        """검색 인덱스를 삭제한다."""
        stmt = select(SearchProductIndex).where(SearchProductIndex.product_id == object_id)
        db_obj = db.scalar(stmt)
        if db_obj:
            db.delete(db_obj)
            db.commit()
        return db_obj


class SearchKeywordCRUD(CRUDBase[SearchKeyword]):
    """검색 키워드 집계 CRUD."""

    def create(self, db: Session, obj_in: SearchKeywordCreate) -> SearchKeyword:
        """검색 키워드를 생성한다."""
        obj_data = obj_in.model_dump()
        db_obj = SearchKeyword(**obj_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get(self, db: Session, object_id: str) -> Optional[SearchKeyword]:
        """검색 키워드를 keyword로 조회한다."""
        stmt = select(SearchKeyword).where(SearchKeyword.keyword == object_id)
        return db.scalar(stmt)

    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> list[SearchKeyword]:
        """검색 키워드 목록을 조회한다."""
        stmt = (
            select(SearchKeyword)
            .offset(skip)
            .limit(limit)
            .order_by(SearchKeyword.search_count.desc())
        )
        return list(db.scalars(stmt))

    def update(
        self, db: Session, db_obj: SearchKeyword, obj_in: SearchKeywordUpdate
    ) -> SearchKeyword:
        """검색 키워드를 수정한다."""
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, object_id: str) -> SearchKeyword:
        """검색 키워드를 삭제한다."""
        stmt = select(SearchKeyword).where(SearchKeyword.keyword == object_id)
        db_obj = db.scalar(stmt)
        if db_obj:
            db.delete(db_obj)
            db.commit()
        return db_obj

    def increment_search_count(
        self, db: Session, keyword: str
    ) -> Optional[SearchKeyword]:
        """검색 키워드의 검색 횟수를 증가시킨다."""
        stmt = select(SearchKeyword).where(SearchKeyword.keyword == keyword)
        db_obj = db.scalar(stmt)
        if db_obj:
            db_obj.search_count = SearchKeyword.search_count + 1
            db_obj.last_searched_at = func.now()
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)
        return db_obj

    def get_popular_keywords(
        self, db: Session, *, limit: int = 10
    ) -> list[SearchKeyword]:
        """인기 검색어 목록을 조회한다."""
        stmt = (
            select(SearchKeyword)
            .order_by(SearchKeyword.search_count.desc())
            .limit(limit)
        )
        return list(db.scalars(stmt))


class SearchAutocompleteCRUD(CRUDBase[SearchAutocomplete]):
    """자동완성 데이터 CRUD."""

    def create(self, db: Session, obj_in: SearchAutocompleteCreate) -> SearchAutocomplete:
        """자동완성 데이터를 생성한다."""
        obj_data = obj_in.model_dump()
        db_obj = SearchAutocomplete(**obj_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get(self, db: Session, object_id: int) -> Optional[SearchAutocomplete]:
        """자동완성 데이터를 id로 조회한다."""
        stmt = select(SearchAutocomplete).where(SearchAutocomplete.id == object_id)
        return db.scalar(stmt)

    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> list[SearchAutocomplete]:
        """자동완성 데이터 목록을 조회한다."""
        stmt = (
            select(SearchAutocomplete)
            .offset(skip)
            .limit(limit)
            .order_by(SearchAutocomplete.weight.desc())
        )
        return list(db.scalars(stmt))

    def update(
        self, db: Session, db_obj: SearchAutocomplete, obj_in: SearchAutocompleteUpdate
    ) -> SearchAutocomplete:
        """자동완성 데이터를 수정한다."""
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, object_id: int) -> SearchAutocomplete:
        """자동완성 데이터를 삭제한다."""
        stmt = select(SearchAutocomplete).where(SearchAutocomplete.id == object_id)
        db_obj = db.scalar(stmt)
        if db_obj:
            db.delete(db_obj)
            db.commit()
        return db_obj

    def search_by_keyword(
        self, db: Session, keyword: str, *, limit: int = 10
    ) -> list[SearchAutocomplete]:
        """키워드로 자동완성 데이터를 검색한다."""
        stmt = (
            select(SearchAutocomplete)
            .where(SearchAutocomplete.keyword.ilike(f"{keyword}%"))
            .order_by(SearchAutocomplete.weight.desc())
            .limit(limit)
        )
        return list(db.scalars(stmt))


class SearchSynonymCRUD(CRUDBase[SearchSynonym]):
    """동의어 데이터 CRUD."""

    def create(self, db: Session, obj_in: SearchSynonymCreate) -> SearchSynonym:
        """동의어 데이터를 생성한다."""
        obj_data = obj_in.model_dump()
        db_obj = SearchSynonym(**obj_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get(self, db: Session, object_id: int) -> Optional[SearchSynonym]:
        """동의어 데이터를 id로 조회한다."""
        stmt = select(SearchSynonym).where(SearchSynonym.id == object_id)
        return db.scalar(stmt)

    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> list[SearchSynonym]:
        """동의어 데이터 목록을 조회한다."""
        stmt = (
            select(SearchSynonym)
            .offset(skip)
            .limit(limit)
            .order_by(SearchSynonym.id)
        )
        return list(db.scalars(stmt))

    def update(
        self, db: Session, db_obj: SearchSynonym, obj_in: SearchSynonymUpdate
    ) -> SearchSynonym:
        """동의어 데이터를 수정한다."""
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, object_id: int) -> SearchSynonym:
        """동의어 데이터를 삭제한다."""
        stmt = select(SearchSynonym).where(SearchSynonym.id == object_id)
        db_obj = db.scalar(stmt)
        if db_obj:
            db.delete(db_obj)
            db.commit()
        return db_obj

    def get_synonyms_by_keyword(
        self, db: Session, keyword: str
    ) -> list[SearchSynonym]:
        """키워드에 대한 동의어 목록을 조회한다."""
        stmt = select(SearchSynonym).where(SearchSynonym.keyword == keyword)
        return list(db.scalars(stmt))


# 모듈 레벨 싱글턴 인스턴스
search_product_index_crud = SearchProductIndexCRUD(SearchProductIndex)
search_keyword_crud = SearchKeywordCRUD(SearchKeyword)
search_autocomplete_crud = SearchAutocompleteCRUD(SearchAutocomplete)
search_synonym_crud = SearchSynonymCRUD(SearchSynonym)
