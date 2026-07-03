"""Provider-agnostic embedding client — local CPU or API-based embeddings.

Two code paths:
  local-cpu → sentence-transformers (all-MiniLM-L6-v2, 384-dim)
  fireworks / openai → openai.AsyncOpenAI.embeddings API
  opencode → NOT SUPPORTED (OpenCode Zen has no /embeddings endpoint)

Usage:
  provider = get_provider_for_agent(cfg, "agent1_embedding")
  client = EmbeddingClient(provider)
  vectors = await client.embed(["article text 1", "article text 2"])
  # vectors: [[float, ...], [float, ...]] — 384-dim per text
"""
import os
import logging
from typing import Any

import numpy as np
import openai

logger = logging.getLogger("narrative_nexus.embeddings")

# ── Provider categories ──────────────────────────────────────────────────

# Providers that use sentence-transformers locally (no API call)
_LOCAL_PROVIDERS = {"local-cpu"}

# Providers that use openai.AsyncOpenAI.embeddings
_API_PROVIDERS = {"fireworks", "openai"}

# Providers that are known NOT to support embeddings
_UNSUPPORTED_EMBEDDING_PROVIDERS = {"opencode", "deepseek"}

# ── Model dimension lookup (Phase 2 — T2c) ──────────────────────────────

# Known dimensions for embedding models. Used to validate cached embeddings
# and prevent cross-model dimension mismatch.
MODEL_DIMS: dict[str, int] = {
    "all-MiniLM-L6-v2": 384,
    "nomic-ai/nomic-embed-text-v1.5": 768,
    "BAAI/bge-base-en-v1.5": 768,
    "BAAI/bge-small-en-v1.5": 384,
    "thenlper/gte-large": 1024,
    "thenlper/gte-base": 768,
}


# ── Base URLs for API providers ──────────────────────────────────────────

_EMBEDDING_BASE_URLS: dict[str, str] = {
    "fireworks": "https://api.fireworks.ai/inference/v1",
    "openai": "https://api.openai.com/v1",
}


class EmbeddingError(Exception):
    """Raised when embeddings cannot be generated (unsupported provider, etc.)."""


class EmbeddingClient:
    """Async embedding client — local sentence-transformers or remote API.

    The model is loaded lazily on first embed() call for local-cpu.  API
    providers use openai.AsyncOpenAI under the hood.

    All providers produce 384-dim vectors (all-MiniLM-L6-v2 dimension).
    API providers may return different dimensions depending on the model,
    but callers should expect 384-dim as the default.
    """

    def __init__(self, provider: dict[str, Any], *, api_key: str = ""):
        """Create an embedding client for a given provider.

        Args:
          provider: Dict with id, name, model fields.
          api_key: Required for API providers, ignored for local-cpu.

        Raises:
          EmbeddingError: if the provider doesn't support embeddings.
          ValueError: if api_key is missing for an API provider.
        """
        import os

        self.provider_id: str = provider["id"]
        self.model: str = provider["model"]
        self.provider_name: str = provider["name"]
        self._api_key: str = api_key

        if self.provider_id in _UNSUPPORTED_EMBEDDING_PROVIDERS:
            raise EmbeddingError(
                f"{self.provider_name} does not support embeddings. "
                f"Use local-cpu, fireworks, or openai instead."
            )

        if self.provider_id in _API_PROVIDERS:
            if not api_key:
                env_name = f"{self.provider_id.upper()}_API_KEY"
                api_key = os.environ.get(env_name, "")
            if not api_key:
                raise ValueError(
                    f"No API key for embedding provider {self.provider_id!r}. "
                    f"Set {self.provider_id.upper()}_API_KEY or pass api_key=."
                )
            self._api_key = api_key
            # Defer openai import until needed
            self._openai_client = None

        # For local-cpu: model loaded lazily on first embed()
        self._local_model = None

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a list of text strings.

        Returns a list of float vectors, one per input text.  Empty input
        returns an empty list.  All vectors have the same dimension.

        Phase 2 D1b: prepends "clustering: " for nomic models per
        nomic-embed-text-v1 training spec. Without this task disambiguator,
        vectors encode generic news-article style rather than topic-specific
        similarity — causing all articles to merge into one mega-cluster.
        """
        if not texts:
            return []

        # D1b: nomic models need "clustering: " prefix for topic separation
        if "nomic" in self.model.lower():
            texts = [f"clustering: {t}" for t in texts]

        if self.provider_id in _LOCAL_PROVIDERS:
            return await self._embed_local(texts)

        if self.provider_id in _API_PROVIDERS:
            return await self._embed_api(texts)

        raise EmbeddingError(
            f"Unknown embedding provider: {self.provider_id!r}"
        )

    # ── Local path (sentence-transformers) ────────────────────────────

    async def _embed_local(self, texts: list[str]) -> list[list[float]]:
        """Run sentence-transformers locally on CPU."""
        if self._local_model is None:
            # Lazy import + load — only happens once, ~1.3s cold start
            from sentence_transformers import SentenceTransformer
            self._local_model = SentenceTransformer(self.model)

        # sentence-transformers encode is synchronous, runs in caller's thread.
        # Wrapped in an async method so the interface is uniform.
        embeddings: np.ndarray = self._local_model.encode(
            texts,
            show_progress_bar=False,
        )
        return embeddings.tolist()

    # ── API path (openai embeddings) ──────────────────────────────────

    async def _embed_api(self, texts: list[str]) -> list[list[float]]:
        """Call the provider's embeddings API via openai.AsyncOpenAI."""
        if self._openai_client is None:
            base_url = _EMBEDDING_BASE_URLS.get(self.provider_id)
            if base_url is None:
                raise EmbeddingError(
                    f"No base URL for embedding provider {self.provider_id!r}"
                )
            self._openai_client = openai.AsyncOpenAI(
                base_url=base_url,
                api_key=self._api_key,
                timeout=30.0,
            )

        # openai embeddings API accepts up to ~2048 tokens per input string,
        # batches of up to 2048 texts.  For hackathon scale we send all at once.
        response = await self._openai_client.embeddings.create(
            model=self.model,
            input=texts,
        )
        # T3: log embedding usage (input count; API may not return token counts)
        logger.info(
            "embedding_call provider=%s model=%s input_count=%d",
            self.provider_id, self.model, len(texts),
        )
        return [d.embedding for d in response.data]
