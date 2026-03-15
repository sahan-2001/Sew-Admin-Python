from sqlalchemy import text
from core.database import engine

def apply_migrations():
    with engine.begin() as conn:
        try:
            conn.execute(text("ALTER TABLE warehouse_items ADD COLUMN item_type VARCHAR(50) DEFAULT 'inventory';"))
            conn.execute(text("ALTER TABLE warehouse_items ADD COLUMN description VARCHAR(255);"))
            conn.execute(text("ALTER TABLE warehouse_items ADD COLUMN is_active BOOLEAN DEFAULT 1;"))
            print("Successfully altered table.")
        except Exception as e:
            print(f"Migration error or already applied: {e}")

if __name__ == '__main__':
    apply_migrations()
