from core.database import engine, Base
import modules.settings.models
import modules.purchasing.models
import modules.sales.models
import modules.production.models
import modules.inventory.models
import modules.accounting.models
import modules.users.models

from sqlalchemy import text

with engine.begin() as conn:
    conn.execute(text("SET FOREIGN_KEY_CHECKS=0;"))
    Base.metadata.drop_all(conn)
    conn.execute(text("SET FOREIGN_KEY_CHECKS=1;"))
    print("Dropped all tables safely.")
    
    Base.metadata.create_all(conn)
    print("Re-created all tables safely.")
