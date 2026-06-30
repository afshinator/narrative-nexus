# Narrative Nexus

A B2B Media Risk and OSINT workflow platform for hedge funds, PR firms, and geopolitical analysts. Monitors ~20 news outlets and algorithmically measures their reporting behavior over time — not to judge who is "right," but to answer which sources reliably break stories ahead of consensus, which generate noise, and which quietly rewrite history after publication.

> *"Narrative Nexus tracks consensus reality, not truth."*

---

## Stack

| Layer | Tools |
|-------|-------|
| Frontend | React 19.2, TypeScript 6, Vite 8, Tailwind 4, shadcn (Nova) |
| Routing / State | react-router v8, zustand 5 |
| Visualizations | D3 v7 (scatter, sparklines, waterfall, timeline, pipeline), Chart.js 4 (radar) |
| Backend | FastAPI, SQLite (WAL), APScheduler |
| ML | Provider-agnostic: configurable LLM + embedding backends. Local CPU (sentence-transformers for embeddings), OpenCode Zen (free LLM), Fireworks (AMD Instinct), OpenAI, DeepSeek |

## Quick start

### Local development

```bash
npm install
npm run dev       # Vite dev server on port 5173, proxies /api to localhost:8000
```

Backend (separate terminal):

```bash
pip install -r requirements.txt
OPENCODE_API_KEY=... uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Docker (hackathon submission format)

All submissions must be containerized. Docker Compose is the delivery format.

```bash
# 1. Build the frontend
npm install && npm run build

# 2. Build Docker images
docker compose build

# 3. Run (app + db — embeddings on CPU, LLM via OpenCode Zen)
OPEN...=sk-... docker compose up

# Optional: run with GPU worker (requires AMD GPU pod)
docker compose --profile gpu up
```

**What runs where:**

| Container | What it does | GPU? |
|-----------|-------------|------|
| `app` | FastAPI server, all 4 pipeline agents, frontend static files | No |
| `db` | SQLite volume holder (WAL mode, shared via named volume) | No |
| `worker` | Sentence-transformer embeddings on AMD GPU via ROCm (optional, `--profile gpu`) | Yes |

**API keys:** Set `OPENCODE_API_KEY` for LLM inference (required). Other keys (`FIREWORKS_API_KEY`, `DEEPSEEK_API_KEY`, `OPENAI_API_KEY`) are optional — set them when switching providers on the Pipeline Flow page. Keys are read from the host environment at `docker compose up` time.

**Data persistence:** The SQLite database lives in the `nn-data` Docker volume. It survives container restarts. To reset: `docker compose down -v`.

### Provider configuration

Pipeline stages use configurable AI providers. Defaults in `config/providers.json`, runtime overrides on the Pipeline Flow page.

| Pipeline stage | Provider category | Options | Works today |
|----------------|-------------------|---------|-------------|
| Stage 1 — Embeddings (Agent 1) | embedding | Fireworks, OpenAI, **Local CPU** | Local CPU (sentence-transformers) |
| Stage 1 — Classification (Agent 1) | llm | Fireworks, **OpenCode Zen**, DeepSeek, OpenAI | OpenCode Zen (free tier) |
| Stage 2 — Forensic Extraction (Agent 2) | llm | same 4 | OpenCode Zen |
| Stage 3 — Consensus Alignment (Agent 3) | none | Pure Python on CPU, not configurable | Always works |
| Stage 4 — Silent Auditor (Agent 4) | llm | same 4 | OpenCode Zen |

Providers without a set API key (`{PROVIDER}_API_KEY` env var) appear dimmed on the Pipeline Flow page. The AMD shortcut (1-click) switches all agents to Fireworks — dimmed until `FIREWORKS_API_KEY` is set.

---

## Documentation map

The project follows the [dev-workflow](https://github.com/afshinator/dev-workflow) process. Here's which doc to reach for when:

| When you need… | Open this |
|----------------|-----------|
| The product narrative, architecture, analytical model, demo strategy | `docs/design-v1.2.md` |
| Tagged requirements that `verify-spec-coverage.ts` checks | `spec/requirements.md` |
| Resolved design decisions (filtering behavior, badge colors, etc.) | `docs/context.md` |
| Architecture decision records (why we built it this way) | `docs/adr/0001` through `0004` |
| Implementation reference (commands, gotchas, dependency notes) | `docs/older/TODO-pre-workflow.md` |

### How they relate

- **`docs/design-v1.2.md`** — the design document. Product narrative, system architecture, analytical model, page descriptions, demo strategy. Reference it for context behind the requirements.
- **`spec/requirements.md`** — the dev-workflow spec. Every requirement is tagged (`[desired]`, `[compromise]`, `[stack-bound]`, `[aspirational]`). This is what `verify-spec-coverage.ts` checks, what plan slices reference, and what adversarial reviews verify against.
- **`docs/context.md`** — domain glossary of design decisions made during the grilling phase. Captures the nuance between a requirement and its implementation (e.g., "scatter plot uses dim-mode filtering, not hide-mode; radar chart inverts three axes so outward = favorable").
- **`docs/adr/`** — Architecture Decision Records. Each documents a significant decision, alternatives considered, and consequences.

## Phases

The project is in implementation. All 17 slices completed. Build passes, 356 tests pass (217 pytest + 139 vitest).

---

## Pre-submission cleanup

Items to address before finalizing the project:

| Item | Location | Notes |
|------|----------|-------|
| `.commandcode/` | Project root | Personal Codex taste config — doesn't belong in project. Move to `~/.codex/` or delete. |
| `.libretto/` | Project root | Personal Libretto sessions — doesn't belong in project. Move to `~/.libretto/` or delete. |
| `__pycache__/` | Project root | Auto-generated Python bytecode. Delete (already gitignored). |
| Uncommitted DB changes | `data/nn.db` | Modified but uncommitted — likely from recent pipeline runs. Commit or reset. |
| `docs/plan/` | Empty directory | All plan docs deleted (slices complete). Remove directory. |
| `docs/older/TODO-pre-workflow.md` | Reference | Consider archiving or deleting if stale. |

---

*"Narrative Nexus tracks consensus reality, not truth."*
