# Battle Plan: AI Infrastructure for Narrative Nexus

*Three scenarios, one architecture — pick the right provider at startup.*
*Last updated: 2026-06-27*

> **Note:** The spec and design docs still reference specific AMD sources (Fireworks API, GPU pod). Updating them to reflect provider-agnostic selection is covered in `docs/impact-provider-agnostic-architecture.md`. In short: REQ-017 and REQ-018 need broadening, design doc §3/§8/§9 need rewriting. Do this before implementing the provider abstraction layer.

---

## Overview

The system needs two AI capabilities:

| Capability | Used by | What it does |
|-----------|---------|-------------|
| **Text embeddings** | Agent 1 (Intake) | Convert article text to vectors, cluster by semantic similarity |
| **LLM inference** | Agent 2 (Forensic), Agent 4 (Silent) | Extract structured claims from articles, diff article snapshots |

The hackathon flyer promises both an AMD GPU pod (via AMD Developer Cloud) and $50 in Fireworks API credits. This doc covers the ideal split, every fallback option identified through research, and a concrete action plan.

---

## New findings from research

Before the scenarios, two discoveries that change the picture:

### 1. qmd proves local embedding on CPU is real, right now

The `qmd` tool already runs local embeddings on this machine using llama.cpp with GGUF models:

| Component | Model | Size | Runs on |
|-----------|-------|------|---------|
| Embedding | `embeddinggemma-300M-Q8_0` | 328 MB | CPU (no GPU needed) |
| Reranking | `Qwen3-Reranker-0.6B-Q8_0` | 639 MB | CPU |
| Generation | `qmd-query-expansion-1.7B-q4_k_m` | 1.28 GB | CPU |

The infrastructure is already installed (`/home/afshin/.cache/qmd/models/`). This means **we can run embeddings locally on CPU right now** — no API key needed, no GPU required. A 300M embedding model produces 768-dim vectors, runs ~5-10 articles/sec on CPU. At 1,800 articles per poll, that's 3-6 minutes for the full embedding pass — acceptable for a daily cron job.

### 2. We already have an API key and free models

The OpenCode Go provider is authenticated and working (`sk-pbB...`). Through it we have API access to:

**Free models (already available, no billing needed):**
- `deepseek-v4-flash-free` — DeepSeek V4 Flash, 200K context, free tier
- `nemotron-3-ultra-free` — NVIDIA Nemotron 3 Ultra, free tier
- `north-mini-code-free` — Free code completion model
- `mimo-v2.5-free` — Free general model

**Paid models (same API key, likely usage-billed):**
- `deepseek-v4-flash` / `deepseek-v4-pro` — DeepSeek full models
- `gpt-5` series including `gpt-5-codex`, `gpt-5.1-codex`, `gpt-5.4-mini`, `gpt-5.4-nano`
- `gemini-3-flash`, `gemini-3.1-pro`, `gemini-3.5-flash`
- `claude-*` series (haiku, sonnet, opus variants)
- `glm-5`, `glm-5.1`, `glm-5.2`
- `kimi-k2.5`, `kimi-k2.6`
- `qwen3.5-plus`, `qwen3.6-plus`

All accessible via OpenAI-compatible API at `https://opencode.ai/zen/v1` with model name `deepseek-v4-flash-free` etc.

**No embedding models available through OpenCode.** Embeddings must come from elsewhere: OpenAI, Fireworks, or local CPU.

---

## Scenario A — Full AMD hardware (ideal)

**Both AMD GPU pod AND Fireworks API credits are available.**

### Architecture

```
                    ┌──────────────────────┐
                    │    AMD GPU Pod        │
                    │  (ROCm + PyTorch)     │
                    │                       │
                    │ sentence-transformers │
                    │ all-MiniLM-L6-v2      │
                    │  384-dim embeddings   │
                    └──────────┬───────────┘
                               │ HTTP (port 8001)
                               ▼
┌─────────────────────────────────────────────────────┐
│                  App Server (CPU)                    │
│                                                      │
│  Agent 1 (Intake) → calls worker:8001/embed         │
│  Agent 3 (Consensus) → pure Python, no API needed   │
│                                                      │
│  ─── Fireworks API (AMD Instinct hardware) ─────    │
│  Agent 2 (Forensic) → POST chat/completions         │
│  Agent 4 (Silent)   → POST chat/completions         │
└─────────────────────────────────────────────────────┘
```

### GPU pod — what runs there

The worker container (`Dockerfile.worker`) switches to `rocm/pytorch:latest` base image and runs a FastAPI server that loads `sentence-transformers/all-MiniLM-L6-v2`:

```
POST /embed  {"texts": ["...", ...]}  →  [[384 floats], ...]
GET  /health                           →  {"status": "ok"}
```

