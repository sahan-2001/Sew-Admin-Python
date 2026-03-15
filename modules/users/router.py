from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta

from core.database import get_db
from core.security import ACCESS_TOKEN_EXPIRE_MINUTES, create_access_token, verify_password, get_password_hash
from core.dependencies import get_current_active_user, get_current_user, log_activity, require_permission
from modules.users.models import User, ActivityLog
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
        "available_sites": [{"id": s.id, "name": s.name} for s in current_user.available_sites]
    }

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
