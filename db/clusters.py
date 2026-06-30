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
    """List clusters, optionally filtered by vertical.

    Pass limit=0 to return all rows (no LIMIT clause).
    """
    query = "SELECT * FROM clusters"
    params: list = []

    if vertical is not None:
        query += " WHERE vertical = ?"
        params.append(vertical)

    query += " ORDER BY created_at DESC"

    if limit > 0:
        query += " LIMIT ? OFFSET ?"
        params.extend([limit, offset])

    rows = conn.execute(query, params).fetchall()
    return [dict(r) for r in rows]


def delete_cluster(conn: sqlite3.Connection, cluster_id: int) -> bool:
    """Delete a cluster by id. Returns True if a row was deleted."""
    cur = conn.execute("DELETE FROM clusters WHERE id = ?", (cluster_id,))
    conn.commit()
    return cur.rowcount > 0
