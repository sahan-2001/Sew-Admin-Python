from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import List, Optional

from core.database import get_db
from core.dependencies import get_current_user, require_permission
from modules.users.models import User
from modules.warehouse.models import ItemType

from modules.items.schemas import (
    ItemCreate, ItemUpdate, ItemResponse, ItemStockResponse
)
from modules.items.services import ItemService

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse)
@router.get("", response_class=HTMLResponse, include_in_schema=False)
def get_items_dashboard(request: Request):
    """Serve the items management dashboard."""
    # We will create an items.html next
    return templates.TemplateResponse("items.html", {"request": request})

@router.post("/", response_model=ItemResponse)
def create_item(
    req: ItemCreate,
    db: Session = Depends(get_db),
    cur: User = Depends(require_permission("items", "create"))  # Using generic permission check
):
    service = ItemService(db)
    return service.create_item(req)

@router.get("/list", response_model=List[ItemResponse])
def list_items(
    category: Optional[str] = None,
    item_type: Optional[ItemType] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    cur: User = Depends(get_current_user)
):
    service = ItemService(db)
    return service.get_items(category, item_type, is_active)

@router.get("/{item_id}", response_model=ItemStockResponse)
def get_item(
    item_id: int,
    warehouse_id: Optional[int] = None,
    db: Session = Depends(get_db),
    cur: User = Depends(get_current_user)
):
    service = ItemService(db)
    return service.get_item_with_stock(item_id, warehouse_id)

@router.patch("/{item_id}", response_model=ItemResponse)
def update_item(
    item_id: int,
    req: ItemUpdate,
    db: Session = Depends(get_db),
    cur: User = Depends(require_permission("items", "edit"))
):
    service = ItemService(db)
    return service.update_item(item_id, req)

@router.delete("/{item_id}")
def delete_item(
    item_id: int,
    hard_delete: bool = False,
    db: Session = Depends(get_db),
    cur: User = Depends(require_permission("items", "delete"))
):
    service = ItemService(db)
    return service.delete_item(item_id, hard_delete)
