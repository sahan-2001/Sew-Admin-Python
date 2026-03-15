import enum
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Float, Enum, Text, JSON
from core.database import Base, TimestampMixin
from datetime import datetime

class SalesType(str, enum.Enum):
    BULK = "Bulk Order"
    SAMPLE = "Sample Order"
    SCRAP = "Scrap Sale"

class SalesStatus(str, enum.Enum):
    OPEN = "Open"
    PENDING_APPROVAL = "Pending Approval"
    RELEASED = "Released"
    IN_PRODUCTION = "In Production"
    READY_TO_SHIP = "Ready to Ship"
    SHIPPED = "Shipped"
    INVOICED = "Invoiced"
    CLOSED = "Closed"

class SalesOrder(TimestampMixin, Base):
    __tablename__ = "sales_orders"
    id = Column(Integer, primary_key=True, index=True)
    so_number = Column(String(50), unique=True, index=True)
    customer_id = Column(Integer)
    order_type = Column(Enum(SalesType))
    status = Column(Enum(SalesStatus), default=SalesStatus.OPEN)
    order_date = Column(DateTime, default=datetime.utcnow)
    total_amount = Column(Float, default=0.0)
    
    # Financial linkages
    delivery_term_id = Column(Integer, ForeignKey("delivery_terms.id"), nullable=True)
    payment_term_id = Column(Integer, ForeignKey("payment_terms.id"), nullable=True)

class SalesOrderLine(TimestampMixin, Base):
    __tablename__ = "sales_order_lines"
    id = Column(Integer, primary_key=True, index=True)
    so_id = Column(Integer, ForeignKey("sales_orders.id"))
    
    # Linked attributes (populated for scrap sales etc)
    item_id = Column(Integer, ForeignKey("warehouse_items.id"), nullable=True)
    location_id = Column(Integer, ForeignKey("inventory_locations.id"), nullable=True)
    
    # Manual entry requested by the user
    item_name = Column(String(255))
    item_description = Column(String(255), nullable=True)
    uom = Column(String(50), default="pcs")
    
    unit_price = Column(Float, default=0.0)
    quantity = Column(Integer, default=0)
    line_total = Column(Float, default=0.0)

class Shipment(TimestampMixin, Base):
    __tablename__ = "shipments"
    id = Column(Integer, primary_key=True, index=True)
    so_id = Column(Integer, ForeignKey("sales_orders.id"))
    ship_date = Column(DateTime, default=datetime.utcnow)
    from_location_id = Column(Integer, ForeignKey("inventory_locations.id")) # Fixed to correct warehouse location table
    is_shipped = Column(Boolean, default=False)
