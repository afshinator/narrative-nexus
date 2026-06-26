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
    def test_run_once_inserts_articles(self, db):
        s = ScraperScheduler(":memory:")
        s.run_once()
        from db.articles import list_articles
        articles = list_articles(db)
        assert len(articles) > 0, "Should have inserted articles from live RSS"

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
