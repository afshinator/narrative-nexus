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
        agent = IntakeClusteringAgent()
        assert isinstance(agent, BasePipelineAgent)

    def test_forensic_agent_instantiates(self):
        agent = ForensicExtractionAgent()
        assert isinstance(agent, BasePipelineAgent)

    def test_consensus_agent_instantiates(self):
        agent = ConsensusAlignmentAgent()
        assert isinstance(agent, BasePipelineAgent)

    def test_silent_agent_instantiates(self):
        agent = SilentAuditorAgent()
        assert isinstance(agent, BasePipelineAgent)


class TestIntakeClusteringAgent:
    @pytest.mark.asyncio
    async def test_run_returns_list(self):
        agent = IntakeClusteringAgent()
        result = await agent.run()
        assert isinstance(result, list)
        assert result == []

    @pytest.mark.asyncio
    async def test_run_accepts_article_texts(self):
        agent = IntakeClusteringAgent()
        result = await agent.run(article_texts=["text1", "text2"])
        assert isinstance(result, list)


class TestForensicExtractionAgent:
    @pytest.mark.asyncio
    async def test_run_returns_list(self):
        agent = ForensicExtractionAgent()
        result = await agent.run()
        assert isinstance(result, list)
        assert result == []

    @pytest.mark.asyncio
    async def test_run_accepts_article_texts(self):
        agent = ForensicExtractionAgent()
        result = await agent.run(article_texts=["text"])
        assert isinstance(result, list)


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
    async def test_run_returns_list(self):
        agent = SilentAuditorAgent()
        result = await agent.run()
        assert isinstance(result, list)
        assert result == []

    @pytest.mark.asyncio
    async def test_run_accepts_article_ids(self):
        agent = SilentAuditorAgent()
        result = await agent.run(article_ids=[1, 2, 3])
        assert isinstance(result, list)


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
