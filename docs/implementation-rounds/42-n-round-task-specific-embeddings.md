# 42 — N-Round: Task-Specific Embedding Spaces

**Date:** 2026-07-03
**Target DB:** data/demo/demo.db
**No commits made.**

---

## N0: CONFIG SPLIT

### Code changes:

1. **config/providers.json**: New entry `fireworks-nomic` (model: nomic-ai/nomic-embed-text-v1.5), new default `claim_matching_embedding: "fireworks-nomic"`.

2. **pipeline/provider_config.py:18**: Added `"claim_matching_embedding": "embeddings"` to `_SLOT_CATEGORY`.

3. **pipeline/claim_matching.py:33-46**: New `get_claim_matching_embed_client()` resolves the slot and creates an `EmbeddingClient` with the nomic provider. Passes `FIREWORKS_API_KEY` explicitly (fireworks-nomic uses same Fireworks API).

4. **pipeline/embedding_client.py**: Added `fireworks-nomic` to `_API_PROVIDERS` and `_EMBEDDING_BASE_URLS`.

### Both resolution chains:

```
CLUSTERING: provider=fireworks, model=BAAI/bge-base-en-v1.5
CLAIM MATCHING: provider=fireworks-nomic, model=nomic-ai/nomic-embed-text-v1.5
```

Nomic prefix ("clustering: ") applies automatically — embedding_client.py:126 checks `"nomic" in self.model.lower()` → True for "nomic-ai/nomic-embed-text-v1.5".

---

## N1: HYGIENE

Claim matching does NOT read or write the article embeddings table. Cite: `pipeline/claim_matching.py` — the word "embeddings" appears only as a local variable name (lines 106, 111, 112): an in-memory list of float vectors returned by `embed_client.embed()`. Zero SQL queries against the `embeddings` table. Claim vectors are computed in-memory per run and never persisted.

---

## N2: RE-RUN match_all_clusters sim=0.85 (nomic, no recluster)

```
Claim matching embed client: Fireworks AI (nomic) (nomic-ai/nomic-embed-text-v1.5)

Clusters with claims: 14
Clusters processed (had merges): 0
Total merges: 0
Sources linked: 0
Elapsed: 6.7s

Claims after: 283
Claims >=2 distinct sources: 0
Claims >=2 T1/T2 pool sources: 0
```

### Per-cluster merge counts:

```
Cluster 654 (3 claims): 0 merges
Cluster 655 (6 claims): 0 merges
Cluster 656 (3 claims): 0 merges
Cluster 657 (3 claims): 0 merges
Cluster 658 (124 claims): 0 merges
Cluster 660 (2 claims): 0 merges
Cluster 661 (2 claims): 0 merges
Cluster 662 (2 claims): 0 merges
Cluster 663 (3 claims): 0 merges
Cluster 664 (2 claims): 0 merges
Cluster 665 (2 claims): 0 merges
Cluster 666 (42 claims): 0 merges
Cluster 667 (74 claims): 0 merges
Cluster 668 (14 claims): 0 merges
```

### 10 merged pairs (sim >= 0.85):

NO MERGED PAIRS — no pairs above 0.85.

### 5 near-misses (0.80 <= sim < 0.85):

```
sim=0.8496 | NHK World: "Hundreds of people are believed to be buried in th" | MercoPress: "At least 172 people remain trapped under the rubbl"
sim=0.8492 | apnews: "Venezuelans searched for missing loved ones on Jun" | apnews: "Families in La Guaira, Venezuela mourned loved one"
sim=0.8488 | aljazeera: "A 21-year-old man was pulled alive from the rubble" | NHK World: "On Thursday, Venezuela's Interim President Delcy R"
sim=0.8485 | nytimes: "The U.S. demanded allegiance from the successor of" | theintercept: "U.S. authorities took Venezuela President Nicolás "
sim=0.8485 | bbc: "Residents carried out much of the rescue effort." | batimes: "Rescuers used their bare hands to remove people ca"
```

Total near-misses in cluster 658 (0.80-0.85): 201

### Comparison: BGE vs nomic on same claims

| Metric | BGE (M-round) | Nomic (N-round) |
|--------|---------------|-----------------|
| Max pairwise sim | 0.8252 | 0.8496 |
| Near-misses 0.80-0.85 | 1 | 201 |
| Near-misses 0.75-0.80 | 10 | (not measured) |
| Merges at 0.85 | 0 | 0 |

Nomic produces higher claim-level similarities than BGE. Top pair at 0.8496 is 0.0004 below threshold. 201 pairs in the 0.80-0.85 band vs BGE's 1.

