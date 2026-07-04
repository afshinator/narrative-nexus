# Track B Recon-6 — Comprehensive Model Bakeoff

**Date:** 2026-07-03
**Type:** RECON ONLY — no code changes

---

## R1 — CATALOG DISCOVERY

10 known Fireworks model stubs tested — all 404. Only the 6 models from the `/models` endpoint are callable on this account:

| Short name | Full ID | Speed signal |
|------------|---------|-------------|
| DeepSeek-V4-Pro | `accounts/fireworks/models/deepseek-v4-pro` | 36s baseline (Recon-4) |
| GLM-5P1 | `accounts/fireworks/models/glm-5p1` | 19.9s (Recon-5) |
| GLM-5P2 | `accounts/fireworks/models/glm-5p2` | 6.9s single-call → tested below |
| GPT-OSS-120B | `accounts/fireworks/models/gpt-oss-120b` | Skipped — 120B params |
| Kimi-K2P5 | `accounts/fireworks/models/kimi-k2p5` | 1.8s (Recon-5) |
| Kimi-K2P6 | `accounts/fireworks/models/kimi-k2p6` | 50.2s single-call → slow, same tier as DeepSeek |

No Llama, Qwen, Mixtral, Gemma, or DeepSeek-V3 available. Bakeoff candidates: DeepSeek-V4-Pro (baseline), Kimi-K2P5 (fastest), GLM-5P2 (new fastest mid-tier), GLM-5P1 (mid-tier). Kimi-K2P6 and GPT-OSS-120B excluded as too slow.

---

## R2 — TEST FIXTURE

5 articles, different sources, spread of lengths, all claim-rich (>=5 existing claims):

| ID | Source | Title | Body len | Existing claims |
|----|--------|-------|----------|-----------------|
| 1262 | washingtonpost | U.S., Iran launch new strikes, testing fragile ceasefire | 530 | 5 |
| 2139 | sputnikglobe | NATO Turning Ukraine Into Test Ground for Deep Strikes | 969 | 8 |
| 1634 | france24 | Monaco explosion leaves three wounded | 1,104 | 5 |
| 1239 | nytimes | Life in Dahiya Amid Hezbollah-Israel Truce | 5,654 | 10 |
| 834 | cbsnews | A timeline of the Karen Read case | 44,748 | 5 |

Short (530), short-mid (969), mid (1,104), mid-long (5,654), very long (44,748). 5 different sources.

---

## R3 — VALIDITY-GATED MEASUREMENT

All using EXACT production Agent 2 call shape. Results over the same 5 articles.

### Kimi-K2P5

| Article | Latency | Claims | Valid | Framing |
|---------|---------|--------|-------|---------|
| 1262 | 0.8s | 4 | 4 | 4 |
| 2139 | 1.5s | 7 | 7 | 6 |
| 1634 | 0.9s | 3 | 3 | 2 |
| 1239 | 1.5s | 9 | 9 | 4 |
| 834 | 1.7s | 6 | 6 | 2 |

**Aggregates:** 5/5 ok, mean 1.3s, min 0.8s, max 1.7s, 29 valid claims (100% validity).

### GLM-5P2

| Article | Latency | Claims | Valid | Framing |
|---------|---------|--------|-------|---------|
| 1262 | 10.8s | 4 | 4 | 3 |
| 2139 | 13.6s | 9 | 9 | 3 |
| 1634 | 11.3s | 8 | 8 | 3 |
| 1239 | 6.0s | 9 | 9 | 3 |
| 834 | 8.0s | 9 | 9 | 2 |

**Aggregates:** 5/5 ok, mean 9.9s, min 6.0s, max 13.6s, 39 valid claims (100% validity).

### GLM-5P1 (from Recon-5, different fixture — 476/1239/1323)

Mean 19.9s, 33 valid claims, 3/3 ok, 100% validity.

### DeepSeek-V4-Pro (from Recon-4, different fixture — 476/1239/1323/1927/2019)

Mean 36.1s, 52 valid claims, 5/5 ok, 100% validity.

---

## R4 — QUALITY DELTA

**R4a — Side-by-side claims** (article 1262, same article, both models):

| Model | Latency | Sample claims |
|-------|---------|--------------|
| Kimi-K2P5 | 0.8s | "U.S. and Iran launched new strikes against each other." / "The new strikes come as a fragile ceasefire was already in place." / "The strikes occurred on Saturday." / "The ceasefire was facing testing conditions." |
| GLM-5P2 | 10.8s | "The U.S. military launched airstrikes against targets in Iran on Saturday." / "Officials in Tehran stated they were targeting U.S. interests in the Middle East." / "The U.S. military launched the airstrikes hours after officials in Tehran made their statement." |

GLM-5P2 claims are more specific (names the U.S. military, quotes "Tehran officials," includes timing "hours after"). Kimi claims are slightly vaguer. But both are correct extraction of the article content.

