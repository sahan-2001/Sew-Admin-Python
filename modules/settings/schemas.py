from pydantic import BaseModel
from typing import Optional, List, Dict
from modules.settings.models import SiteType, UserRole

# User Management
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
    permissions: Optional[dict] = None # e.g. {"sales": ["view"]}
    password: Optional[str] = None

class UserProfileUpdate(BaseModel):
    email: Optional[str] = None
    theme_preference: Optional[str] = None
    password: Optional[str] = None

# Category
class CategoryBase(BaseModel):
    name: str

class CategoryCreate(CategoryBase):
    pass

class CategoryResponse(CategoryBase):
    id: int
    class Config:
        from_attributes = True

# SubCategory
class SubCategoryBase(BaseModel):
    name: str
    category_id: int

class SubCategoryCreate(SubCategoryBase):
    pass

class SubCategoryResponse(SubCategoryBase):
    id: int
    class Config:
        from_attributes = True

# Sites
class SiteBase(BaseModel):
    name: str
    site_type: SiteType = SiteType.OTHER

class SiteCreate(SiteBase):
    pass

class SiteResponse(SiteBase):
    id: int
    class Config:
        from_attributes = True

class AssignUsersRequest(BaseModel):
    user_ids: List[int]

# Company Info
class CompanyInfoBase(BaseModel):
    name: str
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    tax_id: Optional[str] = None
    logo_url: Optional[str] = None

class CompanyInfoUpdate(CompanyInfoBase):
    pass

class CompanyInfoResponse(CompanyInfoBase):
    id: int
    class Config:
        from_attributes = True

# Approval Setup
class ApprovalSetupBase(BaseModel):
    document_type: str
    requires_approval: bool

class ApprovalSetupUpdate(ApprovalSetupBase):
    pass

class ApprovalSetupResponse(ApprovalSetupBase):
    id: int
    class Config:
        from_attributes = True

# Email Template
class EmailTemplateBase(BaseModel):
    name: str
    subject: str
    body_template: str

class EmailTemplateUpdate(EmailTemplateBase):
    pass

class EmailTemplateResponse(EmailTemplateBase):
    id: int
    class Config:
        from_attributes = True

# Currencies
class CurrencyBase(BaseModel):
    code: str
    name: str
    symbol: str
    is_global_default: bool = False

class CurrencyCreate(CurrencyBase):
    pass

class CurrencyUpdate(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None
    symbol: Optional[str] = None
    is_global_default: Optional[bool] = None

class CurrencyResponse(CurrencyBase):
    id: int
    class Config:
        from_attributes = True
