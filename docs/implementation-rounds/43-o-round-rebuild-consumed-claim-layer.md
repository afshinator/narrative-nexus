# 43 — O-Round: Rebuild Consumed Claim Layer

**Date:** 2026-07-03
**Target DB:** /tmp/demo.db
**No commits made.**

---

## O0: VERIFY TRUNCATION DIAGNOSIS

Evidence from docs + DB:

- **B4 (doc 39):** Agent 2 produced 524 claims from 160 articles. After match: 283 claims, 241 merges, 186 sources linked.
- **M/N-round (doc 41):** Claims = 283, claim_variants = 0. Similarity measured on 283 surviving canonicals.
- **Current DB (after O3):** 827 claims from 164 articles (1 article with 0 claims: ID 290).

**Conclusion:** The M/N-round "similarity ceilings" (BGE max 0.8252, nomic max 0.8496) were measured on B4's post-merge residue of 283 canonical claims. The 241 merged pairs were already consumed. reset_claim_state deleted claim_variants without restoring them, permanently losing the duplicates. The O-round rebuilds the claim layer from scratch with a true un-merge fix.

---

## O1: FIX reset_claim_state.py

Added true un-merge logic:
- Before deleting claim_variants, RESTORE each variant as an independent claim row (original text, article_id, cluster_id from article's current claim).
- Rebuild claim_sources 1:1 after restoration.

Unit test: 4 claims → simulated merge to 3 (1 variant) → reset → 4 claims restored. **PASS.**

Code: `/project/narrative-nexus/scripts/reset_claim_state.py` (full rewrite with variant restoration).

---

## O2: BACKUP

```
/tmp/demo-pre-rebuild.db  3.8M
/tmp/demo.db              3.8M
```

---

## O3: FRESH CLAIM LAYER

Deleted all claims/claim_sources/claim_variants/article_framing. Ran Agent 2 on all 165 body-bearing articles.

- **Chunk 1-4 (background):** 90 articles, 431 claims (process killed by timeout)
- **Chunk 5-7 (background):** 45 articles, 222 claims (process completed)
- **Foreground:** 29 articles, 174 claims (execute_code timed out, 7 done)
- **Background:** 23 articles, 196 claims (process completed)
- **Final:** 1 article (ID 290) returned 0 claims after 182s (extraction failure)

**Total: 827 claims, 164 articles processed, 1 remaining (0 claims).**

**Per-story claims:**
- Venezuela: 417
- Hormuz: 108
- Heatwave: 280
- Anthropic: 22

---

## O4 ADDENDUM: CHECK BEFORE MATCHING

**(a) Orphaned claims:** 0. All claims have cluster_ids that exist in clusters.

**(b) Per-story claim-to-cluster mapping:** ALL 827 claims are in temp clusters (164 clusters, "Temp" titles). E2 story clusters (658, 666, 667, 668) have **0 claims**.

**Decision: NO** — do not match on junk clusters. Run recluster_all first.

### Recluster_all (BGE, eps=0.35, ms=2, guard ON):

- Hygiene guard: 165 cached hits, 0 re-embedded. **PASS.**
- Blob guard: 154-article cluster split at eps=0.25 → 83 + 4 + 22 + 45. Then 83 split → 80 + 3.
- **15 clusters created**, 827 claims reassigned.

**Per-story separation reproduces E2:**

| Story | Cluster | Articles | Sources | Claims |
|-------|---------|----------|---------|--------|
| Venezuela | 889 | 80 | 21 | 404 |
| Hormuz | 897 | 22 | 10 | 90 |
| Heatwave | 898 | 44 | 12 | 256 |
| Anthropic | 899 | 6 | 5 | 16 |

### MATCH + CONSENSUS:

**match_all_clusters (nomic, sim=0.85):**
```
Clusters with claims: 15
Clusters processed (had merges): 14
Total merges: 507
Sources linked: 365
Elapsed: 11.6s
```

Claims after: 320
Claims >=2 distinct sources: 64
Claims >=2 T1/T2 pool sources: 32

**Per-cluster merge counts:**
```
Cluster 889 (Venezuela): 133 claims, 271 merges
Cluster 898 (Heatwave): 89 claims, 167 merges
Cluster 897 (Hormuz): 49 claims, 41 merges
Cluster 899 (Anthropic): 10 claims, 6 merges
```

**10 merged pairs (quality sample):**
```
sim=0.9268 [CROSS] "Iran stated on Saturday that it had closed the Str..." → "Iran's central military command announced on Satur..."
sim=0.9683 [CROSS] "The earthquakes caused damage to buildings in the..." → "The earthquakes caused damage in Caracas and other..."
sim=0.8976 [CROSS] "According to the United States Geological Survey, ..." → "The earthquakes caused damage in Caracas and other..."
sim=0.8998 [CROSS] "The earthquakes forced the closure of Venezuela's..." → "The earthquakes caused damage in Caracas and other..."
sim=0.8810 [CROSS] "Delcy Rodríguez said that 20 aftershocks followed..." → "On Thursday, June 25, 2026, Interim President Delc..."
```

**5 near-misses (0.80-0.85) on cluster 889:**
```
sim=0.8496 | apnews: "Earthquakes typically occur along edges of tectoni..." | batimes: "The earthquakes occurred within less than a minute..."
sim=0.8491 | MercoPress: "At least 172 people remain trapped under the rubbl..." | batimes: "People are trapped beneath rubble of collapsed bui..."
sim=0.8487 | theguardian: "A senior administration official said on Monday th..." | theguardian: "The US official said the repair work aims to allow..."
sim=0.8487 | nytimes: "The U.S. demanded allegiance from the successor of..." | theintercept: "U.S. President Donald Trump stated that America wo..."
sim=0.8486 | nytimes: "Delcy Rodriguez, Venezuela's president, is accused..." | NHK World: "On Thursday, June 25, 2026, Interim President Delc..."
```

Total near-misses in cluster 889: 178

**Agent 3 (consensus):**
```
Agent 3: 15 clusters, 6 classified
Claims by state: PENDING=314, CONSENSUS_ABSORBED=6
Absorbed TOTAL: 6
```

**Absorbed per story:**
- Venezuela: 3 absorbed (sources=15, 13, 12)
- Hormuz: 0 absorbed (top: 2/4 pool = 50% < 65%)
- Heatwave: 3 absorbed (sources=9, 8, 6)
- Anthropic: 0 absorbed (top: 2/3 pool = 66.7% < 75%)

---

## O5: backfill_snapshots --since 2026-04-01

```
95 dates, 10545 rows
```

**R_val + R_orig (2026-07-04):** Non-zero R_val for many sources:
```
apnews:    T1  R_orig=96.0  R_val=17.0
bbc:       T1  R_orig=88.0  R_val=35.0
npr:       T1  R_orig=50.0  R_val=35.0
theguardian: T1  R_orig=100.0 R_val=22.0
nytimes:   T2  R_orig=79.0  R_val=87.0
aljazeera: T3  R_orig=62.0  R_val=70.0
globaltimes: T3 R_orig=54.0  R_val=74.0
theintercept: T4 R_orig=12.0  R_val=96.0
cbsnews:   T2  R_orig=38.0  R_val=91.0
abcnews:   T2  R_orig=4.0   R_val=100.0
```

T6a: 0 | T6b: 0 — both PASS.

---

## O6: Per-story one-line + VERDICT

| Story | Own cluster? | Absorbed >0? |
|-------|-------------|-------------|
| Venezuela | YES (889, 80 art, 21 src) | **YES (3)** |
| Hormuz | YES (897, 22 art, 10 src) | NO (0) |
| Heatwave | YES (898, 44 art, 12 src) | **YES (3)** |
| Anthropic | YES (899, 6 art, 5 src) | NO (0) |

**VERDICT: PARTIAL — on trajectory to judge-ready.**

**Single limiting factor:** Absorption is thin (6/320 = 1.9%). Hormuz and Anthropic are close but below threshold:
- **Hormuz:** Top claim "The US conducted strikes on Iran." — pool=2/4=50%, needs 65%. One more T1/T2 source reporting this claim would push it to 3/4=75%.
- **Anthropic:** Top claim "An official said that Anthropic's Mythos model found vulnerabilities..." — pool=2/3=66.7%, needs 75%. One more T1/T2 source would push it to 3/3=100%.

The Venezuela and Heatwave stories demonstrate the full pipeline works: per-story cluster separation, 507 claim merges, multi-source claims, and consensus absorption. The smaller stories (Hormuz: 22 articles, 10 sources; Anthropic: 6 articles, 5 sources) lack the critical mass of pool sources to reach consensus thresholds.
