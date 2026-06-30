"""CRUD operations for the snapshots table."""

from typing import Optional
import sqlite3


def insert_snapshot(
    conn: sqlite3.Connection,
    source_id: int,
    vertical: str,
    date: str,
    r_orig: Optional[float] = None,
    r_val: Optional[float] = None,
    r_speed: Optional[float] = None,
    r_frame: Optional[float] = None,
    r_edit: Optional[float] = None,
    r_correct: Optional[float] = None,
    archetype: Optional[str] = None,
) -> int:
    """Insert a new snapshot. Returns the new row id."""
    cur = conn.execute(
        "INSERT OR REPLACE INTO snapshots "
        "(source_id, vertical, date, r_orig, r_val, r_speed, r_frame, r_edit, r_correct, archetype) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (source_id, vertical, date, r_orig, r_val, r_speed, r_frame, r_edit, r_correct, archetype),
    )
    conn.commit()
    return cur.lastrowid


def get_snapshot(conn: sqlite3.Connection, snapshot_id: int) -> Optional[dict]:
    """Get a snapshot by id. Returns None if not found."""
    row = conn.execute(
        "SELECT * FROM snapshots WHERE id = ?", (snapshot_id,)
    ).fetchone()
    return dict(row) if row else None


def list_snapshots(
    conn: sqlite3.Connection,
    source_id: Optional[int] = None,
    vertical: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
) -> list[dict]:
    """List snapshots, optionally filtered by source_id and/or vertical.

    Pass limit=0 to return all rows (no LIMIT clause).
    """
    query = "SELECT * FROM snapshots"
    params: list = []
    conditions = []

    if source_id is not None:
        conditions.append("source_id = ?")
        params.append(source_id)
    if vertical is not None:
        conditions.append("vertical = ?")
        params.append(vertical)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY date DESC"

    if limit > 0:
        query += " LIMIT ? OFFSET ?"
        params.extend([limit, offset])

    rows = conn.execute(query, params).fetchall()
    return [dict(r) for r in rows]


def get_source_vertical_snapshot(
    conn: sqlite3.Connection,
    source_id: int,
    vertical: str,
    date: str,
) -> Optional[dict]:
    """Get the snapshot for a specific source+vertical+date combo."""
    row = conn.execute(
        "SELECT * FROM snapshots WHERE source_id = ? AND vertical = ? AND date = ?",
        (source_id, vertical, date),
    ).fetchone()
    return dict(row) if row else None


def delete_snapshot(conn: sqlite3.Connection, snapshot_id: int) -> bool:
    """Delete a snapshot by id. Returns True if a row was deleted."""
    cur = conn.execute("DELETE FROM snapshots WHERE id = ?", (snapshot_id,))
    conn.commit()
    return cur.rowcount > 0
