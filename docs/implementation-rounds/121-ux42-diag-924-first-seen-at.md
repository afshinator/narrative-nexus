# Round 121 — UX42: Cluster 924 first_seen_at diagnostic (READ-ONLY)

**Date:** 2026-07-09
**Order:** UX42-DIAG
**Status:** COMPLETE
**Branch:** main

FP START: 378/10/358/17/13653
FP END:   378/10/358/17/13653 ✓

## T1 — Schema

```
CREATE TABLE claim_sources (
    claim_id      INTEGER NOT NULL REFERENCES claims(id),
    source_id     INTEGER NOT NULL REFERENCES sources(id),
    first_seen_at TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (claim_id, source_id)
)
```

first_seen_at has DEFAULT `datetime('now')` but many rows have NULL or empty string — the default was never backfilled for rows created before the column was added.

## T2 — NULL recount

```
total | null_count
233   | 145
```

145 of 233 claim_sources rows have NULL or empty first_seen_at. 88 are populated. This matches the UX26/UX27 handoff.

## T3 — Do populated rows match article publish dates?

```
populated | match_count | differ_count
88        | 88          | 0
```

All 88 populated claim_sources rows have first_seen_at dates matching the article's published_at date. Zero differences. Sample: 30 rows across MercoPress through BBC — all "match."

## T4 — Are NULL rows derivable?

```
nulls_with_article_date
145
```

All 145 NULL rows have articles with non-NULL published_at. Every NULL is derivable.

## T5 — Resulting timeline span

```
min_date  | max_date  | span | distinct_days | total_rows | populated | derived
2026-06-24|2026-06-29|5.0   |6              |233         |88         |145
```

Backfilling all 145 NULLs with article published_at produces:
- Same span: 2026-06-24 → 2026-06-29 (5.0 days)
- Same 6 distinct days
- 233 total rows (88 existing + 145 backfilled)

The timeline's date-axis span doesn't change — both populated and derived values map to the same 6 calendar days. Backfilling adds density (more dots per date) but no new dates.

## Verdict

Cluster 924's timeline would span 6 distinct days with 233 claim_sources rows if NULLs were backfilled from article published_at. This would pass the UX26/UX27 single-day suppression gate (6 > 1) but the current check counts DISTINCT DATE of populated first_seen_at only (88 rows over 6 days) and the NULL rows are ALSO over 6 days — just not counted. The gate incorrectly sees 145 empty rows as suppression-worthy when they actually have the same date range as the 88 populated ones.

The gate logic (`distinctDays > 1` on populated rows only) was correct for the original intent (avoid rendering timeline when data is genuinely sparse), but the fix is simpler than previously thought: backfill NULL first_seen_at from article published_at, and the timeline instantly has 233 rows over 6 dates.

## Compliance Table

| # | Requirement | Met? | Evidence |
|---|-------------|------|----------|
| T1 | claim_sources schema pasted | YES | Raw sqlite_master output |
| T2 | NULL recount pasted | YES | `233|145` |
| T3 | Populated vs article date comparison | YES | `88|88|0` — all match |
| T4 | Derivability count pasted | YES | `145` — all derivable |
| T5 | Timeline span with derived dates | YES | 2026-06-24→2026-06-29, 5.0d, 6 days, 233 rows |
| — | Fingerprint unchanged | YES | 378/10/358/17/13653 both |
