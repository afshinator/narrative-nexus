# Plan: Provider Abstraction Layer + Agents 1/2/4

**Slice:** Provider-agnostic LLM/embedding client → wire Agent 1/2/4 stubs → API config endpoints → Pipeline Flow dropdowns + AMD shortcut
**Status:** Plan
**Date:** 2026-06-27

---

## 1. What changes and why

Replace three agent stubs returning `[]` with working implementations that call configurable AI providers. One thin client (`openai` library, already installed) speaks to all providers because they all expose OpenAI-compatible chat+embedding APIs. Config lives in `config/providers.json` (already created) + runtime overrides via API.

This unblocks: claim extraction, story clustering, silent edit detection, and the full 4-agent pipeline — all working against OpenCode Zen (free tier) today, swap to Fireworks/AMD when credits arrive.

## 2. Dependencies

| Dep | Status | Version |
|-----|--------|---------|
| `openai` (Python) | Installed (v2.24.0) — NOT in requirements.txt | Add to requirements.txt |
| `scikit-learn` | Installed (v1.9.0) | Add to requirements.txt |
| `sentence-transformers` | Installed (v5.6.0) — NOT in requirements.txt | Add to requirements.txt |
| `numpy` | Available via deps | — |
| OpenCode Zen API key | Set in env (`OPENCODE_API_KEY`, 67 chars) | Working for LLM only — NO embeddings support |
| Fireworks API key | NOT set (credits pending) | env var empty |
| DeepSeek API key | NOT set | env var empty |
| OpenAI API key | NOT set | env var empty |
| Local sentence-transformers | `all-MiniLM-L6-v2` — 384-dim, works on CPU | Verified (1.3s load, 384-dim vectors) |
| Local DBSCAN clustering | `sklearn.cluster.DBSCAN(eps=0.5, min_samples=2, metric='cosine')` | Verified — correctly clusters 8 test articles into 2 topics |

## 3. Architecture decisions

### 3.1 One client, many providers

**Decision:** `pipeline/provider_client.py` — a single class wrapping `openai.AsyncOpenAI` with `base_url` + `api_key` per provider. No interface, no factory, no registry pattern. Provider config is a plain dict from `config/providers.json`.

**Why:** Every provider speaks OpenAI-compatible API. Fireworks, OpenCode Zen, DeepSeek, OpenAI — same chat completions endpoint, same embeddings endpoint. `openai` library supports custom `base_url`. One client is 30 lines, a plugin system would be 300.

### 3.2 Provider config flow

```
config/providers.json  ──read on startup──→  app.state.providers  ←──PUT──  Pipeline Flow dropdowns
                                            ↓
                                     provider_client.py reads `app.state.providers`
                                     on each pipeline run
```

**Decision:** Backend is source of truth. Frontend dropdowns call PUT to persist. No localStorage-only config — backend needs it for pipeline runs.

### 3.3 Agent 1 — Intake & Clustering

**Decision:** Load `all-MiniLM-L6-v2` via `sentence-transformers` (local CPU) → DBSCAN clustering → insert clusters into DB. Returns `{article_id: cluster_id}` mapping for Agent 2.

**Ponytail:** Local sentence-transformers, not API embeddings. OpenCode Zen does NOT support `/embeddings` endpoint (verified 404). Local model loads in 1.3s, 384-dim vectors, zero API cost. DBSCAN (`sklearn.cluster.DBSCAN`, eps=0.5, min_samples=2, metric='cosine') on normalized embeddings — verified to correctly cluster 8 test articles into 2 topics.

**Ponytail:** All article clusters assigned to `geopolitics` vertical. Vertical classifier (LLM prompt) is future work.

### 3.4 Agent 2 — Forensic Extraction

**Decision:** Call LLM API (OpenCode Zen, `deepseek-v4-flash-free`) with structured JSON extraction prompt → parse JSON → insert claims into DB. Uses `response_format={"type": "json_object"}` for guaranteed valid JSON. Temperature 0.0 for deterministic extraction.

**Ponytail:** Single-pass prompt — framing neutralization + claim extraction in one call, not two. Separate neutralization pass adds latency and token cost for marginal quality gain at hackathon scale.

**Skip:** Per-claim entity extraction, source attribution — article_id already links claim to source.

### 3.5 Agent 4 — Silent Auditor

**Decision:** Re-fetch article bodies via `ArticleExtractor` → compare against stored bodies → flag diffs > 10% character change. No LLM needed for text diff — `difflib.SequenceMatcher` from stdlib.

**Ponytail:** Pure Python text diff. No semantic comparison, no LLM evaluation of "significant" changes. 10% threshold catches real edits, ignores whitespace/encoding noise.

