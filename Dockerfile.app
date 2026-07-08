# Narrative Nexus — App Container (Multi-Stage)
# Stage 1: Node — frontend build (npm ci + vite build)
# Stage 2: Python — FastAPI server + baked demo DB
# No GPU required (REQ-108)
#
# All 4 pipeline agents run in this container when pipeline is enabled:
#   Agent 1 — sentence-transformers embeddings (CPU, all-MiniLM-L6-v2)
#   Agent 2 — LLM extraction (configurable provider)
#   Agent 3 — consensus math (pure Python)
#   Agent 4 — silent auditor (text diff, stdlib)
#
# The worker container is optional (--profile gpu) and only needed
# when embedding workloads run on an AMD GPU pod via ROCm.

# ── Stage 1: Frontend build ─────────────────────────────────────────────
FROM node:20-slim AS frontend

WORKDIR /app

# Install dependencies (layer cache: only re-runs when package*.json changes)
COPY package.json package-lock.json ./
RUN npm ci

# Copy build config and source
COPY tsconfig.json tsconfig.app.json tsconfig.node.json vite.config.ts ./
COPY index.html ./
COPY components.json ./
COPY src/ ./src/
COPY public/ ./public/

# Build frontend (tsc + vite build → dist/)
RUN npm run build


# ── Stage 2: Python production image ────────────────────────────────────
FROM python:3.12-slim

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application modules
COPY app/      ./app/
COPY db/       ./db/
COPY pipeline/ ./pipeline/
COPY config/   ./config/

# Copy frontend build from Stage 1 (self-sufficient — no pre-build step needed)
COPY --from=frontend /app/dist/ ./dist/

# Bake the golden demo database into the image
# VOLUME/COPY INTERACTION: docker-compose.yml does NOT mount a volume at /data
# for the app service (the nn-data volume is only on the db service).
# Because no volume shadows /data, the baked COPY is visible at runtime.
RUN mkdir -p /data
COPY data/demo/demo.db /data/nn.db

# T1: baked read-only sentinel — disables scraper in deployed instances
RUN touch /app/.readonly

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
