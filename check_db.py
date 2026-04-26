from app.database import SessionLocal
from sqlalchemy import text

def check_data():
    db = SessionLocal()
    try:
        # 현재 생성된 브랜드 목록 조회 예시
        result1 = db.execute(text("SELECT id, brand_name FROM ecommerce.brand"))
        brands = result1.fetchall()
        print(f"--- 브랜드 목록 ({len(brands)}개) ---")
        for brand in brands:
            print(f"ID: {brand.id} | 이름: {brand.brand_name}")
            
        # 상품 개수 확인
        result2 = db.execute(text("SELECT id, parent_category_id, category_name, category_depth FROM ecommerce.category"))
        categorys = result2.fetchall()
        print(f"--- 카테고리 목록 ({len(categorys)}개) ---")
        for category in categorys:
            print(f"ID: {category.id} | 부모 카테고리 ID: {category.parent_category_id} | 이름: {category.category_name} | 깊이: {category.category_depth}")
        
    finally:
        db.close()

if __name__ == "__main__":
    check_data()