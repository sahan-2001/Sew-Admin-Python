from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta

from core.database import get_db
from core.security import ACCESS_TOKEN_EXPIRE_MINUTES, create_access_token, verify_password
from core.dependencies import get_current_active_user, get_current_user, log_activity, require_permission
from modules.users.models import User, ActivityLog
router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/settings", response_class=HTMLResponse)
def get_user_settings(request: Request):
    return templates.TemplateResponse("user_settings.html", {"request": request})

@router.get("/logs", response_class=HTMLResponse)
def get_user_logs(request: Request):
    return templates.TemplateResponse("user_logs.html", {"request": request})

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
        raise HTTPException(status_code=400, detail="Inactive user")
        
    log_activity(db, user.id, "login", "users", "User logged in successfully")
            
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer", "theme_preference": user.theme_preference}

@router.get("/me")
def read_users_me(current_user: User = Depends(get_current_active_user)):
    return {"id": current_user.id, "username": current_user.username, "role": current_user.role, "permissions": current_user.permissions}

@router.get("/activity-logs")
def get_recent_activity_logs(db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    # Restrict to admin or module specific logic if needed
    if current_user.role != "admin":
        logs = db.query(ActivityLog).filter(ActivityLog.user_id == current_user.id).order_by(ActivityLog.timestamp.desc()).limit(50).all()
    else:
        logs = db.query(ActivityLog).order_by(ActivityLog.timestamp.desc()).limit(100).all()
    return logs

