# 41 — M-Round: Matcher Processed Zero Clusters

**Date:** 2026-07-03
**Target DB:** data/demo/demo.db
**No commits made.**

---

## M0: EXPLAIN "processed: 0"

### match_all_clusters cluster-selection logic (claim_matching.py:195-202):

```python
    clusters = conn.execute("""
        SELECT DISTINCT c.id
        FROM clusters c
        JOIN claims cl ON cl.cluster_id = c.id
        GROUP BY c.id
        HAVING COUNT(cl.id) >= 2
        ORDER BY c.id
    """).fetchall()
```

### Skip logic inside match_claims_in_cluster (claim_matching.py:66-86):

```python
    if len(rows) < 2:
        return {merges: 0, ...}  # Skip: fewer than 2 claims

    # Idempotency check
    claim_ids = [r["id"] for r in rows]
    already_processed = conn.execute(
        f"SELECT COUNT(*) FROM claim_variants WHERE canonical_claim_id IN ({placeholders})",
        claim_ids,
    ).fetchone()[0]
    if already_processed > 0:
        return {merges: 0, ...}  # Skip: already processed
```

### clusters_processed counter (claim_matching.py:215-218):

```python
            if result["merges"] > 0:
                total_merges += result["merges"]
                total_sources_linked += result["sources_linked"]
                clusters_processed += 1
```

**"processed: 0" does NOT mean "skipped: 0".** It means "0 clusters had merges." The counter only increments when merges > 0. The matcher DID run on all 14 eligible clusters (took 6.0s = embedding API time for 283 claims), found 0 pairs above sim=0.85, and reported 0 merges.

### Per-cluster state (15 clusters with claims, 14 with >= 2 claims):

```
cluster_id | claims | variants | skip_reason
654        | 3      | 0        | ran, 0 merges
655        | 6      | 0        | ran, 0 merges
656        | 3      | 0        | ran, 0 merges
657        | 3      | 0        | ran, 0 merges
658        | 124    | 0        | ran, 0 merges
659        | 1      | 0        | skipped (< 2 claims)
660        | 2      | 0        | ran, 0 merges
661        | 2      | 0        | ran, 0 merges
662        | 2      | 0        | ran, 0 merges
663        | 3      | 0        | ran, 0 merges
664        | 2      | 0        | ran, 0 merges
665        | 2      | 0        | ran, 0 merges
666        | 42     | 0        | ran, 0 merges
667        | 74     | 0        | ran, 0 merges
668        | 14     | 0        | ran, 0 merges
```

All 14 eligible clusters: 0 claim_variants (idempotency check passes), claims >= 2 (size check passes). Matcher ran on all 14. 0 merges found in every cluster.

---

## M1: INTEGRITY

### Orphaned claims:

```
orphaned_claims: 0
```

All 283 claims' cluster_ids exist in the clusters table. No orphans.

### E2 recluster log — claims reassignment:

E2's recluster output DID include "Step 4: Reassigning claims.cluster_id... Updated 283 claims with new cluster_id." The step executed. Claims are not orphaned. My E6 verdict claim that the step was missing was wrong — I misread the output.

No fix needed. Orphan count = 0.

---

## M2: RE-RUN match_all_clusters sim=0.85

### Results:

```
Clusters with claims: 14
Clusters processed (had merges): 0
Total merges: 0
Sources linked: 0
Elapsed: 6.0s

Claims after: 283
Claims >=2 distinct sources: 0
Claims >=2 T1/T2 pool sources: 0
```

### 5 merged pairs (sim >= 0.85):

NONE — no pairs above 0.85 in any cluster.

### 5 near-misses (0.75 <= sim < 0.85):

```
sim=0.8252 | NHK World: "Rescue operations are underway." | bbc: "Residents carried out much of the rescue effort."
sim=0.7875 | batimes: "The rescue took place in La Guaira." | bbc: "Damage is visible in La Guaira."
sim=0.7798 | sputnikglobe: "Infrastructure was damaged." | sputnikglobe: "Gas supply was disrupted."
sim=0.7723 | sputnikglobe: "Infrastructure was damaged." | sputnikglobe: "Maiquetia International Airport was closed due to infrastructure damage."
sim=0.7706 | theguardian: "Jorge Rodríguez is the president of the national assembly." | aljazeera: "Jorge Rodriguez stated in an address on state television on Monday."
```

### 5 same-fact claim pairs from different sources (top cross-source):

```
sim=0.8252 | NHK World: "Rescue operations are underway."
           | bbc: "Residents carried out much of the rescue effort."

sim=0.7875 | batimes: "The rescue took place in La Guaira."
           | bbc: "Damage is visible in La Guaira."

sim=0.7706 | theguardian: "Jorge Rodríguez is the president of the national assembly."
           | aljazeera: "Jorge Rodriguez stated in an address on state television on Monday."

sim=0.7644 | NHK World: "Rescue operations are underway."
           | batimes: "The rescue took place in La Guaira."

sim=0.7636 | batimes: "Rescuers used their bare hands to remove people caught under rubble."
           | bbc: "People are using bare hands and shovels to shift through rubble in La Guaira."
```

