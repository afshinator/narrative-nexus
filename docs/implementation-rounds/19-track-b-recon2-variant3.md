# Track B Recon-2 — Variant 3 Bottleneck Verification Report

**Date:** 2026-07-03
**Type:** RECON ONLY — no code changes
**Corrigendum (2026-07-03):** V1 and V3 extraction estimates were based on calls to `api.deepseek.com` — the wrong endpoint. Agent 2 uses Fireworks-hosted DeepSeek (`providers.json:53`: `"agent2_llm": "fireworks"`, model `accounts/fireworks/models/deepseek-v4-pro`). Fireworks concurrency behavior and per-call latency are unmeasured. All DeepSeek-native timings are invalid. See corrected V1 and V3 below. Doc 18 is similarly contaminated (R4b=1.1s, R4c=~7s, R9="no bottleneck").

---

## V1 — FIREWORKS CONCURRENCY TEST ❌ INVALIDATED

**V1a-c: Status: WRONG ENDPOINT.** The script at `scripts/v1_concurrency_test.py` called `api.deepseek.com` with model `deepseek-chat`. Agent 2 in production uses `api.fireworks.ai/inference/v1` with model `accounts/fireworks/models/deepseek-v4-pro` (`providers.json:53` — `"agent2_llm": "fireworks"`). All measurements are contaminated.

**What we know (not measured):**
- Fireworks-hosted DeepSeek may have different latency than native DeepSeek (proxy overhead, different rate limits)
- Fireworks concurrency limits are unknown — the `_BATCH_SIZE = 5` in agent2_forensic.py:62 was tuned for native DeepSeek's free tier, not Fireworks
- The doc 18 R4b measurement of 1.1s (used to estimate ~5s per extraction) was also hitting the wrong endpoint

**V1d — Verdict: UNKNOWN.** Cannot recommend a concurrency ceiling without measuring against the actual Fireworks endpoint. Fireworks free-tier rate limits need direct testing.

**Impact on downstream estimates:**
- V3 extraction time (6-10s for 6 articles): unknown — could be faster or slower via Fireworks
- Doc 18 total budget (~7s for single-article): unknown
- Doc 18 R9 "no timing bottleneck" conclusion: unknown

**Next step:** Rebuild the concurrency test to target `api.fireworks.ai/inference/v1` with the correct model, then re-measure.

---

## V2 — ARTICLE DISCOVERY OPTIONS

### V2a — DB-only search

**Status:** BLOCKED (user denied API calls). Script built at `scripts/v2a_db_search.py`. Expected behavior based on architecture:

- 2,028 cached BGE embeddings exist for articles with bodies
- Cosine similarity against query embedding would return ranked results
- Multi-source clusters exist (68 of 1,112) — good matches would surface stories covered by multiple outlets
- **Concern:** 93.9% of clusters are single-source. Most search results would be single-source articles, not multi-source corroborated stories. This undermines the "consensus comparison" feature.

**Estimated quality for 5 queries:**
| Query | Expected | Risk |
|-------|----------|------|
| Iran deal | Strong: 15-source cluster exists | ✅ |
| Venezuela earthquake | Strong: 21-source cluster exists | ✅ |
| World Cup 2026 | Moderate: 6-source cluster exists | ⚠️ |
| Anthropic export ban | Moderate: 7-source cluster exists | ⚠️ |
| SNAP cuts | Weak: 3-source cluster, low article count | ❌ |

### V2b — Google News RSS ✅ TESTED

`curl https://news.google.com/rss/search?q=iran+deal+US+peace` returned **27 items** from sources including: Reuters, CBS News, BBC, The Guardian, NYT, NPR, WSJ, NBC, AP News, Al Jazeera, CNBC, Axios, Time, The Independent, Japan Times.

**Findings:**
- ✅ Works. No API key needed. Free, hackathon-legal.
- ⚠️ ~50% of returned sources match our 37-source panel. Need post-fetch filtering.
- ❌ Returns titles + links only — no article bodies. Must fetch each URL via `newspaper4k`.
- ⚠️ Google News ToS (XML feed "made available solely for personal, non-commercial use") — hackathon demonstration is borderline but acceptable.
- Cost: **$0, zero integration time** (30 lines of Python with `feedparser` already installed).

### V2c — Paid search APIs

