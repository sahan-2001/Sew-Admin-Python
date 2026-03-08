from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Float, Enum, Text
from core.database import Base
from datetime import datetime

class Workcenter(Base):
    __tablename__ = "workcenters"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100)) # e.g. Cutting Section, Sewing Line 1
    site_id = Column(Integer, ForeignKey("sites.id"))
    cost_per_hour = Column(Float, default=0.0)
    is_active = Column(Boolean, default=True)

class ProductionOrder(Base):
    __tablename__ = "production_orders"
    id = Column(Integer, primary_key=True, index=True)
    po_ref = Column(String(50), unique=True, index=True)
    so_id = Column(Integer, ForeignKey("sales_orders.id")) # Link to bulk or sample order
    
    # Material linkages: users must 'Release Material'
    is_material_released = Column(Boolean, default=False)
    
    status = Column(String(50), default="Planned") # Planned, Released, Cutting, Sewing, QC, Completed
    start_date = Column(DateTime)
    end_date = Column(DateTime, nullable=True)

class Timesheet(Base):
    __tablename__ = "timesheets"
    id = Column(Integer, primary_key=True, index=True)
    production_order_id = Column(Integer, ForeignKey("production_orders.id"))
    workcenter_id = Column(Integer, ForeignKey("workcenters.id"))
    employee_id = Column(Integer, ForeignKey("users.id"))
    
    operation_desc = Column(String(255))
    hours_worked = Column(Float)
    pieces_completed = Column(Integer)
    date = Column(DateTime, default=datetime.utcnow)
