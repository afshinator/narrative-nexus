# Track B Recon-3 — Corrected Fireworks Concurrency Measurement

**Date:** 2026-07-03
**Type:** RECON ONLY — no code changes
**Corrigendum:** This replaces the invalidated V1 from Recon-2. All calls hit `api.fireworks.ai/inference/v1` via the production `LLMClient` code path.

---

## W1 — PRODUCTION PATH CONFIRMED

**W1a — Dispatch point:** `agent2_forensic.py:118,140`
```python
client = LLMClient(self._llm_provider, api_key=self._api_key)  # line 118
raw = await client.chat(                                         # line 140
    messages=[
        {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
        {"role": "user", "content": text},
    ],
    temperature=0.0, max_tokens=600, response_format={"type": "json_object"},
)
```
`LLMClient` wraps `openai.AsyncOpenAI` with base URL `https://api.fireworks.ai/inference/v1` (`llm_client.py:28`).

**W1b — Model:** `providers.json:27` — `"model": "accounts/fireworks/models/deepseek-v4-pro"`, `"agent2_llm": "fireworks"` (line 53).

**W1c — API key:** `FIREWORKS_API_KEY` present, length 25.

---

## W2 — SINGLE-CALL BASELINE

**W2a — Test article:** article 2479, "US Supreme Court blocks Trump's firing of Fed's Cook", 1,538 chars body.

**W2b — First call:** 30.4s, HTTP 200, 0 claims (body[:400] too short for extraction).

**W2c — 3-call sequential (articles 2479, 1935, 1936):**

| Article | Latency | Body len | Claims |
|---------|---------|----------|--------|
| 2479 (nhk) | 31.0s | 1,538 | 0 |
| 1935 (punchng) | 13.4s | 6,385 | 0 |
| 1936 (punchng) | 9.1s | 3,038 | 0 |
| **Mean** | **17.8s** | | |

First call is likely cold-start (model loading). Subsequent calls stabilize at 9-13s. **Fireworks is ~18x slower per call than native DeepSeek (17.8s vs 1.1s).**

Note: 0 claims extracted because the test used `body[:400]` like the production batch prompt does — the agent batches 5 articles per call, combining titles + first 400 chars of each body.

---

## W3 — CONCURRENT LOAD TEST

**W3a — 6 concurrent (articles 1935, 1288, 1893, 820, 1880, 1865):**

| Metric | Value |
|--------|-------|
| Wall-clock total | **21.9s** |
| Per-call min | 9.6s |
| Per-call median | 13.9s |
| Per-call max | 21.7s |
| 429 errors | **0** |
| Speedup vs sequential | 4.9x (near-linear) |

**W3b — 10 concurrent (same 6 articles, 4 duplicates):**

| Metric | Value |
|--------|-------|
| Wall-clock total | **37.6s** |
| Per-call min | 10.5s |
| Per-call median | 15.8s |
| Per-call max | 37.6s |
| 429 errors | **0** |
| Speedup vs sequential | 2.8x (diminishing) |

10 concurrent shows tail latency (29-38s on late completions) suggesting internal queuing, but **no rate-limit errors at either level.** Fireworks appears to accept 10 concurrent without rejecting.

---

## W4 — VERDICT

**W4a — Recommended concurrency: 6 concurrent.** Safe, near-linear speedup, no errors. 10 has diminishing returns from internal queuing.

**W4b — Corrected Variant 3 runtime:**

| Stage | Time |
|-------|------|
| Discovery (Google News RSS) | 1-2s |
| Parallel fetch (6 URLs, asyncio) | 3-6s |
| Batched embedding (6 articles, BGE) | 1-2s |
| Concurrent extraction (6 articles, 6 workers) | **22s** |
| Matching + consensus | 0.5s |
| **Total** | **28-33s** |

**W4c — Verdict: YELLOW (28-33s boundary).**

Right at the 30s threshold. If cold-start hits any worker (31s as seen in W2b), total pushes to ~35s. SSE streaming with per-worker progress indicators can mask the latency — the user sees stages completing as they happen rather than staring at a spinner.

---

## W5 — RECOMMENDATION

**Verdict: YELLOW — proceed with Variant 3 but cap at 5 articles (not 6).**

At 5 articles × 6 concurrent workers: extraction drops to ~22s (same parallel batch size), total ~27-32s. Slightly safer margin.

**One-sentence rationale:** Fireworks hosts DeepSeek at 9-18s per call with no rate-limiting up to 10 concurrent; 6 concurrent gives near-linear speedup making Variant 3 viable, but the cold-start risk and 18x slower-than-native latency mean we should cap articles to 5 and lean heavily on SSE progress indicators to keep the UX feeling alive.
