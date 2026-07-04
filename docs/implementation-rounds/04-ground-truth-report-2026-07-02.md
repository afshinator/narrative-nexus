# NARRATIVE NEXUS — GROUND-TRUTH STATUS REPORT

**Generated:** 2026-07-02 against live DB (`data/nn.db`)

---

## SECTION A: STACK & REPO GROUND TRUTH

### A1. Repo tree (2 levels)

```
.
├── CLAUDE.md
├── Dockerfile.app
├── Dockerfile.worker
├── README.md
├── app/
│   ├── main.py
│   └── test_routes.py
├── config/
│   └── providers.json
├── data/
│   ├── nn.db
│   ├── narrative_nexus.db
│   ├── test.db
│   └── backfill-2026-06-27.db
├── db/
│   ├── __init__.py, articles.py, claims.py, clusters.py, connection.py
│   ├── corrections.py, framing.py, silent_edits.py, snapshots.py, sources.py
│   └── test_*.py (10 files)
├── docker-compose.yml
├── docs/
│   ├── adr/, mocks/, older/, plan/, poc/
│   ├── design-v1.2.md, design-tokens.md
│   └── faq-*.md (3 files), open-issues.md
├── pipeline/
│   ├── agent1_intake.py, agent2_forensic.py, agent3_consensus.py, agent4_silent.py
│   ├── base_agent.py, llm_client.py, embedding_client.py
│   ├── consensus.py, resolution.py, archetype.py
│   ├── framing.py, corrections.py, vertical_classifier.py
│   ├── runner.py, runner_scheduler.py, scheduler.py
│   ├── snapshots.py, provider_config.py, worker_client.py
│   └── test_*.py (19 files)
├── package.json
├── requirements.txt
├── scripts/
│   ├── backfill_corrections.py, backfill_framing.py, backfill_snapshots.py
│   ├── seed_demo.py, *_backfill_*.py
│   └── *.js (3 files), *.py (7 more)
├── spec/requirements.md
├── src/
│   ├── App.tsx, main.tsx, store.ts, index.css
│   ├── components/ (AppNav, ScatterPlot, OnboardingDialog, VfTrendChart, + ui/)
│   ├── data/ (sources.ts, thresholds.ts, scores.ts)
│   ├── pages/ (Sources, SourceProfile, Timeline, ClusterReport, PipelineFlow, Investigate, Panel, Settings, NotFound)
│   ├── utils/ (format.ts, shapes.ts, polarity.ts, cssVar.ts)
│   └── __tests__/ (19 test files)
├── vite.config.ts
└── worker/server.py
```

### A2. Frontend stack

Framework: **React 19.2.7** (`package.json:26`)
Build tool: **Vite 8.1.0** (`package.json:50`) with `@vitejs/plugin-react` 6.0.2
CSS: **Tailwind CSS 4.3.1** (`package.json:32`) with `@tailwindcss/vite` 4.3.1
Chart libraries: **D3 v7.9.0** (`package.json:23`), **Chart.js 4.5.1** (`package.json:20`), **react-chartjs-2 5.3.1** (`package.json:27`)
Router: **react-router 7.18.0** (`package.json:29`)
State: **zustand 5.0.14** (`package.json:34`)
UI primitives: **radix-ui 1.6.0** (`package.json:25`), **shadcn 4.11.0** (`package.json:30`), **lucide-react 1.21.0** (`package.json:24`)
Fonts: Space Grotesk, IBM Plex Sans, IBM Plex Mono (via `@fontsource/*`)
Testing: **vitest 4.1.9** + **@testing-library/react 16.3.2** + **jsdom 29.1.1**

The real app is `src/` (React SPA). `docs/mocks/` contains static HTML design references, not the application.

### A3. Backend stack

Entrypoint: `app/main.py:71` — `app = FastAPI(title="Narrative Nexus", version="0.1.0", lifespan=lifespan)`
Framework: **FastAPI** (`requirements.txt:1`: `fastapi>=0.115.0`)
Server: **uvicorn** (`requirements.txt:2`: `uvicorn>=0.34.0`)
Database: **SQLite** (stdlib `sqlite3`, WAL mode), accessed via `db/connection.py`
Scheduler: **APScheduler** (`requirements.txt:3`: `apscheduler>=3.11.0`)
ML: sentence-transformers, scikit-learn, openai, vaderSentiment

