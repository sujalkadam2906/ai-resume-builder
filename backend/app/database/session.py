"""PostgreSQL database engine, session factory, and FastAPI dependency."""

import logging
from typing import Generator, Tuple
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from backend.app.config import settings

logger = logging.getLogger(__name__)


def get_normalized_database_url(url: str) -> str:
    """Normalize connection string for SQLAlchemy with psycopg3.
    
    Converts legacy postgres:// or standard postgresql:// to postgresql+psycopg://
    unless another driver or dialect is already explicitly configured.
    """
    if not url:
        return "postgresql+psycopg://postgres:postgres@localhost:5432/resume_builder"
    
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg://", 1)
    elif url.startswith("postgresql://") and not url.startswith("postgresql+"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    
    return url


def create_db_engine(db_url: str):
    """Instantiate a resilient SQLAlchemy 2.0 engine."""
    normalized_url = get_normalized_database_url(db_url)
    
    if normalized_url.startswith("sqlite"):
        return create_engine(
            normalized_url,
            connect_args={"check_same_thread": False},
        )
    
    return create_engine(
        normalized_url,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        pool_recycle=300,
    )


# Primary application engine and sessionmaker
engine = create_db_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency for yielding transactional database sessions.
    
    Ensures safe lifecycle management: session rolls back on unhandled error and is always closed.
    """
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def check_db_connection(target_engine=None) -> Tuple[bool, str]:
    """Verify live database connectivity by executing a lightweight query.
    
    Returns:
        Tuple of (is_healthy: bool, status_message: str)
    """
    eng = target_engine or engine
    try:
        with eng.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True, "Database connection healthy"
    except Exception as exc:
        logger.warning("Database connectivity check failed: %s", exc)
        return False, str(exc)