**Resource usage:** <2GB VRAM, fits any Radeon or Instinct GPU. The model is 80MB.

**Docker changes (from current stub):**

```dockerfile
FROM rocm/pytorch:latest
RUN pip install sentence-transformers fastapi uvicorn
COPY worker/ ./worker/
EXPOSE 8001
CMD ["uvicorn", "worker.server:app", "--host", "0.0.0.0", "--port", "8001"]
```

The `docker-compose.yml` worker service gets:
```yaml
  worker:
    # ...existing config...
    devices:
      - /dev/kfd
      - /dev/dri
    group_add:
      - video
```

### Fireworks — what runs there

Two agents call the Fireworks API. Both use the OpenAI-compatible endpoint:

- **Base URL:** `https://api.fireworks.ai/inference/v1`
- **Auth:** `Authorization: Bearer $FIREWORKS_API_KEY`
- **SDK:** OpenAI Python SDK (`pip install openai`)
- **Recommended model:** `accounts/fireworks/models/deepseek-v3p1` (or evaluate DeepSeek-V4-Pro vs Llama 3.3 70B when key arrives — per design doc §3)

**Agent 2 — Forensic Extraction:**
```
POST /chat/completions
Model: accounts/fireworks/models/deepseek-v3p1
response_format: { type: "json_schema", json_schema: { name: "claim_extraction", ... } }
```
Enforces structured JSON output — no freeform text, only parseable claim arrays.

**Agent 4 — Silent Audit:**
```
POST /chat/completions
Model: accounts/fireworks/models/deepseek-v3p1
```
Takes old body + new body, returns structured diff with significance score.

---

## Scenario B — Fireworks only, no GPU pod

**Fireworks credits arrive but AMD Developer Cloud has no available GPUs.** This is where we stand right now.

### Architecture

```
  Agent 1 (Intake) → Fireworks /v1/embeddings → all-MiniLM-L6-v2 or nomic-embed-text-v1.5
  Agent 2 (Forensic) → Fireworks /v1/chat/completions
  Agent 4 (Silent)   → Fireworks /v1/chat/completions
  Worker container → removed or repurposed
```

### Changes needed

1. **`pipeline/worker_client.py`** — Replace local HTTP stub with Fireworks API call
2. **`Dockerfile.worker`** — No longer needed for production
3. **`requirements.txt`** — Add `openai`
4. **Cost:** ~$0.07/poll for embeddings ($50 credits = ~700 polls)

**Fireworks also hosts `sentence-transformers/all-MiniLM-L6-v2`** on their API. Same model as the GPU pod plan.

---

## Scenario C — Total fallback (worst case)

**Neither AMD GPU credits nor Fireworks credits arrive until on-site day.**

This is where research paid off: we have options that work *right now*.

### Option C1 — OpenCode API (free models) + local CPU embeddings

The strongest fallback. Uses what's already available on this machine.

| Component | What to use | Auth | Cost |
|-----------|------------|------|------|
| LLM (Agents 2, 4) | OpenCode Zen API → `deepseek-v4-flash-free` | Existing API key (`sk-pbB...`) | **Free** |
| Embeddings (Agent 1) | Local CPU via llama.cpp → `embeddinggemma-300M` | None (local) | **Free** |

```python
# LLM client config
client = OpenAI(
    base_url="https://opencode.ai/zen/v1",
    api_key=os.environ["OPENCODE_API_KEY"]  # already set
)
# Model: "deepseek-v4-flash-free" — 200K context, free tier
```

```python
# Embedding via llama.cpp (same infra as qmd)
# Use subprocess to call llama-embedding, or integrate via ctypes
# Model: /home/afshin/.cache/qmd/models/hf_ggml-org_embeddinggemma-300M-Q8_0.gguf
# Produces 768-dim vectors, runs on CPU
```

### Option C2 — DeepSeek API ($5 free) + OpenAI embeddings

If we sign up for DeepSeek (free $5 credits) and/or OpenAI ($5 min):

| Component | Provider | Cost |
|-----------|----------|------|
| LLM (Agents 2, 4) | DeepSeek API → `deepseek-v4-flash` | $0.28/M output tokens (~$0.01/poll) |
| Embeddings (Agent 1) | OpenAI API → `text-embedding-3-small` | $0.02/1M tokens (~$0.18/poll) |

### Option C3 — Local CPU for both (emergency)

Both embeddings and a small LLM can run on CPU using llama.cpp GGUF models:

