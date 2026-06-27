"""APScheduler-powered scraper loop. Coordinates poll → extract → insert."""
import sqlite3
from datetime import datetime, timezone

from apscheduler.schedulers.background import BackgroundScheduler

from db.connection import get_db, load_schema
from db.sources import get_source_by_domain, insert_source, list_sources
from db.articles import insert_article
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

    def run_once(self):
        """Execute one full poll cycle. Used by scheduler and for manual testing."""
        conn = get_db(self.db_path)
        load_schema(conn)
        try:
            for entry in self._poller.fetch_all():
                source = get_source_by_domain(conn, entry["source_domain"])
                if source is None:
                    continue
                body = ""
                body_status = entry["body_status"]
                if body_status == "AVAILABLE":
                    body, body_status = self._extractor.extract(entry["url"])
                try:
                    insert_article(
                        conn,
                        source_id=source["id"],
                        url=entry["url"],
                        title=entry["title"],
                        body=body,
                        published_at=entry["published_at"],
                        body_status=body_status,
                    )
                    self._articles_inserted += 1
                except sqlite3.IntegrityError:
                    pass  # duplicate URL — skip
        finally:
            conn.close()
        self._last_run = datetime.now(timezone.utc).isoformat()

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
