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
        s._ensure_sources()
        s.run_once()
        from db.articles import list_articles
        from db.connection import get_db
        conn = get_db(db_path)
        try:
            articles = list_articles(conn)
            assert len(articles) > 0, "Should have inserted articles from live RSS"
        finally:
            conn.close()

    @pytest.mark.network
    def test_run_once_inserts_with_empty_bodies(self, tmp_path):
        """Phase 1: articles inserted with body='' (deferred extraction)."""
        db_path = str(tmp_path / "test2.db")
        from db.connection import init_db, get_db
        from db.articles import list_articles
        init_db(db_path)
        s = ScraperScheduler(db_path)
        s._ensure_sources()
        s.run_once(max_sources=3)  # only first 3 feeds, fast
        conn = get_db(db_path)
        try:
            articles = list_articles(conn, limit=100)
            assert len(articles) > 0
            for a in articles:
                assert a["body"] == "" or a["body"] is None, \
                    f"Expected empty body, got {a['body'][:50]!r}"
        finally:
            conn.close()

    @pytest.mark.network
    def test_run_once_respects_max_sources(self, tmp_path):
        """max_sources limits how many feeds are polled."""
        db_path = str(tmp_path / "test_max.db")
        from db.connection import init_db, get_db
        from db.articles import list_articles
        init_db(db_path)
        s = ScraperScheduler(db_path)
        s._ensure_sources()
        s.run_once(max_sources=1)
        conn = get_db(db_path)
        try:
            articles = list_articles(conn, limit=200)
            source_ids = {a["source_id"] for a in articles}
            # With max_sources=1, only the first feed's source should appear
            assert len(source_ids) == 1, \
                f"Expected articles from 1 source, got {len(source_ids)}"
        finally:
            conn.close()

    def test_extract_pending_fills_bodies(self, tmp_path):
        """Phase 2: extract_pending fills in empty bodies."""
        db_path = str(tmp_path / "test_extract.db")
        from db.connection import init_db, get_db
        from db.sources import insert_source
        from db.articles import insert_article, get_article
        init_db(db_path)
        conn = get_db(db_path)
        src = insert_source(conn, "Test", "test.com", 1)
        # Insert a pending article (empty body, AVAILABLE status)
        aid = insert_article(conn, src, "https://test.com/1", "Test Title",
                             body="", body_status="AVAILABLE")
        conn.close()

        s = ScraperScheduler(db_path)
        extracted = s.extract_pending(limit=1)
        assert extracted == 1

        conn = get_db(db_path)
        try:
            art = get_article(conn, aid)
            assert art["body"] is not None
            # Body was extracted from a real URL — should have content or
            # status changed to BODY_UNAVAILABLE on failure
            assert (len(art["body"]) > 0 and art["body_status"] == "AVAILABLE") or \
                   art["body_status"] == "BODY_UNAVAILABLE"
        finally:
            conn.close()

    def test_extract_pending_skips_already_extracted(self, tmp_path):
        """extract_pending only picks up articles with empty body."""
        db_path = str(tmp_path / "test_skip.db")
        from db.connection import init_db, get_db
        from db.sources import insert_source
        from db.articles import insert_article
        init_db(db_path)
        conn = get_db(db_path)
        src = insert_source(conn, "Test", "test.com", 1)
        # Article with real body — should NOT be re-extracted
        insert_article(conn, src, "https://test.com/done", "Done",
                       body="already extracted", body_status="AVAILABLE")
        conn.close()

        s = ScraperScheduler(db_path)
        extracted = s.extract_pending(limit=10)
        assert extracted == 0, "Should skip articles that already have bodies"

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
