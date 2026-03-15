from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import List

from core.database import get_db
from core.dependencies import get_current_user, require_permission
from modules.users.models import User
from modules.sales.models import SalesOrder, SalesOrderLine, SalesOrderVariation, SalesStatus
from modules.sales.schemas import SalesOrderCreate, SalesOrderUpdate, SalesOrderResponse

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse)
def get_sales(request: Request):
    return templates.TemplateResponse("sales.html", {"request": request})

@router.post("/orders", response_model=SalesOrderResponse)
def create_sales_order(
    data: SalesOrderCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    import time
    so_number = f"SO-{int(time.time())}"
    
    so = SalesOrder(
        so_number=so_number,
        customer_id=data.customer_id,
        order_type=data.order_type,
        status=data.status,
        total_amount=data.total_amount
    )
    db.add(so)
    db.commit()
    db.refresh(so)
    
    for line in data.lines:
        db_line = SalesOrderLine(
            so_id=so.id,
            item_name=line.item_name,
            item_id=line.item_id,
            location_id=line.location_id,
            item_description=line.item_description,
            uom=line.uom,
            unit_price=line.unit_price,
            quantity=line.quantity,
            line_total=line.line_total
        )
        db.add(db_line)
        db.commit()
        db.refresh(db_line)
        
        for var in line.variations:
            db_var = SalesOrderVariation(
                so_line_id=db_line.id,
                color=var.color,
                size=var.size,
                quantity=var.quantity,
                unit_price=var.unit_price
            )
            db.add(db_var)
    db.commit()
    db.refresh(so)
    return so

@router.put("/orders/{so_id}", response_model=SalesOrderResponse)
def update_sales_order(
    so_id: int, 
    data: SalesOrderCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    so = db.query(SalesOrder).filter(SalesOrder.id == so_id).first()
    if not so:
        raise HTTPException(status_code=404, detail="Order not found")
    
    if so.status != SalesStatus.OPEN:
        raise HTTPException(status_code=400, detail="Only OPEN orders can be edited directly")
        
    so.customer_id = data.customer_id
    so.order_type = data.order_type
    so.total_amount = data.total_amount
    
    # Replace lines and variations (cascading delete handles variants)
    db.query(SalesOrderLine).filter(SalesOrderLine.so_id == so_id).delete()
    
    for line in data.lines:
        db_line = SalesOrderLine(
            so_id=so.id,
            item_name=line.item_name,
            item_id=line.item_id,
            location_id=line.location_id,
            item_description=line.item_description,
            uom=line.uom,
            unit_price=line.unit_price,
            quantity=line.quantity,
            line_total=line.line_total
        )
        db.add(db_line)
        db.commit()
        db.refresh(db_line)
        
        for var in line.variations:
            db_var = SalesOrderVariation(
                so_line_id=db_line.id,
                color=var.color,
                size=var.size,
                quantity=var.quantity,
                unit_price=var.unit_price
            )
            db.add(db_var)
        
    db.commit()
    db.refresh(so)
    return so

@router.get("/orders", response_model=List[SalesOrderResponse])
def get_all_sales_orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    orders = db.query(SalesOrder).all()
    return orders

@router.put("/orders/{so_id}/status", response_model=SalesOrderResponse)
def update_sales_order_status(
    so_id: int, 
    data: SalesOrderUpdate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    so = db.query(SalesOrder).filter(SalesOrder.id == so_id).first()
    if not so:
        raise HTTPException(status_code=404, detail="Order not found")
        
    if data.status:
        so.status = data.status
        
    db.commit()
    db.refresh(so)
    return so
