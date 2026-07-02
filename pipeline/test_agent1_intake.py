"""Tests for pipeline.agent1_intake — embeddings + DBSCAN clustering + DB insert."""
import pytest
import tempfile
import os
from unittest.mock import AsyncMock, patch

from db.connection import init_db, get_db
from db.sources import insert_source
from db.articles import insert_article
from db.clusters import list_clusters

# ── Check sentence-transformers availability ──
_sent_trans_available = True
try:
    from sentence_transformers import SentenceTransformer  # noqa: F401
except ImportError:
    _sent_trans_available = False


# ── Fixtures ────────────────────────────────────────────────────────────

LOCAL_CPU_PROVIDER = {
    "id": "local-cpu",
    "name": "Local CPU",
    "model": "all-MiniLM-L6-v2",
    "amd": False,
}


@pytest.fixture
def db_path():
    """Temp DB with sources and articles, no claims yet."""
    path = tempfile.mktemp(suffix=".db")
    init_db(path)
    conn = get_db(path)
    try:
        s1 = insert_source(conn, name="Reuters", domain="reuters.com", tier=1)
        s2 = insert_source(conn, name="BBC", domain="bbc.com", tier=2)
        # Articles with real-ish titles for clustering
        insert_article(conn, source_id=s1, url="http://r.com/1",
                       title="Climate bill signed into law", body="Climate legislation passes.")
        insert_article(conn, source_id=s1, url="http://r.com/2",
                       title="Congress approves climate legislation", body="Environmental bill advances.")
        insert_article(conn, source_id=s2, url="http://b.com/1",
                       title="Lakers beat Celtics in overtime", body="NBA finals game 7 thriller.")
        insert_article(conn, source_id=s2, url="http://b.com/2",
                       title="Celtics fall to Lakers in finals", body="Boston loses dramatic game.")
        # Article with no body (BODY_UNAVAILABLE)
        insert_article(conn, source_id=s1, url="http://r.com/3",
                       title="Empty article", body="",
                       body_status="BODY_UNAVAILABLE")
        conn.commit()
    finally:
        conn.close()
    yield path
    os.unlink(path)


# ── IntakeClusteringAgent ────────────────────────────────────────────────


class TestIntakeClusteringAgent:
    def test_agent_takes_db_path_and_provider(self):
        from pipeline.agent1_intake import IntakeClusteringAgent
        agent = IntakeClusteringAgent(
            db_path=":memory:",
            embedding_provider=LOCAL_CPU_PROVIDER,
        )
        assert agent.db_path == ":memory:"
        assert agent._embedding_provider["id"] == "local-cpu"

    @pytest.mark.asyncio
    @pytest.mark.skipif(not _sent_trans_available, reason="sentence-transformers not installed")
    async def test_run_returns_clusters_and_mapping(self, db_path):
        """End-to-end: embeddings → DBSCAN → DB insert."""
        from pipeline.agent1_intake import IntakeClusteringAgent

        agent = IntakeClusteringAgent(
            db_path=db_path,
            embedding_provider=LOCAL_CPU_PROVIDER,
        )
        result = await agent.run()

        assert "clusters" in result
        assert "articles_clustered" in result
        assert "article_map" in result

    @pytest.mark.asyncio
    @pytest.mark.skipif(not _sent_trans_available, reason="sentence-transformers not installed")
    async def test_run_creates_clusters_in_db(self, db_path):
        """Clusters are actually persisted."""
        from pipeline.agent1_intake import IntakeClusteringAgent

        agent = IntakeClusteringAgent(
            db_path=db_path,
            embedding_provider=LOCAL_CPU_PROVIDER,
        )
        await agent.run()

        conn = get_db(db_path)
        try:
            clusters = list_clusters(conn)
            assert len(clusters) >= 1
            # ponytail: vertical is now classifier-driven, not hardcoded
            from pipeline.vertical_classifier import get_vertical_list
            valid_verticals = set(get_vertical_list())
            assert all(c["vertical"] in valid_verticals for c in clusters)
        finally:
            conn.close()

    @pytest.mark.asyncio
    @pytest.mark.skipif(not _sent_trans_available, reason="sentence-transformers not installed")
    async def test_run_skips_body_unavailable_articles(self, db_path):
        """Articles with body_status='BODY_UNAVAILABLE' are skipped."""
        from pipeline.agent1_intake import IntakeClusteringAgent

        agent = IntakeClusteringAgent(
            db_path=db_path,
            embedding_provider=LOCAL_CPU_PROVIDER,
        )
        result = await agent.run()

        # Only 4 articles have bodies; the 5th (BODY_UNAVAILABLE) is excluded
        assert result["articles_clustered"] <= 4

    @pytest.mark.asyncio
    async def test_run_empty_db_returns_empty(self):
        """Clean DB with no articles returns empty result."""
        path = tempfile.mktemp(suffix=".db")
        init_db(path)
        try:
            from pipeline.agent1_intake import IntakeClusteringAgent

            agent = IntakeClusteringAgent(
                db_path=path,
                embedding_provider=LOCAL_CPU_PROVIDER,
            )
            result = await agent.run()
            assert result["clusters"] == 0
            assert result["articles_clustered"] == 0
            assert result["article_map"] == {}
        finally:
            os.unlink(path)

    @pytest.mark.asyncio
    @pytest.mark.skipif(not _sent_trans_available, reason="sentence-transformers not installed")
    async def test_run_assigns_geopolitics_vertical(self, db_path):
        """All clusters are geopolitics (ponytail: hardcoded until vertical classifier)."""
        from pipeline.agent1_intake import IntakeClusteringAgent

        agent = IntakeClusteringAgent(
            db_path=db_path,
            embedding_provider=LOCAL_CPU_PROVIDER,
        )
        await agent.run()

        conn = get_db(db_path)
        try:
            clusters = list_clusters(conn)
            assert len(clusters) >= 1
            # ponytail: vertical is now classifier-driven, not hardcoded
            from pipeline.vertical_classifier import get_vertical_list
            valid_verticals = set(get_vertical_list())
            assert all(c["vertical"] in valid_verticals for c in clusters)
        finally:
            conn.close()
