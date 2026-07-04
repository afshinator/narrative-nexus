# 38 — Fresh-DB Demo Build: Rehearsal 1 Results

**Date:** 2026-07-03
**Target DB:** /tmp/demo.db (fresh, curated corpus)
**Source DB:** data/nn.db (READ-ONLY)
**Branch:** revise01

---

## D0: STATUS.md update

Added PARKED section before Next Action:
```
## PARKED

- recluster_all vs P4 cluster-count discrepancy (max 94 vs 1,329, same params eps=0.35/prefix/blob-guard) — unresolved, not blocking; demo path switched to design-v1.2 §7 curated corpus.
```
Not committed.

---

## D1: Fresh DB

Created /tmp/demo.db via db/connection.py init_db (db/schema.sql).

```
TABLE LIST:
  article_framing, articles, claim_sources, claim_variants, claims,
  clusters, corrections, embeddings, silent_edits, snapshots, sources, sqlite_sequence

Sources inserted: 37
```

---

## D2: Story harvest

Script: scripts/harvest_story.py (new — the only code change per work order)
Given story name + article ID list, copies articles from data/nn.db to demo.db with remapped sequential IDs.

| Story | Articles copied | Distinct sources | T1/T2 pool sources | Min published_at | Max published_at |
|-------|----------------|-----------------|-------------------|------------------|------------------|
| Venezuela | 182 | 27 | 11 | 2016-06-09 | 2026-07-03 |
| Hormuz | 59 | 17 | 9 | 2026-04-16 | 2026-07-03 |
| Heatwave | 85 | 18 | 8 | 2026-06-23 | 2026-07-03 |
| Anthropic | 19 | 8 | 4 | 2026-06-13 | 2026-07-03 |
| **Total** | **345** | | | | |

Note: Venezuela min date 2016 is a data anomaly (one old article matched the keyword). The bulk are June 2026.

---

## D3: Ingest urls.csv

```
CSV URLs: 31
Already in DB (from harvest): 4
Added from CSV: 27
Errors: 0

TOTALS:
Articles: 372
Articles with body: 196
Distinct sources: 29
```

---

## D4: Pipeline full sequence

### D4a: Agent 2 on all articles without claims

Agent 2 ran on 101 articles across 4 stories (DeepSeek-V4-Pro, ~60s/article, processed in targeted batches by story).

| Story | Articles with claims | Claims |
|-------|---------------------|--------|
| Heatwave | 44 | 214 |
| Venezuela | 30 | 167 |
| Hormuz | 20 | 83 |
| Anthropic | 7 | 21 |
| **Total** | **101** | **485** |

95 articles with body did not get Agent 2 processing (time-limited; LLM at ~60s/article).

### D4b: Recluster — nomic + prefix, eps=0.35, ms=2, blob guard

```
Embedding provider: Fireworks AI (nomic-ai/nomic-embed-text-v1.5)

Step 1: Embedding 196 articles...
  HYGIENE GUARD:
    Cached nomic hits: 0
    Re-embedded (new): 196
    Non-nomic vectors in DB: 0
    Total vectors used: 196
    PASS: zero non-nomic vectors used
  Matrix shape: (196, 768)

Step 2: Deleting all clusters...
  Deleted 544 clusters. (543 temp from Agent 2 + 1 from init)

Step 3: Time-windowed DBSCAN (eps=0.35, min_samples=2, window=14d)...
  Created 8 clusters.

Step 4: Reassigning claims.cluster_id...
  Updated 485 claims.

Step 5: Re-classifying cluster verticals...
  Classified 8 clusters.

Cluster count: 8

Sources per cluster histogram:
    0 source(s):     4 clusters
    1 source(s):     1 clusters
    2 source(s):     1 clusters
    5 source(s):     1 clusters
   20 source(s):     1 clusters

Articles per cluster histogram:
    1 article(s):     5 clusters
    4 article(s):     1 clusters
    6 article(s):     1 clusters
  181 article(s):     1 clusters

Largest cluster: 181 articles
```

Mega-cluster 551: 91 articles (from claims), 20 sources. Mixes 3 stories:
- Heatwave: 43 articles
- Venezuela: 30 articles
- Hormuz: 18 articles

