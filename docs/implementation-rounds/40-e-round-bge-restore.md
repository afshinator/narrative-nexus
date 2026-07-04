# 40 — E-Round: Restore BGE Embedding Space + Demo Rebuild

**Date:** 2026-07-03
**Target DB:** /tmp/demo.db
**Source DB:** data/nn.db (READ-ONLY)
**No commits made.**

---

## E0: STATUS.md reconciliation

Diff:
```
-## PARKED
-
-- recluster_all vs P4 cluster-count discrepancy (max 94 vs 1,329, same params) — unresolved, not blocking; demo path switched to design-v1.2 §7 curated corpus.
+## RESOLVED
+
+- recluster_all vs P4 cluster-count discrepancy: RESOLVED. P1 sweep and P4 (max 94) ran on cached BGE vectors (F5-REDO baseline: embeddings table = 2,028 BGE). All true-nomic runs produced floor-limited mega-clusters (809 / 1,329 / 154). Locked params (eps=0.35, floor=0.25, sim=0.85) were calibrated in BGE space. Embedding model hereby locked to BAAI/bge-base-en-v1.5 on empirical grounds, superseding the nomic intent. "clustering:" prefix is nomic-specific and moot under BGE.
```

Evidence chain:
- P1 sweep + P4 (max 94): ran on cached BGE vectors (F5-REDO baseline confirmed 2,028 BGE)
- F5-REDO (nomic, no prefix): max 809
- F5-REDO-2 (nomic, prefix ON): max 1,329
- B0/B1 (nomic, prefix ON, 196 articles): max 181 → 154 after curation
- All nomic runs: floor-limited, guard cannot split below 60
- Conclusion: locked params calibrated in BGE space. BGE is the empirically correct model.

---

## E1: Config

providers.json line 7: nomic → BGE
```
"model": "BAAI/bge-base-en-v1.5",
```

Resolution chain check:
```
RESOLVED: provider=fireworks, model=BAAI/bge-base-en-v1.5
PASS: BAAI/bge-base-en-v1.5
```

Hygiene guard: keys on model string (`WHERE model != ?`). "clustering:" prefix code checks `"nomic" in self.model.lower()` → False for BGE → prefix is moot. BGE dim = 768 (same as nomic, so model string is the real differentiator, not dim).

---

## E2: Re-embed + recluster

```
Embedding provider: Fireworks AI (BAAI/bge-base-en-v1.5)

Step 1: Embedding 165 articles...
  HYGIENE GUARD:
    Cached nomic hits: 0
    Re-embedded (new): 165
    Non-nomic vectors in DB for these articles: 0
    Total vectors used: 165
    PASS: zero non-BGE vectors used
  Matrix shape: (165, 768)

Step 2: Deleting all clusters...
  Deleted 4 clusters.

Step 3: Time-windowed DBSCAN (eps=0.35, min_samples=2, window=14d)...
  [BLOB GUARD] depth=0 label=0 size=154 eps=0.3 → sub-clusters: {0: 83, -1: 4, 1: 22, 2: 45}
  [BLOB GUARD] depth=1 label=0 size=83 eps=0.25 → sub-clusters: {0: 80, -1: 3}
  [BLOB GUARD] depth=2 label=0 size=80 — at floor eps=0.25, cannot split further
  Created 15 clusters.

Cluster count: 15

Sources per cluster histogram:
    1 source(s):    10 clusters
    2 source(s):     1 clusters
    5 source(s):     1 clusters
    9 source(s):     1 clusters
   13 source(s):     1 clusters
   17 source(s):     1 clusters

Articles per cluster histogram:
    1 article(s):    10 clusters
    2 article(s):     1 clusters
    6 article(s):     1 clusters
   22 article(s):     1 clusters
   45 article(s):     1 clusters
   80 article(s):     1 clusters

Largest cluster: 80 articles
```

BGE SPLIT: The 154-article mega-cluster split into 83 + 22 + 45 + 4 noise at eps=0.30. The 83 split further into 80 + 3 at eps=0.25. Max 80, floor-limited.

