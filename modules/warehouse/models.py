from sqlalchemy import Column, Integer, String, ForeignKey, Float, Enum, DateTime, func
from sqlalchemy.orm import relationship
from core.database import Base
import enum

# -----------------------
# Inventory Location Types
# -----------------------
class LocationType(str, enum.Enum):
    ARRIVAL = "arrival"
    PICKING = "picking"
    SHIPMENT = "shipment"

# -----------------------
# Warehouse
# -----------------------
class Warehouse(Base):
    __tablename__ = "warehouses"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(String(255), nullable=True)
    location = Column(String(255), nullable=True)

    # Relationships
    inventory_locations = relationship("InventoryLocation", back_populates="warehouse")

    def __repr__(self):
        return f"<Warehouse {self.name}>"

# -----------------------
# Inventory Location
# -----------------------
class InventoryLocation(Base):
    __tablename__ = "inventory_locations"

    id = Column(Integer, primary_key=True)
    warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=False)
    name = Column(String(100), nullable=False)
    location_type = Column(Enum(LocationType), nullable=False)
    description = Column(String(255), nullable=True)

    # Relationships
    warehouse = relationship("Warehouse", back_populates="inventory_locations")
    item_journals = relationship("WarehouseItemJournal", back_populates="location")

    def __repr__(self):
        return f"<InventoryLocation {self.name} ({self.location_type})>"

from sqlalchemy import Column, Integer, String, ForeignKey, Float, Enum, DateTime, Boolean, func

class ItemType(str, enum.Enum):
    INVENTORY = "inventory"
    NON_INVENTORY = "non_inventory"

# -----------------------
# Item
# -----------------------
class WarehouseItem(Base):
    """
    Independent item model specifically for the warehouse module.
    Could be linked to global items if needed.
    """
    __tablename__ = "warehouse_items"

    id = Column(Integer, primary_key=True)
    sku = Column(String(50), nullable=False, unique=True)
    name = Column(String(100), nullable=False)
    category = Column(String(50), nullable=True)
    sub_category = Column(String(50), nullable=True)
    base_uom = Column(String(20), nullable=False)
    item_type = Column(Enum(ItemType), default=ItemType.INVENTORY, nullable=False)
    description = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    qty_on_hand = Column(Float, default=0.0)

    # Relationships
    item_journals = relationship("WarehouseItemJournal", back_populates="item")

    def __repr__(self):
        return f"<Item {self.sku} - {self.name}>"

# -----------------------
# Item Journal (Stock Movements)
# -----------------------
class JournalType(str, enum.Enum):
    INCREMENT = "increment"
    DECREMENT = "decrement"
    ADJUSTMENT = "adjustment"

class WarehouseItemJournal(Base):
    __tablename__ = "item_journals"

    id = Column(Integer, primary_key=True)
    item_id = Column(Integer, ForeignKey("warehouse_items.id"), nullable=False)
    location_id = Column(Integer, ForeignKey("inventory_locations.id"), nullable=False)
    journal_type = Column(Enum(JournalType), nullable=False)
    qty = Column(Float, nullable=False)
    reference = Column(String(100), nullable=True)  # e.g., PO number, shipment
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    item = relationship("WarehouseItem", back_populates="item_journals")
    location = relationship("InventoryLocation", back_populates="item_journals")

    def __repr__(self):
        return f"<WarehouseItemJournal {self.item.sku} {self.journal_type} {self.qty}>"

# -----------------------
# Physical Inventory Adjustment
# -----------------------
class PhysicalInventory(Base):
    __tablename__ = "physical_inventory"

    id = Column(Integer, primary_key=True)
    item_id = Column(Integer, ForeignKey("warehouse_items.id"), nullable=False)
    location_id = Column(Integer, ForeignKey("inventory_locations.id"), nullable=False)
    counted_qty = Column(Float, nullable=False)
    system_qty = Column(Float, nullable=False)
    adjustment_qty = Column(Float, nullable=False)  # counted - system
    created_at = Column(DateTime, server_default=func.now())
    reference = Column(String(100), nullable=True)  # e.g., inventory cycle count

    # Relationships
    item = relationship("WarehouseItem")
    location = relationship("InventoryLocation")

    def __repr__(self):
        return f"<PhysicalInventory {self.item.sku} adjusted {self.adjustment_qty}>"
