from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import List

from core.database import get_db
from core.dependencies import get_current_user, require_permission
from modules.users.models import User
from modules.customers import models, schemas
from modules.warehouse.models import WarehouseItem

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/ui", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
def get_customers_ui(request: Request):
    return templates.TemplateResponse("customers.html", {"request": request})

@router.get("/all", response_model=List[schemas.CustomerOut])
def get_all_customers(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    customers = db.query(models.Customer).all()
    return customers

@router.post("/", response_model=schemas.CustomerOut)
def create_customer(customer: schemas.CustomerCreate, db: Session = Depends(get_db), current_user: User = Depends(require_permission("sales", "create"))):
    db_customer = models.Customer(**customer.model_dump())
    db.add(db_customer)
    db.commit()
    db.refresh(db_customer)
    return db_customer

@router.put("/{customer_id}", response_model=schemas.CustomerOut)
def update_customer(customer_id: int, customer: schemas.CustomerUpdate, db: Session = Depends(get_db), current_user: User = Depends(require_permission("sales", "edit"))):
    db_customer = db.query(models.Customer).filter(models.Customer.id == customer_id).first()
    if not db_customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    update_data = customer.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_customer, key, value)
        
    db.commit()
    db.refresh(db_customer)
    return db_customer

@router.delete("/{customer_id}")
def delete_customer(customer_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_permission("sales", "delete"))):
    db_customer = db.query(models.Customer).filter(models.Customer.id == customer_id).first()
    if not db_customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # Delete related prices and discounts
    db.query(models.CustomerItemPrice).filter(models.CustomerItemPrice.customer_id == customer_id).delete()
    db.query(models.CustomerItemDiscount).filter(models.CustomerItemDiscount.customer_id == customer_id).delete()
    
    db.delete(db_customer)
    db.commit()
    return {"message": "Customer deleted successfully"}

# ---------------------------- #
# Prices and Discounts
# ---------------------------- #
@router.post("/{customer_id}/prices", response_model=schemas.CustomerItemPriceOut)
def add_customer_price(customer_id: int, price_data: schemas.CustomerItemPriceCreate, db: Session = Depends(get_db), current_user: User = Depends(require_permission("sales", "edit"))):
    db_item = db.query(WarehouseItem).filter(WarehouseItem.id == price_data.item_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")

    new_price = models.CustomerItemPrice(**price_data.model_dump(), customer_id=customer_id)
    db.add(new_price)
    db.commit()
    db.refresh(new_price)
    return new_price

@router.delete("/{customer_id}/prices/{price_id}")
def delete_customer_price(customer_id: int, price_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_permission("sales", "edit"))):
    db_price = db.query(models.CustomerItemPrice).filter(models.CustomerItemPrice.id == price_id, models.CustomerItemPrice.customer_id == customer_id).first()
    if not db_price:
         raise HTTPException(status_code=404, detail="Price not found")
    
    db.delete(db_price)
    db.commit()
    return {"message": "Price deleted successfully"}

@router.post("/{customer_id}/discounts", response_model=schemas.CustomerItemDiscountOut)
def add_customer_discount(customer_id: int, discount_data: schemas.CustomerItemDiscountCreate, db: Session = Depends(get_db), current_user: User = Depends(require_permission("sales", "edit"))):
    db_item = db.query(WarehouseItem).filter(WarehouseItem.id == discount_data.item_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")

    new_discount = models.CustomerItemDiscount(**discount_data.model_dump(), customer_id=customer_id)
    db.add(new_discount)
    db.commit()
    db.refresh(new_discount)
    return new_discount

@router.delete("/{customer_id}/discounts/{discount_id}")
def delete_customer_discount(customer_id: int, discount_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_permission("sales", "edit"))):
    db_discount = db.query(models.CustomerItemDiscount).filter(models.CustomerItemDiscount.id == discount_id, models.CustomerItemDiscount.customer_id == customer_id).first()
    if not db_discount:
         raise HTTPException(status_code=404, detail="Discount not found")
    
    db.delete(db_discount)
    db.commit()
    return {"message": "Discount deleted successfully"}