Per-story membership:
```
Venezuela: cluster 658 (60 art, 17 src) — OWN CLUSTER, NO MIXING
Hormuz:    cluster 666 (21 art, 9 src) — OWN CLUSTER, NO MIXING
Heatwave:  cluster 667 (37 art, 13 src) — OWN CLUSTER, NO MIXING
Anthropic: cluster 668 (6 art, 5 src) — OWN CLUSTER, NO MIXING
```

Each story has its own primary cluster. Singletons are noise articles. No cross-story mixing.

Acceptance: max 80 > 60. CANNOT COMPLY on <=60 bound — but guard log shows floor with sub-cluster detail. The 80-article cluster is floor-limited at eps=0.25.

---

## E3: Rebuild claim layer

### reset_claim_state
```
Before: claims=283, claim_sources=404, claim_variants=241
After: claims=283, claim_sources=283, claim_variants=0
VERIFIED
```

### match_all_clusters sim=0.85
```
Clusters with claims: 14
Clusters processed: 0
Total merges: 0
Sources linked: 0
Elapsed: 6.3s

Claims after: 283
Claims >=2 distinct sources: 0
Claims >=2 T1/T2 pool sources: 0
```

0 merges. BGE embeddings at sim=0.85 do not merge any claims from different sources. Every claim stays 1-source.

### Agent 3
```
Agent 3: 15 clusters, 0 classified
PENDING: 283
Absorbed TOTAL: 0
```

### Top 5 claims arithmetic (no interpretation)

```
   ID Text                                                         Pool PoolSize    Pct Thresh Absorb?
  802 Sheera Frenkel is a New York Times tech reporter.               1        3  33.3%    75%      NO
  746 The World Weather Attribution study was released on Friday.     1        4  25.0%    75%      NO
  743 The British military reported that a vessel was hit by a pro    1        4  25.0%    65%      NO
  742 A United Nations agency paused the evacuation of ships throu    1        4  25.0%    65%      NO
  741 Trump's social media post did not identify the ship.            1        4  25.0%    65%      NO
```

Each claim: 1 pool source reporting, out of pool sizes 3-4. Pct 25-33%, thresholds 65-75%. No claim reaches threshold.

Root cause: 0 merges at sim=0.85 → every claim stays 1-source → no claim can reach the corroboration threshold (MIN_CORROBORATION=2).

---

## E4: Fix REQ-046

### Code change

scripts/backfill_snapshots.py rewritten from r_frame-only UPDATE to full 6-dimension compute over calendar range.

Old: iterated `SELECT DISTINCT date FROM snapshots` (only dates that already had snapshots)
New: iterates `datetime` calendar range from `--since` to `--until` (default: today), writing every source/vertical/day unconditionally.

```python
current = start
while current <= end:
    date_str = current.isoformat()
    rows = _compute_and_write_snapshots(conn, date_str=date_str, as_of=date_str + "T23:59:59+00:00")
    conn.commit()
    total_rows += rows
    current += timedelta(days=1)
```

### Run result

```
Deleted 1665 existing snapshots in range
Done. 95 dates, 10545 rows.
```

95 dates (2026-04-01 to 2026-07-04), 10,545 rows (95 × 37 × 3 = 10,545). Matches expected.

### Full 37-source R_val + R_orig (latest date 2026-07-04)