### A4. API endpoints (registered routes)

| Method | Path | Returns | File:Line |
|--------|------|---------|-----------|
| GET | `/api/health` | `{status, version}` | `app/main.py:95` |
| GET | `/api/sources` | `{sources: [...]}` all sources | `app/main.py:100` |
| GET | `/api/sources/{source_id}` | `{source: {...}}` single source | `app/main.py:106` |
| GET | `/api/sources/{source_id}/profile` | `{source, snapshots, tierAvg, panelMedian, events, edits, claimSummary}` | `app/main.py:113` |
| GET | `/api/scores` | `{scores: [{sourceId, vertical, R_orig, R_val, ...}]}` latest per source | `app/main.py:251` |
| GET | `/api/articles` | `{articles: [...]}` paginated | `app/main.py:280` |
| GET | `/api/clusters` | `{clusters: [...]}` paginated | `app/main.py:286` |
| GET | `/api/claims` | `{claims: [...]}` paginated | `app/main.py:292` |
| GET | `/api/snapshots` | `{snapshots: [...]}` paginated | `app/main.py:298` |
| GET | `/api/timeline/{cluster_id}` | `{cluster, sources: [{domain, tier, claims: [...]}]}` | `app/main.py:304` |
| GET | `/api/clusters/{cluster_id}/report` | `{cluster, claims, sources, baselinePct, thresholds}` | `app/main.py:346` |
| GET | `/api/scraper/status` | `{running: bool, active_feeds: int, last_poll: str}` | `app/main.py:405` |
| POST | `/api/scraper/start` | `{status: "started"}` | `app/main.py:410` |
| POST | `/api/scraper/stop` | `{status: "stopped"}` | `app/main.py:416` |
| GET | `/api/config/providers` | Current provider assignments + catalog | `app/main.py:424` |
| PUT | `/api/config/providers` | Update runtime provider overrides | `app/main.py:432` |
| GET | `/api/config/providers/available` | Full provider catalog | `app/main.py:451` |

**No ad-hoc analysis/Investigate endpoint exists.** No SSE or WebSocket endpoints.

### A5. Test commands and results

**Python:** `python3 -m pytest -m "not network"`
```
247 passed, 18 failed
```
All 18 failures: `ModuleNotFoundError: No module named 'sentence_transformers'`

