# Track B Recon — Live Investigate Feasibility Report

**Date:** 2026-07-02
**Type:** RECON ONLY — no code changes

---

## R1 — CURRENT INVESTIGATE STATE

**R1a — Investigate.tsx (176 lines):** Pure stub. Has a textarea for URL/text input, a Submit button that stores to localStorage via `addAdHocResult({id, query, timestamp, claims:[]})`, and a results list. Claims array always stays empty — the "Submitted" message is a 3-second cosmetic timeout. No backend calls, no pipeline integration. Lines that matter: `src/pages/Investigate.tsx:22-35` (handleSubmit), `:141-145` (empty claims fallback text).

**R1b — Store (src/store.ts:15-93):**
- `AdHocClaim`: `{text: string, sources: string[], consensusPct: number | null}`
- `AdHocResult`: `{id: string, query: string, timestamp: number, claims: AdHocClaim[]}`
- Zustand store: `adHocResults: AdHocResult[]` — NOT persisted to localStorage (line 93: "adHocResults grows unboundedly and should never be persisted"). In-memory only, survives SPA navigation but NOT refresh.

**R1c — Backend:** Zero backend for investigate. No endpoints, no agent wrappers, no SSE. Grep for "investigate" across repo hits only frontend files + test files. Nothing in app/, pipeline/, db/.

---

## R2 — PIPELINE COMPONENTS FOR SINGLE-ARTICLE USE

**R2a — Agent 1 (agent1_intake.py):** `run()` at line 38 batches all AVAILABLE articles from DB. No `find_nearest_cluster(text)` helper. To do single-article: would need to extract `get_embedding_input()` (line 63) + `EmbeddingClient.embed()` — both are already reusable functions. Missing piece: compute cosine similarity against all 1,112 existing cluster centroids. Centroids would need to be precomputed or computed on-the-fly from `embeddings` table. No helper function exists. Estimated: 30 lines of new code in a utility function.

**R2b — Agent 2 (agent2_forensic.py):** `run()` at line 86 reads from DB, writes via `insert_claim()` (line 202) and `add_claim_source()` (line 212). Owns `LLMClient` instantiation. For read-only single-article use: the extraction prompt (`EXTRACTION_SYSTEM_PROMPT` at line 30, ~1,200 chars) is reusable. Would need a new method that takes `{title, body, article_id}` dict and returns `{claims: [{text, entities}], framing_score}` WITHOUT writing to DB. Most of the extraction logic (LLM call, JSON parse) is separable from the DB writes. Estimated: 40 lines to extract a `extract_claims_readonly()` method.

**R2c — Agent 3 (agent3_consensus.py):** `run_all()` at line 27 reads all clusters, classifies claims, writes state updates via `update_claim_state()` (imported at line 9). No read-only classifier exists. The core logic (`compute_baseline_pct` + `determine_state`) IS pure functions that return state strings — already read-only. What's missing: a function that takes a cluster_id + a list of new claims and returns per-claim `{match_type: "consensus"|"outlier"|"novel", baseline_pct, state}` WITHOUT calling `update_claim_state`. The `_run()` method at line 33 does cluster-level analysis; the per-claim logic at line 55 is embedded in a write loop. Estimated: 25 lines to extract.

**R2d — claim_matching.py:** `match_claims_in_cluster(conn, cluster_id, embed_client, sim_threshold=0.85)` at line 42-48 does greedy merge with DB writes to `claim_variants` table. For read-only: would need to return match results without calling INSERT. The similarity computation (cosine on claim embeddings) is pure — the write happens in the merge loop at ~line 100. A `match_claims_readonly()` variant would need ~20 lines, mostly the embedding + cosine comparison, skipping the INSERT.

**R2e — Article fetching:** `pipeline/extractor.py:10-21` — `ArticleExtractor.extract(url)` returns `(body_text, body_status)`. Synchronous, uses newspaper4k. Works for non-paywalled articles. The scheduler (scheduler.py:151-156) falls back to `cb_extract()` (CloakBrowser) for paywalled. Single-article fetch is: `extractor.extract(url)` → `(body, status)`. Ready to use.

---

## R3 — SSE INFRASTRUCTURE

