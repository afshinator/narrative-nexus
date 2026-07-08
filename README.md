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

## AMD Platform Usage

**All AI pipeline stages are configured to run on Fireworks AI, which serves inference on AMD Instinct hardware.** This includes:

| Pipeline Stage | Default Provider | Evidence |
|----------------|-----------------|----------|
| Agent 1 — Embeddings & Clustering | Fireworks AI | `config/providers.json:57` (`"agent1_embedding": "fireworks"`) |
| Agent 1 — LLM Classification | Fireworks AI | `config/providers.json:59` (`"agent1_llm": "fireworks"`) |
| Agent 2 — Forensic Claim Extraction | Fireworks AI | `config/providers.json:60` (`"agent2_llm": "fireworks"`) |
| Agent 4 — Silent Auditor | Fireworks AI | `config/providers.json:61` (`"agent4_llm": "fireworks"`) |
| Claim Matching (cross-stage) | Fireworks AI (nomic) | `config/providers.json:58` (`"claim_matching_embedding": "fireworks-nomic"`) |

Fireworks AI runs on AMD Instinct MI300X and MI250X accelerators. Every LLM inference and embedding call through the Fireworks provider routes through AMD Instinct hardware. The design document states: *"calling Fireworks IS using AMD Instinct hardware"* (`docs/design-v1.3.md` §3).

**Provider configurability:** Runtime provider selection is visible in the Pipeline Flow page (`/pipeline`) where each agent stage shows a dropdown of available compute providers. Fireworks AI entries are marked with an `(AMD)` badge. When all AI stages are set to Fireworks, the page displays: *"All AI stages running on AMD Instinct accelerators via Fireworks AI"* (`src/pages/PipelineFlow.tsx:195-197`).

**Development credits:** The Fireworks AI API credits used during hackathon development were provided by the hackathon organizers ($50 allocation, documented in `docs/design-v1.3.md` §2). All pipeline runs during development used these credits for AMD Instinct-backed inference.

**Important:** The wording "configured to run" is used because no per-inference-row hardware provenance exists. The system is configured — via `config/providers.json` defaults and Pipeline page dropdowns — to route AI workloads through Fireworks AI on AMD Instinct accelerators. Individual LLM responses do not carry a hardware attestation trail.

## Quick start

### Host development (outside Docker)

If Docker is running, stop it first — ports 3000–3019 are published from the container:
```bash
docker compose down
```

```bash
# 1. Install deps
npm install
pip install --break-system-packages -r requirements.txt

# 2. Create .env with API keys (gitignored)
cat > .env << 'EOF'
DEEPSEEK_API_KEY=sk-...
FIREWORKS_API_KEY=fw-...
EOF

# 3. Start backend (port 8000)
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# 4. Start frontend — production build only (no HMR, fastest, most stable)
npm run build
npx vite preview --host 0.0.0.0 --port 5173
```

**Verify everything works:**

```bash
python3 scripts/sanity_check.py --backend http://localhost:8000 --frontend http://localhost:5173
```

Open http://localhost:5173 in your browser.

| Port | Service |
|------|---------|
| 8000 | Backend API (FastAPI/uvicorn) |
| 5173 | Frontend (Vite preview) |

### Docker (hackathon submission format)

All submissions must be containerized. Docker Compose is the delivery format.

Ports 3000–3019 are published to the host from inside the container. If you switch to host development, run `docker compose down` first.

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

## Future work

### R_correct — Formal Correction Detection

Current implementation detects corrections via inline body markers (AP, CNN, NYT patterns). Future enhancements:

- **Option C — Scrape corrections pages:** Some outlets publish corrections on dedicated URLs (e.g., nytimes.com/corrections, apnews.com/about/ap-news-corrections). Requires per-site scraping rules and periodic polling.
- **Option D — Wayback/archive diffing:** Periodically re-fetch old article URLs, diff against stored body text. Detects both silent edits and formal corrections. Heavy on bandwidth and computation; needs a rate-limited polling schedule.

### R_frame — Framing Consistency

Current implementation collects 3 framing scores (LLM, lexical, sentiment) per article. R_frame snapshot wiring (variance computation + percentile rank) deferred to user's scorer selection.

### Hackathon Docker requirements

| Req | Detail | Status |
|-----|--------|--------|
| REQ-007 | Docker Compose with ≥2 services | Done — app + db + optional worker |
| REQ-017 | GPU worker on AMD ROCm via sentence-transformers | Done — worker profile optional |
| REQ-019 | Consensus math + scoring on CPU only | Done — all pipeline agents in app container |
| REQ-106 | Fireworks API calls from app container only | Done |
| REQ-126 | 1-click AMD shortcut on Pipeline Flow page | Done |
| REQ-096 | Pre-baked 90-day corpus, 30+ sources | Done — 37 sources, 90+ days of snapshots |
| REQ-097–099 | Demo landing: scatter plot + radar in motion | Done |
| — | Python 3.11 (Ubuntu 24.04 base image) | ⚠ Currently on Python 3.12 — downgrade to 3.11 for submission |
| — | Vite proxy port | ⚠ `vite.config.ts` points to 8000 (host dev) — change to 3006 for Docker |

---

## Pre-submission cleanup

Items to address before finalizing the project:

| Item | Location | Notes |
|------|----------|-------|
| Python version | `Dockerfile` | Must be 3.11, not 3.12 (hackathon requirement) |
| Vite proxy port | `vite.config.ts` | Change 8000 → 3006 for Docker submission |
| `.commandcode/` | Project root | Personal Codex taste config — move to `~/.codex/` or delete. |
| `.libretto/` | Project root | Personal Libretto sessions — move to `~/.libretto/` or delete. |
| `__pycache__/` | Project root | Auto-generated Python bytecode. Delete (already gitignored). |
| Uncommitted DB changes | `data/nn.db` | Modified but uncommitted — commit or reset. |
| `docs/plan/` | Empty directory | All plan docs deleted (slices complete). Remove directory. |
| `docs/older/TODO-pre-workflow.md` | Reference | Archive or delete if stale. |

---

*"Narrative Nexus tracks consensus reality, not truth."*
