"""CRUD operations for the claim_sources join table."""

import sqlite3


def add_claim_source(
    conn: sqlite3.Connection,
    claim_id: int,
    source_id: int,
    *,
    first_seen_at: str | None = None,
) -> bool:
    """Link a claim to a source. Returns True if inserted (False if already exists).

    If first_seen_at is provided (non-empty and non-None), it is used as-is.
    Otherwise explicit NULL is inserted — unknown dates must not be stamped with processing time.
    """
    try:
        if first_seen_at is not None and first_seen_at != "":
            conn.execute(
                "INSERT INTO claim_sources (claim_id, source_id, first_seen_at) "
                "VALUES (?, ?, ?)",
                (claim_id, source_id, first_seen_at),
            )
        else:
            conn.execute(
                "INSERT INTO claim_sources (claim_id, source_id, first_seen_at) VALUES (?, ?, NULL)",
                (claim_id, source_id),
            )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False


def list_claim_sources(
    conn: sqlite3.Connection,
    claim_id: int,
) -> list[dict]:
    """List all source links for a given claim."""
    rows = conn.execute(
        "SELECT * FROM claim_sources WHERE claim_id = ? ORDER BY first_seen_at",
        (claim_id,),
    ).fetchall()
    return [dict(r) for r in rows]


def list_source_claims(
    conn: sqlite3.Connection,
    source_id: int,
) -> list[dict]:
    """List all claim links for a given source."""
    rows = conn.execute(
        "SELECT * FROM claim_sources WHERE source_id = ? ORDER BY first_seen_at",
        (source_id,),
    ).fetchall()
    return [dict(r) for r in rows]


def remove_claim_source(
    conn: sqlite3.Connection,
    claim_id: int,
    source_id: int,
) -> bool:
    """Remove a claim-source link. Returns True if a row was deleted."""
    cur = conn.execute(
        "DELETE FROM claim_sources WHERE claim_id = ? AND source_id = ?",
        (claim_id, source_id),
    )
    conn.commit()
    return cur.rowcount > 0
