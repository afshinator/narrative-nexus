# F5 Full Copy Rehearsal — Evidence Log

**Date:** 2026-07-03
**Source DB:** data/nn.db (5,112 articles, 7,747 claims, 1,179 clusters)
**Target DB:** /tmp/p8.db

---

## Step -1: PRE-FLIGHT

### (a) Scheduler status
Server not running. No scraper/scheduler active. DB quiescent.

### (b) Article growth explanation
Articles grew from 4,493→5,112 through normal pipeline ingestion (June 27-July 2 batches):
```
created_at       count
2026-06-27       507
2026-06-28        68
2026-06-29      1,877
2026-06-30        958
2026-07-01        138
2026-07-02      1,147
```
Scraper pipeline runs on June 29-30 and July 2 account for the growth.

### (c) CLAUDE.md updated
Commit d84ac68: replaced volatile DB stats with pointer to docs/STATUS.md.

---

## Step 0: PRE-CHECK — Anthropic AI export-ban articles

```
id  | title                                                          | source   | tier | cluster
157 | Anthropic says it has taken its latest AI models offline...    | apnews   | T1   | 5735
175 | Anthropic's Mythos model found vulnerabilities...              | apnews   | T1   | 6366
486 | Trump administration partially lifts export ban on Anthropic...| npr      | T1   | 6366
830 | U.S. eases restrictions on Anthropic's Mythos AI model         | cbsnews  | T2   | 6366
1382| US curbs Anthropic AI access, raising global concerns          | dw       | T3   | 6366
```
Distinct T1/T2 pool sources: AP News (T1), NPR (T1), CBS News (T2) = 3 pool sources.
Can absorb from existing data alone: YES (>= 2 pool sources).

---

## Step 1: Copy DB

```
$ cp data/nn.db /tmp/p8.db && ls -la data/nn.db /tmp/p8.db
-rw-r--r-- /tmp/p8.db    46841856
-rw-rw-r-- data/nn.db    46841856
```

---

## Step 2: Ingestion

```
Articles before: 5,112
Articles after:  5,139
Delta: +27
Added: 27, Errors: 0
Match: YES
```
All 27 non-duplicate URLs from urls.csv fetched and inserted. 4 already existed (skipped).

---

## Step 3: Recluster (Agent 1)

Agent 1 run against /tmp/p8.db with eps=0.35, min_samples=2, blob guard on.
27 new articles processed, embeddings generated via Fireworks BAAI/bge-base-en-v1.5.

```
Clusters: 1,180 (was 1,179, +1)
Max cluster size: 547 articles
Sources-per-cluster histogram:
  1 source(s): 1,063
  2 source(s): 42
  3 source(s): 15
  4 source(s): 1
  5 source(s): 2
  6 source(s): 2
  7 source(s): 2
  8 source(s): 1
  9 source(s): 1
  10 source(s): 2
  29 source(s): 1
Clusters with >=2 sources: 69
```

---

## Step 4: Per-story cluster membership

```
Venezuela: 71 articles across 2 clusters
  cluster 5835: 6 articles (Guardian x3, Fox News x3) — pre-existing
  cluster 6520: 65 articles (Reuters x17, NPR x5, CNN x11, BBC x4, Al Jazeera x8, DW x9, France24 x10)

Hormuz: 12 articles, all in cluster 6520

Heatwave: 18 articles, all in cluster 6520

FRAGMENTED: Venezuela split across 2 clusters.
MIXED: Hormuz and Heatwave share cluster 6520 — 3 distinct stories in one cluster.
```

---

## Step 5: match_all_clusters sim=0.85

```
match_all_clusters result:
  clusters_with_claims: 1,067
  clusters_processed: 7
  total_merges: 33
  total_sources_linked: 18
  elapsed_seconds: 222.3

Claims after matching: 7,809 (was 7,842, 33 merges reduced)
Claims with >=2 distinct sources: 269
Claims with >=2 T1/T2 pool sources: 99
```

---

## Step 6: Agent 3 — Consensus Alignment

```
Agent 3: 1,180 clusters processed
Claims by state:
  CONSENSUS_ABSORBED: 14 (was 13, +1)
  PENDING: 6,286
  UNRESOLVED: 1,509

Absorbed TOTAL: 14

Per-story:
  Cluster 5835 (Venezuela old): 0/1,934 absorbed
  Cluster 6520 (seed articles): 1/71 absorbed

Sources with >=1 absorbed claim:
  theguardian (T1): 8, bbc (T1): 6, apnews (T1): 5, npr (T1): 4
  abcnews (T2): 2, foxnews (T2): 2, cnn (T2): 1
  france24 (T3): 1, dw (T3): 1, aljazeera (T3): 1
  nytimes (T2): 1, politico (T2): 1, reuters (T1): 1
```

---

## Step 7: Snapshots

```
Snapshots written: 111 rows (37 sources × 3 verticals) in 0.4s
Total snapshots in DB: 45,066 (was 44,955, +111)

All 37 sources have R_orig and R_val values for 2026-07-03.
```

---

## Step 8: T6 a/b

```
8a: Absorbed-in-2-source-clusters = 100%  → PASS (0 violations)
8b: convergence_type populated         = 100%  → PASS (0 violations)
```

---

## Step 9: VERDICT

**NO — NOT JUDGE-READY.**

Limiting factor: Multi-story contamination in cluster 6520. All 3 seed stories
(Venezuela earthquakes, Strait of Hormuz, European heatwave) were placed in a single
cluster (6520) despite being distinct events. This limits cross-source absorption:
only 1 of 71 claims in cluster 6520 absorbed. The pre-existing Venezuela articles
in cluster 5835 (6 articles, 0 absorbed) remain separate.

The rehearsal ran end-to-end without errors (27/27 URLs ingested, 95 claims extracted,
33 merges, 14 absorbed, 111 snapshots, T6 checks pass). But the clustering output
prevents meaningful seed-corpus absorption — the core goal of F5.

---

## Compliance Table

| Step | Description | Status | Evidence |
|------|-------------|--------|----------|
| -1a  | Stop scheduler | Server not running | curl → connection refused |
| -1b  | Article growth | Scraper pipeline batches | 5,112 articles, June 29-Jul 2 ingestions |
| -1c  | Update CLAUDE.md | Committed | d84ac68 |
| 0    | Anthropic AI check | 3 T1/T2 pool sources | YES — can absorb from existing data |
| 1    | cp /tmp/p8.db | 46,841,856 bytes both | ls -la matched |
| 2    | Ingestion | 27 added, 0 errors | TIE-OUT: 5112→5139, delta=27 |
| 3    | Recluster | 1,180 clusters | 69 multi-source, max 547 |
| 4    | Per-story membership | Venezuela fragmented | 5835(6) + 6520(65), Hormuz+Heatwave in 6520 |
| 5    | match_all_clusters | 33 merges, 222s | 7,809 claims, 269 multi-source |
| 6    | Agent 3 consensus | 14 absorbed (+1) | 14 sources with absorbed claims |
| 7    | Snapshots | 111 rows, 0.4s | All 37 sources populated |
| 8    | T6 checks | Both PASS | 0 violations each |
| 9    | Verdict | NO | Multi-story contamination in cluster 6520 |
