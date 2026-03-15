import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime, Enum, Text, JSON, Table
from sqlalchemy.orm import relationship
from sqlalchemy_utils import StringEncryptedType
from sqlalchemy_utils.types.encrypted.encrypted_type import FernetEngine
from core.database import Base, TimestampMixin
from core.config import settings

secret_key = settings.SECRET_KEY

# Enums
class UserRole(str, enum.Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    WORKER = "worker"
    ACCOUNTANT = "accountant"

class SiteType(str, enum.Enum):
    SHOP = "shop"
    HEAD_OFFICE = "head_office"
    BRANCH = "branch"
    OUTLET = "outlet"
    WAREHOUSE = "warehouse"
    ADMIN_OFFICE = "admin_office"
    OTHER = "other"

# Association Tables
user_sites = Table(
    "user_sites", 
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id")),
    Column("site_id", Integer, ForeignKey("sites.id"))
)

class Currency(TimestampMixin, Base):
    __tablename__ = "currencies"
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(10), unique=True, index=True) # e.g. USD, LKR, EUR
    name = Column(String(50))
    symbol = Column(String(10))
    is_global_default = Column(Boolean, default=False)

class Country(TimestampMixin, Base):
    __tablename__ = "countries"
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(10), unique=True)
    name = Column(String(100))

class VatGroup(TimestampMixin, Base):
    __tablename__ = "vat_groups"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50)) # e.g. Standard, Exempt, Reduced
    percentage = Column(Float, default=0.0)
    group_type = Column(String(20)) # "Item", "Customer", "Supplier"

class DeliveryTerm(TimestampMixin, Base):
    __tablename__ = "delivery_terms"
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(20)) # e.g. FOB, CIF, EXW
    description = Column(String(255))

class PaymentTerm(TimestampMixin, Base):
    __tablename__ = "payment_terms"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50)) # e.g. Net 30, COD
    days = Column(Integer, default=0)

class PaymentMethod(TimestampMixin, Base):
    __tablename__ = "payment_methods"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50)) # e.g. Bank Transfer, Cash, Card

class ItemCategory(TimestampMixin, Base):
    __tablename__ = "item_categories"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True)

class ItemSubCategory(TimestampMixin, Base):
    __tablename__ = "item_sub_categories"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), index=True)
    category_id = Column(Integer, ForeignKey("item_categories.id"))

class Site(Base):
    __tablename__ = "sites"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True) # e.g. Factory 1, Head Office
    site_type = Column(Enum(SiteType), default=SiteType.OTHER)

    # Audit fields
    created_at  = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by  = Column(Integer, ForeignKey("users.id"), nullable=True)
    updated_at  = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=True)
    updated_by  = Column(Integer, ForeignKey("users.id"), nullable=True)
    deleted_at  = Column(DateTime, nullable=True)
    deleted_by  = Column(Integer, ForeignKey("users.id"), nullable=True)

    users = relationship("User", secondary=user_sites, back_populates="available_sites")

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    
    # Encrypt PII data directly in the database
    email = Column(StringEncryptedType(String, secret_key, FernetEngine, length=255))
    phone = Column(StringEncryptedType(String, secret_key, FernetEngine, length=255))
    
    hashed_password = Column(String(255))
    role = Column(Enum(UserRole), default=UserRole.WORKER)
    is_active = Column(Boolean, default=True)
    theme_preference = Column(String(20), default="system") # dark, light, system
    default_site_id = Column(Integer, ForeignKey("sites.id"))
    
    # Granular permissions mapping JSON: e.g. {"sales_orders": ["create", "edit", "view"]}
    permissions = Column(JSON, nullable=True)

    # Audit fields
    created_at  = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at  = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=True)
    deleted_at  = Column(DateTime, nullable=True)
    deleted_by  = Column(Integer, nullable=True)

    available_sites = relationship("Site", secondary=user_sites, back_populates="users")

class ActivityLog(Base):
    __tablename__ = "activity_logs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    action = Column(String(255))
    module = Column(String(50))
    timestamp = Column(DateTime, default=datetime.utcnow)
    details = Column(Text)

class CompanyInfo(TimestampMixin, Base):
    __tablename__ = "company_info"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255))
    address = Column(Text)
    phone = Column(String(100))
    email = Column(String(100))
    website = Column(String(255))
    tax_id = Column(String(50))
    logo_url = Column(String(255))

class ApprovalSetup(TimestampMixin, Base):
    __tablename__ = "approval_setups"
    id = Column(Integer, primary_key=True, index=True)
    document_type = Column(String(100), unique=True) # e.g. "Sales Order"
    requires_approval = Column(Boolean, default=True)

class EmailTemplate(TimestampMixin, Base):
    __tablename__ = "email_templates"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True) # e.g. "Sales Order Creation"
    subject = Column(String(255))
    body_template = Column(Text)

