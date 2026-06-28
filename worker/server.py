"""Worker embedding server — sentence-transformers on CPU or AMD GPU (ROCm).

Started by: docker compose --profile gpu up worker

ponytail: Minimal FastAPI server. One endpoint. Loads model at startup.
Production: add health check endpoint, model warm-up, batch processing.
"""

from fastapi import FastAPI
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer

# ── Model loaded once at startup ───────────────────────────────────────
MODEL_NAME = "all-MiniLM-L6-v2"  # 384-dim, VRAM-light (<2GB)
model = SentenceTransformer(MODEL_NAME)

app = FastAPI(title="Narrative Nexus Worker")


class EmbedRequest(BaseModel):
    texts: list[str]


class EmbedResponse(BaseModel):
    embeddings: list[list[float]]


@app.post("/embed", response_model=EmbedResponse)
def embed(request: EmbedRequest) -> EmbedResponse:
    """Generate sentence-transformer embeddings for a list of texts."""
    vectors = model.encode(request.texts, show_progress_bar=False)
    return EmbedResponse(embeddings=vectors.tolist())


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "model": MODEL_NAME}
