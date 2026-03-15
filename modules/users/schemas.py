from pydantic import BaseModel
from typing import Optional, List, Dict
from modules.users.models import UserRole

class UserCreate(BaseModel):
    username: str
    password: str
    email: Optional[str] = None
    role: UserRole = UserRole.WORKER
    is_active: bool = True

class UserUpdate(BaseModel):
    email: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    permissions: Optional[Dict[str, List[str]]] = None
    password: Optional[str] = None

class UserProfileUpdate(BaseModel):
    email: Optional[str] = None
    theme_preference: Optional[str] = None
    password: Optional[str] = None
