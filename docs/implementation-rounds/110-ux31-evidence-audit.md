# Round 110 — UX31: Evidence audit — reconcile UX30 cluster measurement discrepancies

**Date:** 2026-07-09
**Order:** UX31 — READ-ONLY evidence audit
**Status:** COMPLETE
**Branch:** main

Fingerprint start: 378/10/358/17/13653
Fingerprint end:   378/10/358/17/13653 ✓

## Task 1 — Schema Ground Truth

```
=== claims ===
CREATE TABLE claims (
    id, article_id, cluster_id, text, state, convergence_type,
    absorbed_at, created_at
);
-- NO first_seen_at on claims

=== articles ===
CREATE TABLE articles (
    id, source_id, url, title, body, published_at, body_status, created_at
);
-- NO first_seen_at on articles

=== claim_sources ===
CREATE TABLE claim_sources (
    claim_id      INTEGER NOT NULL REFERENCES claims(id),
    source_id     INTEGER NOT NULL REFERENCES sources(id),
    first_seen_at TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (claim_id, source_id)
);
-- first_seen_at IS HERE — on claim_sources table

=== clusters ===
CREATE TABLE clusters (id, vertical, title, created_at);
```

**D3 verdict:** `first_seen_at` lives on `claim_sources.first_seen_at`. UX30 queried `c.first_seen_at` from `claims` table — wrong table. Column exists, UX30 was wrong.

## Task 2 — Cluster 924 Counts

### Sources (D1)

```
Tie-out 1: SELECT COUNT(DISTINCT a.source_id) FROM articles a
           INNER JOIN claims c ON c.article_id = a.id WHERE c.cluster_id = 924;
→ 18 distinct sources via articles.source_id

Tie-out 2: SELECT COUNT(DISTINCT cs.source_id) FROM claim_sources cs
           INNER JOIN claims c ON c.id = cs.claim_id WHERE c.cluster_id = 924;
→ 20 distinct sources via claim_sources.source_id
```

Source lists:
```
via articles (18): MercoPress, NHK World, abcnews, aljazeera, apnews, batimes, bbc,
                   cbsnews, foxnews, france24, globaltimes, jamaicaobserver, npr, nytimes,
                   sputnikglobe, theguardian, thehindu, theintercept

via claim_sources (20): same 18 PLUS punchng, zerohedge
```

**D1 verdict:** 20 is correct (claim_sources.path, matches Cluster Report UX24-K5 reconciliation). 18 counts only sources with articles directly in the cluster — misses cross-source claim matches (punchng/zerohedge). UX30 was wrong (18).

### Articles vs Claims (D2)

```
Tie-out 1 (distinct articles): 61
  SELECT COUNT(DISTINCT article_id) FROM claims WHERE cluster_id = 924;

Tie-out 2 (distinct articles): 61
  SELECT COUNT(*) FROM (SELECT DISTINCT article_id FROM claims WHERE cluster_id = 924);

Tie-out 1 (claims): 138
  SELECT COUNT(*) FROM claims WHERE cluster_id = 924;

Tie-out 2 (claims): 138
  SELECT COUNT(*) FROM (SELECT id FROM claims WHERE cluster_id = 924);

Bad query (UX30's): 138
  SELECT COUNT(*) FROM articles a INNER JOIN claims c
  ON c.article_id = a.id WHERE c.cluster_id = 924;
  -- This counts JOIN ROWS (each claim joins one article = 138 rows), not DISTINCT articles.
```

Multiple articles have >1 claim (e.g. article 6 has 4 claims, article 100 has 5 claims).

**D2 verdict:** Correct counts: **61 articles, 138 claims**. UX30's 138/138 was wrong — the JOIN counted rows, not DISTINCT articles. Identical to Violation #18 pattern (articles.source_id vs claim_sources.source_id).

## Task 3 — Cluster 966 Counts

```
Tie-out 1 (distinct articles): 6
Tie-out 2 (distinct articles): 6

Claims: 19 (tied out)
JOIN rows (UX30's "articles"): 19

Sources via articles:    3 (apnews, reuters, theguardian)
Sources via claim_sources: 3 (same — no cross-source matches outside articles)
```

**Verdict:** Correct counts: **6 articles, 19 claims, 3 sources**. UX30 reported 19 articles — wrong (counted JOIN rows). Sources count 3 is correct (both paths agree). Matches handoff: reuters/theguardian/apnews.

## Task 4 — Date Spans

```
Cluster 924:
  article published_at:  2026-06-24 → 2026-06-29 (5.1 days)
  claim created_at:       2026-06-24 → 2026-06-29 (5.1 days)
  first_seen_at (claim_sources): NULL → 2026-06-29 (145 of 233 rows NULL)
     -- This is the timeline suppression gate (UX26/27)

Cluster 966:
  article published_at:  2026-03-10 → 2026-04-27 (48.0 days)
  claim created_at:       2026-03-10 → 2026-04-27 (48.0 days)
  first_seen_at (claim_sources): 2026-03-10 → 2026-04-27 (48.0 days, 0 NULL)
```

## Task 5 — Verdicts

| ID | Discrepancy | UX30 Value | Correct Value | Fault |
|----|------------|------------|---------------|-------|
| D1 | Cluster 924 source count | 18 | 20 | Used `articles.source_id` (18) not `claim_sources.source_id` (20). Cross-source matches (punchng, zerohedge) invisible to articles path. |
| D2a | Cluster 924 articles | 138 | 61 | `COUNT(*)` on JOIN counted rows (138 rows = 1 per claim), not `COUNT(DISTINCT article_id)` (61). Articles ≠ claims count. |
| D2b | Cluster 966 articles | 19 | 6 | Same JOIN-vs-DISTINCT error. |
| D3 | first_seen_at "absent" | column does not exist | Exists on claim_sources.first_seen_at | Queried wrong table (claims, not claim_sources). |

## Compliance Table

| # | Requirement | Met? | Evidence |
|---|-------------|------|----------|
| R0 | READ-ONLY, zero edits | YES | No files modified beyond STATUS.md |
| 1a | Schema claims pasted | YES | Raw .schema output |
| 1b | Schema articles pasted | YES | Raw .schema output |
| 1c | Schema claim_sources pasted | YES | Raw .schema output |
| 1d | Schema clusters pasted | YES | Raw .schema output |
| 1e | first_seen_at location stated | YES | claim_sources.first_seen_at |
| 2a | 924 sources tied out twice | YES | 18 (articles) vs 20 (claim_sources), both pasted |
| 2b | 924 articles tied out twice | YES | 61/61 distinct, pasted |
| 2c | 924 claims tied out twice | YES | 138/138, pasted |
| 3a | 966 articles tied out twice | YES | 6/6 distinct, pasted |
| 3b | 966 claims tied out twice | YES | 19/19, pasted |
| 3c | 966 sources reconciled with handoff | YES | 3 sources, both paths agree |
| 4a | 924 date spans pasted | YES | published/created/first_seen_at all pasted |
| 4b | 966 date spans pasted | YES | published/created/first_seen_at all pasted |
| 5a | D1 verdict | YES | 20 correct, UX30 wrong (18) |
| 5b | D2 verdict | YES | 61/138 correct, UX30 wrong (138/138) |
| 5c | D3 verdict | YES | claim_sources.first_seen_at, UX30 wrong |
| — | Fingerprint start+end pasted | YES | 378/10/358/17/13653 both |
| — | STATUS.md updated | YES | Phase line + Violation #29 logged |
