# Phase 2 Gate Report — T1-T4

**Date:** 2026-07-02
**Status:** STOPPED AT GATE — awaiting eps approval for T5

---

## T1 — FIX THE 90-DAY ZOMBIE BUG ✅

**Root cause:** `agent3_consensus.py:71-73` patched `determine_state()` output after the fact — single-source claims at 100% got ABSORBED by the state machine, then force-flipped to PENDING. At day 90, same cycle repeated forever.

**Fix:**
- `pipeline/resolution.py` — `determine_state()` now accepts `reporting: int | None` parameter. When `reporting < MIN_CORROBORATION` (2), absorption is blocked and the claim falls through to day-based logic.
- `pipeline/agent3_consensus.py` — passes `reporting=reporting` to `determine_state()`, removed post-hoc patch. Removed unused `MIN_CORROBORATION` import.

**Tests (10/10 pass):**
- `test_single_source_below_min_corroboration_day_89` → PENDING
- `test_single_source_below_min_corroboration_day_90` → UNRESOLVED (was zombie)
- `test_two_source_at_threshold_absorbed` → ABSORBED (pct=65, threshold=65, reporting=2)
- `test_two_source_below_threshold_pending` → PENDING
- `test_two_source_below_threshold_day_90_unresolved` → UNRESOLVED
- 5 existing tests unchanged (backward compatible when `reporting=None`)

---

## T2 — EMBEDDING MODEL HYGIENE ✅

**T2a:** Cache query in `agent1_intake.py:72` filtered on `model` only — **NOT on dim**. Fixed: query now fetches `dim` column, guard loop checks it.

**T2b:** Mixed-dim vectors would crash `np.array()` with `ValueError: inhomogeneous shape` — not silently corrupt. Guard prevents reaching that point.

**T2c:** `MODEL_DIMS` dict added to `pipeline/embedding_client.py` mapping model names to expected dimensions. Cached vectors with wrong dim are logged as warnings and treated as cache miss → re-embedded.

**Files changed:**
- `pipeline/embedding_client.py` — +MODEL_DIMS dict
- `pipeline/agent1_intake.py` — dim-aware cache lookup + guard

---

## T3 — RECLUSTER PATH ✅

`scripts/recluster_all.py` — 307 lines.
1. Embeds (or loads cached) ALL articles with body_status='AVAILABLE' using nomic
2. Deletes all rows from clusters
3. Runs time-windowed DBSCAN over all articles, creating fresh clusters
4. Reassigns claims.cluster_id = the new cluster of the claim's article
5. Re-runs vertical classification per cluster
6. Prints: cluster count, sources-per-cluster histogram, articles-per-cluster histogram, largest cluster size

Claims/claim_sources/claim_variants are NOT modified. Loads `.env` for API keys.

---

## T4a — 15 LABELED STORY GROUPS

All groups confirmed as the same real-world events across >= 3 different sources.

| # | Group | Sources | Key Article IDs |
|---|-------|---------|-----------------|
| 1 | US-Iran peace deal | 15 | 451, 1745, 1522, 1492, 345, 133, 2175, 789, 1255, 1842, 2199, 169, 189, 153, 2198 |
| 2 | Venezuela earthquakes | 21 | 1491, 1695, 106, 332, 2216, 2048, 2201, 1687, 2200, 1678, 772, 692, 567, 249, 1688 |
| 3 | World Cup 2026 | 6 | 1748, 1720, 1933, 1650, 1641, 838, 1263, 1328, 1275, 1276, 1230, 1340, 1723, 1719, 1708 |
| 4 | Japan M7.2 earthquake | 3 | 1498, 134, 1525, 1863 |
| 5 | Messi at World Cup | 3 | 1752, 1746, 1737, 1732, 1727, 1726, 1723, 1719, 1703, 1698 |
| 6 | Trump birthright citizenship | 12 | 711, 2729, 2707, 2725, 3152, 2837, 2834, 453, 312, 118 |
| 7 | SNAP benefits cuts | 3 | 2078, 145, 2473 |
| 8 | Western Europe heat wave | 11 | 186, 244, 174, 1564, 135, 1483, 187, 193, 180, 175 |
| 9 | Israel-Gaza-Hezbollah | 10 | 168, 2184, 2173, 453, 1861, 1239, 2148, 2123, 1885, 2910 |
| 10 | China-EU trade dispute | 4 | 1630, 1562, 1555, 1608, 1598, 1556, 1551, 1548, 764, 540 |
| 11 | Anthropic AI export ban | 7 | 157, 175, 486, 1493, 830 |
| 12 | Strait of Hormuz closure | 5 | 1518, 147, 131, 307, 306 |
| 13 | North Korea missile/navy | 5 | 336, 155, 1430, 2559, 3485 |
| 14 | Ukraine drone attack | 5 | 164, 277, 327, 1838 |
| 15 | Lebanon Hezbollah deal | 5 | 453, 2148, 2123, 1885, 2910 |

---

## T4b — EPS SWEEP RESULTS

Embedding: Fireworks nomic-ai/nomic-embed-text-v1.5 (768-dim), 2,028 articles, 18.4s

| eps | Clusters | Groups Merged | Merge Rate | Over-merges | Largest Cluster |
|-----|----------|---------------|------------|-------------|-----------------|
| 0.30 | 857 | 5/15 | 31.3% | 3 (1 mega: 930 arts) | 930 |
| 0.35 | 496 | 6/15 | 33.9% | 2 (1 mega: 1,297 arts) | 1,297 |
| 0.40 | 328 | 6/15 | 33.9% | 2 (1 mega: 1,421 arts) | 1,421 |
| 0.45 | 226 | 6/15 | 33.9% | 2 (1 mega: 1,431 arts) | 1,431 |
| 0.50 | 161 | 6/15 | 33.9% | 2 (1 mega: 1,432 arts) | 1,432 |

Critical finding: at eps >= 0.35, a single mega-cluster swallows 64-71% of all 2,028 articles. The nomic embeddings produce very low pairwise cosine distances for most news articles — they capture "general news language" similarity rather than topic-specific similarity.

---

## T4c — RECOMMENDATION

**Recommended eps: 0.30** — the least bad option. Highest cluster count (857), lowest over-merge severity.

**Root cause is the embedding model, not eps.** Nomic-embed-text-v1.5 produces embeddings where most articles cluster tightly regardless of topic. Options to fix:
1. Try lower eps (0.15-0.25) to force separation
2. Switch embedding model (OpenAI text-embedding-3-small)
3. Pre-process text to emphasize distinctive keywords
4. Secondary clustering pass within mega-clusters

**Concrete recommendation: eps=0.30 for T5** with the understanding that clustering quality will be poor with nomic, and a follow-up phase should address the embedding model choice.
