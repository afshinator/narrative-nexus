"""APScheduler-powered scraper loop. Coordinates poll → extract → insert."""
import sqlite3
from datetime import datetime, timezone

from apscheduler.schedulers.background import BackgroundScheduler

from db.connection import get_db, load_schema
from db.sources import get_source_by_domain, insert_source, list_sources
from db.articles import insert_article, list_pending_articles, update_article_body
from pipeline.scraper import RSSPoller, FEED_CONFIG
from pipeline.extractor import ArticleExtractor


class ScraperScheduler:
    """Manages the scraping loop. Starts paused — call start() to begin."""

    def __init__(self, db_path: str = ":memory:"):
        self.db_path = db_path
        self._scheduler = BackgroundScheduler(daemon=True)  # review-03 T01: daemon so tests don't hang
        self._running = False
        self._last_run: str | None = None
        self._articles_inserted = 0
        self._extractor = ArticleExtractor()
        self._poller = RSSPoller()

    def is_running(self) -> bool:
        return self._running

    def start(self):
        """Resume polling. Idempotent."""
        if self._running:
            return
        self._ensure_sources()
        self._scheduler.add_job(
            self.run_once, "interval", minutes=30, id="scrape",
            next_run_time=datetime.now(timezone.utc),
        )
        if not self._scheduler.running:
            self._scheduler.start()
        self._running = True

    def stop(self):
        """Pause polling. Idempotent."""
        if not self._running:
            return
        self._scheduler.remove_job("scrape")
        self._running = False

    def status(self) -> dict:
        return {
            "running": self._running,
            "last_run": self._last_run,
            "articles_inserted": self._articles_inserted,
        }

    def shutdown(self):
        self.stop()
        if self._scheduler.running:
            self._scheduler.shutdown(wait=False)

    def run_once(self, max_sources: int | None = None):
        """Phase 1: poll RSS feeds + insert articles (no body extraction).

        Polls all feeds and inserts articles with empty body.  Body extraction
        is deferred to extract_pending() so the poll cycle completes quickly
        regardless of how slow individual article fetches are.

        Sources must be seeded before calling (via start() or _ensure_sources()).

        max_sources: limit to first N sources (for sample runs / testing).
        """
        conn = get_db(self.db_path)
        load_schema(conn)
        try:
            source_count = 0
            for name, cfg in FEED_CONFIG.items():
                if max_sources is not None and source_count >= max_sources:
                    break
                source_count += 1
                for entry in self._poller.fetch(name):
                    source = get_source_by_domain(conn, entry["source_domain"])
                    if source is None:
                        continue
                    try:
                        insert_article(
                            conn,
                            source_id=source["id"],
                            url=entry["url"],
                            title=entry["title"],
                            body="",  # ponytail: deferred extraction
                            published_at=entry["published_at"],
                            body_status=entry["body_status"],
                        )
                        self._articles_inserted += 1
                    except sqlite3.IntegrityError:
                        pass  # duplicate URL — skip
        finally:
            conn.close()
        self._last_run = datetime.now(timezone.utc).isoformat()

    def extract_pending(self, limit: int = 50) -> int:
        """Phase 2: extract bodies for articles awaiting extraction.

        Picks up articles where body_status='AVAILABLE' and body is empty,
        fetches + parses each article page, and updates the row.

        Returns the number of articles processed.
        """
        conn = get_db(self.db_path)
        load_schema(conn)
        try:
            pending = list_pending_articles(conn, limit=limit)
            extracted = 0
            for article in pending:
                body, body_status = self._extractor.extract(article["url"])
                update_article_body(conn, article["id"], body, body_status)
                extracted += 1
            return extracted
        finally:
            conn.close()

    def extract_google_news(self, limit: int = 50) -> int:
        """Phase 2b: extract bodies for Google News articles (opaque redirect URLs).

        Uses CloakBrowser to resolve the Google News redirect to the canonical
        article URL, then tries newspaper4k for extraction.  Falls back to
        CloakBrowser's visible-text extraction for paywalled sources.

        Returns the number of articles successfully converted from
        BODY_UNAVAILABLE to AVAILABLE.
        """
        from pipeline.cloakbrowser_extractor import extract as cb_extract

        conn = get_db(self.db_path)
        load_schema(conn)
        converted = 0
        try:
            rows = conn.execute(
                """SELECT a.id, a.url
                   FROM articles a
                   WHERE a.body_status = 'BODY_UNAVAILABLE'
                     AND (a.body IS NULL OR a.body = '')
                   ORDER BY a.id LIMIT ?""",
                (limit,),
            ).fetchall()

            for row in rows:
                article_id = row["id"]
                url = row["url"]

                # Try newspaper4k first (fast, works for non-paywalled)
                body, status = self._extractor.extract(url)

                # If newspaper4k fails (paywalled or Google News URL), try CloakBrowser
                if not body:
                    body, status = cb_extract(url)

                if body:
                    update_article_body(conn, article_id, body, "AVAILABLE")
                    converted += 1

            return converted
        finally:
            conn.close()

    # ponytail: sources seeded lazily on first start, no separate seed step
    def _ensure_sources(self):
        conn = get_db(self.db_path)
        load_schema(conn)
        try:
            existing = list_sources(conn)
            if len(existing) >= 37:
                return
            seen = {s["domain"] for s in existing}
            for cfg in FEED_CONFIG.values():
                domain = cfg["domain"]
                if domain not in seen:
                    name = domain.split(".")[0]
                    insert_source(conn, name=name, domain=domain, tier=cfg["tier"])
        finally:
            conn.close()
