from sqlalchemy.orm import Session
from core.database import engine, Base
from modules.users.models import User, Site, UserRole
from modules.accounting.models import ChartOfAccount, AccountType
from modules.inventory.models import Item
from core.security import get_password_hash

def seed_database():
    # Attempt to create tables (Ensure XAMPP MySQL is running first!)
    Base.metadata.create_all(bind=engine)
    
    with Session(engine) as db:
        # Seed Sites (Warehouse / Locations)
        if not db.query(Site).first():
            db.add_all([
                Site(name="Head Office"),
                Site(name="Factory 1"),
                Site(name="Warehouse 1"),
                Site(name="Warehouse 2")
            ])
            db.commit()
            print("Seeded Sites.")

        # Seed Users
        if not db.query(User).first():
            admin = User(
                username="admin", 
                email="admin@sewadmin.com", 
                phone="+940000000",
                hashed_password=get_password_hash("password123"),
                role=UserRole.ADMIN,
                default_site_id=1
            )
            db.add(admin)
            db.commit()
            print("Seeded Admin User (admin / password123)")

        # Seed Chart of Accounts
        if not db.query(ChartOfAccount).first():
            db.add_all([
                ChartOfAccount(code="1000", name="Cash", account_type=AccountType.ASSET),
                ChartOfAccount(code="1200", name="Accounts Receivable", account_type=AccountType.ASSET),
                ChartOfAccount(code="1300", name="Inventory", account_type=AccountType.ASSET),
                ChartOfAccount(code="2000", name="Accounts Payable", account_type=AccountType.LIABILITY),
                ChartOfAccount(code="3000", name="Owner Equity", account_type=AccountType.EQUITY),
                ChartOfAccount(code="4000", name="Sales Revenue", account_type=AccountType.REVENUE),
                ChartOfAccount(code="5000", name="Cost of Goods Sold (COGS)", account_type=AccountType.EXPENSE),
                ChartOfAccount(code="5200", name="Scrap Sales Income", account_type=AccountType.REVENUE)
            ])
            db.commit()
            print("Seeded Default Chart of Accounts for Apparel Manufacturing.")

            # === ADDING ERP CONFIGURATION DEFAULTS ===
            from modules.settings.models import Currency, Country, VatGroup, DeliveryTerm, PaymentTerm, PaymentMethod
            
            if not db.query(Currency).first():
                db.add_all([
                    Currency(code="USD", name="US Dollar", symbol="$", is_global_default=True),
                    Currency(code="LKR", name="Sri Lankan Rupee", symbol="Rs", is_global_default=False)
                ])
                db.commit()
                
            if not db.query(DeliveryTerm).first():
                db.add_all([
                    DeliveryTerm(code="FOB", description="Free On Board"),
                    DeliveryTerm(code="CIF", description="Cost, Insurance, and Freight"),
                    DeliveryTerm(code="EXW", description="Ex Works")
                ])
                db.commit()

            if not db.query(PaymentTerm).first():
                db.add_all([
                    PaymentTerm(name="Cash on Delivery (COD)", days=0),
                    PaymentTerm(name="Net 30", days=30),
                    PaymentTerm(name="Net 60", days=60)
                ])
                db.commit()
                
            if not db.query(PaymentMethod).first():
                db.add_all([
                    PaymentMethod(name="Bank Transfer"),
                    PaymentMethod(name="Credit Card"),
                    PaymentMethod(name="Cash")
                ])
                db.commit()
                
            if not db.query(VatGroup).first():
                db.add_all([
                    VatGroup(name="Standard Item VAT", percentage=18.0, group_type="Item"),
                    VatGroup(name="Exempt Customer VAT", percentage=0.0, group_type="Customer"),
                    VatGroup(name="Standard Supplier VAT", percentage=18.0, group_type="Supplier")
                ])
                db.commit()
                print("Seeded Default Settings (Currencies, Terms, VAT groups).")

        # Seed Default Items (BOM raw materials & products)
        if not db.query(Item).first():
            db.add_all([
                Item(sku="MAT-FAB-01", name="100% Cotton Fabric", category="Fabric", base_uom="meters"),
                Item(sku="MAT-THR-02", name="Polyester Thread", category="Thread", base_uom="cones"),
                Item(sku="PRD-101", name="Basic T-Shirt", category="Completed Garment", base_uom="pcs")
            ])
            db.commit()
            print("Seeded Inventory Items.")

if __name__ == "__main__":
    from core.config import settings
    print(f"Connecting to database at: {settings.DB_HOST}...")
    try:
        seed_database()
        print("Done Seeding! 🎉")
    except Exception as e:
        print(f"Failed to seed db: {e}")
        print("Please ensure XAMPP MySQL is turned ON and the 'sew_admin' database exists.")
