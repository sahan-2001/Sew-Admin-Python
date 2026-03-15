from fastapi import APIRouter, Request, Depends, HTTPException, Body
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import List, Optional

from core.database import get_db
from core.security import ACCESS_TOKEN_EXPIRE_MINUTES, create_access_token, verify_password, get_password_hash
from core.dependencies import get_current_active_user, get_current_user, log_activity, require_permission
from modules.settings.models import ItemCategory, ItemSubCategory, Site, SiteType, User
from modules.settings.schemas import (
    CategoryCreate, CategoryResponse, SubCategoryCreate, SubCategoryResponse, 
    SiteCreate, SiteResponse, AssignUsersRequest,
    UserCreate, UserUpdate
)

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse)
@router.get("", response_class=HTMLResponse, include_in_schema=False)
def get_settings(request: Request):
    return templates.TemplateResponse("settings.html", {"request": request})

# User Management API
@router.get("/users")
def get_all_users(db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    users = db.query(User).all()
    return [{
        "id": u.id, 
        "username": u.username, 
        "email": u.email,
        "role": u.role,
        "is_active": u.is_active,
        "permissions": u.permissions or {},
        "available_sites": [{"id": s.id, "name": s.name} for s in u.available_sites]
    } for u in users]

@router.post("/users")
def create_new_user(user_data: UserCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    existing = db.query(User).filter(User.username == user_data.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")
        
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        role=user_data.role,
        is_active=user_data.is_active
    )
    db.add(new_user)
    db.commit()
    return {"status": "success"}

@router.put("/users/{user_id}")
def update_user_info(user_id: int, user_data: UserUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    if user_data.email is not None:
        user.email = user_data.email
    if user_data.role is not None:
        user.role = user_data.role
    if user_data.is_active is not None:
        user.is_active = user_data.is_active
    if user_data.permissions is not None:
        user.permissions = user_data.permissions
    if user_data.password:
        user.hashed_password = get_password_hash(user_data.password)
        
    db.commit()
    return {"status": "success"}

@router.delete("/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    db.delete(user)
    db.commit()
    return {"status": "success"}

# Sites API
@router.get("/sites/types")
def get_site_types():
    return [{"value": e.value, "label": e.name.replace("_", " ").title()} for e in SiteType]

@router.get("/sites")
def list_sites(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Return all sites (admin) or only assigned sites (regular users)."""
    if current_user.role == "admin":
        sites = db.query(Site).filter(Site.deleted_at == None).all()
    else:
        sites = [s for s in current_user.available_sites]
    return [
        {"id": s.id, "name": s.name, "site_type": s.site_type}
        for s in sites
    ]

@router.post("/sites")
def create_site(
    name: str = Body(..., embed=True),
    site_type: str = Body("other", embed=True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    existing = db.query(Site).filter(Site.name == name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Site with this name already exists")
    site = Site(name=name, site_type=site_type, created_by=current_user.id)
    db.add(site)
    db.commit()
    db.refresh(site)
    return {"status": "success", "id": site.id, "name": site.name}

@router.put("/sites/{site_id}")
def update_site(
    site_id: int,
    name: Optional[str] = Body(None, embed=True),
    site_type: Optional[str] = Body(None, embed=True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    site = db.query(Site).filter(Site.id == site_id, Site.deleted_at == None).first()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    if name is not None:
        site.name = name
    if site_type is not None:
        site.site_type = site_type
    site.updated_by = current_user.id
    db.commit()
    return {"status": "success"}

@router.delete("/sites/{site_id}")
def delete_site(
    site_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    from datetime import datetime
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    site = db.query(Site).filter(Site.id == site_id, Site.deleted_at == None).first()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    site.deleted_at = datetime.utcnow()
    site.deleted_by = current_user.id
    db.commit()
    return {"status": "success"}

@router.post("/sites/{site_id}/assign/{user_id}")
def assign_user_to_site_api(
    site_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    site = db.query(Site).filter(Site.id == site_id).first()
    user = db.query(User).filter(User.id == user_id).first()
    if not site or not user:
        raise HTTPException(status_code=404, detail="Site or User not found")
    if site not in user.available_sites:
        user.available_sites.append(site)
        db.commit()
    # Auto-set default site if not already set
    if user.default_site_id is None:
        user.default_site_id = site_id
        db.commit()
    return {"status": "success"}

@router.delete("/sites/{site_id}/unassign/{user_id}")
def unassign_user_from_site_api(
    site_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    site = db.query(Site).filter(Site.id == site_id).first()
    user = db.query(User).filter(User.id == user_id).first()
    if not site or not user:
        raise HTTPException(status_code=404, detail="Site or User not found")
    if site in user.available_sites:
        user.available_sites.remove(site)
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
