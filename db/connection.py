"""SQLite connection management and schema loading."""

import sqlite3
from pathlib import Path

SCHEMA_PATH = Path(__file__).resolve().parent.parent / "db" / "schema.sql"


def load_schema(conn: sqlite3.Connection) -> None:
    """Load the SQL schema from db/schema.sql into the given connection."""
    schema_sql = SCHEMA_PATH.read_text()
    conn.executescript(schema_sql)


def get_db(path: str = ":memory:") -> sqlite3.Connection:
    """Create a SQLite connection.

    Defaults to in-memory database for testing. Pass a file path for
    persistent storage. Schema is NOT loaded here — call init_db() once
    at application startup for persistent databases, or call load_schema()
    explicitly for in-memory test databases.
    """
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(path: str) -> None:
    """Initialize a persistent database: create schema if it doesn't exist."""
    conn = sqlite3.connect(path)
    try:
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA foreign_keys = ON")
        load_schema(conn)
    finally:
        conn.close()