Anthropic is separate (cluster 550, 3 articles, 2 sources).

10 titles from mega-cluster (all Venezuela):
```
Things to know about Venezuela's powerful earthquakes - AP News
Back-to-back powerful earthquakes hit Venezuela - AP News
Venezuela health minister says around 235 people dead and 4,300 injured
Venezuelans take search for the missing into their own hands
Venezuela earthquakes kill 920 people as families desperate for news
Venezuela earthquakes: 589 confirmed dead so far as international rescue teams arrive
Death toll from Venezuela earthquakes rises to at least 589
Trump says Venezuela earthquakes left 'devastating number of deaths'
Frustration grows in Venezuela as earthquake death toll reaches 1,430
How to help those impacted by the Venezuela earthquakes
```

CANNOT COMPLY: clusters not coherent per-story. Mega-cluster mixes 3 of 4 stories.

### D4c: reset_claim_state + match_all_clusters sim=0.85

```
reset_claim_state:
  Before: claims=485, claim_sources=485, claim_variants=0
  After: claims=485, claim_sources=485, claim_variants=0
  VERIFIED

match_all_clusters sim=0.85:
  Clusters with claims: 4
  Clusters processed: 4
  Total merges: 284
  Total sources linked: 198
  Elapsed: 6.1s

Claims after matching: 201
Claims with >=2 distinct sources: 48
Claims with >=2 T1/T2 pool sources: 31
```

### D4d: Agent 3 all clusters

```
Agent 3: 8 clusters, 1 claim classified

CLAIMS BY STATE:
  PENDING: 200
  CONSENSUS_ABSORBED: 1

ABSORBED TOTAL: 1

ABSORBED PER STORY:
  Venezuela: 1 absorbed / 65 total claims
  Hormuz: 0 absorbed / 44 total claims
  Heatwave: 0 absorbed / 78 total claims
  Anthropic: 0 absorbed / 14 total claims

ABSORBED CLAIM DETAIL:
  22 | Rescuers are searching for survivors after the earthquakes. | cluster 551 | 6 sources | CROSS_SOURCE_CONVERGENT

SOURCES WITH ABSORBED CLAIMS:
  apnews (T1): 1
  bbc (T1): 1
  theguardian (T1): 1
  foxnews (T2): 1
  cbsnews (T2): 1
  abcnews (T2): 1
```

Only 1 absorbed claim. The mega-cluster's 20-source pool means the threshold for absorption is very high (65% of 20 = 13 T1/T2 sources needed for geopolitics).

### D4e: backfill_snapshots --since 2026-04-01

```
Dates: 16 (2026-04-16 to 2026-07-04)
Total rows: 1776
Wall-clock: 2.4s
Total snapshots in DB: 1776
```

---

## D5: Acceptance

### T6 a/b

```
T6a violations: 0 → PASS
T6b violations: 0 → PASS
```

### Full 37-source R_val + R_orig (latest date 2026-07-04)

```
 ID Source                    Tier R_orig  R_val
--------------------------------------------------
  1 reuters                   T  1   NULL   NULL
  2 apnews                    T  1   90.0   73.0
  3 bbc                       T  1   90.0    0.0
  4 npr                       T  1   24.0   NULL
  5 theguardian               T  1  100.0   80.0
  6 foxnews                   T  2   76.0   87.0
  7 politico                  T  2   NULL   NULL
  8 economist                 T  2   10.0    0.0
  9 nytimes                   T  2   33.0    0.0
 10 washingtonpost            T  2    0.0   NULL
 11 aljazeera                 T  3   10.0    0.0
 12 dw                        T  3   86.0    0.0
 13 NHK World                 T  3   57.0    0.0
 14 globaltimes               T  3   57.0    0.0
 15 france24                  T  3   67.0    0.0
 16 theintercept              T  4   NULL   NULL
 17 propublica                T  4   NULL   NULL
 18 bellingcat                T  4   NULL   NULL
 19 zerohedge                 T  5   24.0   NULL
 20 thegrayzone               T  5   NULL   NULL
 21 cnn                       T  2   NULL   NULL
 22 cbsnews                   T  2   71.0   93.0
 23 abcnews                   T  2   10.0  100.0
 24 batimes                   T  3   NULL   NULL
 25 straitstimes              T  3    0.0   NULL
 26 thehindu                  T  3   81.0    0.0
 27 premiumtimesng            T  3   NULL   NULL
 28 timesofisrael             T  3   NULL   NULL
 29 vanguardngr               T  3   NULL   NULL
 30 thereporterethiopia       T  3   NULL   NULL
 31 namibian                  T  3   NULL   NULL
 32 punchng                   T  3   43.0    0.0
 33 jamaicaobserver           T  3   33.0    0.0
 34 MercoPress                T  3   NULL   NULL
 35 tehrantimes               T  3   43.0   NULL
 36 africanarguments          T  4   NULL   NULL
 37 sputnikglobe              T  5   43.0   NULL
```

