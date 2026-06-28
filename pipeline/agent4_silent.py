"""Silent Auditor Agent — detects unreported article edits.

Re-fetches article bodies via the scraper's extractor and diffs against
stored body text.  Uses difflib.SequenceMatcher from the stdlib — no LLM
needed for text comparison.  Flags articles where the body changed by more
than 10% without a formal correction notice.

ponytail: Pure Python text diff (difflib).
ponytail: 10% change threshold — catches real edits, ignores whitespace noise.
ponytail: No LLM evaluation of "significant" changes.
"""

import sqlite3
from difflib import SequenceMatcher

from pipeline.base_agent import BasePipelineAgent
from pipeline.extractor import ArticleExtractor
from db.connection import get_db


# ── Threshold ────────────────────────────────────────────────────────────
# Edit detection: fraction of text that changed.  0.10 = 10% threshold.
# Catches: paragraph rewrites, headline changes, substantial body edits.
# Ignores: whitespace changes, minor punctuation fixes.

_EDIT_THRESHOLD = 0.10


def _detect_edit(stored_body: str, fetched_body: str) -> bool:
    """Return True if the fetched body differs from stored by >10%.

    Uses difflib.SequenceMatcher for ratio comparison.  Returns True for
    empty→non-empty and non-empty→empty transitions.
    """
    if not stored_body and not fetched_body:
        return False
    if not stored_body or not fetched_body:
        return True  # article appeared or disappeared entirely

    ratio = SequenceMatcher(None, stored_body, fetched_body).ratio()
    return ratio < (1.0 - _EDIT_THRESHOLD)


class SilentAuditorAgent(BasePipelineAgent):
    """Compares current article bodies against stored snapshots.

    Re-fetches articles via ArticleExtractor and diffs against the stored
    body.  No LLM, no GPU — pure Python text diffing.
    """

    def __init__(self, *, db_path: str):
        """Create the auditor agent.

        Args:
          db_path: Path to the SQLite database.
        """
        self.db_path = db_path
        self._extractor = ArticleExtractor()

    async def run(self) -> dict[str, int]:
        """Re-fetch article bodies and detect edits.

        Reads all articles with body_status='AVAILABLE' from the database,
        re-fetches each one, and diffs against the stored text.

        Returns:
          dict with keys: articles_checked (count), edits_detected (count).
        """
        conn = get_db(self.db_path)
        try:
            rows = conn.execute(
                """SELECT id, url, body
                   FROM articles
                   WHERE body_status = 'AVAILABLE'
                     AND body IS NOT NULL
                     AND body != ''"""
            ).fetchall()
        finally:
            conn.close()

        if not rows:
            return {"articles_checked": 0, "edits_detected": 0}

        articles_checked = 0
        edits_detected = 0

        for row in rows:
            article_id = row["id"]
            url = row["url"]
            stored_body = row["body"] or ""

            # Re-fetch the article
            fetched_body, body_status = self._extractor.extract(url)

            if body_status != "AVAILABLE" or not fetched_body:
                # Article became unavailable — skip (not an edit, it's a 404)
                articles_checked += 1
                continue

            if _detect_edit(stored_body, fetched_body):
                edits_detected += 1
                # ponytail: log the edit, don't write to DB yet.
                # Full edit tracking (correction notice detection, edit log)
                # is future work — this just counts the flags.
                print(
                    f"[SilentAuditor] Edit detected: article={article_id} "
                    f"url={url}"
                )

            articles_checked += 1

        return {
            "articles_checked": articles_checked,
            "edits_detected": edits_detected,
        }
