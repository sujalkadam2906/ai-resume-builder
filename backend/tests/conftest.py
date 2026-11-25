"""Pytest configuration and test environment hardening for backend tests."""

import sqlite3
from sqlalchemy import event
from sqlalchemy.engine import Engine


@event.listens_for(Engine, "connect")
def _handle_test_sqlite_auth_schema(dbapi_connection, connection_record):
    """Ensures test-only in-memory SQLite engines support 'auth' schema references for auth.users."""
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        try:
            cursor.execute("ATTACH DATABASE ':memory:' AS auth")
        except Exception:
            pass
        finally:
            cursor.close()
