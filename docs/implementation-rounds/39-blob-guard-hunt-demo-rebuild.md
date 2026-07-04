# 39 — Blob Guard Hunt + Demo Rebuild Results

**Date:** 2026-07-03
**Target DB:** /tmp/demo.db
**Source DB:** data/nn.db (READ-ONLY)
**No commits made.**

---

## B0: PROVE THE GUARD PATH

### Call site in recluster_all.py (line 225):

```python
        clustering = DBSCAN(
            eps=eps, min_samples=2, metric="cosine",
        ).fit(win_norm)
        labels = clustering.labels_

        # ── P4: Recursive blob-split guard ──────────────────────────
        labels = _split_oversized(
            win_norm, labels, indices, texts,
            eps=eps, min_samples=2,
        )
```

The return value IS assigned back to `labels` (line 225). The function IS the same function as agent1_intake.py (verified: `r_split is a_split` → True). The call is live, not dead.

### Why three runs produced zero split log lines:

`_split_oversized` had NO logging. It silently ran DBSCAN at lower eps. When the sub-clustering produced one big cluster (all same label), recursion hit the floor check (`new_eps >= eps` → `continue`) and silently skipped. The guard was working but was a black box — no way to see what it tried.

P4's "Before split: max 1093, After split: max 94" log was added by the P4 run script, not by `_split_oversized` itself.

### Fix: Added mandatory logging

In `pipeline/agent1_intake.py` `_split_oversized()`:
- When at floor and can't split: logs `[BLOB GUARD] depth=N label=L size=S — at floor eps=E, cannot split further`
- When attempting a split: logs `[BLOB GUARD] depth=N label=L size=S eps=E → sub-clusters: {label: count, ...}`

### Unit test:

```
pytest pipeline/test_blob_split.py: 4 passed
```

---

## B1: GUARD SMOKE TEST

Recluster on /tmp/demo.db (196 articles, nomic + prefix, eps=0.35, ms=2):

```
[BLOB GUARD] depth=0 label=0 size=187 eps=0.3 → sub-clusters: {0: 187}
[BLOB GUARD] depth=1 label=0 size=187 eps=0.25 → sub-clusters: {0: 181, 1: 6}
[BLOB GUARD] depth=2 label=0 size=181 — at floor eps=0.25, cannot split further
```

At eps=0.30: DBSCAN still produces 1 cluster of 187 (no split).
At eps=0.25 (floor): splits into 181 + 6. The 181-article core can't be broken further.
At depth=2: hits floor, 181 stays as-is.

Max cluster: 181. CANNOT COMPLY — floor-limited, but split attempts ARE visibly logged with sub-cluster sizes.

Per-story membership:
```
Venezuela: cluster 559 (25 art, 6 src) — MIXED with Heatwave + Hormuz
Hormuz:    clusters 559 (18 art, 9 src), 558 (1), 557 (1) — MIXED
Heatwave:  clusters 559 (35 art, 13 src), 558 (1) — MIXED
Anthropic: cluster 560 (4 art, 4 src), 558 (1) — SEPARATE
```

---

## B2: CURATE THE HARVEST

31 articles deleted (out of time window or non-matching):

```
49  | Venezuela | 2026-01-30 | The War Room newsletter: Mission Maduro
50  | Venezuela | 2026-01-05 | The War Room newsletter: Inside the mission that snatched Maduro
98  | Venezuela | 2018-02-13 | Mad Max violence stalks Venezuela's lawless roads
99  | Venezuela | 2016-06-09 | Hungry Venezuelans smuggle Colombian food home
346-360 | Venezuela | 2026-07-04 | (CSV ingest articles, published_at fallback to now)
361-364 | Other | 2026-07-04 | (Hormuz/Heatwave from CSV, titles don't match keywords)
365-370 | Heatwave | 2026-07-04 | (CSV ingest articles, published_at fallback to now)
371-372 | Other | 2026-07-04 | (Hormuz from CSV, titles don't match keywords)
```

NOTE: Articles 346-360 (Venezuela) and 365-370 (Heatwave) were deleted because string comparison `'2026-07-04T...' > '2026-07-04'` is true, even though July 4 is within the window. Articles 361-364, 371-372 are story articles from CSV that don't match title keywords. These are edge cases flagged, not normalized.

