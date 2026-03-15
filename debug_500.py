from core.database import SessionLocal
from modules.settings.models import ItemCategory, ItemSubCategory
from sqlalchemy.orm import Session

def test_query():
    db = SessionLocal()
    try:
        print("Querying categories...")
        cats = db.query(ItemCategory).all()
        print(f"Found {len(cats)} categories")
        
        print("Querying sub-categories...")
        subs = db.query(ItemSubCategory).all()
        print(f"Found {len(subs)} sub-categories")
    except Exception as e:
        print("ERROR OCCURRED:")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_query()
