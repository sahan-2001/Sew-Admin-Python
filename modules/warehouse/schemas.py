from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime
from modules.warehouse.models import LocationType, JournalType

class WarehouseBase(BaseModel):
    name: str = Field(..., max_length=100)
    description: Optional[str] = None
    location: Optional[str] = None

class WarehouseCreate(WarehouseBase):
    pass

class WarehouseResponse(WarehouseBase):
    id: int
    class Config:
        from_attributes = True

class InventoryLocationBase(BaseModel):
    warehouse_id: int
    name: str = Field(..., max_length=100)
    location_type: LocationType
    description: Optional[str] = None

class InventoryLocationCreate(InventoryLocationBase):
    pass

class InventoryLocationResponse(InventoryLocationBase):
    id: int
    class Config:
        from_attributes = True

class ItemBase(BaseModel):
    sku: str = Field(..., max_length=50)
    name: str = Field(..., max_length=100)
    category: Optional[str] = None
    base_uom: str = Field(..., max_length=20)

class ItemCreate(ItemBase):
    pass

class ItemResponse(ItemBase):
    id: int
    qty_on_hand: float
    class Config:
        from_attributes = True

class StockMovementRequest(BaseModel):
    item_id: int
    location_id: int
    qty: float = Field(..., gt=0)
    reference: Optional[str] = None

class StockTransferRequest(BaseModel):
    item_id: int
    from_location_id: int
    to_location_id: int
    qty: float = Field(..., gt=0)
    reference: Optional[str] = None

class PickItemRequest(StockMovementRequest):
    allow_partial: bool = False

class PhysicalCountRequest(BaseModel):
    item_id: int
    location_id: int
    counted_qty: float = Field(..., ge=0)
    reference: Optional[str] = None

class ItemJournalResponse(BaseModel):
    id: int
    item_id: int
    location_id: int
    journal_type: JournalType
    qty: float
    reference: Optional[str]
    created_at: datetime
    class Config:
        from_attributes = True

class PhysicalInventoryResponse(BaseModel):
    id: int
    item_id: int
    location_id: int
    counted_qty: float
    system_qty: float
    adjustment_qty: float
    reference: Optional[str]
    created_at: datetime
    class Config:
        from_attributes = True