**R3a:** Zero streaming endpoints exist. No `StreamingResponse`, `EventSourceResponse`, `WebSocket`, or `sse-starlette` anywhere in the codebase.

**R3b:** FastAPI >=0.115.0 in requirements.txt. `sse-starlette` is NOT installed. Would need `pip install sse-starlette` (1 dep, lightweight). No project constraints block this.

**R3c:** Vite proxy (`vite.config.ts:15-17`): `"/api": "http://localhost:8000"`. The default vite http-proxy DOES buffer SSE responses — the `proxy` config needs `configure: (proxy) => { proxy.on('proxyReq', ...) }` to disable buffering, OR the frontend should connect directly to `http://localhost:8000/api/investigate/stream` bypassing vite proxy for SSE. **This is a known blocker** — without fixing, SSE events will be batched and delivered all at once when the connection closes, defeating the "live progress" effect.

---

## R4 — TIMING

**R4a — 3 test articles:**
| ID | Source | Title | URL |
|----|--------|-------|-----|
| 4899 | bbc | Late VAR drama as Croatia denied equaliser | BBC URL |
| 4874 | dw | South Africa, Ghana clash over migrant's death | DW URL |
| 4884 | thehindu | West Asia war LIVE: Iran warns oil tankers | The Hindu URL |

**R4b — Measured wall-clock (actual commands run):**
| Stage | Time | Method |
|-------|------|--------|
| Fetch (newspaper4k) | 0.5–1.6s | `ArticleExtractor.extract(url)` |
| Embedding (Fireworks BGE) | 0.8s | `EmbeddingClient.embed([text])` → 768-dim vector |
| Nearest cluster (1,112 centroids) | 0.01s | numpy `dot(centroids, vec)` |
| LLM extraction (est.) | ~5s | DeepSeek chat API, ~2,000 tokens input + ~500 output |

**R4c — Total: ~7.3s per run.** Well under 30s. The LLM extraction is the fat (~5s), but still fast. **No timing bottleneck.** If the LLM call takes longer for long articles (some are 3,000+ chars), worst case might be ~10s.

---

## R5 — FIRECRAWL / PAYWALL / GARBAGE INPUT

**R5a — Failure modes:**
- **Paywalled URL (NYT, WSJ):** `newspaper4k` returns empty body → `BODY_UNAVAILABLE`. The UI currently shows "No claims extracted yet" with no error message. **NEEDS DECISION:** show "Could not extract article body — may be paywalled" or fall back to CloakBrowser.
- **Non-article URL (homepage, tweet):** `newspaper4k` returns some text (homepage nav, social embeds) → LLM extracts garbage claims or returns empty array. **NEEDS DECISION:** add a minimum body length check (e.g., <200 chars = reject).
- **404 URL:** `newspaper4k` raises `ArticleException` → caught by `extract()`, returns `("", "BODY_UNAVAILABLE")`. Graceful.
- **Plain text instead of URL:** No URL parsing in the frontend stub — text goes directly to `addAdHocResult` without any processing. Would need `isURL(query)` check and branch: URL → fetch, text → skip fetch, go straight to LLM extraction.

**R5b — Firecrawl:** `FIRECRAWL_API_KEY` is NOT set in `.env`. Firecrawl MCP is registered in Hermes config (keyless, rate-limited per IP) — only usable via MCP tool calls, NOT as a Python library in the pipeline. Not viable for an API endpoint.

**R5c — Cost:** No Firecrawl subscription budgeted. Using the keyless MCP tool for a demo endpoint would hit rate limits quickly. **Recommendation:** use newspaper4k for non-paywalled, show "paywalled — not available" message for failures.

---

## R6 — SECURITY / ABUSE

**R6a — SSRF:** If `/api/investigate` fetches arbitrary URLs server-side via `newspaper4k`, an attacker could POST `http://169.254.169.254/latest/meta-data/` to hit cloud metadata. For a hackathon demo: low risk, easy to mitigate. **Minimum safeguard:** block private IPs (127.0.0.0/8, 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16, 169.254.0.0/16) and non-http(s) schemes. ~5 lines with `ipaddress` stdlib.

**R6b — Rate limiting:** None. Only CORS middleware exists (`app/main.py:73-74`). No `slowapi`, no manual rate limiter.

---