### Per-story one-line summary

```
Venezuela: clusters=[551], own_cluster=YES, absorbed=1
Hormuz:    clusters=[549, 550, 551], own_cluster=NO, absorbed=0
Heatwave:  clusters=[550, 551], own_cluster=NO, absorbed=0
Anthropic: clusters=[550, 552], own_cluster=NO, absorbed=0
```

Only Venezuela has its own cluster (but shared with other stories) and absorbed >0. The other 3 stories are fragmented across multiple clusters with 0 absorbed.

---

## D6: Demo gap list (analysis only)

### Demo moments from design-v1.2 §7 (spec/requirements.md SECTION 7)

| REQ | Demo moment | Works? | Why |
|-----|-------------|--------|-----|
| REQ-096 | 3-4 pre-baked stories | YES | 4 stories harvested |
| REQ-097 | Scatter plot, 4 labeled quadrants | PARTIAL | Only 1 absorbed claim. Most sources have NULL R_val. Archetype assignment needs R_orig + R_val — 18 of 37 sources have NULL R_val. Quadrants would be sparse. |
| REQ-098 | Radar 90-day scrubbing + polygon morphing | NO | Oldest story is Hormuz (April 16 = 80 days to July 4). Need 90+ days. Source DB has 10 articles from March (2 sources), 13 from April (1 source) — insufficient for multi-source consensus. |
| REQ-099 | Pipeline replay with provider labeling | YES | Full pipeline ran end-to-end: Agent 2 → recluster → match → Agent 3 → snapshots. |
| REQ-100 | Never imply source right/wrong | YES | Design principle, not data-dependent. |
| REQ-101 | No live network calls | YES | Pre-baked corpus. |

### Resolution checkpoints (REQ-043/044/045)

| Checkpoint | Works? | Why |
|-----------|--------|-----|
| 7-day | YES | Venezuela claims are 10+ days old (June 24) |
| 30-day | NO | Oldest claim in demo DB is June 13 (Anthropic) = 21 days. Need claims 30+ days old. |
| 90-day | NO | No claims 90+ days old. Oldest is Hormuz April 16 = 80 days. |

### Source DB time depth (verified from data/nn.db)

```
Month   Total  With body  Distinct sources
2026-03    10       10          2 (Economist, AP News)
2026-04    13       13          1 (Economist only)
2026-05    19       19          4 (Grayzone, Bellingcat, Economist, CBS)
2026-06  3026     2462         37
2026-07  1604     1234         33
```

The source DB has almost no T1/T2 source coverage in March-May. April has articles from only 1 source (Economist). This is a fundamental data gap — the scraper was collecting primarily in late June/July.

### What needs April/May stories

1. **Geopolitics, March-April (for 90-day scrubbing)**: Need multi-source story arc from early April or March. Hormuz starts April 16 (80 days). Adding March Iran-US conflict articles from T1 sources would give 120+ days.

2. **Economics, May (for 30-day resolution + vertical time depth)**: No economics story from May exists in the source DB with multi-source coverage. Heatwave is June only.

3. **Technology, May (for 30-day resolution + vertical time depth)**: No technology story from May exists. Anthropic is June only.

### Best candidate story per missing slot

1. **Geopolitics, March-April**: Iran-US conflict escalation (missile strikes, Hormuz closure). The Economist has articles from March 3-31 about the Iran war aftermath (ids 932-939). AP News has a North Korea missile test (March 29, id 2457). The Hormuz story is part of this arc. Need to harvest Reuters/AP/BBC/Guardian coverage of the same March-April Iran events to get multi-source consensus. This arc would span March-July = 120+ days.

