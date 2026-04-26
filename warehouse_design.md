# Warehouse & Warehouse Stock 설계 가이드

## 1. 개요
본 문서는 창고(warehouse) 및 창고 재고(warehouse_stock) 설계 시 고려해야 할 구조와 실무 베스트 프랙티스를 정리한다.

---

## 2. FK 관계 설계

### 결론
- `warehouse_stock.warehouse_id` → `warehouse.id` FK 연결 필수

### 이유
- 데이터 무결성 보장
- 잘못된 warehouse_id 입력 방지
- 운영 및 유지보수 안정성 확보

---

## 3. 테이블 구조

### warehouse
- 창고 기본 정보

### warehouse_stock
- 창고별 SKU 재고 정보

---

## 4. 조회 설계 (핵심)

### 문제
단순 JOIN 사용 시:
- SKU 수 많을 경우 성능 저하
- API 응답 지연

---

## 5. 해결 전략 (CQRS)

### Write Model
- warehouse
- warehouse_stock

### Read Model
- API 응답용 별도 구조
- 캐싱 또는 집계 데이터 활용

---

## 6. API 설계

### 창고 상세
GET /warehouses/{id}

### 창고 재고 목록
GET /warehouses/{id}/stocks?page=1

---

## 7. 성능 전략

- 인덱스: (warehouse_id, sku_id)
- Redis 캐싱

---

## 8. 핵심 포인트

- JOIN 남용 금지
- Read / Write 분리
- 요약 데이터 활용

---

## 9. 요약

Write는 정규화 + FK  
Read는 비정규화 + 분리