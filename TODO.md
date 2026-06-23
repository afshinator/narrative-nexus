# Narrative Nexus — Build Todo List
*Ordered by dependency. Items within a phase can run in parallel.*
*API access not yet available — all Phase 1–5 work is fully unblocked.*

---

## PHASE 1 — Project scaffolding
*Everything else depends on this being done first. Half a day.*

- [ ] **1.1** Scaffold Vite + React project: `npm create vite@latest narrative-nexus -- --template react`
- [ ] **1.2** Install core dependencies in one shot:
  ```
  npm install react-router-dom zustand chart.js d3 recharts
  npm install -D tailwindcss postcss autoprefixer
  npx tailwindcss init -p
  ```
- [ ] **1.3** Run shadcn/ui init (`npx shadcn@latest init`) — do this now, before any components exist, so it modifies `tailwind.config.js` and `globals.css` cleanly
- [ ] **1.4** Create `src/styles/tokens.css` — paste in all CSS custom properties from design-system-v1.md (dark mode `:root`, light mode `html.light`). This is the single source of truth for every color, spacing token, and type size.
- [ ] **1.5** Update `tailwind.config.js` to extend colors and fontFamily with CSS var references (Section 1 of design doc)
- [ ] **1.6** Create the Zustand store — **first component file in the project**:
  ```js
  // src/store.js — theme, vertical, filter, scale, onboardingComplete
  // use persist middleware — replaces all manual localStorage calls
  ```
- [ ] **1.7** Create `src/utils/cssVar.js`, `archetype.js`, `polarity.js`, `format.js` — these are referenced by almost every component and are trivial to write now
- [ ] **1.8** Set up React Router with all 8 routes as empty stub pages (Sources, SourceProfile, ClusterReport, Timeline, PipelineFlow, Investigate, Panel, Settings)
- [ ] **1.9** Build `AppNav.jsx` and `PageShell.jsx` — sticky nav, all 8 links, stub treatment for non-built pages, footer tagline on every page
- [ ] **1.10** Set up Vite dev server proxy: add to `vite.config.js`:
  ```js
  server: { proxy: { '/api': 'http://localhost:8000' } }
  ```

---

## PHASE 2 — FastAPI skeleton + database schema
*Pure Python/SQL. No API access needed. Run in parallel with Phase 3.*

- [ ] **2.1** Write `schema.sql` — all CREATE TABLE statements from spec Section 10.2. Tables: `source_panel`, `story_clusters`, `cluster_verticals`, `cluster_articles`, `source_reputation`, `outlier_claims`, `reputation_snapshots`, `silent_edits`, `ingestion_manifest_log`, `discovery_run_log`, `firecrawl_usage`, `pipeline_queue`, `pipeline_run_log`
- [ ] **2.2** Write `database_seed.py` — activates exactly the 20 default sources (spec Section 2 seed list), seeds all others as INACTIVE
- [ ] **2.3** Write `app.py` FastAPI skeleton — all `/api/*` routes returning hardcoded mock JSON in the correct response shape. Priority order:
  - `/api/leaderboard`
  - `/api/scatter`
  - `/api/source/{domain}/radar`
  - `/api/pipeline/status`
  - `/api/cluster/{cluster_id}`
  - `/api/source/{domain}/waterfall`
  - `/api/panel/catalog`
  - All remaining endpoints
- [ ] **2.4** Add the FastAPI catch-all route **last** in `app.py` — must register after all `/api/*` routes or it swallows them:
  ```python
  @app.get("/{full_path:path}")
  async def serve_frontend(full_path: str):
      return FileResponse("dist/index.html")
  ```
- [ ] **2.5** Verify the frontend dev proxy (1.10) and mock endpoints (2.3) work end-to-end — Sources page should fetch `/api/leaderboard` and render the mock data before any real backend exists

---

## PHASE 3 — Frontend pages
*Build in spec order. Each page uses mock API data from Phase 2.*

