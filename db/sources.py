"""CRUD operations for the sources table."""

from typing import Optional
import sqlite3


def insert_source(
    conn: sqlite3.Connection,
    name: str,
    domain: str,
    tier: int,
    active: int = 1,
) -> int:
    """Insert a new source. Returns the new row id."""
    cur = conn.execute(
        "INSERT INTO sources (name, domain, tier, active) VALUES (?, ?, ?, ?)",
        (name, domain, tier, active),
    )
    conn.commit()
    return cur.lastrowid


def get_source(conn: sqlite3.Connection, source_id: int) -> Optional[dict]:
    """Get a source by id. Returns None if not found."""
    row = conn.execute(
        "SELECT * FROM sources WHERE id = ?", (source_id,)
    ).fetchone()
    return dict(row) if row else None


def get_source_by_domain(conn: sqlite3.Connection, domain: str) -> Optional[dict]:
    """Get a source by domain. Returns None if not found."""
    row = conn.execute(
        "SELECT * FROM sources WHERE domain = ?", (domain,)
    ).fetchone()
    return dict(row) if row else None


def list_sources(conn: sqlite3.Connection, active_only: bool = False) -> list[dict]:
    """List all sources, optionally filtering to active only."""
    if active_only:
        rows = conn.execute(
            "SELECT * FROM sources WHERE active = 1 ORDER BY tier, name"
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM sources ORDER BY tier, name"
        ).fetchall()
    return [dict(r) for r in rows]


def update_source_active(conn: sqlite3.Connection, source_id: int, active: int) -> bool:
    """Set the active flag on a source. Returns True if a row was updated."""
    cur = conn.execute(
        "UPDATE sources SET active = ? WHERE id = ?", (active, source_id)
    )
    conn.commit()
    return cur.rowcount > 0


def delete_source(conn: sqlite3.Connection, source_id: int) -> bool:
    """Delete a source by id. Returns True if a row was deleted."""
    cur = conn.execute("DELETE FROM sources WHERE id = ?", (source_id,))
    conn.commit()
    return cur.rowcount > 0
