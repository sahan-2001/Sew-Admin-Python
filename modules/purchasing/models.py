import enum
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Float, Enum, Text
from core.database import Base
from datetime import datetime

class PurchaseStatus(str, enum.Enum):
    DRAFT = "Draft"
    PR_ISSUED = "PR Issued"
    RFQ_SENT = "RFQ Sent"
    PO_GENERATED = "PO Generated"
    PARTIAL_GRN = "Partial GRN"
    FULL_GRN = "Full GRN"
    INVOICED = "Invoiced"
    PAID = "Paid"

class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"
    id = Column(Integer, primary_key=True, index=True)
    po_number = Column(String(50), unique=True, index=True)
    supplier_id = Column(Integer) # ForeignKey to suppliers if exists
    order_date = Column(DateTime, default=datetime.utcnow)
    status = Column(Enum(PurchaseStatus), default=PurchaseStatus.DRAFT)
    # Requisition links
    mrn_ref = Column(String(50), nullable=True) # Material Requisition Note
    prn_ref = Column(String(50), nullable=True) # Purchase Requisition Note
    rfq_ref = Column(String(50), nullable=True) # Request for Quotation
    
    total_amount = Column(Float, default=0.0)
    payment_term_id = Column(Integer, ForeignKey("payment_terms.id"), nullable=True)
    
class GRN(Base):
    __tablename__ = "grns" # Goods Receipt Note
    id = Column(Integer, primary_key=True, index=True)
    grn_number = Column(String(50), unique=True)
    po_id = Column(Integer, ForeignKey("purchase_orders.id"))
    receive_date = Column(DateTime, default=datetime.utcnow)
    destination_location_id = Column(Integer, ForeignKey("locations.id")) # Arrival (for QC) or Picking (direct)
    is_qc_passed = Column(Boolean, default=False)
