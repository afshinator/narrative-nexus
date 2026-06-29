"""CRUD operations for the silent_edits table."""
import sqlite3


def insert_silent_edit(
    conn: sqlite3.Connection,
    article_id: int,
    change_ratio: float,
    stored_body_length: int,
    fetched_body_length: int,
) -> int:
    """Insert a detected silent edit. Returns the new row id."""
    cur = conn.execute(
        "INSERT INTO silent_edits (article_id, change_ratio, stored_body_length, fetched_body_length) "
        "VALUES (?, ?, ?, ?)",
        (article_id, change_ratio, stored_body_length, fetched_body_length),
    )
    conn.commit()
    return cur.lastrowid


def list_silent_edits(
    conn: sqlite3.Connection,
    article_id: int,
) -> list[dict]:
    """List all silent edits for a given article, most recent first."""
    rows = conn.execute(
        "SELECT * FROM silent_edits WHERE article_id = ? ORDER BY detected_at DESC",
        (article_id,),
    ).fetchall()
    return [dict(r) for r in rows]
