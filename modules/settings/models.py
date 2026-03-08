from sqlalchemy import Column, Integer, String, Float, Boolean
from core.database import Base

class Currency(Base):
    __tablename__ = "currencies"
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(10), unique=True, index=True) # e.g. USD, LKR, EUR
    name = Column(String(50))
    symbol = Column(String(10))
    is_global_default = Column(Boolean, default=False)

class Country(Base):
    __tablename__ = "countries"
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(10), unique=True)
    name = Column(String(100))

class VatGroup(Base):
    __tablename__ = "vat_groups"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50)) # e.g. Standard, Exempt, Reduced
    percentage = Column(Float, default=0.0)
    group_type = Column(String(20)) # "Item", "Customer", "Supplier"

class DeliveryTerm(Base):
    __tablename__ = "delivery_terms"
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(20)) # e.g. FOB, CIF, EXW
    description = Column(String(255))

class PaymentTerm(Base):
    __tablename__ = "payment_terms"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50)) # e.g. Net 30, COD
    days = Column(Integer, default=0)

class PaymentMethod(Base):
    __tablename__ = "payment_methods"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50)) # e.g. Bank Transfer, Cash, Card
