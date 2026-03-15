from sqlalchemy import create_engine, Column, Integer, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, declared_attr
from datetime import datetime
from core.config import settings

# SQLite database configuration
# Default: sew_admin.db in project root
SQLALCHEMY_DATABASE_URL = getattr(settings, "database_url", "sqlite:///./sew_admin.db")

# SQLite requires check_same_thread=False
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# Session maker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


class TimestampMixin:
    """
    Mixin that adds standard audit columns to every model:
      - site_id      : the site this record belongs to
      - created_at   : UTC timestamp when the record was created
      - created_by   : user.id who created the record
      - updated_at   : UTC timestamp of the last update
      - updated_by   : user.id who last updated the record
      - deleted_at   : UTC timestamp of soft-delete (NULL = not deleted)
      - deleted_by   : user.id who soft-deleted the record
    """

    @declared_attr
    def site_id(cls):
        return Column(Integer, ForeignKey("sites.id"), nullable=True, index=True)

    created_at  = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by  = Column(Integer, ForeignKey("users.id"), nullable=True)
    updated_at  = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=True)
    updated_by  = Column(Integer, ForeignKey("users.id"), nullable=True)
    deleted_at  = Column(DateTime, nullable=True)  # NULL = active
    deleted_by  = Column(Integer, ForeignKey("users.id"), nullable=True)


# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()