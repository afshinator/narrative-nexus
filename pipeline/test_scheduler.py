"""Tests for pipeline.scheduler — ScraperScheduler."""
import pytest
from pipeline.scheduler import ScraperScheduler


class TestScraperScheduler:
    def test_starts_paused(self, db):
        s = ScraperScheduler(":memory:")
        assert s.is_running() is False

    def test_start_stop_idempotent(self, db):
        s = ScraperScheduler(":memory:")
        s.start()
        assert s.is_running() is True
        s.start()  # idempotent
        assert s.is_running() is True
        s.stop()
        assert s.is_running() is False
        s.stop()  # idempotent
        assert s.is_running() is False

    @pytest.mark.network
    def test_run_once_inserts_articles(self, db, tmp_path):
        # Use a temp file so scheduler and assertion share the same DB (review-03 T02)
        db_path = str(tmp_path / "test.db")
        from db.connection import init_db
        init_db(db_path)
        s = ScraperScheduler(db_path)
        s.run_once()
        from db.articles import list_articles
        from db.connection import get_db
        conn = get_db(db_path)
        try:
            articles = list_articles(conn)
            assert len(articles) > 0, "Should have inserted articles from live RSS"
        finally:
            conn.close()

    def test_ensure_sources_preserves_tiers(self, db):
        s = ScraperScheduler(":memory:")
        s._ensure_sources()
        from db.sources import list_sources
        sources = list_sources(db)
        from pipeline.scraper import FEED_CONFIG
        expected = {cfg["domain"]: cfg["tier"] for cfg in FEED_CONFIG.values()}
        for src in sources:
            assert src["tier"] == expected[src["domain"]], \
                f"{src['domain']} got tier {src['tier']}, expected {expected[src['domain']]}"

    def test_status(self, db):
        s = ScraperScheduler(":memory:")
        st = s.status()
        assert st["running"] is False
        assert "last_run" in st
        assert "articles_inserted" in st
