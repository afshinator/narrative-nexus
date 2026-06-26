"""HTTP client for the worker container (sentence-transformers embeddings).

Per ADR-0003, the worker is a thin HTTP server on port 8001 running
sentence-transformers on AMD GPU via ROCm. The app sends raw text and
receives embedding vectors back."""

import httpx


class WorkerClient:
    """Stub client for the sentence-transformers worker.

    Returns zero-vectors until the worker container is deployed.
    Shape: [len(texts), 384] (all-MiniLM-L6-v2 default dimension).
    """

    def __init__(self, base_url: str = "http://worker:8001"):
        self.base_url = base_url
        self._client = httpx.AsyncClient(base_url=base_url)

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a list of texts.

        Stub: returns zero vectors of dimension 384.
        Real implementation: POST /embed with JSON body {"texts": [...]}
        """
        _ = texts  # unused in stub
        return [[0.0] * 384 for _ in texts]

    async def health(self) -> bool:
        """Check if the worker is reachable. Stub: returns False."""
        try:
            resp = await self._client.get("/health", timeout=5.0)
            return resp.status_code == 200
        except Exception:
            return False

    async def close(self) -> None:
        await self._client.aclose()
