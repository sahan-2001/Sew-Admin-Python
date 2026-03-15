from fastapi import APIRouter, Depends, HTTPException, status, Request, Body
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import Optional

from core.database import get_db
from core.security import ACCESS_TOKEN_EXPIRE_MINUTES, create_access_token, verify_password, get_password_hash
from core.dependencies import get_current_active_user, get_current_user, log_activity, require_permission
from modules.users.models import User, ActivityLog, Site, SiteType, user_sites
from modules.users.schemas import UserCreate, UserUpdate, UserProfileUpdate

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/settings", response_class=HTMLResponse)
def get_user_settings(request: Request):
    return templates.TemplateResponse("user_settings.html", {"request": request})

@router.get("/logs", response_class=HTMLResponse)
def get_user_logs(request: Request):
    return templates.TemplateResponse("user_logs.html", {"request": request})

@router.get("/login", response_class=HTMLResponse)
def get_login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.get("/logout")
def logout(request: Request):
    response = HTMLResponse(content="<script>localStorage.removeItem('token'); window.location.href='/api/users/login';</script>")
    return response

@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
        
    log_activity(db, user.id, "login", "users", "User logged in successfully")
            
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer", "theme_preference": user.theme_preference}

@router.get("/me")
def read_users_me(current_user: User = Depends(get_current_active_user)):
    return {
        "id": current_user.id, 
        "username": current_user.username, 
        "email": current_user.email,
        "role": current_user.role, 
        "permissions": current_user.permissions,
        "theme_preference": current_user.theme_preference,
        "default_site_id": current_user.default_site_id,
        "available_sites": [{"id": s.id, "name": s.name, "site_type": s.site_type} for s in current_user.available_sites]
    }

@router.put("/me/site")
def set_active_site(
    site_id: Optional[int] = Body(None, embed=True),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Persist the user's currently selected site as their default_site_id."""
    if site_id is not None:
        # Verify user has access to this site (admin bypass)
        if current_user.role != "admin":
            allowed_ids = [s.id for s in current_user.available_sites]
            if site_id not in allowed_ids:
                raise HTTPException(status_code=403, detail="Site not assigned to this user")
    current_user.default_site_id = site_id
    db.commit()
    return {"status": "success", "default_site_id": site_id}

@router.put("/me/profile")
def update_user_profile(
    profile_data: UserProfileUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    if profile_data.email is not None:
        current_user.email = profile_data.email
    if profile_data.theme_preference is not None:
        current_user.theme_preference = profile_data.theme_preference
    if profile_data.password:
        current_user.hashed_password = get_password_hash(profile_data.password)
        
    db.commit()
    db.refresh(current_user)
    log_activity(db, current_user.id, "update_profile", "users", "User updated profile")
    return {"status": "success"}

@router.get("/")
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

@router.post("/")
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

@router.put("/{user_id}")
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

@router.delete("/{user_id}")
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

@router.get("/activity-logs")
def get_recent_activity_logs(db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    if current_user.role != "admin":
        logs = db.query(ActivityLog).filter(ActivityLog.user_id == current_user.id).order_by(ActivityLog.timestamp.desc()).limit(50).all()
    else:
        logs = db.query(ActivityLog).order_by(ActivityLog.timestamp.desc()).limit(100).all()
    return logs

# -----------------------------------------------------------------------
# Site Management Endpoints
# -----------------------------------------------------------------------

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
def assign_user_to_site(
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
def unassign_user_from_site(
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
