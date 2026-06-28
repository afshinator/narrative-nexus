"""Tests for pipeline.agent4_silent — article diff + edit detection."""
import pytest
import tempfile
import os
from difflib import SequenceMatcher
from unittest.mock import AsyncMock, patch

from db.connection import init_db, get_db
from db.sources import insert_source
from db.articles import insert_article


# ── Fixtures ────────────────────────────────────────────────────────────


@pytest.fixture
def db_path():
    """Temp DB with articles that have stored body text."""
    path = tempfile.mktemp(suffix=".db")
    init_db(path)
    conn = get_db(path)
    try:
        s1 = insert_source(conn, name="Reuters", domain="reuters.com", tier=1)
        insert_article(conn, source_id=s1, url="http://r.com/1",
                       title="Original title",
                       body="The president signed the bill into law.")
        insert_article(conn, source_id=s1, url="http://r.com/2",
                       title="Short article",
                       body="Short body.")
        conn.commit()
    finally:
        conn.close()
    yield path
    os.unlink(path)


# ── SilentAuditorAgent ───────────────────────────────────────────────────


class TestSilentAuditorAgent:
    def test_agent_takes_db_path(self):
        from pipeline.agent4_silent import SilentAuditorAgent
        agent = SilentAuditorAgent(db_path=":memory:")
        assert agent.db_path == ":memory:"

    @pytest.mark.asyncio
    async def test_run_calls_diagnostics(self):
        """Agent opens DB and reads articles — broad smoke test."""
        path = tempfile.mktemp(suffix=".db")
        init_db(path)
        try:
            from pipeline.agent4_silent import SilentAuditorAgent
            agent = SilentAuditorAgent(db_path=path)
            result = await agent.run()
            assert isinstance(result, dict)
            assert result["articles_checked"] == 0  # empty DB
            assert result["edits_detected"] == 0
        finally:
            os.unlink(path)

    @pytest.mark.asyncio
    async def test_run_detects_text_changes(self, db_path):
        """When re-fetched body differs from stored body, flag it."""
        from pipeline.agent4_silent import SilentAuditorAgent

        # Mock ArticleExtractor to return a modified body
        with patch("pipeline.agent4_silent.ArticleExtractor") as mock_ext_cls:
            mock_ext = mock_ext_cls.return_value
            # First article: body changed significantly
            # Second article: body unchanged
            mock_ext.extract.side_effect = [
                ("The president vetoed the bill after heated debate.", "AVAILABLE"),
                ("Short body.", "AVAILABLE"),
            ]

            agent = SilentAuditorAgent(db_path=db_path)
            result = await agent.run()

            assert result["articles_checked"] >= 1
            # At least the first article should be flagged as changed
            assert result["edits_detected"] >= 1

    @pytest.mark.asyncio
    async def test_detect_edit_finds_significant_changes(self):
        """The diff helper correctly identifies edits above threshold."""
        from pipeline.agent4_silent import _detect_edit

        # Identical text → no edit
        assert _detect_edit("hello world", "hello world") is False

        # Minor change (one word) → no edit (below 10%)
        assert _detect_edit("hello world", "hello world!") is False

        # Major change → edit detected
        assert _detect_edit(
            "The president signed the bill.",
            "The president vetoed the bill after a long debate.",
        ) is True

        # Completely different → edit detected
        assert _detect_edit(
            "Original story about climate change legislation.",
            "Updated: Market rally continues as tech stocks surge.",
        ) is True

    @pytest.mark.asyncio
    async def test_detect_edit_empty_bodies(self):
        """Edge case: empty strings on one or both sides."""
        from pipeline.agent4_silent import _detect_edit

        # Empty stored, non-empty fetched → edit
        assert _detect_edit("", "new content") is True

        # Non-empty stored, empty fetched → edit (article removed?)
        assert _detect_edit("old content", "") is True

        # Both empty → no edit
        assert _detect_edit("", "") is False
