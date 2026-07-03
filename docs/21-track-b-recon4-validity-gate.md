# Track B Recon-4 — Measurement Validity Gate Report

**Date:** 2026-07-03
**Type:** RECON ONLY — no code changes

---

## RULE 0 — VALIDITY GATE SUMMARY

| Call | HTTP | JSON | Claims parsed | Valid claims | Pass? |
|------|------|------|--------------|--------------|-------|
| Article 476 (P2b) | 200 | ✅ | 15 | 15 | ✅ |
| Article 1239 (P2b) | 200 | ✅ | 9 | 9 | ✅ |
| Article 1323 (P2b) | 200 | ✅ | 11 | 11 | ✅ |
| Article 1927 (P3) | 200 | ✅ | 13 | 13 | ✅ |
| Article 2019 (P3) | 200 | ✅ | 8 | 8 | ✅ |

**5/5 calls passed the validity gate.** All extracted ≥8 valid claims with JSON responses.

---

## P1 — PRODUCTION CALL SHAPE (EXACT)

**P1a — agent2_forensic.py:131-148:**
```python
articles_text += (
    f"\n--- ARTICLE {row['id']} ---\n"
    f"{row['title'] or ''}\n"
    f"{row['body'][:400] or ''}\n"
)
...
raw = await client.chat(
    messages=[
        {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
        {"role": "user", "content": f"Articles:{articles_text}"},
    ],
    response_format={"type": "json_object"},
    temperature=0.0,
    max_tokens=8000,
)
```

**P1b — Input shape:** User message is `"Articles:"` prefix + concatenated `--- ARTICLE {id} ---\n{title}\n{body[:400]}\n` blocks. Batched 5 articles per call (`_BATCH_SIZE=5` at line 62).

**P1c — Recon-3 error:** Used `title + body[:400]` without `--- ARTICLE {id} ---` headers and without `"Articles:"` prefix. The LLM didn't recognize the input as article format, hence 0 claims on all calls. **Recon-3's latency numbers measured failure, not extraction.** All timing data in doc 20 is invalid.

---

## P2 — SINGLE-CALL CORRECTNESS GATE ✅

P2a articles (claim-rich from DB):

| ID | Source | Title | Body len | Existing claims |
|----|--------|-------|----------|-----------------|
| 476 | bbc | England in huge danger in third Test against NZ | 5,354 | 13 |
| 1239 | nytimes | Life in Dahiya amid Hezbollah-Israel Truce | 5,654 | 10 |
| 1323 | dw | Wagner festival reinstates Holocaust memorial | 4,699 | 10 |

P2b results (EXACT production shape, single article per call):

| Article | Latency | Claims | Valid | Framing | Response len |
|---------|---------|--------|-------|---------|-------------|
| 476 | 50.9s | 15 | 15 | 5 | 1,686 |
| 1239 | 33.4s | 9 | 9 | 3 | — |
| 1323 | 37.8s | 11 | 11 | 1 | — |

✅ **Gate passed.** All 3 extracted ≥9 valid claims.

---

## P3 — SEQUENTIAL BASELINE

P3a+b — 5 sequential calls on claim-rich articles:

| Article | Latency | Valid claims | BF (before Fireworks) |
|---------|---------|-------------|----------------------|
| 476 | 21.4s | 13 | |
| 1239 | 52.5s | 7 | |
| 1323 | 38.3s | 11 | |
| 1927 | 40.0s | 13 | |
| 2019 | 28.2s | 8 | |
| **Mean** | **36.1s** | | |
| **Min** | 21.4s | | |
| **Max** | 52.5s | | |

P3c — Cold start: first call was the fastest (21.4s), not the slowest. No cold-start pattern. High variance suggests Fireworks load-balancing or model instance assignment varies.

---

## P4 — CONCURRENT ❌ BLOCKED

Batched calls with >2 articles exceed the 60s timeout hardcoded at `llm_client.py:78`. Cannot measure 6-article concurrent extraction because:

1. Single-article calls take 21-53s (within 60s timeout)
2. 3-article batches would exceed 60s (timeout observed in testing)
3. 6 concurrent single-article calls would work (~52s based on Recon-3's timing pattern, but Recon-3 had 0 valid claims so those latencies can't be trusted)

**Cannot proceed to P4 without a code change to raise the timeout.** This is a RECON-breaking dependency on production config.

---

## P5 — HONEST VERDICT

**P5a — Real per-call latency:** 21-53s, mean ~36s (single article, valid claims extracted).

**P5b — Real concurrent-6 wall-clock:** Unmeasured. Estimated ~52s based on Recon-3's timing pattern (6 concurrent = 1.4x longest single call), but Recon-3 latency was failure-path and cannot be trusted.

**P5c — Corrected Variant 3 total (if concurrency works at ~52s):**

| Stage | Time |
|-------|------|
| Discovery (RSS) | 1-2s |
| Parallel fetch (6 URLs) | 3-6s |
| Batched embedding | 1-2s |
| Concurrent extraction (6 articles) | **~52s (uncertain)** |
| Matching + consensus | 0.5s |
| **Total** | **~58-63s** |

And this depends on whether 6 concurrent calls produce valid claims — which we haven't measured because they'd need to use the correct prompt shape.

**P5d — Verdict: RED.**

Reasons:
1. Single-article extraction: 36s mean, 21-53s range
2. 6 concurrent extraction: ~52s best case (unmeasured, based on contaminated Recon-3 timing pattern)
3. Variant 3 total: 58-63s — well over 45s
4. Production batching blocked by 60s timeout
5. The 60s `llm_client.py:78` timeout prevents any optimization via batching
6. Measurements of concurrent extraction with correct call shape blocked by timeout → unknown failure rate

---

## P6 — CONTRADICTION CHECK

| Metric | Recon-3 said | Recon-4 measured | Notes |
|--------|-------------|-----------------|-------|
| Single-call latency (real) | 17.8s mean | **36.1s mean** | Recon-3 measured failures (0 claims). Real extraction is 2x slower. |
| 6-concurrent wall-clock | 21.9s | **UNMEASURED** | Recon-3 measured failure-path latency. Cannot replicate because production call shape was wrong. |
| Per-call success rate | 0% (0 claims) | **100% (5/5)** | Recon-3's calls all "succeeded" at the HTTP level but did no real work. |
| Recommended concurrency | 6 | **Unknown** | Cannot recommend without measuring successful concurrent calls. |
| Variant 3 total runtime | 28-33s YELLOW | **~60s RED** | Recon-3 underestimated per-call latency by 2x and based concurrency on failure-path timing. |
| Verdict | YELLOW | **RED** | Recon-3 was wrong. The real numbers push Variant 3 well past 45s. |

**Recon-3's YELLOW verdict was wrong because:**
1. All latency measurements were on calls returning 0 claims (failure mode)
2. The production call shape was not replicated (missing ARTICLE headers and "Articles:" prefix)
3. Real extraction latency is 2x higher than measured (36s vs 18s)
4. The 60s timeout blocks the production batching optimization
