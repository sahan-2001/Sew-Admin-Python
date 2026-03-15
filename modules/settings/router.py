from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import List

from core.database import get_db
from modules.settings.models import ItemCategory, ItemSubCategory
from modules.settings.schemas import CategoryCreate, CategoryResponse, SubCategoryCreate, SubCategoryResponse, SiteCreate, SiteResponse, AssignUsersRequest
from modules.users.models import Site, SiteType, User

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse)
@router.get("", response_class=HTMLResponse, include_in_schema=False)
def get_settings(request: Request):
    return templates.TemplateResponse("settings.html", {"request": request})

# Sites API
@router.get("/sites/types")
def get_site_types():
    return [{"value": e.value, "label": e.name.replace("_", " ").title()} for e in SiteType]

@router.get("/sites", response_model=List[SiteResponse])
def get_sites(db: Session = Depends(get_db)):
    return db.query(Site).all()

@router.post("/sites", response_model=SiteResponse)
def create_site(site: SiteCreate, db: Session = Depends(get_db)):
    existing = db.query(Site).filter(Site.name == site.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Site already exists")
    new_site = Site(name=site.name, site_type=site.site_type)
    db.add(new_site)
    db.commit()
    db.refresh(new_site)
    return new_site

@router.delete("/sites/{site_id}")
def delete_site(site_id: int, db: Session = Depends(get_db)):
    site = db.query(Site).filter(Site.id == site_id).first()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    db.delete(site)
    db.commit()
    return {"status": "success"}

@router.put("/sites/{site_id}", response_model=SiteResponse)
def update_site(site_id: int, site: SiteCreate, db: Session = Depends(get_db)):
    existing = db.query(Site).filter(Site.id == site_id).first()
    if not existing:
        raise HTTPException(status_code=404, detail="Site not found")
    
    # Check name collision
    conflict = db.query(Site).filter(Site.name == site.name, Site.id != site_id).first()
    if conflict:
        raise HTTPException(status_code=400, detail="Site name already exists")
        
    existing.name = site.name
    existing.site_type = site.site_type
    db.commit()
    db.refresh(existing)
    return existing

@router.get("/sites/{site_id}/users")
def get_site_users(site_id: int, db: Session = Depends(get_db)):
    site = db.query(Site).filter(Site.id == site_id).first()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    return [{"id": u.id, "username": u.username} for u in site.users]

@router.post("/sites/{site_id}/assign_users")
def assign_users_to_site(site_id: int, req: AssignUsersRequest, db: Session = Depends(get_db)):
    site = db.query(Site).filter(Site.id == site_id).first()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    
    users = db.query(User).filter(User.id.in_(req.user_ids)).all()
    site.users = users
    db.commit()
    return {"status": "success"}

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
    # Check for duplicate sub-category name under the same parent
    existing_sub = db.query(ItemSubCategory).filter(
        ItemSubCategory.name == sub.name,
        ItemSubCategory.category_id == sub.category_id
    ).first()
    if existing_sub:
        raise HTTPException(status_code=400, detail=f"Sub-category '{sub.name}' already exists under '{cat.name}'")
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
