"""SQLAlchemy declarative base and common database mixins."""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List
from sqlalchemy import Column, DateTime, func, JSON, Table, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# Compatible JSON column: uses PostgreSQL JSONB in production, standard JSON in SQLite/testing
JSONVariant = JSON().with_variant(JSONB(), "postgresql")


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy 2.0 ORM models."""
    pass


# Supabase Auth users table stub in 'auth' schema for SQLAlchemy foreign-key resolution
auth_users = Table(
    "users",
    Base.metadata,
    Column("id", Uuid, primary_key=True),
    schema="auth",
)


class TimestampMixin:
    """Mixin adding created_at and updated_at timezone-aware audit timestamps."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
