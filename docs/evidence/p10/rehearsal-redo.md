# F5-REDO — Full Copy Rehearsal Evidence Log

**Date:** 2026-07-03
**Source DB:** data/nn.db (READ-ONLY)
**Target DB:** /tmp/p9.db
**Branch:** revise01

---

## Step 0: WHERE DID BGE COME FROM

### Embedding model resolution chain (BEFORE fix)

```
config/providers.json:7  →  fireworks embedding model = "BAAI/bge-base-en-v1.5"
config/providers.json:51 →  defaults.agent1_embedding = "fireworks"
pipeline/embedding_client.py:85  →  reads model from provider dict (no hardcoded default)
pipeline/provider_config.py      →  pure config resolution, no override
env: no EMBED/BGE/NOMIC overrides
```

**Root cause:** providers.json had the right key name (`agent1_embedding`) pointing to `fireworks` provider, but the fireworks embedding model was set to BGE instead of nomic.

### Fix 1: providers.json — BGE → nomic

```diff
- "model": "BAAI/bge-base-en-v1.5",
+ "model": "nomic-ai/nomic-embed-text-v1.5",
```
Commit: 2b3b1df

### Fix 2: Remove nomic "clustering:" prefix (embedding_client.py:126-127)

The nomic prefix was proven to make clustering WORSE per `references/nomic-prefix-disaster.md`:
- At eps=0.30, without prefix: 857 clusters, mega=930
- At eps=0.30, with prefix: 313 clusters, mega=1,425

The prefix code was never removed after the disaster was documented. Removed lines 125-127 from embedding_client.py.

### Fix 3: Align text input format (recluster_all.py:148)

recluster_all.py used `body[:200]` while agent1_intake.py used `get_embedding_input(title, body, max_body_chars=1000)` with cleaned body. Changed to match agent1_intake.py.

Commit: 435edfe

### Resolution chain (AFTER fix)

```
$ python3 -c "
from pipeline.provider_config import load_provider_config, get_provider_for_agent
cfg = load_provider_config('config/providers.json')
ep = get_provider_for_agent(cfg, 'agent1_embedding')
print(f'RESOLVED: provider={ep[\"id\"]}, model={ep.get(\"model\")}')
"
RESOLVED: provider=fireworks, model=nomic-ai/nomic-embed-text-v1.5
PASS: nomic-ai/nomic-embed-text-v1.5
```

### Commits
- 2b3b1df — Fix embedding model BGE→nomic + add blob guard + hygiene guard to recluster_all.py
- 435edfe — Remove nomic prefix (proven worse) + align text input to get_embedding_input(1000 chars)

---

## Step 1: Fresh copy

```
$ rm -f /tmp/p8.db; cp data/nn.db /tmp/p9.db && ls -la data/nn.db /tmp/p9.db
644  /tmp/p9.db  44.7M
664  data/nn.db  44.7M
```

Baseline (from /tmp/p9.db):
```
articles|5112
claims|7747
clusters|1179
embeddings|2028 (all BAAI/bge-base-en-v1.5)
snapshots|44955
```

p8.db discarded (contaminated — BGE embeddings + prefix).

---

## Step 2: Ingestion

```
CSV URLs: 31
Previously in DB: 28
Added this pass: 3
Errors: 0
Articles before: 5112
Articles after: 5139
Delta: +27
CSV URLs matched in DB: 31/31
```

Method: Firecrawl AsyncFirecrawl.scrape(url, formats=["markdown"]) — concurrent fetch.
First pass (web_extract): 23 added before 5-min timeout.
Second pass (Firecrawl): 3 remaining added in 2 seconds.

Tie-out: 5,112 → 5,139, delta +27, zero errors.

---

## Step 3: FULL recluster

### Pre-recluster: delete stale BGE embeddings

```sql
DELETE FROM embeddings;  -- removed 2028 BGE vectors
```

### Recluster run

