import enum
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Float, Enum, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from core.database import Base, TimestampMixin

class AccountType(str, enum.Enum):
    ASSET = "Asset"
    LIABILITY = "Liability"
    EQUITY = "Equity"
    REVENUE = "Revenue"
    EXPENSE = "Expense"

class ChartOfAccount(TimestampMixin, Base):
    __tablename__ = "accounts"
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, index=True) # e.g. 1000 for Cash
    name = Column(String(100), index=True)
    account_type = Column(Enum(AccountType))
    is_active = Column(Boolean, default=True)

class JournalEntry(TimestampMixin, Base):
    __tablename__ = "journal_entries"
    id = Column(Integer, primary_key=True, index=True)
    reference = Column(String(50), index=True) # e.g. INV-001, PAY-002
    date = Column(DateTime, default=datetime.utcnow)
    description = Column(String(255))
    # created_by and site_id come from TimestampMixin

class TransactionLine(TimestampMixin, Base):
    __tablename__ = "transaction_lines"
    id = Column(Integer, primary_key=True, index=True)
    journal_id = Column(Integer, ForeignKey("journal_entries.id"))
    account_id = Column(Integer, ForeignKey("accounts.id"))
    debit = Column(Float, default=0.0)
    credit = Column(Float, default=0.0)
    
    # Optional ledgers for Supplier / Customer tracking AP/AR directly
    partner_id = Column(Integer, nullable=True) # Could be Supplier.id or Customer.id based on context
    partner_type = Column(String(50), nullable=True) # Supplier, Customer
