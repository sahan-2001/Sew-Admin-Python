from pydantic import BaseModel, Field
from typing import Optional
from .models import LocationType, JournalType

class StockMovementRequest(BaseModel):
    item_id: int
    location_id: int
    quantity: float = Field(..., gt=0.0)
    reference: str = Field(..., max_length=100)

class PickItemsRequest(BaseModel):
    item_id: int
    location_id: int
    quantity: float = Field(..., gt=0.0)
    reference: str = Field(..., max_length=100)
    allow_partial: bool = False

class PhysicalCountRequest(BaseModel):
    item_id: int
    location_id: int
    counted_qty: float = Field(..., ge=0.0)
    reference: str = Field(..., max_length=100)

class LocationCreateRequest(BaseModel):
    site_id: int
    name: str = Field(..., max_length=100)
    loc_type: LocationType
    is_qc_required: bool = False

class WarehouseCreateRequest(BaseModel):
    name: str = Field(..., max_length=100)

class StockJournalResponse(BaseModel):
    id: int
    item_id: int
    location_id: int
    journal_type: JournalType
    quantity: float
    reference: str

    class Config:
        orm_mode = True

class PhysicalInventoryResponse(StockMovementRequest):
    id: int
    counted_qty: float
    system_qty: float
    adjustment_qty: float

    class Config:
        orm_mode = True
