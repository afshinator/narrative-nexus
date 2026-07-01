"""CRUD operations for the corrections table."""
import sqlite3
from typing import Any


def init_corrections_table(conn: sqlite3.Connection) -> None:
    """Create the corrections table if it doesn't exist."""
    conn.execute(
        """CREATE TABLE IF NOT EXISTS corrections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            article_id INTEGER NOT NULL REFERENCES articles(id),
            detected_pattern TEXT NOT NULL,
            matched_text TEXT,
            detected_at TEXT NOT NULL DEFAULT (datetime('now'))
        )"""
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_corrections_article ON corrections(article_id)"
    )
    conn.commit()


def insert_correction(
    conn: sqlite3.Connection,
    article_id: int,
    *,
    detected_pattern: str,
    matched_text: str | None = None,
) -> int:
    """Insert a detected correction. Returns the new row id."""
    cur = conn.execute(
        "INSERT INTO corrections (article_id, detected_pattern, matched_text) "
        "VALUES (?, ?, ?)",
        (article_id, detected_pattern, matched_text),
    )
    conn.commit()
    return cur.lastrowid


def get_corrections_for_article(
    conn: sqlite3.Connection, article_id: int
) -> list[dict[str, Any]]:
    """List all corrections detected for an article."""
    rows = conn.execute(
        "SELECT * FROM corrections WHERE article_id = ? ORDER BY id",
        (article_id,),
    ).fetchall()
    return [dict(r) for r in rows]


def count_corrections_per_source(
    conn: sqlite3.Connection, *, as_of: str | None = None
) -> dict[int, int]:
    """Count corrections per source. Optional as_of date filter."""
    query = """
        SELECT a.source_id, COUNT(DISTINCT c.id) as cnt
        FROM corrections c
        JOIN articles a ON a.id = c.article_id
    """
    params: tuple = ()
    if as_of:
        query += " WHERE c.detected_at <= ?"
        params = (as_of,)
    query += " GROUP BY a.source_id"

    rows = conn.execute(query, params).fetchall()
    return {r["source_id"]: r["cnt"] for r in rows}
