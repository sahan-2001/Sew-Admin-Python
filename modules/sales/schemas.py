from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime
from modules.sales.models import SalesType, SalesStatus

class SalesOrderVariationBase(BaseModel):
    color: Optional[str] = None
    size: Optional[str] = None
    quantity: int = 0
    unit_price: float = 0.0

class SalesOrderVariationCreate(SalesOrderVariationBase):
    pass

class SalesOrderVariationResponse(SalesOrderVariationBase):
    id: int
    so_line_id: int
    class Config:
        from_attributes = True

class SalesOrderLineBase(BaseModel):
    item_name: str
    item_id: Optional[int] = None
    location_id: Optional[int] = None
    item_description: Optional[str] = None
    uom: str = "pcs"
    unit_price: float = 0.0
    quantity: int = 1
    line_total: float = 0.0

class SalesOrderLineCreate(SalesOrderLineBase):
    variations: List[SalesOrderVariationCreate] = []

class SalesOrderLineResponse(SalesOrderLineBase):
    id: int
    so_id: int
    variations: List[SalesOrderVariationResponse] = []
    class Config:
        from_attributes = True

class SalesOrderBase(BaseModel):
    customer_id: int
    order_type: SalesType = SalesType.BULK
    status: SalesStatus = SalesStatus.OPEN
    total_amount: float = 0.0

class SalesOrderCreate(SalesOrderBase):
    lines: List[SalesOrderLineCreate]

class SalesOrderUpdate(BaseModel):
    status: Optional[SalesStatus] = None

class SalesOrderResponse(SalesOrderBase):
    id: int
    so_number: str
    order_date: datetime
    lines: List[SalesOrderLineResponse] = []
    
    class Config:
        from_attributes = True
