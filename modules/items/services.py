from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException
from modules.warehouse.models import WarehouseItem as Item, ItemType, WarehouseItemJournal as ItemJournal, JournalType, InventoryLocation, Warehouse
from modules.items.schemas import ItemCreate, ItemUpdate, ItemStockResponse, StockLocationDetail

class ItemService:
    def __init__(self, db: Session):
        self.db = db

    def create_item(self, data: ItemCreate) -> Item:
        existing = self.db.query(Item).filter(Item.sku == data.sku).first()
        if existing:
            raise HTTPException(status_code=400, detail="Item with this SKU already exists")

        item = Item(
            sku=data.sku,
            name=data.name,
            category=data.category,
            sub_category=data.sub_category,
            base_uom=data.base_uom,
            item_type=data.item_type,
            description=data.description,
            is_active=True,
            qty_on_hand=0.0
        )
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def get_items(self, category: str = None, item_type: ItemType = None, is_active: bool = None) -> list[Item]:
        query = self.db.query(Item)
        if category:
            query = query.filter(Item.category == category)
        if item_type:
            query = query.filter(Item.item_type == item_type)
        if is_active is not None:
            query = query.filter(Item.is_active == is_active)
        return query.all()

    def get_item_with_stock(self, item_id: int, warehouse_id: int = None) -> ItemStockResponse:
        item = self.db.query(Item).filter(Item.id == item_id).first()
        if not item:
            raise HTTPException(status_code=404, detail="Item not found")

        # Fetch locations stock if inventory item
        locations_detail = []
        if item.item_type == ItemType.INVENTORY:
            # Query sum of journals grouped by location mapping to warehouse
            loc_query = self.db.query(
                InventoryLocation.id,
                InventoryLocation.name,
                InventoryLocation.location_type,
                Warehouse.name.label("warehouse_name"),
                func.sum(func.if_(ItemJournal.journal_type == JournalType.DECREMENT, -ItemJournal.qty, ItemJournal.qty)).label("qty")
            ).join(Warehouse, Warehouse.id == InventoryLocation.warehouse_id)\
             .join(ItemJournal, ItemJournal.location_id == InventoryLocation.id)\
             .filter(ItemJournal.item_id == item_id)

            if warehouse_id:
                loc_query = loc_query.filter(Warehouse.id == warehouse_id)

            loc_query = loc_query.group_by(InventoryLocation.id, InventoryLocation.name, InventoryLocation.location_type, Warehouse.name)

            for row in loc_query.all():
                if row.qty > 0:
                    locations_detail.append(StockLocationDetail(
                        location_id=row.id,
                        location_name=row.name,
                        location_type=row.location_type.value,
                        warehouse_name=row.warehouse_name,
                        qty=float(row.qty)
                    ))

        return ItemStockResponse(
            id=item.id,
            sku=item.sku,
            name=item.name,
            category=item.category,
            sub_category=item.sub_category,
            base_uom=item.base_uom,
            item_type=item.item_type,
            description=item.description,
            is_active=item.is_active,
            qty_on_hand=item.qty_on_hand,
            locations=locations_detail
        )

    def update_item(self, item_id: int, data: ItemUpdate) -> Item:
        item = self.db.query(Item).filter(Item.id == item_id).first()
        if not item:
            raise HTTPException(status_code=404, detail="Item not found")

        for var, value in vars(data).items():
            if value is not None:
                setattr(item, var, value)

        self.db.commit()
        self.db.refresh(item)
        return item

    def delete_item(self, item_id: int, hard_delete: bool = False):
        item = self.db.query(Item).filter(Item.id == item_id).first()
        if not item:
            raise HTTPException(status_code=404, detail="Item not found")

        if item.item_type == ItemType.INVENTORY and item.qty_on_hand > 0:
            raise HTTPException(status_code=400, detail="Cannot delete inventory item with positive stock")
            
        if hard_delete:
            self.db.delete(item)
        else:
            item.is_active = False
        self.db.commit()
        return {"status": "success", "message": "Item deleted" if hard_delete else "Item deactivated"}
