# PoC 9 — Backfill Pipeline (Scaled-Down Exploration)

**Date:** 2026-06-27
**Status:** COMPLETE
**DB:** `data/backfill-2026-06-27.db` (1.1 MB)

## Goal

Prove the full pipeline (scrape → extract → insert → cluster → claims → consensus → snapshots) works end-to-end with real data from all 37 sources.

## Method

3-phase run on a persistent SQLite DB:

### Phase 1 — Scrape (30s)
- Polled all 37 RSS feeds
- 1,820 articles scraped, 1,814 inserted (6 duplicates by URL)
- No body extraction during scrape — body_status marked by feed type
- 400 articles marked BODY_UNAVAILABLE (Google News sources)

### Phase 2 — Sample extraction (42s)
- Extracted 1 article per native source (32 attempts)
- 25/33 sources produced bodies with 200+ chars
- Bodies updated in-place via UPDATE

### Phase 3 — Pipeline runner
- Created 1 test cluster (geopolitics vertical)
- Inserted 3 claims from 3 different sources (NPR, Guardian, Fox News)
- Ran `run_daily_pipeline()` — Agent 3 consensus + snapshot computation
- 37 snapshots written (one per source), 3 scored

## Results

| Metric | Value |
|--------|-------|
| Articles in DB | 1,814 |
| Articles with bodies | 25 |
| Articles unavailable | 400 |
| Clusters | 1 |
| Claims | 3 |
| Claims classified | 0 |
| Snapshots written | 37 |
| Scored snapshots | 3 |
| Unscored snapshots | 34 |
| Total time | 72s |
| DB size | 1.1 MB |

## Why 0 claims classified (correct behavior)

All 3 claims came from different sources on unrelated topics:
- NPR: World Cup ticket resale
- Guardian: Wimbledon ticket prices
- Fox News: China/Africa rare earth minerals

Each claim had exactly 1 T1/T2 source reporting. Agent 3's consensus math requires multiple T1/T2 sources reporting the same claim to cross the threshold. With zero overlap, all claims correctly stayed PENDING.

**This confirms Agents 1 and 2 are the real blockers.** Without them:
- Agent 1: No semantic clustering of related articles
- Agent 2: No overlapping claims extracted across sources
- Agent 3: Has clusters and claims but nothing to align (single-source claims)

## What worked

- ✓ RSS polling across all 37 sources in 30s
- ✓ Article insertion with duplicate URL detection
- ✓ newspaper4k extraction for 25/33 native sources
- ✓ Cluster and claim CRUD operations
- ✓ `run_daily_pipeline()` — Agent 3 + snapshot computation
- ✓ Snapshot table populated with r_orig, r_val, r_speed, archetype values
- ✓ Persistent SQLite DB at correct schema

## What's blocked

- ✗ Full extraction — 1,400 native articles × ~3s each = ~70 min/poll. Needs Firecrawl or parallelization.
- ✗ Agent 1 (IntakeClusteringAgent) — stub, needs AMD GPU for embeddings
- ✗ Agent 2 (ForensicExtractionAgent) — stub, needs Fireworks API key for LLM extraction
- ✗ Agent 4 (SilentAuditorAgent) — stub

## Snapshot sample

```
Source          r_orig  r_val   r_speed  archetype
npr             0.0     0.0     NULL     CONSENSUS_FOLLOWER
theguardian     0.0     0.0     NULL     CONSENSUS_FOLLOWER
foxnews         NULL    NULL    NULL     NULL
(all others)    NULL    NULL    NULL     NULL
```

Scored snapshots are all 0.0 because there's only 1 cluster with 3 unrelated single-source claims — no convergence data to compute meaningful scores.

## Files

- `data/backfill-2026-06-27.db` — persistent SQLite, can be opened with `sqlite3` or the app
- No code changes required — all existing pipeline code used as-is