- [ ] **3.1** Convert `sources-v5-dark.html` to React — extract `PulseStrip`, `ScatterMap`, `FilterPills`, `LedgerTable`, `ShapeSig` as individual components. This is the landing page and the demo entry point — it must be pixel-perfect.
- [ ] **3.2** Build `PipelineFlow.jsx` — D3 animated node-edge diagram, 8 stages, AMD GPU vs Fireworks badges on each node, particle flow. **Build this second** — it's the "Application of Technology" showpiece for judges.
- [ ] **3.3** Build `SourceProfile.jsx` — radar chart (Chart.js canvas, 6 axes, previous-period dashed polygon), archetype badge, 30-day sparklines, stat row with delta arrows
- [ ] **3.4** Build `ClusterReport.jsx` — 3-zone layout (consensus summary / distortion matrix / forensic analysis), version indicator, consensus-reality language throughout
- [ ] **3.5** Build `Timeline.jsx` — D3 horizontal Day 0–90 with publication dots, absorption vertical line, echo-mimic dashed connections, play/pause animation. Pre-wire to the demo corpus data.
- [ ] **3.6** Build `Investigate.jsx` — search input, snapshot-mode banner, read-only forensic report
- [ ] **3.7** Build `Panel.jsx` — active sources table, archived section (collapsed), category balance indicator
- [ ] **3.8** Build `Settings.jsx` — font scale slider (updates `--scale` via store, persisted), theme toggle (dark/light), vertical threshold inputs, health panel placeholders. Use shadcn/ui components here.
- [ ] **3.9** Build `Onboarding.jsx` — shadcn/ui Dialog, 5 steps, vocabulary terms as styled monospace chips, re-openable from `?` nav icon, `onboardingComplete` flag in Zustand store

---

## PHASE 4 — Containerization
*Do before writing more backend logic — all subsequent backend code should be written inside the containers it will run in.*

- [ ] **4.1** Write `Dockerfile.app` — Python FastAPI server (APScheduler, SQLite, no GPU)
- [ ] **4.2** Write `Dockerfile.worker` — ROCm base image, sentence-transformers, embedding model. **[PENDING]**: confirm ROCm base image tag for the hackathon's GPU pod once access arrives; use a CPU-compatible base in the meantime so local dev works without a GPU
- [ ] **4.3** Write `docker-compose.yml` — three services: `app`, `worker`, `db` (SQLite volume mount). Worker communicates with app over HTTP. All Fireworks calls originate from `app`.
- [ ] **4.4** Confirm `docker compose up` starts cleanly and frontend is reachable at `localhost:3000`

---

## PHASE 5 — Scraping pipeline
*No API access needed. Real network calls, real edge cases.*

- [ ] **5.1** Write `ingestion.py` — RSS polling with feedparser for all Tier 1+2 sources
- [ ] **5.2** Add newspaper4k article body extraction with the full fallback chain: newspaper4k → RSS `<content:encoded>` → Firecrawl (budget-gated) → RSS summary
- [ ] **5.3** Implement `check_firecrawl_budget()` — `firecrawl_usage` table, daily cap = 16, reset midnight UTC
- [ ] **5.4** Add DuckDuckGo URL discovery for panel fan-out (`site:{domain} {cluster_topic_label}`)
- [ ] **5.5** Add validation gates — character floor (300 chars / 50 words), paywall detection regex, nav-bloat detection. Log all rejections with `passed_validation = 0`.
- [ ] **5.6** Handle source-specific edge cases:
  - Fox News: always fetch fresh URL from RSS, never use stored URL
  - ProPublica: use RSS `<content:encoded>` field directly
  - Paywalled sources (NYT, WaPo, Economist): tag as `BODY_UNAVAILABLE`, use RSS summary only
- [ ] **5.7** Test against all 20 default sources — note which ones fail, mark as `DEGRADED` candidates, verify the fallback chain triggers correctly

---

## PHASE 6 — Consensus math and reputation scoring
*Pure Python. Write unit tests alongside the logic — this is the analytical core.*

