from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List, Optional

from modules.inventory.models import (
    Item, Location, LocationStock, ItemJournal, PhysicalInventory, 
    JournalType, LocationType
)
from modules.users.models import Site

class WarehouseOperationsService:
    def __init__(self, db: Session):
        self.db = db

    # ---------------------------------------------------------
    # 1 & 2. CORE STOCK MOVEMENTS (ADD / REMOVE)
    # ---------------------------------------------------------

    def add_stock(self, item_id: int, location_id: int, quantity: float, reference: str) -> ItemJournal:
        """Add stock (Arrival/Increment) to a location."""
        if quantity <= 0:
            raise ValueError("Addition quantity must be greater than zero.")
        
        return self._process_movement(
            item_id=item_id,
            location_id=location_id,
            quantity=quantity,
            journal_type=JournalType.INCREMENT,
            reference=reference
        )

    def remove_stock(self, item_id: int, location_id: int, quantity: float, reference: str) -> ItemJournal:
        """Remove stock (Shipment/Decrement) from a location."""
        if quantity <= 0:
            raise ValueError("Removal quantity must be greater than zero.")
        
        return self._process_movement(
            item_id=item_id,
            location_id=location_id,
            quantity=-quantity, # Negative for removal
            journal_type=JournalType.DECREMENT,
            reference=reference
        )

    # ---------------------------------------------------------
    # 3. PICKING ITEMS
    # ---------------------------------------------------------

    def pick_items(self, item_id: int, location_id: int, quantity: float, reference: str, allow_partial: bool = False) -> (ItemJournal, float):
        """Pick items specifically from a PICKING location."""
        location = self.db.query(Location).filter(Location.id == location_id).first()
        if not location:
            raise HTTPException(status_code=404, detail="Location not found")
            
        if location.loc_type != LocationType.PICKING:
            raise ValueError("Items can only be picked from a PICKING location.")
            
        stock_record = self._get_location_stock(item_id, location_id)
        current_stock = stock_record.stock_on_hand if stock_record else 0.0
        
        actual_pick_qty = quantity
        
        if current_stock < quantity:
            if allow_partial:
                actual_pick_qty = current_stock
            else:
                raise ValueError(f"Insufficient stock to pick. Requested {quantity}, Available: {current_stock}")
                
        if actual_pick_qty <= 0:
             raise ValueError("Nothing available to pick.")
             
        journal = self._process_movement(
            item_id=item_id,
            location_id=location_id,
            quantity=-actual_pick_qty,
            journal_type=JournalType.DECREMENT,
            reference=reference
        )
        return journal, actual_pick_qty

    # ---------------------------------------------------------
    # 4. PHYSICAL INVENTORY / ADJUSTMENTS
    # ---------------------------------------------------------

    def record_physical_count(self, item_id: int, location_id: int, counted_qty: float, reference: str) -> PhysicalInventory:
        """Record a physical count, calculate adjustments, and apply them."""
        if counted_qty < 0:
            raise ValueError("Counted quantity cannot be negative.")
            
        stock_record = self._get_location_stock(item_id, location_id)
        if not stock_record:
            # If no stock record exists, but we count some, assume system qty = 0
            stock_record = LocationStock(item_id=item_id, location_id=location_id, stock_on_hand=0.0)
            self.db.add(stock_record)
            
        system_qty = stock_record.stock_on_hand
        adjustment_qty = counted_qty - system_qty
        
        # Create physical inventory record
        pi_record = PhysicalInventory(
            location_id=location_id,
            item_id=item_id,
            counted_qty=counted_qty,
            system_qty=system_qty,
            adjustment_qty=adjustment_qty,
            reference=reference
        )
        self.db.add(pi_record)
        
        # If there's a difference, process a journal entry
        if adjustment_qty != 0:
            self._process_movement(
                item_id=item_id,
                location_id=location_id,
                quantity=adjustment_qty,
                journal_type=JournalType.ADJUSTMENT,
                reference=f"PI-ADJ: {reference}"
            )
            
        self.db.commit()
        self.db.refresh(pi_record)
        return pi_record

    # ---------------------------------------------------------
    # 5. INVENTORY LOCATION MANAGEMENT
    # ---------------------------------------------------------

    def create_location(self, site_id: int, name: str, loc_type: LocationType, is_qc_required: bool = False) -> Location:
        site = self.db.query(Site).filter(Site.id == site_id).first()
        if not site:
            raise HTTPException(status_code=404, detail="Site/Warehouse not found")
            
        location = Location(site_id=site_id, name=name, loc_type=loc_type, is_qc_required=is_qc_required)
        self.db.add(location)
        self.db.commit()
        self.db.refresh(location)
        return location

    # ---------------------------------------------------------
    # 6. WAREHOUSE MANAGEMENT (SITES)
    # ---------------------------------------------------------

    def create_warehouse(self, name: str) -> Site:
        site = Site(name=name)
        self.db.add(site)
        self.db.commit()
        self.db.refresh(site)
        return site

    # ---------------------------------------------------------
    # 7. STOCK QUERIES
    # ---------------------------------------------------------
    
    def get_current_stock(self, item_id: int, location_id: Optional[int] = None, site_id: Optional[int] = None):
        """Query flexible stock balances."""
        query = self.db.query(LocationStock).filter(LocationStock.item_id == item_id)
        
        if location_id:
            query = query.filter(LocationStock.location_id == location_id)
            
        if site_id:
            query = query.join(Location).filter(Location.site_id == site_id)
            
        records = query.all()
        return sum([r.stock_on_hand for r in records])

    # ---------------------------------------------------------
    # INTERNAL HELPERS (VALIDATION & JOURNALS)
    # ---------------------------------------------------------

    def _get_location_stock(self, item_id: int, location_id: int) -> Optional[LocationStock]:
        return self.db.query(LocationStock).filter(
            LocationStock.item_id == item_id, 
            LocationStock.location_id == location_id
        ).first()

    def _process_movement(self, item_id: int, location_id: int, quantity: float, journal_type: JournalType, reference: str) -> ItemJournal:
        """Core transactional method for all warehouse movements."""
        try:
            item = self.db.query(Item).filter(Item.id == item_id).with_for_update().first()
            if not item:
                raise HTTPException(status_code=404, detail="Item not found")

            # Get or create LocationStock
            stock_record = self._get_location_stock(item_id, location_id)
            if not stock_record:
                stock_record = LocationStock(item_id=item_id, location_id=location_id, stock_on_hand=0.0)
                self.db.add(stock_record)
                self.db.flush() # Secure an ID
                
            # Validation: Prevent negative stock
            new_stock_value = stock_record.stock_on_hand + quantity
            if new_stock_value < 0:
                raise ValueError(f"Transaction denied. Insufficient stock. Attempted to drop on-hand stock below zero (Result: {new_stock_value})")

            # Create Journal
            journal = ItemJournal(
                item_id=item_id,
                location_id=location_id,
                journal_type=journal_type,
                quantity=quantity,
                reference=reference
            )
            self.db.add(journal)

            # Update Balances
            stock_record.stock_on_hand = new_stock_value
            item.qty_on_hand = (item.qty_on_hand or 0.0) + quantity

            self.db.commit()
            self.db.refresh(journal)
            return journal

        except Exception as e:
            self.db.rollback()
            raise e
