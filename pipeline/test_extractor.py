"""Tests for pipeline.extractor — ArticleExtractor."""
import pytest
from pipeline.extractor import ArticleExtractor


class TestArticleExtractorUnit:
    def test_init(self):
        ex = ArticleExtractor()
        assert ex is not None


@pytest.mark.network
class TestArticleExtractorLive:
    def test_extracts_guardian_article(self):
        # Real Guardian article from RSS feed
        import feedparser
        f = feedparser.parse("https://www.theguardian.com/world/rss")
        assert len(f.entries) > 0, "Guardian RSS must have entries for this test"
        url = f.entries[0].link
        ex = ArticleExtractor()
        body, status = ex.extract(url)
        assert len(body) > 100, f"Body too short: {len(body)} chars"
        assert status == "AVAILABLE"

    def test_paywall_returns_unavailable(self):
        # NYT paywall — newspaper4k gets 403
        import feedparser
        f = feedparser.parse("https://rss.nytimes.com/services/xml/rss/nyt/World.xml")
        assert len(f.entries) > 0, "NYT RSS must have entries for this test"
        url = f.entries[0].link
        ex = ArticleExtractor()
        body, status = ex.extract(url)
        assert status == "BODY_UNAVAILABLE"

    def test_invalid_url_returns_unavailable(self):
        ex = ArticleExtractor()
        body, status = ex.extract("https://this-domain-does-not-exist-12345.com/article")
        assert status == "BODY_UNAVAILABLE"
        assert body == ""