| Component | Model | Size | Speed estimate |
|-----------|-------|------|---------------|
| Embeddings | `embeddinggemma-300M` | 328 MB | 3-6 min / 1,800 articles |
| LLM (Agents 2, 4) | `qmd-query-expansion-1.7B` | 1.28 GB | Slow but functional for single-article extraction |
| LLM (better) | Any GGUF model from HuggingFace (e.g., Llama 3.2 3B) | ~2 GB | 5-10 sec/article |

The qmd infrastructure already has llama.cpp running on this machine. We could drop any GGUF embedding or LLM model into the same cache directory and call it. For claim extraction, a 3B parameter model is small enough to run on CPU and large enough to follow structured output prompts.

### What we already have on this machine

Installed and working right now:

| Tool | Purpose | Status |
|------|---------|--------|
| `qmd` | Local embeddings via llama.cpp (300M model) | **Working** |
| `opencode` | API gateway to 59+ models (free + paid) | **Authenticated** |
| `pi` | Coding assistant with model access | **Installed** |
| `transformers` (Python) | sentence-transformers, HuggingFace models | **Installed** |
| `openai` (Python) | OpenAI SDK for API calls | **Installed** |
| 3 GGUF models | embedding gemma 300M, reranker 0.6B, expansion 1.7B | **Cached** |

---

## Provider quick-reference

### LLM inference (for Agents 2 & 4)

| Provider | Base URL | Auth | JSON schema? | Free tier? | Notes |
|----------|---------|------|-------------|-----------|-------|
| **Fireworks** | `api.fireworks.ai/inference/v1` | `FIREWORKS_API_KEY` | ✅ json_schema | $50 hackathon credits | Runs on AMD Instinct |
| **OpenCode Zen** | `opencode.ai/zen/v1` | `OPENCODE_API_KEY` | ✅ json_schema | `deepseek-v4-flash-free` | **Already have key** |
| **DeepSeek** | `api.deepseek.com` | `DEEPSEEK_API_KEY` | ⚠️ json_object only | ~$5 signup | No embeddings API |
| **OpenAI** | `api.openai.com/v1` | `OPENAI_API_KEY` | ✅ json_schema | None free | Most reliable |
| **Local CPU** | llama.cpp (GGUF) | None | ⚠️ prompt-enforced | Free | 3B+ model recommended |

### Embeddings (for Agent 1)

| Provider | Model | Dims | Cost | Notes |
|----------|-------|------|------|-------|
| **Fireworks** | `nomic-ai/nomic-embed-text-v1.5` | 768 | ~$0.07/poll | Same as GPU pod model |
| **Fireworks** | `sentence-transformers/all-MiniLM-L6-v2` | 384 | ~$0.07/poll | Exact match for GPU pod |
| **OpenAI** | `text-embedding-3-small` | 1,536 | ~$0.18/poll | Best quality |
| **CPU local** | `embeddinggemma-300M` (via llama.cpp/qmd) | 768 | **Free** | 3-6 min/poll, runs now |
| **CPU local** | `all-MiniLM-L6-v2` (via sentence-transformers) | 384 | **Free** | ~10 min/poll, no extra deps |
| **GPU pod** | `all-MiniLM-L6-v2` (via ROCm) | 384 | **Free** | 30 sec/poll, needs AMD GPU |

---

## How small can the LLM job be? Yes, local is viable.

**Agent 2 (Forensic Extraction)** is the right job to test with a small local model:

- Input: 1 article body (~5,000 chars / ~1,500 tokens)
- Output: JSON array of structured claims (~500 tokens)
- Task: Identify named entities, claims, and attributions — this is extraction, not reasoning
- A 3B parameter model (like Llama 3.2 3B or Qwen 2.5 3B in GGUF format) is sufficient

**Agent 4 (Silent Audit)** is even simpler:
- Input: old body + new body (~3,000 tokens total)
- Output: JSON diff with edit classifications
- Pattern matching, not creative generation

**For the hackathon demo**, we could even run Agent 2 with the 1.7B query expansion model already cached by qmd. It won't be as accurate as a larger model, but it proves the pipeline works.

---

## Free credits available right now for testing

| Source | Amount | What you can do |
|--------|--------|----------------|
| **OpenCode API** | Already has key | Call `deepseek-v4-flash-free` immediately |
| **DeepSeek** | ~$5 free on signup | Test `deepseek-v4-flash` for $0.28/M output tokens |
| **OpenAI** | $5 minimum payment | Test `text-embedding-3-small` + `gpt-4o-mini` |
| **Local CPU** | Free (already installed) | Run embeddings via qmd/llama.cpp, no API call needed |

---

## What to do right now (while waiting for credits)

### 1. Build the provider abstraction layer

Create two new files with a clean interface:

