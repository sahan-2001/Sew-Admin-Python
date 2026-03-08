import enum
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Enum, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from sqlalchemy_utils import StringEncryptedType
from sqlalchemy_utils.types.encrypted.encrypted_type import FernetEngine
from core.database import Base
from core.config import settings

secret_key = settings.SECRET_KEY

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    WORKER = "worker"
    ACCOUNTANT = "accountant"

class Site(Base):
    __tablename__ = "sites"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True) # e.g. Factory 1, Head Office

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    
    # Encrypt PII data directly in the database
    email = Column(StringEncryptedType(String, secret_key, FernetEngine, length=255))
    phone = Column(StringEncryptedType(String, secret_key, FernetEngine, length=50))
    
    hashed_password = Column(String(255))
    role = Column(Enum(UserRole), default=UserRole.WORKER)
    is_active = Column(Boolean, default=True)
    theme_preference = Column(String(20), default="system") # dark, light, system
    default_site_id = Column(Integer, ForeignKey("sites.id"))
    
    # Granular permissions mapping JSON: e.g. {"sales_orders": ["create", "edit", "view"]}
    permissions = Column(JSON, nullable=True)

class ActivityLog(Base):
    __tablename__ = "activity_logs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    action = Column(String(255))
    module = Column(String(50))
    timestamp = Column(DateTime, default=datetime.utcnow)
    details = Column(Text)
