"""CRUD operations for the claims table."""

from typing import Optional
import sqlite3

VALID_STATES = {"PENDING", "CONSENSUS_ABSORBED", "UNRESOLVED"}
VALID_CONVERGENCE_TYPES = {"CROSS_SOURCE_CONVERGENT", "SELF_CONSISTENT", None}


def insert_claim(
    conn: sqlite3.Connection,
    article_id: int,
    cluster_id: int,
    text: str,
    state: str = "PENDING",
    convergence_type: Optional[str] = None,
    absorbed_at: Optional[str] = None,
) -> int:
    """Insert a new claim. Returns the new row id."""
    cur = conn.execute(
        "INSERT INTO claims (article_id, cluster_id, text, state, convergence_type, absorbed_at) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (article_id, cluster_id, text, state, convergence_type, absorbed_at),
    )
    conn.commit()
    return cur.lastrowid


def get_claim(conn: sqlite3.Connection, claim_id: int) -> Optional[dict]:
    """Get a claim by id. Returns None if not found."""
    row = conn.execute(
        "SELECT * FROM claims WHERE id = ?", (claim_id,)
    ).fetchone()
    return dict(row) if row else None


def list_claims(
    conn: sqlite3.Connection,
    cluster_id: Optional[int] = None,
    state: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
) -> list[dict]:
    """List claims, optionally filtered by cluster_id and/or state."""
    query = "SELECT * FROM claims"
    params: list = []
    conditions = []

    if cluster_id is not None:
        conditions.append("cluster_id = ?")
        params.append(cluster_id)
    if state is not None:
        conditions.append("state = ?")
        params.append(state)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    rows = conn.execute(query, params).fetchall()
    return [dict(r) for r in rows]


def update_claim_state(
    conn: sqlite3.Connection,
    claim_id: int,
    state: str,
    convergence_type: Optional[str] = None,
    absorbed_at: Optional[str] = None,
) -> bool:
    """Update claim state and optional convergence metadata. Returns True if updated."""
    if state not in VALID_STATES:
        raise ValueError(
            f"Invalid claim state: {state!r}. Must be one of {VALID_STATES}."
        )
    existing = get_claim(conn, claim_id)
    if existing is None:
        return False

    cur = conn.execute(
        "UPDATE claims SET state = ?, convergence_type = ?, absorbed_at = ? WHERE id = ?",
        (state, convergence_type, absorbed_at, claim_id),
    )
    conn.commit()
    return cur.rowcount > 0


def delete_claim(conn: sqlite3.Connection, claim_id: int) -> bool:
    """Delete a claim by id. Returns True if a row was deleted."""
    cur = conn.execute("DELETE FROM claims WHERE id = ?", (claim_id,))
    conn.commit()
    return cur.rowcount > 0
