"""Tests for pipeline.agent2_forensic — LLM extraction + claim insert."""
import json
import pytest
import tempfile
import os
from unittest.mock import AsyncMock, MagicMock, patch

from db.connection import init_db, get_db
from db.sources import insert_source
from db.clusters import create_cluster
from db.articles import insert_article
from db.claims import list_claims


# ── Fixtures ────────────────────────────────────────────────────────────

LLM_PROVIDER = {
    "id": "opencode",
    "name": "OpenCode Zen",
    "model": "deepseek-v4-flash-free",
    "amd": False,
}


@pytest.fixture
def db_path():
    """Temp DB with source, article, and cluster ready for extraction."""
    path = tempfile.mktemp(suffix=".db")
    init_db(path)
    conn = get_db(path)
    try:
        s1 = insert_source(conn, name="Reuters", domain="reuters.com", tier=1)
        a1 = insert_article(conn, source_id=s1, url="http://r.com/1",
                            title="Test Article",
                            body="The president signed a landmark climate bill today.")
        c1 = create_cluster(conn, vertical="geopolitics", title="Test Cluster")
        conn.commit()
    finally:
        conn.close()
    yield path, a1, c1
    os.unlink(path)


# ── ForensicExtractionAgent ──────────────────────────────────────────────


class TestForensicExtractionAgent:
    def test_agent_takes_db_path_and_provider(self):
        from pipeline.agent2_forensic import ForensicExtractionAgent
        agent = ForensicExtractionAgent(
            db_path=":memory:",
            llm_provider=LLM_PROVIDER,
            api_key="test-key",
        )
        assert agent.db_path == ":memory:"

    @pytest.mark.asyncio
    async def test_run_extracts_claims(self, db_path):
        """End-to-end: reads articles → calls LLM → inserts claims."""
        db_file, article_id, cluster_id = db_path

        # Mock the LLM to return structured JSON (batched format)
        mock_response = json.dumps({
            "results": [
                {"article_id": article_id, "claims": [
                    {"text": "The president signed a climate bill",
                     "entities": ["president", "climate bill"]},
                    {"text": "The bill was landmark legislation",
                     "entities": ["bill"]},
                ]}
            ]
        })

        with patch("pipeline.agent2_forensic.LLMClient") as mock_llm_cls:
            mock_client = mock_llm_cls.return_value
            mock_client.chat = AsyncMock(return_value=mock_response)

            from pipeline.agent2_forensic import ForensicExtractionAgent
            agent = ForensicExtractionAgent(
                db_path=db_file,
                llm_provider=LLM_PROVIDER,
                api_key="test-key",
            )
            # Override article_map so Agent 2 knows which articles to process
            result = await agent.run(
                article_map={article_id: cluster_id}
            )

            assert result["claims_extracted"] == 2
            assert result["articles_processed"] == 1

            # Verify claims were inserted
            conn = get_db(db_file)
            try:
                claims = list_claims(conn, cluster_id=cluster_id)
                assert len(claims) == 2
                assert claims[0]["state"] == "PENDING"
            finally:
                conn.close()

    @pytest.mark.asyncio
    async def test_run_handles_malformed_json(self, db_path):
        """Malformed JSON from LLM — agent should log and return 0 claims."""
        db_file, article_id, cluster_id = db_path

        with patch("pipeline.agent2_forensic.LLMClient") as mock_llm_cls:
            mock_client = mock_llm_cls.return_value
            mock_client.chat = AsyncMock(return_value="not valid json {{")

            from pipeline.agent2_forensic import ForensicExtractionAgent
            agent = ForensicExtractionAgent(
                db_path=db_file,
                llm_provider=LLM_PROVIDER,
                api_key="test-key",
            )
            result = await agent.run(
                article_map={article_id: cluster_id}
            )

            assert result["claims_extracted"] == 0
            assert result["articles_processed"] == 0  # article skipped entirely

    @pytest.mark.asyncio
    async def test_run_skips_articles_without_cluster(self, db_path):
        """Articles not in article_map are skipped."""
        db_file, article_id, cluster_id = db_path

        with patch("pipeline.agent2_forensic.LLMClient") as mock_llm_cls:
            mock_client = mock_llm_cls.return_value
            mock_client.chat = AsyncMock()

            from pipeline.agent2_forensic import ForensicExtractionAgent
            agent = ForensicExtractionAgent(
                db_path=db_file,
                llm_provider=LLM_PROVIDER,
                api_key="test-key",
            )
            # Empty article_map → no articles processed
            result = await agent.run(article_map={})

            assert result["claims_extracted"] == 0
            mock_client.chat.assert_not_called()

    @pytest.mark.asyncio
    async def test_run_handles_empty_claims_array(self, db_path):
        """LLM returns valid JSON but with empty claims array."""
        db_file, article_id, cluster_id = db_path

        mock_response = json.dumps({"results": [{"article_id": article_id, "claims": []}]})
        with patch("pipeline.agent2_forensic.LLMClient") as mock_llm_cls:
            mock_client = mock_llm_cls.return_value
            mock_client.chat = AsyncMock(return_value=mock_response)

            from pipeline.agent2_forensic import ForensicExtractionAgent
            agent = ForensicExtractionAgent(
                db_path=db_file,
                llm_provider=LLM_PROVIDER,
                api_key="test-key",
            )
            result = await agent.run(
                article_map={article_id: cluster_id}
            )

            assert result["claims_extracted"] == 0