```
Embedding provider: Fireworks AI (nomic-ai/nomic-embed-text-v1.5)

Step 1: Embedding 2055 articles...
  Embedding 2055 uncached articles via Fireworks AI (nomic-ai/nomic-embed-text-v1.5)...
  Persisted 2055 new embeddings.

  HYGIENE GUARD:
    Cached nomic hits: 0
    Re-embedded (new): 2055
    Non-nomic vectors in DB for these articles: 0
    Total vectors used: 2055
    PASS: zero non-nomic vectors used
  Matrix shape: (2055, 768)

Step 2: Deleting all clusters...
  Deleted 338 clusters.  [from prior interrupted run]

Step 3: Time-windowed DBSCAN (eps=0.35, min_samples=2, window=14d)...
  Created 772 clusters.

Step 4: Reassigning claims.cluster_id...
  Updated 7747 claims with new cluster_id.

Step 5: Re-classifying cluster verticals...
  Classified 772 clusters.

============================================================
Cluster count: 772

Sources per cluster histogram:
    1 source(s):   704 clusters
    2 source(s):    49 clusters
    3 source(s):     8 clusters
    4 source(s):     3 clusters
    5 source(s):     2 clusters
    6 source(s):     3 clusters
    7 source(s):     1 clusters
   12 source(s):     1 clusters
   31 source(s):     1 clusters

Articles per cluster histogram:
    1 article(s):   598 clusters
    2 article(s):    84 clusters
    3 article(s):    43 clusters
    4 article(s):    10 clusters
    5 article(s):    10 clusters
    6 article(s):     8 clusters
    7 article(s):     6 clusters
    8 article(s):     5 clusters
    9 article(s):     2 clusters
   12 article(s):     2 clusters
   19 article(s):     1 clusters
   32 article(s):     1 clusters
   38 article(s):     1 clusters
  809 article(s):     1 clusters

Largest cluster: 809 articles
============================================================
```

### Assessment

- Hygiene guard: PASS (0 non-nomic vectors, 2055 re-embedded, 2055 total)
- Blob guard: RUNNING (772 clusters vs 338 with prefix) but max cluster 809 >> 94 target
- The blob guard splits at eps-0.05=0.30, then 0.25 (floor). The 809-article cluster
  cannot be split below 60 even at eps=0.25 — nomic embeddings produce very high cosine
  similarity for news articles in the same time window.
- This is consistent with nomic-prefix-disaster.md findings: at eps=0.30 without prefix,
  mega-cluster was 930 articles.
- Multi-source clusters (>=2): 68

### Checkpoint commit: (after Step 3)

---

## Step 4: Per-story cluster membership

| Story | Mega-cluster 7512 | Other clusters | Sources in 7512 |
|-------|-------------------|----------------|-----------------|
| Venezuela | 84 articles, 21 sources | 4 singletons (7396, 7390, 7221, 7214) | 21 |
| Hormuz | 22 articles, 10 sources | 7491(2), 7408(1) | 10 |
| Heatwave | 47 articles, 13 sources | 7542(1), 7493(1) | 13 |
| Anthropic | 3 articles, 3 sources | 7427(1) | 3 |

Mega-cluster 7512: 782 articles (from claims), 31 distinct sources.
Orphaned claims: 0.

**FRAGMENTED:** Venezuela split across 5 clusters (84 in mega + 4 singletons).
**MIXED:** All 4 seed stories in cluster 7512 — multi-story contamination.

---

## Agent 2 (pipeline requirement): Forensic extraction on 27 new articles

Agent 1 (incremental): 27 new articles embedded + clustered (1 new cluster, 773 total).
Agent 2: 76 claims extracted from 27 articles.
Total claims: 7,823 (was 7,747 + 76 new).

---

## Step 5: reset_claim_state + match_all_clusters sim=0.85

```
reset_claim_state:
  Before: claims=7823, claim_sources=8190, claim_variants=932
  Reset 7823 claims to PENDING
  Deleted 932 claim_variant rows
  Deleted 8190 claim_sources rows
  Inserted 7823 claim_sources rows
  After: claims=7823, claim_sources=7823, claim_variants=0
  VERIFIED: claim_sources count (7823) == claims count (7823)

match_all_clusters sim=0.85:
  Clusters with claims: 740
  Clusters processed: 145
  Total merges: 521
  Total sources linked: 221
  Elapsed: 227.5s

Claims after matching: 7302
Claims with >=2 distinct sources: 158
Claims with >=2 T1/T2 pool sources: 47
```

---

## Step 6: Agent 3 all clusters

```
Agent 3: 773 clusters, 1445 claims classified

CLAIMS BY STATE:
  PENDING: 5857
  UNRESOLVED: 1441
  CONSENSUS_ABSORBED: 4

ABSORBED TOTAL: 4

ABSORBED PER STORY:
  Venezuela: 0 absorbed / 239 total claims
  Hormuz: 1 absorbed / 93 total claims
  Heatwave: 0 absorbed / 153 total claims
  Anthropic: 0 absorbed / 13 total claims

SOURCES WITH >=1 ABSORBED CLAIM (claim-source links):
  apnews (T1): 3 links (3 distinct claims)
  reuters (T1): 1 link (1 distinct claim)
  npr (T1): 1 link (1 distinct claim)
  theguardian (T1): 1 link (1 distinct claim)
  foxnews (T2): 1 link (1 distinct claim)
  nytimes (T2): 1 link (1 distinct claim)
  cnn (T2): 1 link (1 distinct claim)
  abcnews (T2): 1 link (1 distinct claim)
  aljazeera (T3): 1 link (1 distinct claim)
  france24 (T3): 1 link (1 distinct claim)
```
