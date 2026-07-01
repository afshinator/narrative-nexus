"""CRUD operations for the article_framing table."""
import sqlite3
from typing import Any


def init_framing_table(conn: sqlite3.Connection) -> None:
    """Create the article_framing table if it doesn't exist."""
    conn.execute(
        """CREATE TABLE IF NOT EXISTS article_framing (
            article_id INTEGER PRIMARY KEY REFERENCES articles(id),
            llm_score REAL,
            lexical_score REAL,
            sentiment_score REAL,
            computed_at TEXT NOT NULL DEFAULT (datetime('now'))
        )"""
    )
    conn.commit()


def insert_framing_scores(
    conn: sqlite3.Connection,
    article_id: int,
    *,
    llm_score: float | None = None,
    lexical_score: float | None = None,
    sentiment_score: float | None = None,
) -> None:
    """Insert or replace framing scores for an article."""
    conn.execute(
        """INSERT OR REPLACE INTO article_framing
           (article_id, llm_score, lexical_score, sentiment_score)
           VALUES (?, ?, ?, ?)""",
        (article_id, llm_score, lexical_score, sentiment_score),
    )
    conn.commit()


def get_framing_scores(
    conn: sqlite3.Connection, article_id: int
) -> dict[str, Any] | None:
    """Get framing scores for an article. Returns None if not computed."""
    row = conn.execute(
        "SELECT * FROM article_framing WHERE article_id = ?",
        (article_id,),
    ).fetchone()
    return dict(row) if row else None


def count_unscored(conn: sqlite3.Connection) -> int:
    """Count articles with bodies that have no framing scores."""
    row = conn.execute(
        """SELECT COUNT(*) as cnt
           FROM articles a
           WHERE a.body_status = 'AVAILABLE'
             AND a.body IS NOT NULL
             AND a.body != ''
             AND a.id NOT IN (SELECT article_id FROM article_framing)"""
    ).fetchone()
    return row["cnt"] if row else 0


def get_unscored_articles(
    conn: sqlite3.Connection, limit: int = 100
) -> list[dict[str, Any]]:
    """Get articles with bodies that have no framing scores."""
    rows = conn.execute(
        """SELECT a.id, a.title, a.body
           FROM articles a
           WHERE a.body_status = 'AVAILABLE'
             AND a.body IS NOT NULL
             AND a.body != ''
             AND a.id NOT IN (SELECT article_id FROM article_framing)
           ORDER BY a.id
           LIMIT ?""",
        (limit,),
    ).fetchall()
    return [dict(r) for r in rows]


def get_unllmed_articles(
    conn: sqlite3.Connection, limit: int = 100
) -> list[dict[str, Any]]:
    """Get articles with framing scores but no LLM score yet."""
    rows = conn.execute(
        """SELECT a.id, a.title, a.body
           FROM articles a
           JOIN article_framing af ON af.article_id = a.id
           WHERE af.llm_score IS NULL
           ORDER BY a.id
           LIMIT ?""",
        (limit,),
    ).fetchall()
    return [dict(r) for r in rows]


def count_unllmed(conn: sqlite3.Connection) -> int:
    """Count articles with framing scores but no LLM score yet."""
    row = conn.execute(
        "SELECT COUNT(*) as cnt FROM article_framing WHERE llm_score IS NULL"
    ).fetchone()
    return row["cnt"] if row else 0