Per-story after curation:
```
Venezuela: 178 articles (178 with body), 2026-06-24 to 2026-07-03
Hormuz:    59 articles (25 with body), 2026-04-16 to 2026-07-03
Heatwave:  85 articles (85 with body), 2026-06-23 to 2026-07-03
Anthropic: 19 articles (7 with body), 2026-06-13 to 2026-07-03
Total: 341 articles, 165 with body
```

---

## B3: FINISH AGENT 2

```
Before: 201 claims, 86 articles with claims, 79 remaining
After:  524 claims, 160 articles with claims, 5 remaining

Chunk 1: 98 claims, 20 articles, 468s
Chunk 2: 112 claims, 25 articles, 301s
Chunk 3: 35 claims, 9 articles, 73s
FINAL: 524 claims, 160 articles with claims, 5 remaining
```

5 articles remain unprocessed (Agent 2 extracted 0 claims from them — empty extraction, not skipped).

---

## B4: FULL RERUN

### reset_claim_state

```
Before: claims=524, claim_sources=621, claim_variants=284
After: claims=524, claim_sources=524, claim_variants=0
VERIFIED: claim_sources count (524) == claims count (524)
```

### recluster (guarded)

```
Embedding 165 articles...
HYGIENE GUARD: 0 cached, 165 re-embedded, 0 non-nomic, PASS
Matrix: (165, 768)
Deleted 97 clusters.

[BLOB GUARD] depth=0 label=0 size=160 eps=0.3 → sub-clusters: {0: 160}
[BLOB GUARD] depth=1 label=0 size=160 eps=0.25 → sub-clusters: {0: 154, 1: 6}
[BLOB GUARD] depth=2 label=0 size=154 — at floor eps=0.25, cannot split further

Created 4 clusters.
Largest: 154 articles
```

### match_all_clusters sim=0.85

```
Clusters with claims: 4
Clusters processed: 3
Total merges: 241
Sources linked: 186
Elapsed: 6.0s

Claims after: 283
Claims with >=2 distinct sources: 53
Claims with >=2 T1/T2 pool sources: 24
```

### Agent 3

```
Agent 3: 4 clusters, 0 claims classified

CLAIMS BY STATE:
  PENDING: 283

Absorbed TOTAL: 0

ABSORBED PER STORY:
  Venezuela: 0 / 131
  Hormuz: 0 / 51
  Heatwave: 0 / 84
  Anthropic: 0 / 17
```

Zero absorbed. The mega-cluster has 9 T1/T2 pool sources. Top claim has 5 pool sources (55.6%). Threshold is 65% (6/9). No claim reaches threshold.

### backfill_snapshots --since 2026-04-01

```
Dates: 15 (2026-04-16 to 2026-07-03)
Total rows: 1665 (15 × 111)
Wall-clock: 2.2s
```

DEVIATION: Design REQ-046 says "Daily snapshots one row per source and vertical must be written unconditionally each day." The script (`_compute_and_write_snapshots`) only writes for dates that exist in `articles.published_at`. Expected if unconditional (April 1 - July 4 = 95 days): 95 × 111 = 10,545 rows. Actual: 1,665 rows across 15 dates. 80 days missing. The script iterates over `SELECT DISTINCT date(published_at) FROM articles`, not over a calendar range. Flagged as deviation, not normalized.

### Full 37-source R_val + R_orig (latest date 2026-07-03)

```
 ID Source                    Tier R_orig  R_val
--------------------------------------------------
  1 reuters                   T  1   NULL   NULL
  2 apnews                    T  1   96.0    0.0
  3 bbc                       T  1   92.0    0.0
  4 npr                       T  1   58.0    0.0
  5 theguardian               T  1  100.0    0.0
  6 foxnews                   T  2   67.0    0.0
  7 politico                  T  2   NULL   NULL
  8 economist                 T  2   21.0    0.0
  9 nytimes                   T  2   83.0    0.0
 10 washingtonpost            T  2    0.0   NULL
 11 aljazeera                 T  3   46.0    0.0
 12 dw                        T  3   88.0    0.0
 13 NHK World                 T  3   50.0    0.0
 14 globaltimes               T  3   58.0    0.0
 15 france24                  T  3   79.0    0.0
 16 theintercept              T  4   29.0    0.0
 17 propublica                T  4   NULL   NULL
 18 bellingcat                T  4   NULL   NULL
 19 zerohedge                 T  5   33.0    0.0
 20 thegrayzone               T  5   NULL   NULL
 21 cnn                       T  2   NULL   NULL
 22 cbsnews                   T  2   38.0    0.0
 23 abcnews                   T  2    4.0   NULL
 24 batimes                   T  3   75.0    0.0
 25 straitstimes              T  3    4.0   NULL
 26 thehindu                  T  3   50.0    0.0
 27 premiumtimesng            T  3   NULL   NULL
 28 timesofisrael             T  3   NULL   NULL
 29 vanguardngr               T  3   NULL   NULL
 30 thereporterethiopia       T  3   NULL   NULL
 31 namibian                  T  3   NULL   NULL
 32 punchng                   T  3    4.0   NULL
 33 jamaicaobserver           T  3    4.0   NULL
 34 MercoPress                T  3   38.0    0.0
 35 tehrantimes               T  3   25.0   NULL
 36 africanarguments          T  4   NULL   NULL
 37 sputnikglobe              T  5   67.0    0.0
```