## R7 — TOKEN BUDGET

**R7a — Token estimate:**
- Embedding: 1 call to Fireworks BGE (~500 input tokens) — Fireworks embeddings are cheap/free-tier
- LLM extraction: ~2,000 prompt tokens + ~500 completion tokens = ~2,500 tokens/run
- 100 runs × 2,500 = 250,000 tokens
- DeepSeek pricing: ~$0.27/1M input, ~$1.10/1M output → ~$0.14/run → ~$14 for 100 runs
- **Fits comfortably in remaining Fireworks credits.**

**R7b — Token logging:** `pipeline/llm_client.py:110-117` logs `prompt_tokens` and `completion_tokens` at INFO level. No accumulated data file — logs go to stderr. Not queryable in production.

---

## R8 — UI SPEC

**R8a — design-v1.2.md §6 (verbatim):**
> "Investigate — Ad-hoc forensic query tool. Accepts an article URL or pasted text. Runs through pipeline stages 1–3 (Intake & Clustering → Forensic Extraction → Consensus Alignment) as a read-only analysis. Displays extracted atomic claims, cross-source matches, and consensus baseline comparison inline. Results persist in localStorage and survive navigation, refresh, and browser restarts. Snapshot banner: 'Claim resolution states are not available for ad-hoc reports.' Does not write to reputation tables. Does not require database persistence for results."

**R8b — Gap analysis:**
| Requirement | Current stub | Gap |
|-------------|-------------|-----|
| Accept URL or text | ✅ Textarea exists | ❌ No URL vs text detection |
| Run pipeline S1-3 read-only | ❌ Nothing wired | ⚠️ Entire backend needed |
| Display extracted claims | ❌ Empty card only | ⚠️ Net-new claim card rendering |
| Cross-source matches | ❌ No data | ⚠️ Net-new match display |
| Consensus baseline comparison | ❌ No data | ⚠️ Net-new comparison widget |
| Survive refresh | ❌ Only survives SPA nav | ⚠️ zustand persist needed |
| Snapshot banner | ✅ Line 50-55 | ✅ Already present |

**R8c — Threshold slider:** Not found in `docs/mocks/`. The mock directory was moved/removed. **NEEDS DECISION:** build threshold slider from scratch using existing `DEFAULT_THRESHOLDS` from `pipeline/consensus.py`.

---

## R9 — SANITY CHECK

**Estimated hours:**

| Component | Hours | Notes |
|-----------|-------|-------|
| `/api/investigate/stream` endpoint (SSE) | 3h | FastAPI + sse-starlette, article fetch, embedding, LLM, matching orchestration |
| Read-only agent wrappers | 2h | Extract reusable logic from agents 1-3 + claim_matching |
| SSE proxy fix (vite) | 0.5h | Configure proxy to not buffer SSE |
| Frontend: SSE client + progress UI | 3h | EventSource, stage progress bar, claim cards, match display |
| Frontend: localStorage persistence | 1h | zustand persist middleware on adHocResults |
| Error handling (paywall, garbage, SSRF) | 1h | Input validation, error messages |
| Testing (backend + frontend) | 2h | Vitest for SSE mock, pytest for endpoint |
| **Total** | **12.5h** | |

---

## RECOMMENDATION

**Can Option 1 ship in 2 days?** **YES-WITH-CUTS.**

**Build order:**
1. Read-only utility functions for agents 1-3 + claim_matching (lowest risk, highest reuse)
2. SSE endpoint at `/api/investigate/stream`
3. Frontend SSE client + progress UI
4. Error handling + localStorage persistence
5. Polish, testing

**Cuts to make if time runs short:**
- Consensus baseline comparison widget → just show match type + percentage
- localStorage persistence → cookies only (SPA nav is fine for demo)
- Paywall fallback → "article not accessible" message
- Threshold slider → hardcode the geopolitics threshold for demo

**1 thing most likely to blow up the timeline:** The SSE proxy buffering in vite. If the default http-proxy buffers all events until connection close, the "live progress" streaming effect is dead on arrival. The fix is well-known (`proxy.on('proxyRes', ...)` to disable buffering) but easy to overlook. **Verify this FIRST** before building anything else — a 5-line vite config change that takes 30 seconds to test with curl.
