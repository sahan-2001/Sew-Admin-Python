from sqlalchemy.orm import Session
from fastapi import HTTPException
from modules.warehouse.models import (
    Warehouse, InventoryLocation, WarehouseItem, 
    WarehouseItemJournal, PhysicalInventory, LocationType, JournalType
)
from sqlalchemy import func

class WarehouseOperationsService:
    def __init__(self, db: Session):
        self.db = db

    # -----------------------
    # Warehouse & Location Management
    # -----------------------
    def create_warehouse(self, name: str, description: str = None, location: str = None) -> Warehouse:
        wh = Warehouse(name=name, description=description, location=location)
        self.db.add(wh)
        self.db.commit()
        self.db.refresh(wh)
        return wh

    def create_location(self, warehouse_id: int, name: str, location_type: LocationType, description: str = None) -> InventoryLocation:
        wh = self.db.query(Warehouse).filter(Warehouse.id == warehouse_id).first()
        if not wh:
            raise HTTPException(status_code=404, detail="Warehouse not found")
        loc = InventoryLocation(warehouse_id=warehouse_id, name=name, location_type=location_type, description=description)
        self.db.add(loc)
        self.db.commit()
        self.db.refresh(loc)
        return loc

    def create_item(self, sku: str, name: str, category: str, base_uom: str) -> WarehouseItem:
        item = WarehouseItem(sku=sku, name=name, category=category, base_uom=base_uom)
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    # -----------------------
    # Stock Queries
    # -----------------------
    def get_location_stock(self, item_id: int, location_id: int) -> float:
        """Calculate system stock at a specific location by summing journals"""
        loc_stock = self.db.query(
            func.sum(
                func.if_(WarehouseItemJournal.journal_type == JournalType.DECREMENT, -WarehouseItemJournal.qty, WarehouseItemJournal.qty)
            )
        ).filter(
            WarehouseItemJournal.item_id == item_id,
            WarehouseItemJournal.location_id == location_id
        ).scalar()
        
        return loc_stock if loc_stock else 0.0
        
    def get_total_stock(self, item_id: int, warehouse_id: int = None) -> float:
        query = self.db.query(
            func.sum(
                func.if_(WarehouseItemJournal.journal_type == JournalType.DECREMENT, -WarehouseItemJournal.qty, WarehouseItemJournal.qty)
            )
        ).filter(WarehouseItemJournal.item_id == item_id)
        
        if warehouse_id:
            query = query.join(InventoryLocation).filter(InventoryLocation.warehouse_id == warehouse_id)
            
        total = query.scalar()
        return total if total else 0.0

    # -----------------------
    # Stock Operations (Arrival, Shipment, Adjustments)
    # -----------------------
    def add_stock(self, item_id: int, location_id: int, qty: float, reference: str = None) -> WarehouseItemJournal:
        if qty <= 0:
            raise ValueError("Qty must be greater than 0")
        
        item = self.db.query(WarehouseItem).filter(WarehouseItem.id == item_id).with_for_update().first()
        if not item:
            raise HTTPException(status_code=404, detail="WarehouseItem not found")
            
        loc = self.db.query(InventoryLocation).filter(InventoryLocation.id == location_id).first()
        if not loc:
            raise HTTPException(status_code=404, detail="Location not found")
        
        journal = WarehouseItemJournal(
            item_id=item_id,
            location_id=location_id,
            journal_type=JournalType.INCREMENT,
            qty=qty,
            reference=reference
        )
        self.db.add(journal)
        
        item.qty_on_hand += qty
        
        self.db.commit()
        self.db.refresh(journal)
        return journal

    def remove_stock(self, item_id: int, location_id: int, qty: float, reference: str = None) -> WarehouseItemJournal:
        if qty <= 0:
            raise ValueError("Qty must be greater than 0")
            
        item = self.db.query(WarehouseItem).filter(WarehouseItem.id == item_id).with_for_update().first()
        if not item:
            raise HTTPException(status_code=404, detail="WarehouseItem not found")

        loc_stock = self.get_location_stock(item_id, location_id)
        if loc_stock < qty:
            raise ValueError(f"Insufficient stock at location. Available: {loc_stock}, Required: {qty}")
            
        journal = WarehouseItemJournal(
            item_id=item_id,
            location_id=location_id,
            journal_type=JournalType.DECREMENT,
            qty=qty,
            reference=reference
        )
        self.db.add(journal)
        
        item.qty_on_hand -= qty
        
        self.db.commit()
        self.db.refresh(journal)
        return journal

    def transfer_stock(self, item_id: int, from_location_id: int, to_location_id: int, qty: float, reference: str = None):
        """Move stock directly between two locations using isolated decrement/increment journals without altering global item qty."""
        if qty <= 0:
            raise ValueError("Transfer Qty must be greater than 0")
            
        # Secure locks
        item = self.db.query(WarehouseItem).filter(WarehouseItem.id == item_id).with_for_update().first()
        if not item:
            raise HTTPException(status_code=404, detail="WarehouseItem not found")

        from_loc_stock = self.get_location_stock(item_id, from_location_id)
        if from_loc_stock < qty:
            raise ValueError(f"Insufficient stock at origin location. Available: {from_loc_stock}, Required: {qty}")

        # Decrement Journal
        out_journal = WarehouseItemJournal(
            item_id=item_id,
            location_id=from_location_id,
            journal_type=JournalType.DECREMENT,
            qty=qty,
            reference=reference or "Internal Transfer Out"
        )
        self.db.add(out_journal)

        # Increment Journal
        in_journal = WarehouseItemJournal(
            item_id=item_id,
            location_id=to_location_id,
            journal_type=JournalType.INCREMENT,
            qty=qty,
            reference=reference or "Internal Transfer In"
        )
        self.db.add(in_journal)

        self.db.commit()
        return out_journal, in_journal

    def pick_items(self, item_id: int, location_id: int, qty: float, reference: str = None, allow_partial: bool = False) -> WarehouseItemJournal:
        loc = self.db.query(InventoryLocation).filter(InventoryLocation.id == location_id).first()
        if not loc:
            raise HTTPException(status_code=404, detail="Location not found")
        if loc.location_type != LocationType.PICKING:
            raise ValueError("Location must be of type 'PICKING'")
            
        item = self.db.query(WarehouseItem).filter(WarehouseItem.id == item_id).with_for_update().first()
        if not item:
            raise HTTPException(status_code=404, detail="WarehouseItem not found")

        loc_stock = self.get_location_stock(item_id, location_id)
        
        actual_qty = qty
        if loc_stock < qty:
            if not allow_partial:
                raise ValueError(f"Insufficient stock. Available: {loc_stock}, Requested: {qty}")
            actual_qty = loc_stock
            
        if actual_qty <= 0:
            raise ValueError("No stock available to pick")

        journal = WarehouseItemJournal(
            item_id=item_id,
            location_id=location_id,
            journal_type=JournalType.DECREMENT,
            qty=actual_qty,
            reference=reference
        )
        self.db.add(journal)
        
        item.qty_on_hand -= actual_qty
        
        self.db.commit()
        self.db.refresh(journal)
        return journal

    def record_physical_count(self, item_id: int, location_id: int, counted_qty: float, reference: str = None) -> PhysicalInventory:
        if counted_qty < 0:
            raise ValueError("Counted qty cannot be negative")
            
        item = self.db.query(WarehouseItem).filter(WarehouseItem.id == item_id).with_for_update().first()
        if not item:
            raise HTTPException(status_code=404, detail="WarehouseItem not found")

        system_qty = self.get_location_stock(item_id, location_id)
        adjustment_qty = counted_qty - system_qty

        pi = PhysicalInventory(
            item_id=item_id,
            location_id=location_id,
            counted_qty=counted_qty,
            system_qty=system_qty,
            adjustment_qty=adjustment_qty,
            reference=reference
        )
        self.db.add(pi)

        if adjustment_qty != 0:
            journal_type = JournalType.ADJUSTMENT
            # If adjustment is negative, we could use decrement, but keeping it adjustment and handling logic gracefully.
            journal = WarehouseItemJournal(
                item_id=item_id,
                location_id=location_id,
                journal_type=journal_type,
                qty=adjustment_qty,  # Note: adjustment_qty can be negative
                reference=f"Physical Count {pi.id}" if not reference else reference
            )
            self.db.add(journal)
            item.qty_on_hand += adjustment_qty

        self.db.commit()
        self.db.refresh(pi)
        return pi
