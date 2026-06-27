"""Tests for pipeline.scraper — RSSPoller."""
import pytest
from pipeline.scraper import RSSPoller, FEED_CONFIG


class TestFeedConfig:
    def test_all_37_sources_have_entries(self):
        assert len(FEED_CONFIG) == 37

    def test_every_entry_has_required_keys(self):
        for name, cfg in FEED_CONFIG.items():
            assert "url" in cfg, f"{name} missing url"
            assert "type" in cfg, f"{name} missing type"
            assert cfg["type"] in ("native", "google_news", "feedburner")
            assert "domain" in cfg, f"{name} missing domain"


@pytest.mark.network
class TestRSSPollerLive:
    def test_parses_bbc_feed(self):
        poller = RSSPoller()
        entries = list(poller.fetch("bbc"))
        assert len(entries) > 0
        first = entries[0]
        assert "title" in first
        assert "url" in first
        assert "published_at" in first
        assert "source_domain" in first
        assert first["source_domain"] == "bbc.com"

    def test_parses_google_news_feed(self):
        poller = RSSPoller()
        entries = list(poller.fetch("reuters"))
        assert len(entries) > 0
        first = entries[0]
        assert "title" in first
        assert "url" in first  # opaque Google URL, but present
        assert first["body_status"] == "BODY_UNAVAILABLE"


class TestRSSPollerUnit:
    def test_fetch_unknown_source_returns_empty(self):
        poller = RSSPoller()
        entries = list(poller.fetch("nonexistent"))
        assert entries == []