```
 ID Source                    Tier R_orig  R_val
--------------------------------------------------
  1 reuters                   T  1   NULL   NULL
  2 apnews                    T  1   96.0    0.0
  3 bbc                       T  1   92.0    0.0
  4 npr                       T  1   67.0    0.0
  5 theguardian               T  1  100.0    0.0
  6 foxnews                   T  2   54.0    0.0
  7 politico                  T  2   NULL   NULL
  8 economist                 T  2   17.0    0.0
  9 nytimes                   T  2   79.0   NULL
 10 washingtonpost            T  2    0.0   NULL
 11 aljazeera                 T  3   42.0   NULL
 12 dw                        T  3   88.0   NULL
 13 NHK World                 T  3   58.0    0.0
 14 globaltimes               T  3   67.0    0.0
 15 france24                  T  3   62.0   NULL
 16 theintercept              T  4   17.0    0.0
 17 propublica                T  4   NULL   NULL
 18 bellingcat                T  4   NULL   NULL
 19 zerohedge                 T  5   17.0   NULL
 20 thegrayzone               T  5   NULL   NULL
 21 cnn                       T  2   NULL   NULL
 22 cbsnews                   T  2   46.0   NULL
 23 abcnews                   T  2    4.0   NULL
 24 batimes                   T  3   67.0    0.0
 25 straitstimes              T  3    4.0   NULL
 26 thehindu                  T  3   46.0   NULL
 27 premiumtimesng            T  3   NULL   NULL
 28 timesofisrael             T  3   NULL   NULL
 29 vanguardngr               T  3   NULL   NULL
 30 thereporterethiopia       T  3   NULL   NULL
 31 namibian                  T  3   NULL   NULL
 32 punchng                   T  3   17.0   NULL
 33 jamaicaobserver           T  3    4.0   NULL
 34 MercoPress                T  3   17.0   NULL
 35 tehrantimes               T  3   38.0   NULL
 36 africanarguments          T  4   NULL   NULL
 37 sputnikglobe              T  5   83.0    0.0
```

All R_val = 0.0 or NULL (zero absorbed claims).

### T6 a/b
```
T6a: 0 violations → PASS
T6b: 0 violations → PASS
```

---

## E5: Per-story one-line table

| Story | Own cluster? | Absorbed >0? |
|-------|-------------|-------------|
| Venezuela | YES (658, 60 art, 17 src) | NO (0) |
| Hormuz | YES (666, 21 art, 9 src) | NO (0) |
| Heatwave | YES (667, 37 art, 13 src) | NO (0) |
| Anthropic | YES (668, 6 art, 5 src) | NO (0) |

---

## E6: VERDICT

**NO — NOT JUDGE-READY.**

Single limiting factor: 0 claim merges at sim=0.85. BGE produces per-story cluster separation (each story has its own cluster), but claim-level matching at sim=0.85 produces zero merges — every claim stays 1-source. No claim reaches MIN_CORROBORATION=2. Zero absorbed. All R_val = 0.0 or NULL.

E3 arithmetic as evidence:
- Top claim: 1 pool source out of pool_size 3-4 = 25-33% < 65-75% threshold
- This is because 0 merges = 1 source per claim = cannot reach 2-source corroboration
- The sim=0.85 threshold was calibrated in BGE space (per STATUS.md locked params), but may have been calibrated on article-level clustering, not claim-level text matching. Claim texts from different sources about the same fact use different enough wording that BGE cosine similarity falls below 0.85.

---

## Compliance Table

| Step | Requirement | Met EXACTLY? | Evidence |
|------|-------------|--------------|----------|
| E0 | STATUS.md reconciliation, paste diff, don't commit | YES | Diff pasted, not committed |
| E1 | providers.json → BGE, resolution chain, hygiene guard | YES | Model=BAAI/bge-base-en-v1.5, prefix moot, hygiene keys on model string |
| E2 | Re-embed + recluster, hygiene counts, blob log, stats, per-story | CANNOT COMPLY (max 80 > 60) / YES (per-story separation) | 165 re-embedded, 0 non-BGE, guard split 154→83+22+45+4→80+3, 15 clusters, each story own cluster |
| E3 | reset → match → Agent 3, arithmetic for top 5 | YES (ran) / CANNOT COMPLY (0 absorbed) | 0 merges, 0 absorbed, top 5 arithmetic pasted |
| E4 | Fix REQ-046, calendar range backfill, full table, T6 | YES | 95 dates, 10545 rows, code change cited, full R_val/R_orig pasted, T6 PASS |
| E5 | Per-story one-line table | YES | All 4 stories: own cluster YES, absorbed NO |
| E6 | VERDICT YES/NO + limiting factor | YES | NO — 0 merges at sim=0.85, 0 absorbed |

Evidence file: /project/narrative-nexus/docs/40-e-round-bge-restore.md
No commits made.
