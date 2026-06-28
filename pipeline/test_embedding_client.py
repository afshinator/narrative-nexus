"""Tests for pipeline.embedding_client — local + API embedding providers."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from pipeline.embedding_client import EmbeddingClient, EmbeddingError


# ── Fixtures ────────────────────────────────────────────────────────────

LOCAL_CPU_PROVIDER = {
    "id": "local-cpu",
    "name": "Local CPU",
    "model": "all-MiniLM-L6-v2",
    "amd": False,
}

FIREWORKS_EMBEDDING_PROVIDER = {
    "id": "fireworks",
    "name": "Fireworks AI",
    "model": "nomic-ai/nomic-embed-text-v1.5",
    "amd": True,
}

OPENAI_EMBEDDING_PROVIDER = {
    "id": "openai",
    "name": "OpenAI",
    "model": "text-embedding-3-small",
    "amd": False,
}


# ── EmbeddingClient init ─────────────────────────────────────────────────


class TestEmbeddingClientInit:
    def test_local_cpu_requires_no_api_key(self):
        """local-cpu uses sentence-transformers, no API key needed."""
        client = EmbeddingClient(LOCAL_CPU_PROVIDER)
        assert client.provider_id == "local-cpu"
        assert client.model == "all-MiniLM-L6-v2"

    def test_api_provider_requires_key(self):
        with pytest.raises(ValueError, match="API key"):
            EmbeddingClient(FIREWORKS_EMBEDDING_PROVIDER, api_key="")

    def test_opencode_embeddings_raises(self):
        """OpenCode Zen does not support embeddings (verified 404)."""
        opencode = {"id": "opencode", "name": "OpenCode Zen",
                     "model": "all-MiniLM-L6-v2", "amd": False}
        with pytest.raises(EmbeddingError, match="OpenCode Zen"):
            EmbeddingClient(opencode, api_key="k")


# ── EmbeddingClient.embed (local-cpu) ────────────────────────────────────


class TestEmbeddingClientLocalCPU:
    @pytest.mark.asyncio
    async def test_embed_returns_384d_vectors(self):
        """Integration: local sentence-transformers produces 384-dim vectors."""
        client = EmbeddingClient(LOCAL_CPU_PROVIDER)
        result = await client.embed(["hello world", "test embedding"])
        assert len(result) == 2
        assert len(result[0]) == 384
        assert len(result[1]) == 384

    @pytest.mark.asyncio
    async def test_embed_returns_floats(self):
        client = EmbeddingClient(LOCAL_CPU_PROVIDER)
        result = await client.embed(["text"])
        assert all(isinstance(v, float) for v in result[0])

    @pytest.mark.asyncio
    async def test_embed_single_text(self):
        client = EmbeddingClient(LOCAL_CPU_PROVIDER)
        result = await client.embed(["single"])
        assert len(result) == 1
        assert len(result[0]) == 384

    @pytest.mark.asyncio
    async def test_embed_empty_list(self):
        client = EmbeddingClient(LOCAL_CPU_PROVIDER)
        result = await client.embed([])
        assert result == []


# ── EmbeddingClient.embed (API providers) ────────────────────────────────


class TestEmbeddingClientAPI:
    @pytest.mark.asyncio
    async def test_embed_calls_openai_api(self):
        """API providers use openai.AsyncOpenAI.embeddings.create."""
        with patch("pipeline.embedding_client.openai.AsyncOpenAI") as mock_cls:
            mock_instance = mock_cls.return_value
            mock_embeddings = AsyncMock()
            mock_instance.embeddings.create = mock_embeddings
            mock_embeddings.return_value.data = [
                MagicMock(embedding=[0.1, 0.2, 0.3]),
                MagicMock(embedding=[0.4, 0.5, 0.6]),
            ]

            client = EmbeddingClient(FIREWORKS_EMBEDDING_PROVIDER, api_key="k")
            result = await client.embed(["hello", "world"])

            assert len(result) == 2
            assert result[0] == [0.1, 0.2, 0.3]
            assert result[1] == [0.4, 0.5, 0.6]

            # Verify correct model was passed
            call_kwargs = mock_embeddings.call_args.kwargs
            assert call_kwargs["model"] == "nomic-ai/nomic-embed-text-v1.5"
            assert call_kwargs["input"] == ["hello", "world"]
