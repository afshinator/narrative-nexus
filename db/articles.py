"""CRUD operations for the articles table."""

from typing import Optional
import sqlite3


def insert_article(
    conn: sqlite3.Connection,
    source_id: int,
    url: str,
    title: Optional[str] = None,
    body: Optional[str] = None,
    published_at: Optional[str] = None,
    body_status: str = "AVAILABLE",
) -> int:
    """Insert a new article. Returns the new row id."""
    cur = conn.execute(
        "INSERT INTO articles (source_id, url, title, body, published_at, body_status) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (source_id, url, title, body, published_at, body_status),
    )
    conn.commit()
    return cur.lastrowid


def get_article(conn: sqlite3.Connection, article_id: int) -> Optional[dict]:
    """Get an article by id. Returns None if not found."""
    row = conn.execute(
        "SELECT * FROM articles WHERE id = ?", (article_id,)
    ).fetchone()
    return dict(row) if row else None


def list_articles(
    conn: sqlite3.Connection,
    source_id: Optional[int] = None,
    limit: int = 50,
    offset: int = 0,
) -> list[dict]:
    """List articles, optionally filtered by source_id."""
    if source_id is not None:
        rows = conn.execute(
            "SELECT * FROM articles WHERE source_id = ? ORDER BY published_at DESC LIMIT ? OFFSET ?",
            (source_id, limit, offset),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM articles ORDER BY published_at DESC LIMIT ? OFFSET ?",
            (limit, offset),
        ).fetchall()
    return [dict(r) for r in rows]


def update_article_body(
    conn: sqlite3.Connection,
    article_id: int,
    body: str,
    body_status: str = "AVAILABLE",
) -> bool:
    """Update article body and status. Returns True if a row was updated."""
    cur = conn.execute(
        "UPDATE articles SET body = ?, body_status = ? WHERE id = ?",
        (body, body_status, article_id),
    )
    conn.commit()
    return cur.rowcount > 0


def delete_article(conn: sqlite3.Connection, article_id: int) -> bool:
    """Delete an article by id. Returns True if a row was deleted."""
    cur = conn.execute("DELETE FROM articles WHERE id = ?", (article_id,))
    conn.commit()
    return cur.rowcount > 0