**Skip:** Correction notice detection — not implemented in current scraper.

### 3.6 Runner sequencing

**Decision:** `run_daily_pipeline` calls Agent 1 → 2 → 3 → 4 in sequence. Each agent reads from/get writes to the DB so the next agent has fresh data.

**Ponytail:** Sequential, single-threaded. No async fan-out, no error recovery beyond per-agent try/except. Pipeline runs daily; 30s latency is fine.

### 3.7 API endpoints (3 new routes)

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/config/providers` | Current provider assignments (`app.state.providers`) |
| PUT | `/api/config/providers` | Update assignments (body: `{"agent2_llm": "fireworks"}`) |
| GET | `/api/config/providers/available` | Full provider catalog from `config/providers.json` |

**Ponytail:** Providers dict lives on `app.state` — no separate config table, no DB migration. Survives app restart (re-initialized from JSON defaults, not persisted between restarts). PUT is session-only — sufficient for hackathon demo where config is set once before demo.

**Skip:** Persistence across restarts — add SQLite config table if needed, not now.

### 3.8 Pipeline Flow UI

**Decision:** Each StageCard gets a `<select>` dropdown showing available providers for that agent type. Selected value = current config from GET endpoint. Change fires PUT. AMD shortcut button in header: sets all 4 agents to `fireworks`, one PUT call.

**Ponytail:** Native `<select>` — no dropdown library, no search, no virtualization. 4-8 options each. CSS only for AMD badge styling (`--nn-red`).

**Ponytail:** Legend badges update dynamically from provider config — no hardcoded "AMD GPU" / "Fireworks API" / "CPU" labels. Stage descriptions shortened to remove provider-specific language.

### 3.9 What is explicitly NOT changed

- `pipeline/worker_client.py` — stays as-is (GPU pod path, not needed without AMD credits)
- `Dockerfile.worker` — stays as-is (placeholder until GPU pod access)
- `docker-compose.yml` — worker service stays (can be omitted with profile when ready)
- `worker/server.py` — stays as placeholder
- `pipeline/agent3_consensus.py` — pure Python, no provider dependency
- `pipeline/scheduler.py` — scraper is orthogonal to this slice
- All DB files, all frontend pages except PipelineFlow

## 4. Implementation order (TDD)

1. **`pipeline/provider_client.py`** — new: `ProviderClient` class, `load_provider_config()`, tests
2. **Add `openai`, `scikit-learn` to requirements.txt**
3. **`pipeline/agent1_intake.py`** — rewrite: embeddings + DBSCAN clustering + DB insert, tests
4. **`pipeline/agent2_forensic.py`** — rewrite: LLM extraction prompt + parse + insert, tests
5. **`pipeline/agent4_silent.py`** — rewrite: re-fetch + diff + flag, tests
6. **`pipeline/runner.py`** — add Agent 1/2/4 calls, tests
7. **`app/main.py`** — 3 new provider config routes, tests
8. **`src/pages/PipelineFlow.tsx`** — dropdowns + AMD shortcut button, manual verification (vitest tests TBD)

## 5. Test strategy

- `pipeline/test_provider_client.py` — unit: config loading, client init per provider, mock API responses
- `pipeline/test_agents.py` — update stub tests to test real behavior with mocked `ProviderClient`
- `pipeline/test_runner.py` — integration: full pipeline with real OpenCode Zen calls + temp DB
- `app/test_routes.py` — new tests for GET/PUT /api/config/providers
- Pipeline Flow — manual visual verification (no vitest framework for page-level dropdown tests yet)

## 6. Verification checklist

- [ ] `pytest` — all tests pass (including new tests)
- [ ] `vitest run` — all existing frontend tests still pass
- [ ] `npx tsc --noEmit` — TypeScript clean
- [ ] `npm run build` — Vite build succeeds
- [ ] Manual: start app, open Pipeline Flow, change dropdowns, confirm GET returns updated config
- [ ] Manual: click AMD shortcut, confirm all dropdowns switch to Fireworks
- [ ] Manual: trigger pipeline run, confirm claims appear in /api/claims
- [ ] `ponytail-review` against diff

## 7. Assumptions to validate

1. **OpenCode Zen supports `response_format={"type": "json_object"}`** — verify with one test call before writing Agent 2 prompt
2. **OpenCode Zen embeddings endpoint returns 384-dim vectors** — `sentence-transformers/all-MiniLM-L6-v2` is listed, need to confirm dimension
3. **DBSCAN produces useful clusters at hackathon scale (~50-100 articles)** — run one clustering pass on real article data
4. **Sequenceable pipeline** — Agent 1 clusters must exist before Agent 2 can assign claims to them. Verify DB operations are synchronous enough for sequential flow.
