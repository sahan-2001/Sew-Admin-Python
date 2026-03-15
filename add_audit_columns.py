"""
Migration: Add audit columns (site_id, created_at, created_by, updated_at, updated_by,
           deleted_at, deleted_by) to all existing tables, plus new columns added to
           users and sites tables.

Run once:  python add_audit_columns.py
Safe to re-run — uses TRY/EXCEPT to skip already-existing columns.
"""
from core.database import engine
from sqlalchemy import text

AUDIT_COLUMNS = [
    ("site_id",    "INTEGER REFERENCES sites(id)"),
    ("created_at", "DATETIME"),      # NULL for existing rows; ORM sets it for new rows
    ("created_by", "INTEGER REFERENCES users(id)"),
    ("updated_at", "DATETIME"),
    ("updated_by", "INTEGER REFERENCES users(id)"),
    ("deleted_at", "DATETIME"),
    ("deleted_by", "INTEGER REFERENCES users(id)"),
]

# Tables that get the full mixin (site_id + all audit cols)
TABLES_FULL = [
    "currencies",
    "countries",
    "vat_groups",
    "delivery_terms",
    "payment_terms",
    "payment_methods",
    "item_categories",
    "item_sub_categories",
    "warehouses",
    "inventory_locations",
    "warehouse_items",
    "item_journals",
    "physical_inventory",
    "sales_orders",
    "sales_order_lines",
    "shipments",
    "purchase_orders",
    "grns",
    "accounts",
    "journal_entries",
    "transaction_lines",
    "items",
    "locations",
    "stock_movements",
    "location_stocks",
    "workcenters",
    "production_orders",
    "timesheets",
]

# Sites table: audit cols only, no site_id (would be circular)
TABLES_SITES_AUDIT_ONLY = [
    "sites",
]

# Users table: only timestamp cols (no site_id FK, as users span sites)
USERS_AUDIT_COLS = [
    ("created_at", "DATETIME"),
    ("updated_at", "DATETIME"),
    ("deleted_at", "DATETIME"),
    ("deleted_by", "INTEGER"),
]


def add_column_safe(conn, table: str, col_name: str, col_def: str):
    try:
        conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_def}"))
        conn.commit()
        print(f"  [OK]  {table}.{col_name}")
    except Exception as e:
        msg = str(e).lower()
        if "duplicate column" in msg or "already exists" in msg:
            print(f"  [--]  {table}.{col_name} already exists")
        else:
            print(f"  [ERR] {table}.{col_name}  ERROR: {e}")


with engine.connect() as conn:
    print("\n=== Adding audit columns to all ERP tables ===\n")

    # Full mixin (site_id + all audit cols)
    for table in TABLES_FULL:
        print(f"[{table}]")
        for col_name, col_def in AUDIT_COLUMNS:
            add_column_safe(conn, table, col_name, col_def)

    # Sites table (audit only, no site_id)
    for table in TABLES_SITES_AUDIT_ONLY:
        print(f"[{table}]")
        for col_name, col_def in AUDIT_COLUMNS[1:]:   # skip site_id
            add_column_safe(conn, table, col_name, col_def)

    # Users table
    print("[users]")
    for col_name, col_def in USERS_AUDIT_COLS:
        add_column_safe(conn, "users", col_name, col_def)

    print("\n=== Migration complete ===\n")