**Frontend:** `node_modules/.bin/vitest run` (global vitest can't find local jsdom)
```
Test Files  1 failed | 17 passed | 1 skipped (19)
      Tests  12 failed | 148 passed | 4 skipped (164)
```
All 12 failures in `router-shell.test.tsx` (pre-existing router compat issue)

---

## SECTION B: DATABASE — VERIFY THE NUMBERS

### B1. Schema (9 tables)

```
sources(id, domain, name, tier, region, feed_url, active, created_at)
articles(id, source_id FK, url, title, body, published_at, body_status CHECK(AVAILABLE/BODY_UNAVAILABLE), created_at)
clusters(id, vertical, title, created_at)
claims(id, article_id FK, cluster_id FK, text, state CHECK(PENDING/CONSENSUS_ABSORBED/UNRESOLVED), convergence_type, absorbed_at, created_at)
claim_sources(claim_id FK, source_id FK, first_seen_at, PRIMARY KEY(claim_id, source_id))
snapshots(id, source_id FK, vertical, date, r_orig, r_val, r_speed, r_frame, r_edit, r_correct, archetype, created_at, UNIQUE(source_id, vertical, date))
silent_edits(id, article_id FK, detected_at, change_ratio, stored_body_length, fetched_body_length)
corrections(id, article_id FK, detected_pattern, matched_text, detected_at)
article_framing(article_id PK FK, llm_score, lexical_score, sentiment_score, computed_at)
```

No `framing_scores` table exists.

### B2. Row counts

```
sources:          37
articles:         4,493
clusters:         4,640
claims:           8,567
claim_sources:    8,567
snapshots:        106,673
silent_edits:     256
corrections:      16
article_framing:  2,028
```

### B3. Claims by lifecycle state

```
CONSENSUS_ABSORBED:  2,792
PENDING:             5,202
UNRESOLVED:            573
```

### B4. Per-source absorbed-claim counts (12 sources with >0)

```
economist               678
apnews                  543
bbc                     440
theguardian             291
cnn                     225
reuters                 169
foxnews                  95
nytimes                  93
abcnews                  86
cbsnews                  70
npr                      68
politico                 34
```

### B5. Solo coverage share (per-source)

```
SOURCE                        TOTAL  SOLO       %
cnn                             225   225  100.0%
thereporterethiopia              28    28  100.0%
reuters                         188   169   89.9%
abcnews                         100    81   81.0%
thegrayzone                      55    44   80.0%
jamaicaobserver                 157   115   73.2%
theintercept                     88    63   71.6%
namibian                         63    43   68.3%
bbc                             625   424   67.8%
dw                              711   480   67.5%
straitstimes                    229   152   66.4%
apnews                          835   542   64.9%
vanguardngr                      88    57   64.8%
bellingcat                       39    25   64.1%
zerohedge                       107    66   61.7%
premiumtimesng                   70    43   61.4%
africanarguments                 39    23   59.0%
theguardian                     512   291   56.8%
punchng                         132    72   54.5%
economist                      1229   640   52.1%
foxnews                         187    95   50.8%
npr                             136    68   50.0%
timesofisrael                    61    30   49.2%
propublica                       62    29   46.8%
cbsnews                         137    61   44.5%
tehrantimes                     119    50   42.0%
batimes                         487   184   37.8%
politico                        100    34   34.0%
thehindu                        268    86   32.1%
globaltimes                     257    82   31.9%
nytimes                         231    73   31.6%
sputnikglobe                    269    81   30.1%
www3                            461   128   27.8%
en                               41    11   26.8%
france24                         89    21   23.6%
aljazeera                       128    26   20.3%
washingtonpost                   14     0    0.0%
```

Feasibility: The query works using `claims → articles → sources` and counting distinct `source_id` per `cluster_id`. No direct cluster→source table exists, but the join chain `claims.cluster_id → articles.source_id` is unambiguous.

### B6. R_val storage: NULL for uncomputed, 0 is a valid percentile

```
2026-07-02 geopolitics — R_val column:
  abcnews                      r_orig= 36 r_val= 94
  africanarguments             r_orig=  6 r_val=  0   ← stored as 0, not NULL
  aljazeera                    r_orig= 47 r_val=  0
  apnews                       r_orig= 97 r_val= 89
  batimes                      r_orig= 86 r_val=  0
  bbc                          r_orig= 92 r_val= 92
  bellingcat                   r_orig=  6 r_val=  0
  cbsnews                      r_orig= 56 r_val= 81
  cnn                          r_orig= 67 r_val=100
  ...
  washingtonpost               r_orig=  0 r_val=  0
  zerohedge                    r_orig= 42 r_val=  0
```

25 of 37 sources have `r_val = 0` (this is a valid percentile: 0th percentile among sources with absorbed claims). The DB stores 0, not NULL. The frontend `score?.R_val ?? 0` on Sources.tsx:132-133 coerces both NULL and 0 to the same value.

### B7. Latest snapshot date and scheduler status

Latest snapshot date: **2026-07-02**

Scheduler status: `app/main.py` imports `ScraperScheduler` (line 20) and `start_pipeline_scheduler` (line 21). The lifespan startup at lines 41-84 initializes them. Whether currently running depends on process state — needs `GET /api/scraper/status` against a live server.

---

## SECTION C: SOURCES PAGE — CURRENT IMPLEMENTATION

### C1. Scatter plot y-coordinate mapping

**File:** `src/pages/Sources.tsx:116-138` — `scatterData` useMemo

```typescript
// Sources.tsx:132-133 — NULL→0 coercion:
R_orig: score?.R_orig ?? 0,
R_val: score?.R_val ?? 0,
```

**File:** `src/components/ScatterPlot.tsx:72-73` — D3 scale

```typescript
const xScale = d3.scaleLinear().domain([0, 100]).range([0, width]);
const yScale = d3.scaleLinear().domain([0, 100]).range([height, 0]);
```

Data flows: `/api/scores` → `scoreMap` (keyed by `source.domain`) → `scatterData` (with `?? 0` coercion) → `EnrichedSource.R_val` → `yScale(R_val)`. A source with no absorbed claims gets R_val=0 (from DB), which maps to the bottom of the chart.

### C2. API endpoint feeding the scatter

**`GET /api/scores?vertical=geopolitics`** (`app/main.py:251-277`)

Returns latest snapshot per source. Example for a source with no absorbed claims:
```json
{"sourceId": "aljazeera.com", "vertical": "geopolitics",
 "R_orig": 47, "R_val": 0, "R_speed": null, "R_frame": 75, "R_edit": 0, "R_correct": 0}
```

### C3. Graded vs ungraded filtering

**NOT FOUND.** There is no concept of "graded vs ungraded" sources, no minimum-claim threshold, and no scatter/leaderboard filter for sources without absorbed claims. The `Sources.tsx` archetype filter (`ArchetypePills`) filters by archetype category, not by data availability.

### C4. Scatter plot capabilities

**Library:** D3 v7 (`src/components/ScatterPlot.tsx`, 164 lines)
- **Toggling datasets:** NOT FOUND. Single dataset, no toggle.
- **Log-scale x-axis:** NOT FOUND. Both axes are linear `[0, 100]`.
- **Click-through to source profiles:** **YES.** `onSelect` callback (`ScatterPlot.tsx:34`) routes to `/source/{domain}`.

---

## SECTION D: INVESTIGATE PAGE — CURRENT STATE

### D1. Investigate route exists

**Yes.** `/investigate` renders `InvestigatePage` (`src/pages/Investigate.tsx`, 176 lines, lazy-loaded in `App.tsx:10`).

What renders: A textarea for URL/text input, a Submit button, and a results list. The results list shows submitted queries with empty `claims: []` arrays. The banner says "This analysis runs pipeline stages 1–3 in read-only mode" — but this is aspiration. No backend call is made.

### D2. Backend endpoint for ad-hoc analysis

**NOT FOUND.** There is no `/api/investigate`, `/api/analyze`, or any endpoint that accepts article URL/text and returns pipeline analysis. The Investigate page is purely client-side zustand localStorage (`store.ts:82-93`).

### D3. Pipeline stages 1-3 as library functions

**Yes**, the agents are callable as Python classes:

| Stage | Class | File | Signature |
|-------|-------|------|-----------|
| 1 — Intake | `IntakeClusteringAgent` | `pipeline/agent1_intake.py:27` | `__init__(db_path, embedding_provider)` → `async run() → dict` |
| 2 — Extraction | `ForensicExtractionAgent` | `pipeline/agent2_forensic.py` | `__init__(db_path, llm_provider, api_key)` → `async run(article_map) → dict` |
| 3 — Consensus | `ConsensusAlignmentAgent` | `pipeline/agent3_consensus.py:13` | `__init__(db_path)` → `async run(cluster_id) → dict` |

**Coupling:** All three agents read from and write to a SQLite database. Agent 1 reads `articles` table, writes `clusters`. Agent 2 reads `articles`, writes `claims` + `claim_sources`. Agent 3 reads `claims` + `claim_sources` + `sources`, updates claim `state`. There is no read-only single-article pass — these are DB-coupled batch processors.

### D4. Single-article claim→cluster matching

**NOT FOUND.** No function exists that takes a claim set (not in DB) and matches it against an existing cluster's baseline claims. The consensus computation in `pipeline/consensus.py` works on `reporting_sources / pool_size` — it needs source-level counts from the `claim_sources` table, not text-level claim matching.

### D5. Timing — stages 1-3 on one sample article

**Not run.** Requires active API keys for the configured provider (default: Fireworks for Agent 2 LLM, local CPU for Agent 1 embeddings). The local CPU embedding path (`pipeline/embedding_client.py`) requires `sentence-transformers` which is missing from the current environment (18 pytest failures). Fireworks API key would also need to be set.

### D6. SSE / WebSocket / streaming

**NOT FOUND.** No SSE endpoints, no WebSocket routes, no streaming response patterns exist in `app/main.py`. No job/progress reporting pattern beyond scraper status boolean (`/api/scraper/status` returns `{running: bool}`).

### D7. "Live neutralization + claim extraction + threshold slider demo"

**Found:** `docs/mocks/pipeline.html` (23.1 KB)

This is a standalone HTML mock that:
- Uses browser-side `callClaude()` (Anthropic API directly from the browser)
- Runs neutralization + claim extraction on 4 fictional outlets covering the same event
- Has a draggable consensus threshold slider (65-90%)
- Shows claims crossing the threshold in real-time
- Labeled "for hackathon demo" — NOT integrated with the actual pipeline

Key difference from production: calls Claude API directly, not through any of the 4 pipeline agents.

---

## SECTION E: PROVIDER LAYER & FIREWORKS

### E1. config/providers.json (full)

```json
{
  "providers": {
    "embeddings": [
      {"id": "fireworks", "name": "Fireworks AI", "model": "nomic-ai/nomic-embed-text-v1.5", "amd": true},
      {"id": "openai", "name": "OpenAI", "model": "text-embedding-3-small", "amd": false},
      {"id": "local-cpu", "name": "Local CPU (sentence-transformers)", "model": "all-MiniLM-L6-v2", "amd": false}
    ],
    "llm": [
      {"id": "fireworks", "name": "Fireworks AI", "model": "accounts/fireworks/models/deepseek-v4-pro", "amd": true},
      {"id": "opencode", "name": "OpenCode Zen", "model": "deepseek-v4-flash-free", "amd": false},
      {"id": "deepseek", "name": "DeepSeek API", "model": "deepseek-v4-flash", "amd": false},
      {"id": "openai", "name": "OpenAI", "model": "gpt-4o-mini", "amd": false}
    ]
  },
  "defaults": {
    "agent1_embedding": "local-cpu",
    "agent1_llm": "fireworks",
    "agent2_llm": "fireworks",
    "agent4_llm": "fireworks"
  }
}
```

### E2. Fireworks client

**Module:** `pipeline/llm_client.py` (106 lines) — unified async client using `openai.AsyncOpenAI` against `https://api.fireworks.ai/inference/v1` (line 25).

**Has a successful call been made?** The backfill script `scripts/_fireworks_backfill_300.py` exists (line 2: "Fireworks AI LLM backfill — 300 articles, no pause"). The live DB has 2,028 articles with LLM framing scores, and 8,567 claims — both produced via Agent 2. Whether those were produced via Fireworks or OpenCode Zen depends on which provider was active during the pipeline run.

**Env var:** `FIREWORKS_API_KEY` (`pipeline/llm_client.py:34-35`)

### E3. Agent 2 extraction — structured output mode

Uses `response_format={"type": "json_object"}` — `pipeline/llm_client.py:78-106`. System prompt at `pipeline/agent2_forensic.py:30-58` defines the JSON schema inline (not via function calling / tool use). Prompt-and-parse pattern with JSON validation at `agent2_forensic.py:120-140` — malformed JSON claims are silently skipped.

### E4. Agent 2 model IDs per provider

| Provider | Model | Config source |
|----------|-------|--------------|
| Fireworks | `accounts/fireworks/models/deepseek-v4-pro` | `providers.json:27` |
| OpenCode Zen | `deepseek-v4-flash-free` | `providers.json:33` |
| DeepSeek | `deepseek-v4-flash` | `providers.json:39` |
| OpenAI | `gpt-4o-mini` | `providers.json:45` |

Default: Fireworks (`providers.json:53`)

### E5. Token/cost logging

**NOT FOUND.** No token counting, no cost tracking, no usage logging in `pipeline/llm_client.py` or `pipeline/agent2_forensic.py`. The `LLMClient.chat()` returns raw text content — no token metadata is captured.

### E6. Gemma model integration

**NOT FOUND.** No Gemma, Gemini, or Llama references anywhere in config, pipeline, or provider code.

---

## SECTION F: DEPLOYMENT & SUBMISSION REQUIREMENTS

### F1. Dockerfiles and docker-compose

**Dockerfile.app** (43 lines): `python:3.12-slim`, copies `requirements.txt`, installs deps, copies `app/`, `db/`, `pipeline/`, `config/`, `dist/` (pre-built frontend). Exposes 8000. CMD: uvicorn.

**Dockerfile.worker** (29 lines): Optional GPU worker. Two-stage build: `cpu` (python:3.12-slim + sentence-transformers) or `gpu` (rocm/pytorch:latest + sentence-transformers). Exposes 8001.

**docker-compose.yml** (68 lines): Two services — `app` (builds Dockerfile.app, port 8000, volume `nn-data:/data`, env vars for API keys) and `worker` (profile `gpu`, builds Dockerfile.worker, port 8001).

**Does `docker compose up` work from clean checkout?** Untested. Requires `npm run build` BEFORE `docker compose build` (Dockerfile.app:32 — `COPY dist/`). Requires `OPENCODE_API_KEY` or `FIREWORKS_API_KEY` env var.

### F2. Frontend serving

Frontend is **pre-built** (`npm run build` → `dist/`) and **copied into the container** at build time (`Dockerfile.app:32`). The FastAPI app serves the static files — `app/main.py` includes static file mounting (verified in `lifespan` and the Vite proxy config).

### F3. Deployment target / hosting

**NOT FOUND.** No deployment target, hosting config, or public Application URL is configured. Image sizes: PyTorch (~2GB via sentence-transformers), worker optional (CPU fallback available). No GPU/ROCm dependency for the base container — embeddings fall back to local CPU.

### F4. Licensing

**No LICENSE file found in repo root.** No license metadata in `package.json` or `requirements.txt`.

**CloakBrowser:** Referenced in `docs/faq-source-selection.md:101` as "stealth Chromium" for paywall resolution. NOT FOUND in code — no import, no configuration, no module. Presumably an external tool/service used during data collection, not a runtime dependency.

Key runtime deps and their licenses (from package ecosystems, not verified):
- React 19: MIT
- D3 v7: ISC
- Chart.js 4: MIT
- FastAPI: MIT
- scikit-learn: BSD-3
- sentence-transformers: Apache 2.0 (not MIT-compatible for some corporate use)
- PyTorch (transitive via sentence-transformers): BSD-style

### F5. README and repo visibility

**README.md** exists (179 lines) with setup instructions. Quick start covers npm install, pip install, .env creation, uvicorn start, and docker compose instructions.

Repo visibility: Not determinable from inside the environment.

---

## SECTION G: KNOWN GAPS

### G1. TODO/FIXME/stub markers

**Pipeline/ (`*.py`):** 0 TODO/FIXME/HACK/XXX markers found.

**Frontend (`src/` `*.tsx`):** 0 TODO/FIXME markers found.

**Design docs:** `docs/mocks/pipeline-flow.html:312` — "Pipeline offline — no backend connected." (static mock label, not a code TODO).

### G2. Currently broken

| Item | Detail |
|------|--------|
| **18 pytest failures** | All `ModuleNotFoundError: No module named 'sentence_transformers'` — missing pip package |
| **12 vitest failures** | All in `router-shell.test.tsx` — pre-existing React Router v7 test compat issue |
| **Investigate page** | Frontend-only. Stores queries in localStorage with `claims: []`. No backend integration. Banner text ("runs pipeline stages 1–3 in read-only mode") is aspirational, not functional. |
| **Sentence-transformers** | Listed in `requirements.txt:9` but not installed in current environment. Blocks Agent 1 embeddings and 18 tests. |
| **R_val = 0 for 25 sources** | Stored as integer 0 in DB, rendered at y=0 on scatter plot. This is correct percentile math (0th percentile) but visually clusters 68% of sources at the bottom of the chart. |
| **No streaming/SSE** | Would be net-new for live Investigate results. |
| **No single-article pipeline API** | Agents 1-3 are DB-coupled batch processors. A live Investigate pass would need new API surface or wrapper functions. |