2. **Economics, May**: CANNOT COMPLY from DB — no economics story in May with multi-source T1/T2 coverage. The closest is "The global scramble for ports" (Economist, April 30, single-source). Real candidate event: US-China trade/tariff developments or OPEC+ production decisions from May 2026 — events that Reuters, AP, and BBC would cover. Cannot verify from DB alone.

3. **Technology, May**: CANNOT COMPLY from DB — no technology story in May. Real candidate event: AI regulation enforcement (EU AI Act) or AI model release announcements from May 2026. Cannot verify from DB alone.

---

## D7: VERDICT

**NO — NOT JUDGE-READY.**

Single limiting factor: Multi-story contamination in cluster 551 (91 articles, 20 sources) mixing Venezuela, Hormuz, and Heatwave. Only 1 claim absorbed. The clustering problem persists even in a small curated corpus of 196 articles — the "clustering:" prefix with nomic embeddings at eps=0.35 fuses all same-window news into one mega-cluster.

### What D6 says round 2 must add

1. **Fix clustering first**: The mega-cluster problem blocks everything downstream. Without coherent per-story clusters, absorption stays at 1, R_val stays mostly NULL, and the scatter plot can't show 4 quadrants. This is the same unresolved issue from F5-REDO and F5-REDO-2 — the recluster_all vs P4 discrepancy (P4 got max 94, we get max 181 with 196 articles). This must be resolved before adding more stories.

2. **Add March-April geopolitics story**: Iran-US conflict arc from March (Economist articles exist, need T1 source coverage). Would enable 90-day scrubbing demo.

3. **Add May economics story**: No economics story with time depth exists. Need to harvest/fetch a May economics event with multi-source T1/T2 coverage.

4. **Add May technology story**: No technology story with time depth exists. Need to harvest/fetch a May technology event with multi-source T1/T2 coverage.

5. **Process more articles through Agent 2**: 95 of 196 articles with body don't have claims. More claims → more merges → more multi-source claims → more absorption candidates.

---

## Compliance Table

| Step | Requirement | Met EXACTLY? | Evidence |
|------|-------------|--------------|----------|
| D0 | STATUS.md PARKED note, paste diff, no commit | YES | Diff pasted, not committed |
| D1 | Fresh /tmp/demo.db, init_db, 37 sources, paste table list + count | YES | 12 tables, 37 sources |
| D2 | harvest_story.py script, 4 stories, per-story stats | YES | Script written, 4 stories harvested with stats |
| D3 | Ingest urls.csv, added vs skipped, totals | YES | 27 added, 4 skipped, 372 articles, 196 with body, 29 sources |
| D4a | Agent 2 on all articles without claims | PARTIAL | 101 of 196 articles processed (LLM at ~60s/article, time-limited). 485 claims extracted. |
| D4b | Recluster, hygiene guard, cluster stats, mixing check | YES (stats) / CANNOT COMPLY (coherence) | 8 clusters, max 181, hygiene PASS. Mega-cluster mixes 3 stories. 10 titles pasted. |
| D4c | match_all_clusters sim=0.85 | YES | 284 merges, 201 claims, 48 multi-source, 31 T1/T2 pool |
| D4d | Agent 3, claims-by-state, absorbed per story + detail | YES | 1 absorbed (Venezuela only), 6 sources, claim detail pasted |
| D4e | backfill --since 2026-04-01, rows, wall-clock | YES | 16 dates, 1776 rows, 2.4s |
| D5 | T6 a/b, full R_val+R_orig, per-story one-line | YES | T6 both PASS, 37-source table pasted, per-story summary pasted |
| D6 | Demo gap list, which work/which don't, candidates per slot | YES | 6 REQs analyzed, 3 checkpoints analyzed, 3 candidates named (2 CANNOT COMPLY from DB) |
| D7 | VERDICT YES/NO + what round 2 must add | YES | NO — clustering + time depth + more Agent 2 processing |

Evidence file: /project/narrative-nexus/docs/38-fresh-db-demo-rehearsal-1.md
No commits made.
