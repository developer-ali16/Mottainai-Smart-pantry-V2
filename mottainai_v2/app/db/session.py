"""
Database session management.

Key fixes from the original:
  - `Base.metadata.create_all()` is NO LONGER called on every request.
    It is called once at application startup via create_tables().
  - Connection pooling is explicitly configured.
  - ssl mode is handled via the DATABASE_URL itself (no duplicate connect_args needed).
"""
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings

# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

# Build connect_args conditionally — only add sslmode for PostgreSQL URLs
_connect_args: dict = {}
if settings.database_url.startswith("postgresql"):
    _connect_args["sslmode"] = "require"

engine = create_engine(
    settings.database_url,
    echo=settings.debug,           # log SQL only in debug mode
    pool_pre_ping=True,            # verify connections before use
    pool_size=10,                  # default connection pool size
    max_overflow=20,               # connections allowed above pool_size
    pool_recycle=1800,             # recycle connections every 30 minutes
    connect_args=_connect_args,
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,        # avoids lazy-load after commit
)


# ---------------------------------------------------------------------------
# Declarative base
# ---------------------------------------------------------------------------

class Base(DeclarativeBase):
    """
    All SQLAlchemy models inherit from this base.
    Import from here, not from db_connect.py.
    """
    pass


# ---------------------------------------------------------------------------
# FastAPI dependency
# ---------------------------------------------------------------------------

def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that provides a database session per request.
    Ensures the session is always closed, even on exceptions.

    Usage:
        db: Session = Depends(get_db)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Startup utility
# ---------------------------------------------------------------------------

def create_tables() -> None:
    """
    Create all tables that do not yet exist.
    Called ONCE at application startup — not on every request.
    
    In production, prefer Alembic migrations over this function.
    This is kept as a fallback for development / fresh installs.
    """
    Base.metadata.create_all(bind=engine)


# ---------------------------------------------------------------------------
# Health-check utility
# ---------------------------------------------------------------------------

def check_db_connection() -> bool:
    """Return True if the database is reachable."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
