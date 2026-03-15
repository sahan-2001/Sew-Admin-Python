from typing import Optional, List
from pydantic import BaseModel, Field
from modules.warehouse.models import ItemType

class ItemBase(BaseModel):
    sku: str = Field(..., max_length=50)
    name: str = Field(..., max_length=100)
    category: Optional[str] = None
    sub_category: Optional[str] = None
    base_uom: str = Field(..., max_length=20)
    item_type: ItemType = ItemType.INVENTORY
    description: Optional[str] = None

class ItemCreate(ItemBase):
    pass

class ItemUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    category: Optional[str] = Field(None, max_length=50)
    sub_category: Optional[str] = Field(None, max_length=50)
    base_uom: Optional[str] = Field(None, max_length=20)
    item_type: Optional[ItemType] = None
    description: Optional[str] = Field(None, max_length=255)
    is_active: Optional[bool] = None

class ItemResponse(ItemBase):
    id: int
    qty_on_hand: float
    is_active: bool
    
    class Config:
        from_attributes = True

class StockLocationDetail(BaseModel):
    location_id: int
    location_name: str
    location_type: str
    warehouse_name: str
    qty: float

class ItemStockResponse(ItemResponse):
    locations: List[StockLocationDetail] = []
