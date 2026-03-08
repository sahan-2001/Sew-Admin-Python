from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from core.database import engine, Base

# Import all module routers
from modules.users.router import router as users_router
from modules.accounting.router import router as accounting_router
from modules.customers.router import router as customers_router
from modules.orders.router import router as orders_router
from modules.products.router import router as products_router
from modules.inventory.router import router as inventory_router
from modules.suppliers.router import router as suppliers_router
from modules.production.router import router as production_router
from modules.employees.router import router as employees_router
from modules.reports.router import router as reports_router

# Ensure all Models are loaded for SQL tables auto-creation
import modules.settings.models
import modules.purchasing.models
import modules.sales.models
import modules.production.models
import modules.inventory.models
import modules.accounting.models
import modules.users.models

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Sew-Admin Apparel ERP API",
    description="Python/FastAPI ERP System designed for small and medium-scale apparel manufacturing.",
    version="1.0.0"
)

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Include module-wise routers
app.include_router(users_router, prefix="/api/users", tags=["Users"])
app.include_router(accounting_router, prefix="/api/accounting", tags=["Accounting"])
app.include_router(customers_router, prefix="/api/customers", tags=["Customers"])
app.include_router(orders_router, prefix="/api/orders", tags=["Orders"])
app.include_router(products_router, prefix="/api/products", tags=["Products"])
app.include_router(inventory_router, prefix="/api/inventory", tags=["Inventory"])
app.include_router(suppliers_router, prefix="/api/suppliers", tags=["Suppliers"])
app.include_router(production_router, prefix="/api/production", tags=["Production"])
app.include_router(employees_router, prefix="/api/employees", tags=["Employees"])
app.include_router(reports_router, prefix="/api/reports", tags=["Reports"])

@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