### Similarity distribution (cluster 658, 124 claims, 7,626 pairs):

```
Max: 0.8252
Min: 0.1668
Mean: 0.4561
0.95+:    0
0.90-0.95: 0
0.85-0.90: 0
0.80-0.85: 1
0.75-0.80: 10
0.70-0.75: 32
<0.70:    7583
```

### All 4 story clusters:

```
Cluster 658 (Venezuela): 124 claims, 7626 pairs, max=0.8252, pairs>=0.85: 0
Cluster 666 (Hormuz):     42 claims,  861 pairs, max=0.7711, pairs>=0.85: 0
Cluster 667 (Heatwave):   74 claims, 2701 pairs, max=0.8007, pairs>=0.85: 0
Cluster 668 (Anthropic):  14 claims,   91 pairs, max=0.7422, pairs>=0.85: 0
```

THIS IS THE SEMANTIC FINDING: BGE claim-level cosine similarity for same-fact claims from different sources tops out at 0.8252. The sim=0.85 threshold is above the maximum pairwise similarity in the corpus. The matcher ran correctly — it embedded and compared all 283 claims across all 14 clusters. Zero pairs above 0.85 is an embedding-space property of BGE on claim-length texts, not a mechanical skip.

---

## M3: Agent 3

```
Agent 3: 15 clusters, 0 classified
PENDING: 283
Absorbed TOTAL: 0

ABSORBED PER STORY:
  Venezuela: 0 / 131
  Hormuz: 0 / 51
  Heatwave: 0 / 84
  Anthropic: 0 / 17
```

### Top 5 arithmetic:

```
   ID Text                                                         Pool PoolSize    Pct Thresh Absorb?
  802 Sheera Frenkel is a New York Times tech reporter.               1        3  33.3%    75%      NO
  746 The World Weather Attribution study was released on Friday.     1        4  25.0%    75%      NO
  743 The British military reported that a vessel was hit by a pro    1        4  25.0%    65%      NO
  742 A United Nations agency paused the evacuation of ships throu    1        4  25.0%    65%      NO
  741 Trump's social media post did not identify the ship.            1        4  25.0%    65%      NO
```

Each claim: 1 pool source (no merges → 1 source per claim). Cannot reach MIN_CORROBORATION=2.

---

## M4: backfill_snapshots --since 2026-04-01 (calendar version)

```
Deleted 10545 existing snapshots in range
Done. 95 dates, 10545 rows.
```

### Full 37-source R_val + R_orig (latest date 2026-07-04):

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

### T6 a/b:

```
T6a: 0 violations → PASS
T6b: 0 violations → PASS
```

---

## M5: Per-story one-line table + VERDICT

| Story | Own cluster? | Absorbed >0? |
|-------|-------------|-------------|
| Venezuela | YES (658, 60 art, 17 src) | NO (0) |
| Hormuz | YES (666, 21 art, 9 src) | NO (0) |
| Heatwave | YES (667, 37 art, 13 src) | NO (0) |
| Anthropic | YES (668, 6 art, 5 src) | NO (0) |

**VERDICT: NO — NOT JUDGE-READY.**

Single limiting factor: BGE claim-level cosine similarity for same-fact claims from different sources tops out at 0.8252. The sim=0.85 threshold (locked, calibrated in BGE space) is above the maximum pairwise similarity in the corpus. Zero merges → zero multi-source claims → zero absorbed → all R_val = 0.0 or NULL.

The matcher ran correctly — it embedded and compared all 283 claims across all 14 eligible clusters (6.0s). The 0-merges result is a semantic property of BGE on claim-length texts: short, factual sentences from different sources about the same event use different enough wording that BGE cosine similarity stays below 0.85. The highest cross-source pair (0.8252) is "Rescue operations are underway." vs "Residents carried out much of the rescue effort." — same fact, different phrasing, below threshold.

---

## Compliance Table

| Step | Requirement | Met EXACTLY? | Evidence |
|------|-------------|--------------|----------|
| M0 | Paste skip logic, per-cluster raw check values | YES | Selection + skip logic pasted, 15 clusters with raw values (claims count, variants count, skip reason) |
| M1 | Orphaned claims count, recluster log check, fix if needed | YES | 0 orphans, reassignment step DID execute (correcting E6 error), no fix needed |
| M2 | Re-run match, 5 merged pairs, 5 near-misses, same-fact pairs | YES | 0 merges confirmed. 5 near-misses (0.75-0.85) pasted. 5 cross-source same-fact pairs pasted. Similarity distribution pasted. |
| M3 | Agent 3, claims-by-state, absorbed per story, arithmetic | YES | 0 absorbed, top 5 arithmetic pasted |
| M4 | Calendar backfill, rows, R_val/R_orig, T6 | YES | 95 dates, 10545 rows, full table, T6 PASS |
| M5 | Per-story one-line + verdict | YES | All 4 stories: own cluster YES, absorbed NO. NO — sim=0.85 above BGE max 0.8252 |

Evidence file: /project/narrative-nexus/docs/41-m-round-matcher-zero.md
No commits made.
