# Warehouse 도메인 리팩토링 계획

## 배경
[`warehouse_design.md`](backend/warehouse_design.md) 설계 가이드와 현재 구현 간의 갭을 해소하여 데이터 무결성, API 일관성, 조회 성능을 개선한다.

---

## 변경 대상 파일

| 파일 | 변경 내용 |
|------|----------|
| [`backend/app/models/inventory.py`](backend/app/models/inventory.py) | WarehouseStock: FK + 복합 인덱스 추가 |
| [`backend/app/routers/inventory.py`](backend/app/routers/inventory.py) | WarehouseStock CRUD 엔드포인트 제거 |
| [`backend/app/routers/shipment.py`](backend/app/routers/shipment.py) | warehouse_router 하위에 WarehouseStock sub-router 추가 |
| [`backend/insert_inventory.sql`](backend/insert_inventory.sql) (또는 신규 migration SQL) | FK 제약 + 인덱스 DDL |
| [`backend/tests/unit/test_inventory_domain.py`](backend/tests/unit/test_inventory_domain.py) | WarehouseStock 모델 변경 반영 |

---

## Step 1: Model에 FK + 복합 인덱스 추가

**파일**: [`backend/app/models/inventory.py:118-119`](backend/app/models/inventory.py:118)

### 현재
```python
warehouse_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
# __table_args__ 없음
```

### 변경
```python
warehouse_id: Mapped[int] = mapped_column(
    BigInteger,
    ForeignKey(f"{settings.DB_SCHEMA}.warehouse.id"),
    nullable=False,
)

# 클래스 레벨에 추가
__table_args__ = (
    Index("ix_warehouse_stock_warehouse_sku", "warehouse_id", "sku_id"),
)
```

### 영향도
- `settings.DB_SCHEMA`는 `config.py`에서 이미 정의되어 있음 (`ecommerce`)
- 기존 WarehouseStock 인스턴스 생성 코드는 변경 불필요 (ForeignKey는 DB 레벨 제약)
- `WarehouseStockCRUD.create()`에서 FK 위반 시 SQLAlchemy가 `IntegrityError` 발생

---

## Step 2: DB Migration SQL

**파일**: 신규 [`backend/migrations/add_warehouse_stock_fk_index.sql`](backend/migrations/add_warehouse_stock_fk_index.sql)

```sql
-- warehouse_stock.warehouse_id → warehouse.id FK 추가
ALTER TABLE ecommerce.warehouse_stock
ADD CONSTRAINT fk_warehouse_stock_warehouse
FOREIGN KEY (warehouse_id) REFERENCES ecommerce.warehouse(id);

-- 복합 인덱스 생성
CREATE INDEX IF NOT EXISTS ix_warehouse_stock_warehouse_sku
ON ecommerce.warehouse_stock (warehouse_id, sku_id);
```

> **참고**: `insert_inventory.sql`에서 `warehouse_id=1`로 INSERT하므로, warehouse.id=1 레코드가 먼저 존재해야 FK 제약이 위반되지 않음. 창고 생성 SQL을 먼저 실행할 필요가 있음.

---

## Step 3: WarehouseStock CRUD 라우터 이동

### 현재 (inventory.py)
| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | `/api/v1/inventory/warehouse-stocks` | 목록 조회 (sku_id, warehouse_id 필터) |
| GET | `/api/v1/inventory/warehouse-stocks/{stock_id}` | 상세 조회 |
| POST | `/api/v1/inventory/warehouse-stocks` | 생성 |
| PUT | `/api/v1/inventory/warehouse-stocks/{stock_id}` | 수정 |
| DELETE | `/api/v1/inventory/warehouse-stocks/{stock_id}` | 삭제 |

### 변경 후 (shipment.py — warehouse_router 하위)

**warehouse_stock_router** (`/warehouses/{warehouse_id}/stocks`):

| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | `/api/v1/warehouses/{warehouse_id}/stocks` | 창고별 재고 목록 (page/skip/limit) |
| POST | `/api/v1/warehouses/{warehouse_id}/stocks` | 재고 생성 (warehouse_id는 path에서 추출) |
| GET | `/api/v1/warehouses/{warehouse_id}/stocks/{stock_id}` | 재고 상세 |
| PUT | `/api/v1/warehouses/{warehouse_id}/stocks/{stock_id}` | 재고 수정 |
| DELETE | `/api/v1/warehouses/{warehouse_id}/stocks/{stock_id}` | 재고 삭제 |

### 라우터 등록 (shipment.py 하단)
```python
warehouse_stock_router = APIRouter(prefix="/warehouses/{warehouse_id}/stocks", ...)
# ... 엔드포인트 정의 ...
warehouse_router.include_router(warehouse_stock_router)
```

### 스키마 변경
- `WarehouseStockCreate`에 `warehouse_id`는 path param에서 추출하므로 schema에서 제거하거나 선택 필드로 변경 고려
  - But, `WarehouseStockCRUD.create()`가 `WarehouseStockCreate`를 받고 있으므로 schema는 그대로 두고, 라우터에서 `warehouse_id`를 payload에 주입하는 방식으로 처리

---

## Step 4: 기존 inventory.py WarehouseStock 엔드포인트 제거

**파일**: [`backend/app/routers/inventory.py:165-301`](backend/app/routers/inventory.py:165)

5개 엔드포인트 모두 제거:
- `list_warehouse_stocks()` — lines 170-187
- `get_warehouse_stock()` — lines 195-210
- `create_warehouse_stock()` — lines 219-247
- `update_warehouse_stock()` — lines 255-280
- `delete_warehouse_stock()` — lines 288-301

> **주의**: `inventory.py` 상단의 `WarehouseStock` import도 함께 제거

---

## Step 5: 단위/통합 테스트 업데이트

### 기존 테스트
- search 결과 WarehouseStock 관련 테스트는 현재 **존재하지 않음**
- 다만 라우터 경로 변경 시 통합 테스트에서 참조하는 경로가 있다면 업데이트 필요

### 추가할 테스트
1. [`backend/tests/unit/test_inventory_domain.py`](backend/tests/unit/test_inventory_domain.py):
   - `test_warehouse_stock_has_warehouse_fk()` — FK 제약 확인
   - `test_warehouse_stock_has_composite_index()` — 복합 인덱스 확인

2. (선택) [`backend/tests/integration/test_shipment_api.py`](backend/tests/integration/test_shipment_api.py):
   - WarehouseStock CRUD 통합 테스트 (warehouse_router 하위 경로로)

---

## Step 6: 전체 테스트 실행

```bash
cd backend && python -m pytest tests/ -v --tb=short 2>&1
```

기존 265개 + 신규 테스트 모두 통과 확인.

---

## 데이터 흐름 다이어그램 (변경 후)

```mermaid
flowchart TD
    Client[Client] -->|GET /warehouses/1/stocks| WS_Router[warehouse_stock_router<br>/warehouses/{id}/stocks]
    Client -->|POST /warehouses/1/stocks| WS_Router
    Client -->|GET /inventory/...| Inv_Router[inventory_router<br>/inventory]

    WS_Router -->|warehouse_id 검증| FK[FK: warehouse_stock.warehouse_id<br>→ warehouse.id]
    WS_Router -->|조회| Idx[복합 인덱스<br>(warehouse_id, sku_id)]
    WS_Router -->|CRUD| WS_DB[(warehouse_stock)]

    Inv_Router -->|Inventory<br>Reservation<br>Transaction<br>Adjustment| Inv_DB[(inventory)]

    FK --> Wh_DB[(warehouse)]
```

---

## 실행 순서 요약

| 순서 | 작업 | 파일 |
|------|------|------|
| 1 | Model: FK + 복합 인덱스 추가 | `models/inventory.py` |
| 2 | Migration SQL 생성 | `migrations/add_warehouse_stock_fk_index.sql` |
| 3 | Shipment 라우터: WarehouseStock sub-router 추가 | `routers/shipment.py` |
| 4 | Inventory 라우터: WarehouseStock 엔드포인트 제거 | `routers/inventory.py` |
| 5 | 단위 테스트 업데이트 | `tests/unit/test_inventory_domain.py` |
| 6 | 전체 테스트 실행 | pytest |
