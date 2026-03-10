from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import List

from core.database import get_db
from modules.settings.models import ItemCategory, ItemSubCategory
from modules.settings.schemas import CategoryCreate, CategoryResponse, SubCategoryCreate, SubCategoryResponse

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse)
@router.get("", response_class=HTMLResponse, include_in_schema=False)
def get_settings(request: Request):
    return templates.TemplateResponse("settings.html", {"request": request})

# Categories API
@router.get("/categories", response_model=List[CategoryResponse])
def get_categories(db: Session = Depends(get_db)):
    return db.query(ItemCategory).all()

@router.post("/categories", response_model=CategoryResponse)
def create_category(category: CategoryCreate, db: Session = Depends(get_db)):
    existing = db.query(ItemCategory).filter(ItemCategory.name == category.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Category already exists")
    new_cat = ItemCategory(name=category.name)
    db.add(new_cat)
    db.commit()
    db.refresh(new_cat)
    return new_cat

@router.delete("/categories/{cat_id}")
def delete_category(cat_id: int, db: Session = Depends(get_db)):
    cat = db.query(ItemCategory).filter(ItemCategory.id == cat_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    # Also delete subcategories if needed or restrict wait
    subs = db.query(ItemSubCategory).filter(ItemSubCategory.category_id == cat_id).count()
    if subs > 0:
        raise HTTPException(status_code=400, detail="Cannot delete category with sub-categories")
    db.delete(cat)
    db.commit()
    return {"status": "success"}

# Sub-Categories API
@router.get("/sub-categories", response_model=List[SubCategoryResponse])
def get_sub_categories(category_id: int = None, db: Session = Depends(get_db)):
    query = db.query(ItemSubCategory)
    if category_id:
        query = query.filter(ItemSubCategory.category_id == category_id)
    return query.all()

@router.post("/sub-categories", response_model=SubCategoryResponse)
def create_sub_category(sub: SubCategoryCreate, db: Session = Depends(get_db)):
    cat = db.query(ItemCategory).filter(ItemCategory.id == sub.category_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Parent category not found")
    new_sub = ItemSubCategory(name=sub.name, category_id=sub.category_id)
    db.add(new_sub)
    db.commit()
    db.refresh(new_sub)
    return new_sub

@router.delete("/sub-categories/{sub_id}")
def delete_sub_category(sub_id: int, db: Session = Depends(get_db)):
    sub = db.query(ItemSubCategory).filter(ItemSubCategory.id == sub_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Sub-category not found")
    db.delete(sub)
    db.commit()
    return {"status": "success"}
