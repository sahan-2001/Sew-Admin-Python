from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
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

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()