---

## N3: Agent 3

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

### Top-3 arithmetic per story:

**Venezuela** (pool_size=8, threshold=65%):
```
717 | pool=1 pool_size=8 pct=12.5% thresh=65% | "A helicopter took off from a U.S. Navy ship docked..."
715 | pool=1 pool_size=8 pct=12.5% thresh=65% | "Rosalia Bustamante said she lost several friends."
714 | pool=1 pool_size=8 pct=12.5% thresh=65% | "Rosalia Bustamante said that delays are costing lives."
```

**Hormuz** (pool_size=4, threshold=65%):
```
743 | pool=1 pool_size=4 pct=25.0% thresh=65% | "The British military reported that a vessel was hit..."
742 | pool=1 pool_size=4 pct=25.0% thresh=65% | "A United Nations agency paused the evacuation..."
741 | pool=1 pool_size=4 pct=25.0% thresh=65% | "Trump's social media post did not identify the ship."
```

**Heatwave** (pool_size=4, threshold=75%):
```
746 | pool=1 pool_size=4 pct=25.0% thresh=75% | "The World Weather Attribution study was released..."
482 | pool=1 pool_size=4 pct=25.0% thresh=75% | "People shaded from the sun under umbrellas..."
481 | pool=1 pool_size=4 pct=25.0% thresh=75% | "A girl jumped in a canal to cool off..."
```

**Anthropic** (pool_size=3, threshold=75%):
```
802 | pool=1 pool_size=3 pct=33.3% thresh=75% | "Sheera Frenkel is a New York Times tech reporter."
260 | pool=1 pool_size=3 pct=33.3% thresh=75% | "OpenAI said yesterday that it had agreed..."
259 | pool=1 pool_size=3 pct=33.3% thresh=75% | "The U.S. government retains control..."
```

Every claim: 1 pool source. Zero merges = zero multi-source claims = impossible to reach MIN_CORROBORATION=2.

---

## N4: backfill_snapshots --since 2026-04-01

```
95 dates, 10545 rows
```

### Full 37-source R_val + R_orig (2026-07-04):

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

T6a: 0 violations | T6b: 0 violations

---

## N5: Per-story one-line + VERDICT

| Story | Own cluster? | Absorbed >0? |
|-------|-------------|-------------|
| Venezuela | YES (658, 60 art, 17 src) | NO (0) |
| Hormuz | YES (666, 21 art, 9 src) | NO (0) |
| Heatwave | YES (667, 37 art, 13 src) | NO (0) |
| Anthropic | YES (668, 6 art, 5 src) | NO (0) |

**VERDICT: NO — NOT JUDGE-READY.**

Single limiting factor: sim=0.85 is 0.0004 above the maximum nomic claim-level cosine similarity (0.8496). Zero merges → zero multi-source claims → zero absorbed. The locked threshold was calibrated in BGE article-clustering space, not nomic claim-matching space. Nomic with prefix produces 201 near-misses in the 0.80-0.85 band — the top pair ("Hundreds of people are believed to be buried" vs "At least 172 people remain trapped under the rubble") at sim=0.8496 is a clear same-fact match blocked by 0.0004.

This is the semantic finding the user predicted: nomic claim-level similarities are higher than BGE (0.8496 vs 0.8252), but the locked sim=0.85 threshold is still above the maximum. The threshold was calibrated for a different embedding space and a different task (article clustering, not claim matching).

---

## Compliance Table

| Step | Requirement | Met EXACTLY? | Evidence |
|------|-------------|--------------|----------|
| N0 | Config split, cite code, both resolution chains | YES | 4 file changes cited, both chains pasted |
| N1 | Confirm claim matching doesn't touch embeddings table | YES | Cited: "embeddings" = local variable only, zero SQL against table |
| N2 | Re-run match with nomic, 10 merged pairs, 5 near-misses | YES (ran) / CANNOT COMPLY (0 merges) | 0 merges, 0 merged pairs, 5 near-misses pasted (top=0.8496), 201 total near-misses |
| N3 | Agent 3, absorbed per story, top-3 arithmetic | YES | 0 absorbed, top-3 per story pasted |
| N4 | Calendar backfill, R_val/R_orig, T6 | YES | 95 dates, 10545 rows, full table, T6 PASS |
| N5 | Per-story one-line + verdict | YES | All 4: own cluster YES, absorbed NO. NO — sim=0.85 above nomic max 0.8496 |

Evidence file: /project/narrative-nexus/docs/42-n-round-task-specific-embeddings.md
No commits made.