- [ ] **6.1** Write `reputation.py` — SQLite connection (WAL mode, pragmas from spec), all table read/write helpers
- [ ] **6.2** Implement `compute_gc(cluster_id, threshold)` — consensus baseline from Tier 1+2 source graphs. Denominator = contributing consensus-pool sources only. Handle BODY_UNAVAILABLE sources (they vote but from summary-only graphs).
- [ ] **6.3** Implement `compute_oi(source_graph, gc_nodes)` — omission index. Gate: skip if `body_available = 0`.
- [ ] **6.4** Implement claim resolution state machine — `resolve_claims_7d()`, `resolve_claims_30d()`, `resolve_claims_90d()`. Only `resolve_claims_90d` writes UNRESOLVED. Convergence type written only at absorption.
- [ ] **6.5** Implement all six reputation dimensions: R_orig, R_val (with origin credit + echo-mimic exclusions), R_speed (absorption anchor date logic), R_frame (Vf stddev), R_edit, R_correct
- [ ] **6.6** Implement archetype assignment — compare R_orig and R_val to panel medians, assign one of four archetypes. This must match what the frontend computes for the scatter quadrants.
- [ ] **6.7** Implement `take_daily_snapshot()` — unconditional write once per UTC day per (source, vertical). No change-detection gate — sparklines and time-machine require gapless series.
- [ ] **6.8** Write unit tests for all of the above against synthetic source graphs with known expected outputs

---

## PHASE 7 — Pre-baked demo corpus
*Editorial research + data authoring. Not coding. Can be done any time — start early.*

- [ ] **7.1** Select 3–4 historical stories where coverage famously fractured (a claim that one outlet broke days/weeks before others confirmed it, or a story where outlets described the same event in structurally different ways)
- [ ] **7.2** For each story: write hardcoded article stubs (headline, body excerpt, source, published date) for all relevant panel sources
- [ ] **7.3** Manually assign extracted claims to each article, set `current_state` and `convergence_type` for each claim
- [ ] **7.4** Author the `reputation_snapshots` series for the demo source (the "Civic Eye" time-machine arc, or a real source equivalent) — Day 0 → Day 90 keyframes with event markers matching actual claim resolutions
- [ ] **7.5** Wire the Timeline page (3.5) to replay this corpus on demand — the demo's centerpiece animation

---

## PHASE 8 — Unblocked only after API access arrives
*Do not attempt before credentials are confirmed.*

- [ ] **8.1** Benchmark Fireworks API: DeepSeek-V4-Pro vs Llama 3.3 70B on structured JSON extraction. Run 20 neutralization + claim extraction calls on the demo corpus articles, compare JSON parse failure rate and output quality. Pick the winner.
- [ ] **8.2** Set up sentence-transformers on the GPU pod with ROCm — confirm `device="cuda"` maps correctly to the Radeon GPU via ROCm
- [ ] **8.3** Confirm embedding model fits in GPU pod VRAM — `nomic-embed-text` or `bge-large-en`. Both are under 1GB; this should not be an issue.
- [ ] **8.4** Wire `call_llm()` in `llm_client.py` — OpenAI-compatible client pointing at Fireworks base URL, API key from env
- [ ] **8.5** Write `processing.py` — entity clustering (sentence transformer + DBSCAN), linguistic neutralization (LLM Call 2), embedding generation for Vf
- [ ] **8.6** Write `analysis.py` — graph extraction (LLM Call 3), consensus baseline computation (wraps Phase 6 math), outlier detection (Python set math, FAISS disabled), forensic synthesis (LLM Call 4), label injection
- [ ] **8.7** Run the full pipeline end-to-end on the pre-baked demo corpus — verify graph extraction output, consensus math, reputation scores against known expected values from Phase 7
- [ ] **8.8** Set up APScheduler in `scheduler.py` — 2-hour discovery cycle, daily resolution checks at 3am UTC, daily snapshot at 3:30am UTC, watchdog every 30 min

---

## QUICK REFERENCE — What's blocked vs unblocked

| Unblocked now | Blocked until API access |
|---|---|
| Phases 1–7 entirely | Fireworks API calls (8.1, 8.4) |
| All frontend pages | Sentence-transformer on GPU pod (8.2, 8.3) |
| Database schema + seed | BERTopic clustering (needs embeddings) |
| FastAPI mock endpoints | Full end-to-end pipeline run (8.7) |
| Docker Compose setup | APScheduler with live pipeline (8.8) |
| Scraping pipeline | LLM call wrappers (8.5, 8.6) |
| All consensus + reputation math | — |
| Demo corpus authoring | — |