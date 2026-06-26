"""SQLite connection management and schema loading."""

import sqlite3
from pathlib import Path

SCHEMA_PATH = Path(__file__).resolve().parent.parent / "db" / "schema.sql"


def load_schema(conn: sqlite3.Connection) -> None:
    """Load the SQL schema from db/schema.sql into the given connection."""
    schema_sql = SCHEMA_PATH.read_text()
    conn.executescript(schema_sql)


def get_db(path: str = ":memory:") -> sqlite3.Connection:
    """Create a SQLite connection and load the schema.

    Defaults to in-memory database for testing. Pass a file path for
    persistent storage.
    """
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA foreign_keys = ON")
    load_schema(conn)
    return conn
