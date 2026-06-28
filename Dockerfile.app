# Narrative Nexus — App Container
# FastAPI server + frontend static serving + pipeline execution
# No GPU required (REQ-108)
#
# All 4 pipeline agents run in this container:
#   Agent 1 — sentence-transformers embeddings (CPU, all-MiniLM-L6-v2)
#   Agent 2 — LLM extraction (configurable provider)
#   Agent 3 — consensus math (pure Python)
#   Agent 4 — silent auditor (text diff, stdlib)
#
# The worker container is optional (--profile gpu) and only needed
# when embedding workloads run on an AMD GPU pod via ROCm.

FROM python:3.12-slim

WORKDIR /app

# ── Install Python dependencies ────────────────────────────────────────
# sentence-transformers pulls PyTorch (~2GB) — acceptable for hackathon.
# Production: split embeddings into the GPU worker container.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Copy application modules ───────────────────────────────────────────
COPY app/     ./app/
COPY db/      ./db/
COPY pipeline/ ./pipeline/
COPY config/  ./config/

# ── Copy frontend build ────────────────────────────────────────────────
# Must run `npm run build` BEFORE `docker compose build`.
COPY dist/    ./dist/

# ── Create data directory for SQLite ───────────────────────────────────
RUN mkdir -p /data

EXPOSE 8000

# ponytail: NN_DB_PATH points to the volume-mounted /data directory.
# OPENCODE_API_KEY must be set in the environment (or via .env file).
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
