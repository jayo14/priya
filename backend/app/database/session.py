"""Database engine, session factory, and lifecycle management."""

import time
from typing import Generator, Optional, Tuple

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from app.core.config import settings

# Engine configuration for PostgreSQL with psycopg
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    pool_recycle=3600,
    echo=settings.DEBUG and settings.APP_ENV == "development",
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False,
)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """Provide a transactional database session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_database_connection(timeout_seconds: float = 3.0) -> Tuple[bool, Optional[float], Optional[str]]:
    """
    Safely ping the database without leaking credentials or raw stack traces.
    Returns: (is_connected, latency_ms, status_message)
    """
    start_time = time.perf_counter()
    try:
        with engine.connect() as conn:
            conn.execution_options(timeout=timeout_seconds)
            conn.execute(text("SELECT 1"))
        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
        return True, latency_ms, "Database connected successfully"
    except SQLAlchemyError:
        # Do not expose internal credentials or query parameters
        return False, None, "Database connectivity check failed"
    except Exception:
        return False, None, "Database is unreachable"
