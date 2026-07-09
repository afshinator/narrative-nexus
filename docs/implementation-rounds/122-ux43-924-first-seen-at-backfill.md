# Round 122 — UX43: Cluster 924 first_seen_at backfill (WRITE)

**Date:** 2026-07-09
**Order:** UX43
**Status:** COMPLETE
**Branch:** main

## T1 — Backup

```
data/demo/backups/demo-pre-ux43.db  4.5M
data/demo/demo.db                   4.5M
```

Sizes match. Backup created.

## T2 — Before-state

```
233|145
```

233 total claim_sources rows for cluster 924, 145 NULL/empty.

## T3 — Backfill

```sql
UPDATE claim_sources
SET first_seen_at = (
  SELECT MIN(a.published_at)
  FROM claims c
  JOIN articles a ON a.id = c.article_id
  WHERE c.id = claim_sources.claim_id
    AND a.published_at IS NOT NULL
)
WHERE (first_seen_at IS NULL OR first_seen_at = '')
  AND claim_id IN (SELECT id FROM claims WHERE cluster_id = 924);
```

Rows affected: **145** ✓

## T4 — After-state

```
Tie-out 1: 233|0    (zero NULLs)
Tie-out 2: 2026-06-24|2026-06-29|6   (6 distinct days)
```

## T5 — No collateral damage

```
Fingerprint: 378/10/358/17/13653  ✓
Cluster 966: 20|0 (0 NULL, unchanged)  ✓
Total claim_sources: 569 before, 569 after  ✓
```

## T6 — Gate check

```
Cluster 924: 6 distinct days, 0 empty  → timeline available
Cluster 966: 6 distinct days, 0 empty  → unchanged, already available
```

UX26/UX27 suppression gate: `distinctDays > 1 AND emptyDateCount == 0`. Both conditions now pass for cluster 924. The /stories page should show the "View Timeline" link for both clusters.

## Compliance Table

| # | Requirement | Met? | Evidence |
|---|-------------|------|----------|
| T1 | Backup created, sizes match | YES | Both 4.5M |
| T2 | Before-state: 233\|145 | YES | Pasted |
| T3 | UPDATE run, 145 rows | YES | Statement pasted, changes()=145 |
| T4a | After-state: 233\|0 | YES | Pasted |
| T4b | Distinct days: 6, 2026-06-24→2026-06-29 | YES | Pasted |
| T5a | Fingerprint 378/10/358/17/13653 | YES | Pasted |
| T5b | Cluster 966: 20\|0 unchanged | YES | Pasted |
| T5c | Total claim_sources: 569 unchanged | YES | Before and after both 569 |
| T6 | Gate: 6 distinct, 0 empty, timeline available | YES | Pasted |
| — | STATUS.md not updated (diagnostic+write combo) | n/a | Execution round doc suffices |
