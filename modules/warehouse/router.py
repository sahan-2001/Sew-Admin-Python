from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import List, Optional
from core.database import get_db
from core.dependencies import get_current_user, require_permission
from modules.users.models import User

from modules.warehouse.schemas import (
    WarehouseCreate, WarehouseResponse,
    InventoryLocationCreate, InventoryLocationResponse,
    ItemCreate, ItemResponse,
    StockMovementRequest, StockTransferRequest, PickItemRequest, PhysicalCountRequest,
    ItemJournalResponse, PhysicalInventoryResponse
)
from modules.warehouse.services import WarehouseOperationsService

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse, include_in_schema=False)
def get_warehouse_dashboard(request: Request):
    """Serve the interactive warehouse dashboard."""
    return templates.TemplateResponse("warehouse.html", {"request": request})

@router.post("/warehouses", response_model=WarehouseResponse)
def create_warehouse(
    req: WarehouseCreate,
    db: Session = Depends(get_db),
    cur: User = Depends(require_permission("warehouse", "create"))
):
    service = WarehouseOperationsService(db)
    return service.create_warehouse(req.name, req.description, req.location)

@router.post("/locations", response_model=InventoryLocationResponse)
def create_location(
    req: InventoryLocationCreate,
    db: Session = Depends(get_db),
    cur: User = Depends(require_permission("warehouse", "create"))
):
    service = WarehouseOperationsService(db)
    return service.create_location(req.warehouse_id, req.name, req.location_type, req.description)

@router.post("/items", response_model=ItemResponse)
def create_item(
    req: ItemCreate,
    db: Session = Depends(get_db),
    cur: User = Depends(require_permission("warehouse", "create"))
):
    service = WarehouseOperationsService(db)
    return service.create_item(req.sku, req.name, req.category, req.base_uom)

@router.post("/stock/add", response_model=ItemJournalResponse)
def add_stock(
    req: StockMovementRequest,
    db: Session = Depends(get_db),
    cur: User = Depends(require_permission("warehouse", "edit"))
):
    try:
        service = WarehouseOperationsService(db)
        return service.add_stock(req.item_id, req.location_id, req.qty, req.reference)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/stock/remove", response_model=ItemJournalResponse)
def remove_stock(
    req: StockMovementRequest,
    db: Session = Depends(get_db),
    cur: User = Depends(require_permission("warehouse", "edit"))
):
    try:
        service = WarehouseOperationsService(db)
        return service.remove_stock(req.item_id, req.location_id, req.qty, req.reference)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/stock/transfer")
def transfer_stock(
    req: StockTransferRequest,
    db: Session = Depends(get_db),
    cur: User = Depends(require_permission("warehouse", "edit"))
):
    try:
        service = WarehouseOperationsService(db)
        out_j, in_j = service.transfer_stock(req.item_id, req.from_location_id, req.to_location_id, req.qty, req.reference)
        return {"status": "success", "out_journal_id": out_j.id, "in_journal_id": in_j.id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/stock/pick", response_model=ItemJournalResponse)
def pick_stock(
    req: PickItemRequest,
    db: Session = Depends(get_db),
    cur: User = Depends(require_permission("warehouse", "edit"))
):
    try:
        service = WarehouseOperationsService(db)
        return service.pick_items(req.item_id, req.location_id, req.qty, req.reference, req.allow_partial)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/stock/physical-count", response_model=PhysicalInventoryResponse)
def physical_count(
    req: PhysicalCountRequest,
    db: Session = Depends(get_db),
    cur: User = Depends(require_permission("warehouse", "edit"))
):
    try:
        service = WarehouseOperationsService(db)
        return service.record_physical_count(req.item_id, req.location_id, req.counted_qty, req.reference)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/stock/query")
def get_stock(
    item_id: int,
    location_id: Optional[int] = None,
    warehouse_id: Optional[int] = None,
    db: Session = Depends(get_db),
    cur: User = Depends(get_current_user)
):
    service = WarehouseOperationsService(db)
    if location_id:
        qty = service.get_location_stock(item_id, location_id)
        return {"item_id": item_id, "location_id": location_id, "qty_on_hand": qty}
    
    qty = service.get_total_stock(item_id, warehouse_id)
    return {"item_id": item_id, "warehouse_id": warehouse_id, "qty_on_hand": qty}
