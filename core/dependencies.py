from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from datetime import datetime

from core.database import get_db
from core.security import SECRET_KEY, ALGORITHM
from modules.users.models import User, ActivityLog

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/users/login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    return user

def get_current_active_user(current_user: User = Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def require_permission(module: str, action: str):
    """
    Dependency generator for checking granular permissions.
    Usage: @router.get("/something", dependencies=[Depends(require_permission("sales", "create"))])
    """
    def permission_checker(current_user: User = Depends(get_current_active_user)):
        # Admins have all permissions
        if current_user.role == "admin":
            return current_user
            
        permissions = current_user.permissions or {}
        module_perms = permissions.get(module, [])
        
        if action not in module_perms:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Not enough permissions: requires '{action}' on '{module}'"
            )
        return current_user
    return permission_checker

def log_activity(db: Session, user_id: int, action: str, module: str, details: str = ""):
    """Helper function to log user activities"""
    log_entry = ActivityLog(
        user_id=user_id,
        action=action,
        module=module,
        details=details,
        timestamp=datetime.utcnow()
    )
    db.add(log_entry)
    db.commit()
    db.refresh(log_entry)
    return log_entry
