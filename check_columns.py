from sqlalchemy import create_engine, inspect
from core.config import settings

engine = create_engine(settings.database_url)
inspector = inspect(engine)

for table in ['item_categories', 'item_sub_categories']:
    print(f"\nColumns in {table}:")
    for column in inspector.get_columns(table):
        print(f"  {column['name']} ({column['type']})")