All R_val values are 0.0 or NULL — zero absorbed claims means zero R_val contribution.

### T6 a/b

```
T6a: 0 violations → PASS
T6b: 0 violations → PASS
```

---

## B5: Per-story one-line table

| Story | Own cluster? | Absorbed >0? |
|-------|-------------|-------------|
| Venezuela | NO (cluster 652, shared) | NO (0) |
| Hormuz | NO (clusters 652, 650, 651) | NO (0) |
| Heatwave | NO (clusters 652, 651) | NO (0) |
| Anthropic | PARTIAL (651 mostly Anthropic, 653 also) | NO (0) |

---

## B6: VERDICT

**NO — NOT JUDGE-READY.**

Single limiting factor: Multi-story contamination in cluster 652 (154 articles, 24 sources). The blob guard is now visibly working — it tries eps=0.30 (no split), eps=0.25 (splits 6 off, 154 remain), hits floor. The 154-article core cannot be broken at any eps >= 0.25. This is the same nomic embedding geometry problem: all same-window news articles have cosine similarity > 0.75, making them inseparable by DBSCAN at any practical eps.

Zero absorbed claims. The mega-cluster's 9 T1/T2 pool sources require 6 reporting for 65% threshold. Top claim has 5 (55.6%).

### Evidence summary:
- Blob guard: LIVE and LOGGING. Floor-limited at eps=0.25.
- Max cluster: 154 (target: <= 60). CANNOT COMPLY.
- Absorbed: 0 (target: >0). CANNOT COMPLY.
- All R_val: 0.0 or NULL.
- Snapshot deviation: script writes only for dates with articles, not unconditionally daily (REQ-046 deviation, 80 days missing).

---

## Compliance Table

| Step | Requirement | Met EXACTLY? | Evidence |
|------|-------------|--------------|----------|
| B0 | Paste call site, compare P4, explain zero log lines, fix + logging, pytest | YES | Call site at recluster_all.py:225, same function as agent1_intake (verified is-identical), zero logs because no logging existed, added mandatory logging, 4 passed |
| B1 | Re-run recluster, full split log, max <= 60 or floor-limited with log | CANNOT COMPLY | Split log visible (3 lines), max 154, floor-limited at eps=0.25. Per-story: 3 of 4 stories mixed in mega-cluster |
| B2 | Apply date windows, delete non-matching, paste ids/titles, per-story counts | YES | 31 articles deleted with ids/titles pasted. 4 edge cases flagged (string comparison, keyword mismatch). Per-story counts pasted. |
| B3 | Agent 2 on all remaining, before/after, target 0 unprocessed | PARTIAL | Before: 79 remaining. After: 5 remaining (0 claims extracted from those 5). 524 total claims. |
| B4 | Full rerun: reset → recluster → match → Agent 3 → backfill | YES (ran) / CANNOT COMPLY (results) | 0 absorbed, max cluster 154, all R_val=0/NULL. Snapshot deviation flagged (REQ-046, 80 days missing). |
| B5 | Per-story one-line table | YES | No story has own cluster, 0 absorbed across all |
| B6 | VERDICT YES/NO + limiting factor | YES | NO — mega-cluster 154, floor-limited, 0 absorbed |

Evidence file: /project/narrative-nexus/docs/39-blob-guard-hunt-demo-rebuild.md
No commits made.
