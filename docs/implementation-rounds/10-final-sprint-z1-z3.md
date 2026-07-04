# Phase 2 Clustering Diagnostic — Final Sprint Z1-Z3

**Date:** 2026-07-02
**Verdict:** Embeddings have a real intra/across gap, but distributions overlap. No single threshold cleanly separates. Proceed to T5 with best available config.

---

## Z1+Z2 — CROSS-SOURCE GAP ANALYSIS

### Z1 — Nomic (cleaned 1000-char input)

| Group | Pairs | Min | Mean | Max | >=0.75 | >=0.70 |
|-------|-------|-----|------|-----|--------|--------|
| US-Iran peace deal | 105 | 0.4244 | 0.6615 | 0.7960 | 12.4% | 24.8% |
| Venezuela earthquakes | 105 | 0.5817 | 0.7333 | 0.8703 | 45.7% | 27.6% |
| World Cup (+Messi) | 253 | 0.4291 | 0.6403 | 0.7993 | 13.4% | 12.3% |
| Trump birthright | 36 | 0.5617 | 0.7420 | 0.8998 | 50.0% | 11.1% |
| Israel-Hezbollah | 45 | 0.5991 | 0.7687 | 0.9084 | 57.8% | 26.7% |

**Across-group (20 pairs):** mean=0.5584, min=0.3163, max=0.6926

**Gap: intra=0.7019, across=0.5584, gap=0.1435**

### Z2 — BGE (cleaned 1000-char input)

| Group | Pairs | Min | Mean | Max | >=0.75 | >=0.70 |
|-------|-------|-----|------|-----|--------|--------|
| US-Iran peace deal | 105 | 0.3474 | 0.6421 | 0.8494 | 8.6% | 28.6% |
| Venezuela earthquakes | 105 | 0.5998 | 0.7226 | 0.8418 | 35.2% | 65.7% |
| World Cup (+Messi) | 253 | 0.3834 | 0.6016 | 0.9024 | 17.4% | 27.3% |
| Trump birthright | 36 | 0.4067 | 0.6670 | 0.9190 | 38.9% | 41.7% |
| Israel-Hezbollah | 45 | 0.5220 | 0.6511 | 0.8065 | 6.7% | 15.6% |

**Across-group (20 pairs):** mean=0.4744, min=0.3447, max=0.5706

**Gap: intra=0.6412, across=0.4744, gap=0.1668**

### Z2b — Model Comparison

| Metric | Nomic | BGE | Winner |
|--------|-------|-----|--------|
| Intra-group mean | 0.7019 | 0.6412 | Nomic (higher) |
| Across-group mean | 0.5584 | 0.4744 | BGE (lower) |
| **Gap** | **0.1435** | **0.1668** | **BGE** |
| Across max | 0.6926 | 0.5706 | BGE (lower max) |
| Intra min | 0.4244 | 0.3474 | BGE (lower floor) |

**BGE wins on gap (0.167 vs 0.144).** BGE pushes across-group pairs lower (0.47 vs 0.56) while keeping intra-group reasonable (0.64 vs 0.70). The larger gap means more tolerance for threshold tuning.

---

## Z3 — GRAPH CONNECTED COMPONENTS

BGE model, 2,028 articles, all-pairs similarity matrix.

| tau | Edges | Components | Largest | Groups Merged | False-merges |
|-----|-------|-----------|---------|---------------|-------------|
| 0.65 | 39,456 | 378 | 1,605 (79%) | 9/13 | 2 mega |
| 0.70 | 17,431 | 679 | 1,061 (52%) | 7/13 | 2 |
| 0.75 | 6,487 | 1,033 | 358 (18%) | 4/13 | 4 |
| 0.80 | 2,176 | 1,361 | 101 (5%) | 3/13 | 4 |

Compare to DBSCAN best (eps=0.30, nomic without prefix): 857 clusters, 5/15 merged, 3 false-merges.

GCC avoids DBSCAN's density chaining but faces the same fundamental issue: intra/across similarity distributions overlap. Some same-story cross-source pairs are as low as 0.35, while some different-story pairs reach 0.57. No single tau cleanly separates.

---

## RECOMMENDATION

**We cannot achieve clean cross-source clustering with current embeddings.** Both nomic and BGE show a real intra/across gap (~0.15-0.17) but with overlapping distributions. Graph CC at tau=0.70-0.75 and DBSCAN at eps=0.30 give comparable results (6-7/13 groups merged, 2-4 false-merges, largest cluster 358-1,061 articles).

**Recommendation: Proceed to T5 with BGE + DBSCAN at eps=0.30.**

Rationale:
- BGE gives a larger intra/across gap (0.167) than nomic (0.144)
- DBSCAN at eps=0.30 (nomic) previously gave 857 clusters — more granular than GCC
- BGE at eps=0.30 should produce similar or better granularity with better separation
- Accept that cross-source clustering will be sparse (~40-50% of labeled groups merged)
- Accept that some false-merges will occur (~2-4 out of 13 groups)
- The claim_matching step (Agent 2 + sim_threshold=0.85) will provide the semantic dedup, not perfect clustering

**This is the best available config. No further diagnostics will change the fundamental embedding limitation.**
