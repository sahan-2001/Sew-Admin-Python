from pydantic import BaseModel
from typing import Optional, List
from modules.users.models import SiteType

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
