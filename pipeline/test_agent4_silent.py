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
    async def test_run_writes_edits_to_db(self, db_path):
        """Detected edits are persisted to the silent_edits table."""
        from pipeline.agent4_silent import SilentAuditorAgent

        with patch("pipeline.agent4_silent.ArticleExtractor") as mock_ext_cls:
            mock_ext = mock_ext_cls.return_value
            # First article: significant change → edit detected
            # Second article: unchanged → no edit
            mock_ext.extract.side_effect = [
                ("The president vetoed the bill after heated debate.", "AVAILABLE"),
                ("Short body.", "AVAILABLE"),
            ]

            agent = SilentAuditorAgent(db_path=db_path)
            result = await agent.run()

            assert result["edits_detected"] >= 1

            # Verify silent_edits table has a row
            from db.connection import get_db
            conn = get_db(db_path)
            try:
                rows = conn.execute("SELECT * FROM silent_edits").fetchall()
                assert len(rows) == 1
                assert rows[0]["change_ratio"] > 0.10
                assert rows[0]["stored_body_length"] > 0
            finally:
                conn.close()

    @pytest.mark.asyncio
    async def test_detect_edit_finds_significant_changes(self):
        """The diff helper correctly identifies edits above threshold."""
        from pipeline.agent4_silent import _detect_edit

        # Identical text → no edit
        is_edit, ratio = _detect_edit("hello world", "hello world")
        assert is_edit is False
        assert ratio == 0.0

        # Minor change (one word) → no edit (below 10%)
        is_edit, ratio = _detect_edit("hello world", "hello world!")
        assert is_edit is False

        # Major change → edit detected
        is_edit, ratio = _detect_edit(
            "The president signed the bill.",
            "The president vetoed the bill after a long debate.",
        )
        assert is_edit is True
        assert ratio > 0.10

        # Completely different → edit detected
        is_edit, ratio = _detect_edit(
            "Original story about climate change legislation.",
            "Updated: Market rally continues as tech stocks surge.",
        )
        assert is_edit is True
        assert ratio > 0.10

    @pytest.mark.asyncio
    async def test_detect_edit_empty_bodies(self):
        """Edge case: empty strings on one or both sides."""
        from pipeline.agent4_silent import _detect_edit

        # Empty stored, non-empty fetched → edit
        is_edit, ratio = _detect_edit("", "new content")
        assert is_edit is True
        assert ratio == 1.0

        # Non-empty stored, empty fetched → edit (article removed?)
        is_edit, ratio = _detect_edit("old content", "")
        assert is_edit is True
        assert ratio == 1.0

        # Both empty → no edit
        is_edit, ratio = _detect_edit("", "")
        assert is_edit is False
        assert ratio == 0.0
