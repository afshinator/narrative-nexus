"""Pytest fixtures for Narrative Nexus backend tests."""

import pytest
import sqlite3
from db.connection import get_db


@pytest.fixture
def db():
    """Provide an in-memory SQLite database with schema loaded.

    Each test gets a fresh database.
    """
    conn = get_db()
    from db.connection import load_schema
    load_schema(conn)
    yield conn
    conn.close()