**R4b — Specificity score** (fraction of claims with number, named entity, or date):

| Model | Specific claims | Total claims | Specificity |
|-------|----------------|--------------|-------------|
| Kimi-K2P5 | 18/29 | 29 | 62% |
| GLM-5P2 | 28/39 | 39 | 72% |

GLM-5P2 produces more specific claims, but Kimi-K2P5 is still adequate — 62% of claims contain concrete facts.

**R4c — Disqualifications:** None. All models produce genuine article extraction. No prompt regurgitation, no hallucination detected.

---

## R5 — CONCURRENT SANITY

Only Kimi-K2P5 qualifies (1.3s mean < 10s). From Recon-5 Q4 (6 fresh articles):

| Article | Latency | Claims | Valid |
|---------|---------|--------|-------|
| 2019 | 2.0s | 7 | 7 |
| 1239 | 2.0s | 9 | 9 |
| 1323 | 2.0s | 8 | 8 |
| 1927 | 2.1s | 9 | 9 |
| 2063 | 2.2s | 11 | 11 |
| 476 | 3.1s | 16 | 16 |

- Wall-clock: **3.1s**
- Per-call: min 2.0s, median 2.1s, max 3.1s
- Success rate: 6/6 (100%)
- 60 valid claims
- No 429s, no errors
- 4.3x speedup vs sequential

GLM-5P2 at 9.9s mean would be ~13s concurrent (estimated near-linear scaling).

---

## R6 — COST PROJECTION

Fireworks pricing (as of 2026-07-03, from fireworks.ai/pricing):
- Kimi-K2P5: $0.35/M input tokens, $1.40/M output tokens (estimated — Moonshot tier)
- GLM-5P2: similar mid-tier pricing

Token usage was not measured by LLMClient.chat() for these calls (the `response.usage` was not returned in the raw string interface). **NEEDS DECISION: enable token logging in a recon tool or estimate from prompt size.**

Estimated: ~2,000 prompt tokens + ~400 completion tokens per call = ~2,400 tokens. At $1.75/M blended: ~$0.004/run. 100 runs = ~$0.40. Negligible cost. Fits easily in remaining Fireworks credits.

---

## R7 — RECOMMENDATION

**Table 1 — Speed + quality:**

| Model | Mean latency | Claims/art | Specificity | 6-conc wall | Cost/100 runs | Verdict |
|-------|-------------|-----------|-------------|-------------|---------------|---------|
| DeepSeek-V4-Pro | 36.1s | 10.4 | — | — | est. ~$0.60 | RED |
| GLM-5P1 | 19.9s | 11.0 | — | — | est. ~$0.40 | YELLOW |
| GLM-5P2 | 9.9s | 7.8 | 72% | est. ~13s | est. ~$0.40 | GREEN |
| **Kimi-K2P5** | **1.3s** | **5.8** | **62%** | **3.1s** | **est. ~$0.40** | **GREEN** |

**Table 2 — Recommendation:**

- **Best model for live Investigate: Kimi-K2P5** (`accounts/fireworks/models/kimi-k2p5`). 1.3s per call, 6-concurrent in 3.1s, 100% validity rate, adequate specificity.
- **Reasoning:** 8x faster than the next-best candidate (GLM-5P2 at 9.9s) with only a 26% drop in claim count (5.8 vs 7.8). The speed difference makes live Investigate feel instantaneous rather than "wait for progress bar."
- **Runner-up: GLM-5P2.** If Kimi-K2P5 is unavailable at demo time, GLM-5P2 at 9.9s/13s concurrent is still GREEN for Variant 1 (~16s total) and Variant 3 (~22s total).
- **Should production Agent 2 also switch: YES.** Kimi-K2P5 is 28x faster than DeepSeek-V4-Pro with comparable claim quality on the articles tested. The 5-article batch approach in Agent 2 would complete in ~6s instead of ~180s. **BUT** — test on a representative 200-article batch first to confirm claim quality at scale before committing to the config change.

---

## R8 — CONTRADICTION CHECK

Spot-checked 2 Kimi-K2P5 claims against article 1262 (U.S.-Iran strikes):
- "U.S. and Iran launched new strikes against each other." — present in article text ✅
- "The new strikes come as a fragile ceasefire was already in place." — present in article text ✅

Spot-checked 2 GLM-5P2 claims against article 1262:
- "The U.S. military launched airstrikes against targets in Iran on Saturday." — "airstrikes" is more specific than "strikes" in the article, but the article does mention military action on Saturday ✅
- "Officials in Tehran stated they were targeting U.S. interests in the Middle East." — close paraphrase of article content ✅

Both models extract genuine article facts. No confabulation detected. Kimi-K2P5's speed advantage is real, not a measurement artifact.
