import enum
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Float, Enum, Text, JSON
from core.database import Base
from datetime import datetime

class SalesType(str, enum.Enum):
    BULK = "Bulk Order"
    SAMPLE = "Sample Order"
    SCRAP = "Scrap Sale"

class SalesStatus(str, enum.Enum):
    QUOTATION = "Quotation"
    PROFORMA = "Proforma Invoice"
    SO_CONFIRMED = "SO Confirmed"
    IN_PRODUCTION = "In Production"
    READY_TO_SHIP = "Ready to Ship"
    SHIPPED = "Shipped"
    INVOICED = "Invoiced"

class SalesOrder(Base):
    __tablename__ = "sales_orders"
    id = Column(Integer, primary_key=True, index=True)
    so_number = Column(String(50), unique=True, index=True)
    customer_id = Column(Integer)
    order_type = Column(Enum(SalesType))
    status = Column(Enum(SalesStatus), default=SalesStatus.QUOTATION)
    order_date = Column(DateTime, default=datetime.utcnow)
    total_amount = Column(Float, default=0.0)
    
    # Financial linkages
    delivery_term_id = Column(Integer, ForeignKey("delivery_terms.id"), nullable=True)
    payment_term_id = Column(Integer, ForeignKey("payment_terms.id"), nullable=True)

class SalesOrderLine(Base):
    __tablename__ = "sales_order_lines"
    id = Column(Integer, primary_key=True, index=True)
    so_id = Column(Integer, ForeignKey("sales_orders.id"))
    
    # For Apparel, items change per order so we do not link strictly to Inventory "Items"
    # User requested separate JSON maps for varied specs instead of hard DB link.
    item_description = Column(String(255))
    size_specs = Column(JSON) # e.g. {"S": 100, "M": 200, "L": 150}
    color = Column(String(50))
    material_specs = Column(Text)
    design_notes = Column(Text)
    
    unit_price = Column(Float, default=0.0)
    quantity = Column(Integer, default=0)

class Shipment(Base):
    __tablename__ = "shipments"
    id = Column(Integer, primary_key=True, index=True)
    so_id = Column(Integer, ForeignKey("sales_orders.id"))
    ship_date = Column(DateTime, default=datetime.utcnow)
    from_location_id = Column(Integer, ForeignKey("locations.id")) # Should be a 'SHIPMENT' type location
    is_shipped = Column(Boolean, default=False)
