"""CRUD operations for the clusters table."""

from typing import Optional
import sqlite3


def create_cluster(
    conn: sqlite3.Connection,
    vertical: str,
    title: Optional[str] = None,
) -> int:
    """Create a new cluster. Returns the new row id."""
    cur = conn.execute(
        "INSERT INTO clusters (vertical, title) VALUES (?, ?)",
        (vertical, title),
    )
    conn.commit()
    return cur.lastrowid


def get_cluster(conn: sqlite3.Connection, cluster_id: int) -> Optional[dict]:
    """Get a cluster by id. Returns None if not found."""
    row = conn.execute(
        "SELECT * FROM clusters WHERE id = ?", (cluster_id,)
    ).fetchone()
    return dict(row) if row else None


def list_clusters(
    conn: sqlite3.Connection,
    vertical: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> list[dict]:
    """List clusters, optionally filtered by vertical."""
    if vertical is not None:
        rows = conn.execute(
            "SELECT * FROM clusters WHERE vertical = ? ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (vertical, limit, offset),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM clusters ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (limit, offset),
        ).fetchall()
    return [dict(r) for r in rows]


def delete_cluster(conn: sqlite3.Connection, cluster_id: int) -> bool:
    """Delete a cluster by id. Returns True if a row was deleted."""
    cur = conn.execute("DELETE FROM clusters WHERE id = ?", (cluster_id,))
    conn.commit()
    return cur.rowcount > 0
