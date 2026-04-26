"""Insert initial Inventory and WarehouseStock data."""
from app.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
try:
    # Step 1: Inventory INSERT
    result = db.execute(text("""
        INSERT INTO ecommerce.inventory (sku_id, total_quantity, available_quantity, reserved_quantity, safety_stock_quantity, created_by)
        SELECT s.id, s.stock_quantity, s.stock_quantity, 0, 10, 1
        FROM ecommerce.sku s
        WHERE NOT EXISTS (SELECT 1 FROM ecommerce.inventory i WHERE i.sku_id = s.id)
    """))
    print(f"Inventory INSERT: {result.rowcount} rows")

    # Step 2: WarehouseStock INSERT
    result = db.execute(text("""
        INSERT INTO ecommerce.warehouse_stock (warehouse_id, sku_id, stock_quantity)
        SELECT 1, s.id, s.stock_quantity
        FROM ecommerce.sku s
        WHERE NOT EXISTS (SELECT 1 FROM ecommerce.warehouse_stock ws WHERE ws.sku_id = s.id)
    """))
    print(f"WarehouseStock INSERT: {result.rowcount} rows")

    db.commit()

    # Verify
    rows = db.execute(text("SELECT COUNT(*) FROM ecommerce.inventory")).scalar()
    print(f"Total inventory records: {rows}")
    rows = db.execute(text("SELECT COUNT(*) FROM ecommerce.warehouse_stock")).scalar()
    print(f"Total warehouse_stock records: {rows}")
finally:
    db.close()
