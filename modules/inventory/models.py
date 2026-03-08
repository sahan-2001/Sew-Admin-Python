import enum
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Float, Enum, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from core.database import Base

class MoveType(str, enum.Enum):
    PO_RECEIPT = "Purchase Order Receipt"
    PROD_CUTTING = "Production Cutting Release"
    STOCK_MOVE = "Internal Transfer"
    PHYSICAL_ADJUST = "Physical Count Adjustment"
    SCRAP = "Scrap Sale"
    DESTROY = "Destroy/Write-off"

class Item(Base):
    __tablename__ = "items"
    id = Column(Integer, primary_key=True, index=True)
    sku = Column(String(50), unique=True, index=True)
    name = Column(String(100))
    category = Column(String(50)) # Fabric, Thread, Completed Garment
    base_uom = Column(String(20)) # meters, cones, pcs
    is_active = Column(Boolean, default=True)

class LocationType(str, enum.Enum):
    ARRIVAL = "Arrival"
    PICKING = "Picking"
    SHIPMENT = "Shipment"
    INTERNAL = "Internal"

class Location(Base):
    __tablename__ = "locations"
    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(Integer, ForeignKey("sites.id"))
    name = Column(String(100))
    loc_type = Column(Enum(LocationType), default=LocationType.INTERNAL)
    is_qc_required = Column(Boolean, default=False)

class StockMovement(Base):
    __tablename__ = "stock_movements"
    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, ForeignKey("items.id"))
    from_location_id = Column(Integer, ForeignKey("locations.id"), nullable=True) 
    to_location_id = Column(Integer, ForeignKey("locations.id"), nullable=True)   
    move_type = Column(Enum(MoveType))
    quantity = Column(Float, default=0.0) 
    timestamp = Column(DateTime, default=datetime.utcnow)
    reference = Column(String(100)) 

class LocationStock(Base):
    __tablename__ = "location_stocks"
    id = Column(Integer, primary_key=True, index=True)
    location_id = Column(Integer, ForeignKey("locations.id"))
    item_id = Column(Integer, ForeignKey("items.id"))
    stock_on_hand = Column(Float, default=0.0)
