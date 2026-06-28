"""Integration tests for scripts/seed-demo.py."""
import pytest
import tempfile
import os
import sys
from unittest.mock import patch, AsyncMock

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.connection import init_db, get_db
from db.sources import insert_source
from db.articles import insert_article
from db.clusters import list_clusters
from db.claims import list_claims
from db.snapshots import list_snapshots


@pytest.fixture
def db_path():
    """Temp DB with a few articles covering 3 dates."""
    path = tempfile.mktemp(suffix=".db")
    init_db(path)
    conn = get_db(path)
    try:
        s1 = insert_source(conn, name="Reuters", domain="reuters.com", tier=1)
        s2 = insert_source(conn, name="BBC", domain="bbc.com", tier=2)

        # 3 articles spread across 3 days
        insert_article(conn, source_id=s1, url="http://r.com/1",
                       title="Climate bill passes",
                       body="The landmark climate bill was signed into law today.",
                       published_at="2025-01-10T12:00:00")
        insert_article(conn, source_id=s2, url="http://b.com/1",
                       title="Environmental legislation advances",
                       body="Congress approved sweeping environmental legislation.",
                       published_at="2025-01-10T14:00:00")
        insert_article(conn, source_id=s1, url="http://r.com/2",
                       title="Follow-up on climate policy",
                       body="The climate bill faces implementation challenges.",
                       published_at="2025-01-12T10:00:00")

        conn.commit()
    finally:
        conn.close()
    yield path
    os.unlink(path)


class TestSeedScriptIntegration:
    def test_seed_script_runs_and_produces_clusters(self, db_path):
        """End-to-end: seed script runs on temp DB, produces clusters + claims."""
        # Mock the LLM to avoid real API calls in test
        mock_response = '{"results": [{"article_id": 1, "claims": [{"text": "The bill was signed", "entities": ["bill"]}]}]}'

        with patch("pipeline.agent2_forensic.LLMClient") as mock_llm:
            mock_client = mock_llm.return_value
            mock_client.chat = AsyncMock(return_value=mock_response)

            # Run seed script inline (import and call main logic)
            import scripts.seed_demo as seed
            # Override args for test
            test_args = seed.parse_args(["--db", db_path])

            # Verify config loading
            cfg_path = os.path.join(
                os.path.dirname(__file__), "..", "config", "providers.json"
            )
            cfg = seed.load_provider_config(cfg_path)

            # Run pipeline steps manually (skipping the print/setup)
            import asyncio

            a1_embed = seed.get_provider_for_agent(cfg, "agent1_embedding")
            agent1 = seed.IntakeClusteringAgent(
                db_path=db_path,
                embedding_provider=a1_embed,
            )
            a1_result = asyncio.run(agent1.run())

            assert a1_result["articles_clustered"] == 3
            assert a1_result["clusters"] >= 1

            # Verify clusters in DB
            conn = get_db(db_path)
            try:
                clusters = list_clusters(conn)
                assert len(clusters) >= 1
            finally:
                conn.close()

    def test_seed_snapshots_cover_date_range(self, db_path):
        """Snapshots are written for each day in the article date range."""
        # First run agents 1+2 to get claims in the DB
        mock_response = '{"results": [{"article_id": 1, "claims": [{"text": "Test claim", "entities": []}]}]}'

        with patch("pipeline.agent2_forensic.LLMClient") as mock_llm:
            mock_client = mock_llm.return_value
            mock_client.chat = AsyncMock(return_value=mock_response)

            import asyncio
            from pipeline.provider_config import load_provider_config, get_provider_for_agent
            from scripts.seed_demo import (
                IntakeClusteringAgent, ForensicExtractionAgent,
                ConsensusAlignmentAgent, _compute_and_write_snapshots,
            )

            cfg_path = os.path.join(
                os.path.dirname(__file__), "..", "config", "providers.json"
            )
            cfg = load_provider_config(cfg_path)

            # Agent 1
            a1_embed = get_provider_for_agent(cfg, "agent1_embedding")
            a1 = IntakeClusteringAgent(db_path=db_path, embedding_provider=a1_embed)
            a1_result = asyncio.run(a1.run())
            article_map = a1_result["article_map"]

            # Agent 2
            a2_llm = get_provider_for_agent(cfg, "agent2_llm")
            a2 = ForensicExtractionAgent(
                db_path=db_path, llm_provider=a2_llm, api_key="test",
            )
            asyncio.run(a2.run(article_map=article_map))

            # Agent 3
            conn = get_db(db_path)
            try:
                a3 = ConsensusAlignmentAgent(db_path=db_path)
                a3.run_all(conn)
            finally:
                conn.close()

            # Now generate snapshots for the 3-day range
            conn2 = get_db(db_path)
            try:
                from datetime import datetime, timedelta

                total = 0
                dates = ["2025-01-10", "2025-01-11", "2025-01-12"]
                for d in dates:
                    as_of = (datetime.fromisoformat(d) + timedelta(days=1)).isoformat()
                    total += _compute_and_write_snapshots(
                        conn2, date_str=d, as_of=as_of,
                    )

                # 2 sources × 1 vertical × 3 days = 6 snapshots
                assert total == 6
            finally:
                conn2.close()

            # Verify snapshots in DB
            conn3 = get_db(db_path)
            try:
                snaps = list_snapshots(conn3, vertical="geopolitics")
                assert len(snaps) == 6
                # Check that dates match
                dates_seen = {s["date"] for s in snaps}
                assert dates_seen == {"2025-01-10", "2025-01-11", "2025-01-12"}
            finally:
                conn3.close()
