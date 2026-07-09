# Round 112 — DIAGNOSTIC: Demo DB vs Production DB relationship

**Date:** 2026-07-09
**Order:** DIAGNOSTIC — READ-ONLY
**Status:** COMPLETE
**Branch:** main

FP START: 378/10/358/17/13653
FP END:   378/10/358/17/13653 ✓

## Task 1 — Locate production DB

```
$ find /project/narrative-nexus/data -name "*.db" (excl backups)

data/nn-backup-2026-07-03-1151.db   44.7M  2026-07-03
data/nn-pre-phase2-dryrun-copy.db   28.8M  2026-06-28
data/nn-pre-t5-2026-07-02.db        28.8M  2026-07-02
data/backfill-2026-06-27.db          1.0M  2026-06-27
data/test.db                         8.0K
data/demo/demo.db                    5.8M

data/demo/backups/nn-frozen-2026-07-04.db  44.7M  2026-07-04
```

`data/nn.db` does NOT exist. The canonical production DB path referenced by all scripts (`seed_demo.py`, `backfill_framing.py`, etc.) is not present. The largest candidate is `nn-backup-2026-07-03-1151.db` (44.7M).

## Task 2 — Fingerprint production backup

```
nn-backup-2026-07-03-1151.db:
  fingerprint: 7747/13/4899/1179/44955
  date span: 2013-08-21 → 2026-07-03

nn-frozen-2026-07-04.db:
  fingerprint: 7747/13/5112/1179/44955
  date span: 2013-08-21 → 2026-07-03
```

Matches FAQ numbers: 7,747 claims / 4,899 articles / 1,179 clusters / 44,955 snapshots. Frozen copy has +213 more articles (5,112 vs 4,899).

## Task 3 — Article URL overlap

```
Demo:   358 articles, 358 distinct URLs
Prod:   4899 articles, 4899 distinct URLs

Overlap:           341 demo URLs present in production (95.3%)
Demo-only:          17 URLs NOT in production (4.7%)
Production-only:  4558 URLs NOT in demo
```

Sample demo-only URLs (Google News RSS feeds + CNN-specific):
```
https://news.google.com/rss/articles/CBMiowFBVV95cUxPMHBUeDZPa0UxUkVHeEt4TG...
https://www.cnn.com/2026/06/26/tech/anthropic-mythos-release
https://www.reuters.com/world/asia-pacific/iran-says-oil-blockade-will-continue...
```

## Task 4 — Cluster title overlap (approximate)

```
Demo clusters:   17
Prod clusters: 1130

Title match:     7 titles in both
Demo-only:       10 titles (incl. "US-Iran War: March Escalation & April Ceasefire", "Cluster W169 L-3000")
Prod-only:     1123 titles

Matching titles:
  demo:929 prod:5877  Article 245
  demo:922 prod:5743  Article 246
  demo:931 prod:5575  Article 260
  demo:921 prod:5822  Cluster W168 L0
  demo:923 prod:5823  Cluster W168 L1
  demo:951 prod:6461  Cluster W169 L0
  demo:934 prod:6462  Cluster W169 L1
```

The 7 matches are auto-generated cluster names from the clustering algorithm (W168/W169 labels) — they are NOT the same clusters semantically, just naming collisions. Demo clusters were re-derived by re-running Agent 1 on the curated article set.

## Task 5 — Seed / ingest code path

`scripts/harvest_story.py` copies articles by ID from production to demo:
```python
# Usage:
#   python3 scripts/harvest_story.py --source data/nn.db --db data/demo/demo.db \
#     --story Venezuela --ids 3,21,26,90,...

rows = src.execute(
    "SELECT id, source_id, url, title, body, published_at, body_status
     FROM articles WHERE id IN (...) ORDER BY id", ids,
).fetchall()
# INSERTS into demo DB with remapped IDs
```

`scripts/seed_demo.py` then runs the full pipeline against the demo DB's existing articles:
```python
# Takes --db (default: data/nn.db), runs Agents 1-4 + snapshots
agent1 = IntakeClusteringAgent(db_path=args.db, ...)
agent2 = ForensicExtractionAgent(db_path=args.db, ...)
# ... etc
```

Construction path: Production DB articles → `harvest_story.py` (copy by ID) → demo DB articles → `seed_demo.py` (re-run pipeline on curated set) → demo DB clusters/claims/snapshots.

## Task 6 — Verdict

**Verdict: (B) with nuance — Demo is a near-subset of production, not a strict subset.**

Evidence:
- 341/358 demo articles (95.3%) were harvested from production by article ID
- 17 demo articles (4.7%) were independently ingested: Google News RSS feeds and CNN-specific URLs not present in production
- Demo clusters were RE-DERIVED by re-running Agent 1 on the curated article set — cluster IDs differ from production even when titles collide
- `harvest_story.py` + `seed_demo.py` are the documented construction path

The demo is NOT a strict subset because (a) 17 articles are unique to demo and (b) clusters are re-computed from the curated article set, not copied from production.

## Compliance Table

| # | Requirement | Met? | Evidence |
|---|-------------|------|----------|
| 1 | Locate production DB files | YES | nn-backup-2026-07-03-1151.db (44.7M) + nn-frozen-2026-07-04.db |
| 2 | Fingerprint production DB | YES | 7747/13/4899/1179/44955 matches FAQ |
| 3 | Article URL overlap pasted | YES | 341/358 overlapping, 17 demo-only, 4558 prod-only |
| 4 | Cluster overlap pasted | YES | 7/1130 title matches (auto-generated names) |
| 5 | Seed/ingest code path pasted | YES | harvest_story.py + seed_demo.py lines quoted |
| 6 | Verdict stated with evidence | YES | (B) near-subset with nuance: 95.3% harvested, 4.7% independent, clusters re-derived |
| — | FP start+end pasted | YES | 378/10/358/17/13653 both |
| — | STATUS.md updated | YES | DIAGNOSTIC phase line |
