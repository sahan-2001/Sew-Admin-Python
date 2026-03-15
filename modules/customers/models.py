import enum
from sqlalchemy import Column, Integer, String, Float, ForeignKey, Enum, Boolean
from sqlalchemy.orm import relationship
from core.database import Base, TimestampMixin

class DiscountType(str, enum.Enum):
    FIXED = "Fixed"
    PERCENTAGE = "Percentage"

class Customer(TimestampMixin, Base):
    __tablename__ = "customers"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    address = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True)

    prices = relationship("CustomerItemPrice", back_populates="customer")
    discounts = relationship("CustomerItemDiscount", back_populates="customer")

class CustomerItemPrice(TimestampMixin, Base):
    __tablename__ = "customer_item_prices"
    
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False, index=True)
    item_id = Column(Integer, ForeignKey("warehouse_items.id"), nullable=False, index=True) # Assuming warehouse_items contains master items
    min_qty = Column(Float, default=1.0)
    price = Column(Float, nullable=False)

    customer = relationship("Customer", back_populates="prices")

class CustomerItemDiscount(TimestampMixin, Base):
    __tablename__ = "customer_item_discounts"
    
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False, index=True)
    item_id = Column(Integer, ForeignKey("warehouse_items.id"), nullable=False, index=True)
    min_qty = Column(Float, default=1.0)
    discount_type = Column(Enum(DiscountType), default=DiscountType.PERCENTAGE)
    discount_value = Column(Float, nullable=False) # The actual discount value (e.g. 10% or $10)
    min_discount = Column(Float, nullable=True)    # Optional min limit (usually for percentage)
    max_discount = Column(Float, nullable=True)    # Optional max limit

    customer = relationship("Customer", back_populates="discounts")
