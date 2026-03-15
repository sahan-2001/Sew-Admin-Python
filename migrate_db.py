from core.database import engine
from core.database import Base
from sqlalchemy import text
import modules.settings.models
import modules.warehouse.models

print("Checking and creating any new tables (like item_categories, item_sub_categories)...")
Base.metadata.create_all(bind=engine)

print("Altering warehouse_items to add sub_category column...")
with engine.connect() as conn:
    try:
        conn.execute(text("ALTER TABLE warehouse_items ADD COLUMN sub_category VARCHAR(50) DEFAULT NULL"))
        print("Column sub_category added successfully to warehouse_items.")
        conn.commit()
    except Exception as e:
        if 'Duplicate column' in str(e) or 'Duplicate' in str(e) or 'already exists' in str(e).lower() or '1060' in str(e):
            print("Column sub_category already exists.")
        else:
            print("Error altering table (it might already exist?):", e)

print("Done.")
