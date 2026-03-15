from pydantic import BaseModel, Field
from typing import Optional, List
from modules.customers.models import DiscountType

class CustomerItemPriceBase(BaseModel):
    item_id: int
    min_qty: float = 1.0
    price: float

class CustomerItemPriceCreate(CustomerItemPriceBase):
    pass

class CustomerItemPriceOut(CustomerItemPriceBase):
    id: int
    customer_id: int

    class Config:
        from_attributes = True

class CustomerItemDiscountBase(BaseModel):
    item_id: int
    min_qty: float = 1.0
    discount_type: DiscountType = DiscountType.PERCENTAGE
    discount_value: float
    min_discount: Optional[float] = None
    max_discount: Optional[float] = None

class CustomerItemDiscountCreate(CustomerItemDiscountBase):
    pass

class CustomerItemDiscountOut(CustomerItemDiscountBase):
    id: int
    customer_id: int

    class Config:
        from_attributes = True

class CustomerBase(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    is_active: bool = True

class CustomerCreate(CustomerBase):
    pass

class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    is_active: Optional[bool] = None

class CustomerOut(CustomerBase):
    id: int
    prices: List[CustomerItemPriceOut] = []
    discounts: List[CustomerItemDiscountOut] = []

    class Config:
        from_attributes = True
