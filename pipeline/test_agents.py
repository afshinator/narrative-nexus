"""Tests for pipeline agents — imports, instantiation, stub return types."""

import pytest
from pipeline.base_agent import BasePipelineAgent
from pipeline.agent1_intake import IntakeClusteringAgent
from pipeline.agent2_forensic import ForensicExtractionAgent
from pipeline.agent3_consensus import ConsensusAlignmentAgent
from pipeline.agent4_silent import SilentAuditorAgent
from pipeline.worker_client import WorkerClient


class TestAgentImports:
    def test_base_agent_is_abstract(self):
        with pytest.raises(TypeError):
            BasePipelineAgent()  # cannot instantiate ABC

    def test_intake_agent_instantiates(self):
        agent = IntakeClusteringAgent(db_path=":memory:",
                                      embedding_provider={"id": "local-cpu", "name": "Local CPU", "model": "all-MiniLM-L6-v2", "amd": False})
        assert isinstance(agent, BasePipelineAgent)

    def test_forensic_agent_instantiates(self):
        agent = ForensicExtractionAgent(db_path=":memory:",
                                        llm_provider={"id": "opencode", "name": "OpenCode Zen", "model": "deepseek-v4-flash-free", "amd": False},
                                        api_key="test")
        assert isinstance(agent, BasePipelineAgent)

    def test_consensus_agent_instantiates(self):
        agent = ConsensusAlignmentAgent()
        assert isinstance(agent, BasePipelineAgent)

    def test_silent_agent_instantiates(self):
        agent = SilentAuditorAgent(db_path=":memory:")
        assert isinstance(agent, BasePipelineAgent)


class TestIntakeClusteringAgent:
    @pytest.mark.asyncio
    async def test_run_returns_dict(self):
        """New Agent 1 returns dict with clusters/article_map, not list."""
        import tempfile, os
        from db.connection import init_db
        path = tempfile.mktemp(suffix=".db")
        init_db(path)
        try:
            agent = IntakeClusteringAgent(db_path=path,
                                          embedding_provider={"id": "local-cpu", "name": "Local CPU", "model": "all-MiniLM-L6-v2", "amd": False})
            result = await agent.run()
            assert isinstance(result, dict)
            assert result == {"clusters": 0, "articles_clustered": 0, "article_map": {}}
        finally:
            os.unlink(path)


class TestForensicExtractionAgent:
    @pytest.mark.asyncio
    async def test_run_returns_dict(self):
        """New Agent 2 returns dict with counts, not list."""
        import tempfile, os
        from db.connection import init_db
        path = tempfile.mktemp(suffix=".db")
        init_db(path)
        try:
            agent = ForensicExtractionAgent(db_path=path,
                                            llm_provider={"id": "opencode", "name": "OpenCode Zen", "model": "deepseek-v4-flash-free", "amd": False},
                                            api_key="test")
            result = await agent.run(article_map={})
            assert isinstance(result, dict)
            assert result == {"claims_extracted": 0, "articles_processed": 0}
        finally:
            os.unlink(path)


class TestConsensusAlignmentAgent:
    @pytest.mark.asyncio
    async def test_run_returns_dict(self):
        agent = ConsensusAlignmentAgent()
        result = await agent.run()
        assert isinstance(result, dict)
        assert result["cluster_id"] is None
        assert result["classified"] == 0

    @pytest.mark.asyncio
    async def test_run_accepts_cluster_id(self):
        agent = ConsensusAlignmentAgent()
        result = await agent.run(cluster_id=42)
        assert result["cluster_id"] == 42


class TestSilentAuditorAgent:
    @pytest.mark.asyncio
    async def test_run_returns_dict(self):
        """New Agent 4 returns dict with counts, not list."""
        import tempfile, os
        from db.connection import init_db
        path = tempfile.mktemp(suffix=".db")
        init_db(path)
        try:
            agent = SilentAuditorAgent(db_path=path)
            result = await agent.run()
            assert isinstance(result, dict)
            assert result == {"articles_checked": 0, "edits_detected": 0}
        finally:
            os.unlink(path)


class TestWorkerClient:
    @pytest.mark.asyncio
    async def test_embed_returns_384d_vectors(self):
        client = WorkerClient()
        texts = ["hello world", "test"]
        result = await client.embed(texts)
        assert isinstance(result, list)
        assert len(result) == 2
        assert len(result[0]) == 384
        assert len(result[1]) == 384
        await client.close()

    @pytest.mark.asyncio
    async def test_embed_stub_returns_zeros(self):
        client = WorkerClient()
        result = await client.embed(["text"])
        assert all(v == 0.0 for v in result[0])
        await client.close()

    @pytest.mark.asyncio
    async def test_health_returns_false_in_stub(self):
        client = WorkerClient()
        healthy = await client.health()
        assert healthy is False
        await client.close()