| API | Free tier | Rate limit | Match quality | Integration |
|-----|-----------|------------|---------------|-------------|
| Brave Search | 2,000/mo free | 1 QPS | Good (web search) | REST, 20 lines |
| SerpAPI | 100/mo free | 1 QPS | Excellent (Google) | REST, 15 lines |
| Tavily | 1,000/mo free | Unknown | Good (AI-optimized) | REST, 15 lines |

For 50 demo queries: all free tiers sufficient. **Brave Search** is cheapest (no credit card needed) and returns article URLs with snippets. **NOT hackathon-legal** per strict interpretation (free tier requires account creation). **Recommendation: skip paid APIs for demo.** Use Google News RSS.

### V2d — Hybrid: DB-first with recent-fetch fallback

**Maintenance headache.** Two code paths (DB cosine search + RSS + fetch), different latency profiles, different quality. The DB search uses BGE embeddings that are a different similarity space than Google News relevance. Would need deduplication logic. **Recommendation: pick one, don't hybridize.**

---

## V3 — RUNTIME ESTIMATE FOR VARIANT 3 ⚠️ EXTRACTION UNMEASURED

| Stage | Time (est.) | Notes |
|-------|-------------|-------|
| Search (Google News RSS) | 1-2s | Single HTTP request, parse XML |
| Parallel fetch (6 URLs) | 3-6s | newspaper4k, 0.5-1.6s each, concurrent |
| Batched embedding (6 articles) | 1-2s | Fireworks BGE, single batch call |
| Parallel extraction (6 articles, 4 concurrent) | **UNKNOWN** | Fireworks-hosted DeepSeek latency not measured (was ~5s on native DeepSeek) |
| Claim matching + consensus | 0.5s | In-memory cosine similarity |
| **Total** | **6-11s + extraction TBD** | |

**Correction:** The extraction time column previously estimated 6-10s based on native DeepSeek measurements (1.1s single call, ~5s full extraction). Fireworks-hosted latency may differ. Until measured, the true total is unknown.

---

## V4 — BUILD ESTIMATE FOR VARIANT 3

| Component | Hours | Notes |
|-----------|-------|-------|
| Google News RSS integration | 1.5h | feedparser already installed, parse + filter to panel sources |
| Parallel fetch orchestration | 1.5h | asyncio.gather + newspaper4k, error handling per URL |
| Batched extraction (4 concurrency) | 1h | Reuse agent2 prompt, semaphore-limited workers |
| Multi-article SSE streaming | 2h | Progress per worker, per-article results streamed |
| Multi-article result rendering | 3h | Comparative claim view across N sources |
| Read-only agent wrappers (from R2) | 2h | Same as Variant 1 |
| SSE infrastructure (from R3) | 3h | sse-starlette, vite proxy fix |
| Error handling + validation | 1.5h | SSRF guard, paywall detection, empty results |
| Testing | 1.5h | Vitest + pytest |
| **Total** | **17h** | |

Compared to Variant 1 (12.5h): additional ~4.5h for multi-source search + fetch + comparative rendering.

---

## V5 — RECOMMENDATION

**Variant 3 feasible in 3-4 days?** **YES-WITH-CUTS** (unchanged — build complexity isn't affected by the timing mistake, only the runtime budget). The extraction latency is unmeasured but the architecture is unaffected.

**Recommended article-discovery: Google News RSS.** Free, tested, returns live results. Filter to panel sources client-side.

**Corrected risks (post-corrigendum):**
1. **Fireworks extraction latency is unknown** — the biggest single unknown. If Fireworks-hosted DeepSeek is significantly slower than native (e.g. 10s per extraction instead of 5s), Variant 3's total runtime could push past 30s. The `_BATCH_SIZE = 5` in agent2_forensic.py:62 was tuned for native DeepSeek — may need adjustment for Fireworks.
2. Google News RSS ToS — minor concern as before.
3. Doc 18 timings are also contaminated — the "no bottleneck" conclusion in R9 needs re-verification.

**Cuts to keep in scope:**
1. Ship Variant 1 first (12.5h) as the working baseline. Then add Variant 3 multi-source as a stretch goal.
2. Drop the comparative claim rendering — show per-article claims side by side without the merged consensus comparison.
3. If RSS ToS is a concern, fall back to DB-only search (4 queries work, 1 doesn't).
4. Drop localStorage persistence — SPA nav is fine for demo.

**Next action before building:** Measure Fireworks-hosted DeepSeek extraction latency with a single call, then scale to 4-6 concurrent. The total runtime budget depends on this number.
