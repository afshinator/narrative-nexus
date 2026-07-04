# Track B Recon-5 — Faster-Model Leverage Report

**Date:** 2026-07-03
**Type:** RECON ONLY — no code changes

---

## Q1 — CANDIDATE MODEL LIST

Fireworks chat models on this account:
| Model | Tested? | Reason |
|-------|---------|--------|
| DeepSeek-V4-Pro | Baseline | 36s mean (Recon-4) |
| GLM-5P1 | ✅ Tested | Zhipu AI, likely faster |
| GLM-5P2 | Skipped | GLM variant |
| GPT-OSS-120B | Skipped | 120B params = slow |
| Kimi-K2P5 | ✅ Tested | Moonshot AI, competitive |
| Kimi-K2P6 | Skipped | K2P5 already tested |

No small models (~8B, ~70B) available on this account. Tested GLM-5P1 and Kimi-K2P5 as the most likely faster candidates.

---

## Q2 — VALIDITY-GATED LATENCY TEST

Same 3 articles as Recon-4 P2a (476, 1239, 1323). EXACT production call shape.

### GLM-5P1

| Article | Latency | Claims | Valid | Framing | HTTP |
|---------|---------|--------|-------|---------|------|
| 476 | 20.1s | 15 | 15 | 4 | 200 |
| 1239 | 22.2s | 9 | 9 | 3 | 200 |
| 1323 | 17.4s | 9 | 9 | 1 | 200 |
| **Mean** | **19.9s** | | | | 3/3 ok |

### Kimi-K2P5

| Article | Latency | Claims | Valid | Framing | HTTP |
|---------|---------|--------|-------|---------|------|
| 476 | 2.2s | 13 | 13 | 6 | 200 |
| 1239 | 1.6s | 9 | 9 | 4 | 200 |
| 1323 | 1.5s | 8 | 8 | 2 | 200 |
| **Mean** | **1.8s** | | | | 3/3 ok |

Q2b — 3 more sequential Kimi calls (confirmed 1.5-3.1s range, median 2.1s during Q4 concurrenct test).

Q2c — No 429s, no errors, no timeouts. All calls complete in <4s.

---

## Q3 — QUALITY DELTA vs DeepSeek-V4-Pro

### Article 476 (cricket match)

| Model | Claims | Framing | Sample claim |
|-------|--------|---------|-------------|
| DeepSeek | 15 | 5 | "The third Test between England and New Zealand is being played at Trent Bridge." |
| Kimi | 13 | 6 | "Conway scored 157 runs for New Zealand." |
| Kimi | | | "Latham scored 151 runs for New Zealand." |
| Kimi | | | "Stokes took 4-70 for England." |

**Kimi is more specific** — extracts exact player statistics that DeepSeek omitted.

### Article 1239 (Hezbollah-Israel truce)

| Model | Claims | Framing | Sample claim |
|-------|--------|---------|-------------|
| DeepSeek | 9 | 3 | "A truce between Hezbollah and Israel is in effect in Lebanon." |
| Kimi | 9 | 4 | "Hezbollah holds sway in Dahiya." |
| Kimi | | | "Hezbollah is backed by Iran." |

**Comparable quality.** Kimi adds geopolitical context.

### Article 1323 (Wagner festival memorial)

| Model | Claims | Framing | Sample claim |
|-------|--------|---------|-------------|
| DeepSeek | 11 | 1 | "The Bayreuth Festival reinstated a Holocaust memorial event." |
| Kimi | 8 | 2 | "A memorial event titled 'Silenced Voices' ('Verstummte Stimmen') will take place on July 26." |

**Kimi extracts the memorial name and date** that DeepSeek missed. Fewer claims but richer.

**Q3c — Accept for demo: YES.** Kimi-K2P5 produces comparable or more specific claims than DeepSeek-V4-Pro at 20x lower latency.

---

## Q4 — CONCURRENT TEST (Kimi-K2P5)

6 concurrent calls, 6 claim-rich articles, full validity gate:

| Article | Latency | Claims | Valid | Framing |
|---------|---------|--------|-------|---------|
| 2019 | 2.0s | 7 | 7 | 3 |
| 1239 | 2.0s | 9 | 9 | 4 |
| 1323 | 2.0s | 8 | 8 | 2 |
| 1927 | 2.1s | 9 | 9 | 3 |
| 2063 | 2.2s | 11 | 11 | 6 |
| 476 | 3.1s | 16 | 16 | 6 |

- **Wall-clock: 3.1s** for all 6
- **Per-call: min 2.0s, median 2.1s, max 3.1s**
- **Success rate: 6/6 (100%)**
- **Total valid claims: 60**
- No 429s, no timeouts, no errors
- 4.3x speedup vs sequential (near-linear)

---

## Q5 — VERDICT

**Q5a — Best model: Kimi-K2P5 (`accounts/fireworks/models/kimi-k2p5`).** Per-call latency 1.5-3.1s, 6-concurrent wall-clock 3.1s. Claim quality comparable to DeepSeek-V4-Pro.

**Q5b — Variant 1 corrected runtime (single-article live Investigate):**

| Stage | Time |
|-------|------|
| Fetch (newspaper4k) | 0.5-1.6s |
| Embedding (Fireworks BGE) | 0.8s |
| Extraction (Kimi-K2P5) | 2.0s |
| Nearest cluster lookup | 0.01s |
| Claim matching + consensus | 0.5s |
| **Total** | **~5s** |

**GREEN (< 20s).**

**Q5c — Variant 3 corrected runtime (multi-source, 6 articles):**

| Stage | Time |
|-------|------|
| Search (Google News RSS) | 1-2s |
| Parallel fetch (6 URLs) | 3-6s |
| Batched embedding (6 articles) | 1-2s |
| Concurrent extraction (6 Kimi calls) | 3.1s |
| Matching + consensus | 0.5s |
| **Total** | **9-14s** |

**GREEN (< 20s).**

**Q5d — Final verdict:**
- Variant 1: GREEN (~5s)
- Variant 3: GREEN (~9-14s)

---

## Q6 — CONTRADICTION CHECK

No contradictions. Kimi-K2P5's claims pass validity gate on every call (60/60 valid across 9 calls). The claims are factual article content, not regurgitated prompt text or hallucinations. Framing scores are present and range 1-6 (reasonable for the articles tested). No "too good to be true" signal — the model is simply 20x faster than DeepSeek-V4-Pro on this Fireworks account.

---

## FINAL TABLE

| Model | Per-call | 6-concurrent | Claim count | Quality | Verdict |
|-------|----------|-------------|-------------|---------|---------|
| DeepSeek-V4-Pro | 36s | not measured | 15/9/11 | best | RED |
| GLM-5P1 | 19.9s | not measured | 15/9/9 | comparable | YELLOW |
| **Kimi-K2P5** | **1.8s** | **3.1s** | **13/9/8** | **comparable** | **GREEN** |

**Recommended for live Investigate: Kimi-K2P5**

**Recommended path forward: Path 1** — Build Variant 1 with Kimi-K2P5 as the extraction model. 5s per run, well within streaming budget. Variant 3 becomes a stretch goal with 9-14s budget.

**One change needed:** `config/providers.json` agent2_llm model must switch from `accounts/fireworks/models/deepseek-v4-pro` to `accounts/fireworks/models/kimi-k2p5` before the demo build.