- **`pipeline/llm_client.py`** — Unified LLM client with providers: `fireworks`, `opencode`, `deepseek`, `openai`, `local`
- **`pipeline/embedding_client.py`** — Unified embedding client with providers: `fireworks`, `openai`, `local-llama`, `local-sentence`

Each exposes the same method signature so switching providers is a config change.

### 2. Verify the OpenCode API works

Test `deepseek-v4-flash-free` via OpenCode Zen API with a single article extraction. If it works, we have a free, working LLM pipeline immediately.

### 3. Test local embeddings via qmd's infra

The qmd embedding model (`embeddinggemma-300M`) is already on disk. We can either:
- Call it through qmd's MCP server (`qmd mcp`)
- Call llama.cpp directly (if the binary is available)
- Use sentence-transformers with `all-MiniLM-L6-v2` (pip install, no GPU needed)

### 4. Download a small local LLM for extraction

If we want a fully local fallback, download a 3B GGUF model:
- `llama-3.2-3b-instruct-q4_k_m.gguf` (~2 GB)
- `qwen2.5-3b-instruct-q4_k_m.gguf` (~1.8 GB)
These are small enough to run on CPU and capable of structured JSON extraction.

### 5. Update runner.py to sequence all 4 agents

`pipeline/runner.py` currently only runs Agent 3 + snapshots. It needs to sequence Agents 1→2→4 before Agent 3, with each agent using its configured provider. The runner imports from the same `pipeline/` modules, so it automatically respects whatever provider is set.

### 6. Update scheduler.py to trigger pipeline after scrape

`pipeline/scheduler.py`'s `run_once()` scrapes articles but never fires the pipeline. After each scrape pass, it should call `run_daily_pipeline()` so Agents 1→4 process the new articles. This is what makes the pipeline autonomous — scrape triggers analysis automatically.

### 7. Update Docker strategy

Dockerfile.worker should ship three modes based on build arg:
- `gpu` — ROCm base with sentence-transformers (Scenario A)
- `cpu` — Python slim with sentence-transformers (CPU, Scenario C3)
- `none` — Empty placeholder (Scenarios B, C1, C2)

---

## Fallback quick-reference table

| Scenario | Embeddings | LLM (Agents 2, 4) | Env vars needed | Cost |
|----------|-----------|-------------------|-----------------|------|
| **A — Full AMD** | GPU pod (ROCm) | Fireworks API | `FIREWORKS_API_KEY` | Free (credits) |
| **B — Fireworks only** | Fireworks API | Fireworks API | `FIREWORKS_API_KEY` | $50 credits |
| **C1 — OpenCode + local CPU** | Local llama.cpp (embeddinggemma-300M) | OpenCode Zen (`deepseek-v4-flash-free`) | `OPENCODE_API_KEY` | **Free** |
| **C2 — DeepSeek + OpenAI** | OpenAI API (`text-embedding-3-small`) | DeepSeek API (`deepseek-v4-flash`) | `DEEPSEEK_API_KEY`, `OPENAI_API_KEY` | ~$5 |
| **C3 — All local** | Local CPU (sentence-transformers or llama.cpp) | Local CPU (GGUF 3B model) | None | **Free** |

---

## Key files reference

| File | Current state | What changes |
|------|-------------|-------------|
| `pipeline/llm_client.py` | **Doesn't exist** | Create — provider abstraction (Fireworks, OpenCode, DeepSeek, OpenAI, local) |
| `pipeline/embedding_client.py` | **Doesn't exist** | Create — provider abstraction (Fireworks, OpenAI, local-llama, local-sentence) |
| `pipeline/worker_client.py` | Stub → HTTP to GPU pod | Deprecate or keep as GPU-pod client alongside new embedding_client |
| `pipeline/agent1_intake.py` | Returns `[]` | Wire to embedding_client + DBSCAN clustering |
| `pipeline/agent2_forensic.py` | Returns `[]` | Wire to llm_client with extraction prompt |
| `pipeline/agent4_silent.py` | Returns `[]` | Wire to llm_client with diff prompt |
| `pipeline/runner.py` | Only runs Agent 3 + snapshots | Sequence Agents 1→2→4 before Agent 3 with per-agent provider config |
| `pipeline/scheduler.py` | `run_once()` scrapes only, no pipeline trigger | After scrape, call `run_daily_pipeline()` to process new articles |
| `worker/server.py` | One `print()` placeholder | Real FastAPI server with sentence-transformers (GPU pod scenario only) |
| `requirements.txt` | 8 deps | Add `openai`, `scikit-learn` (DBSCAN) |
| `Dockerfile.worker` | Slim placeholder | Build-arg mode: gpu / cpu / none |
| `docker-compose.yml` | Worker mandatory, assumes Fireworks | Worker conditional on provider config; update comments |
