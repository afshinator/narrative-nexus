# UX8 — NULL first_seen_at Backfill

**Date:** 2026-07-06
**Status:** COMPLETE — uncommitted. Build 470ms, vitest 12/3 baseline. Fingerprint unchanged.

---

## B1 — Pipeline Code Fix

**pipeline/claim_matching.py:142**
```diff
- first_seen = row["published_at"] or row["created_at"] if hasattr(row, "created_at") else ""
+ first_seen = row["published_at"] if row["published_at"] else None
```
Root cause: `row` from the SQL query (lines 76-82) has columns `id, text, article_id, published_at, source_id` — no `created_at` column. The `hasattr(row, "created_at")` check was always False, falling through to empty string `""`. When `published_at` was NULL on the matched variant's article, `first_seen` became `""`. Now: truthy `published_at` → use it; falsy → `None`.

**db/claim_sources.py:15-18**
```diff
- If first_seen_at is provided, it overrides the DEFAULT datetime('now').
+ If first_seen_at is provided (non-empty and non-None), it overrides the DEFAULT datetime('now').

- if first_seen_at is not None:
+ if first_seen_at is not None and first_seen_at != "":
```
Guard: empty string `""` is falsy but not None — previously passed through to INSERT as empty text. Now rejected, falling through to the `else` branch which inserts without `first_seen_at`, letting SQLite's DEFAULT `datetime('now')` apply.

---

## B2 — Data Backfill

**Backup:** `data/demo/backups/demo-before-ux8.db` (4.5M, created before any writes)

**4 rows backfilled from claim_variants → articles:**

| claim_id | source_id | domain | Before | After | Source |
|----------|-----------|--------|--------|-------|--------|
| 2799 | 5 | theguardian.com | NULL | 2026-03-13 | Article 941 (claim_variant → The Guardian) |
| 2802 | 1 | reuters.com | NULL | 2026-03-10 | Article 940 (claim_variant → Reuters) |
| 2811 | 2 | apnews.com | NULL | 2026-03-24 | Article 942 (claim_variant → AP News) |
| 2815 | 2 | apnews.com | NULL | 2026-04-07 | Article 943 (earliest of 2 variants, AP News) |

**Backfill SQL (verbatim):**
```sql
UPDATE claim_sources SET first_seen_at = '2026-03-13T00:00:00+00:00' WHERE claim_id=2799 AND source_id=5;
UPDATE claim_sources SET first_seen_at = '2026-03-10T00:00:00+00:00' WHERE claim_id=2802 AND source_id=1;
UPDATE claim_sources SET first_seen_at = '2026-03-24T00:00:00+00:00' WHERE claim_id=2811 AND source_id=2;
UPDATE claim_sources SET first_seen_at = '2026-04-07T00:00:00+00:00' WHERE claim_id=2815 AND source_id=2;
```

---

## B3 — Fingerprint Verification

```
articles|358
claims|378
absorbed|10
clusters|17
snapshots|13653
```

**Unchanged: 378/10/358/17/13653.**

---

## B4 — Timeline Header After Backfill

```
$ curl -s http://localhost:3000/api/timeline/966 | python3 -c "..."
Header: 3 sources · 20 claims · 48 days (2026-03-10 to 2026-04-27)
NULL remaining: 0
```

**Timeline page renders:** 0 NULL entries. Day range: Mar 10 → Apr 27 = 48 days. The Timeline component computes `days.length` = 49 day-marker boundaries (Mar 10 through Apr 27 inclusive).

All 4 previously-NULL claim_sources rows now have real timestamps from their corresponding variant articles. No recomputation of snapshots needed — snapshot data is unaffected (snapshots use `MIN(first_seen_at)` which was already returning non-NULL for these claims from the non-NULL source rows).

---

## Verification

| Check | Result |
|-------|--------|
| `npm run build` | PASS (470ms) |
| Vitest | 125 pass, 12 fail, 3 files failed (baseline unchanged) |
| Fingerprint | 378/10/358/17/13653 (unchanged) |
| Timeline NULL count | 0 |

---

## Modified Files (uncommitted)

```
M data/demo/demo.db           (4 rows updated)
M db/claim_sources.py         (B1: reject empty string)
M docs/STATUS.md              (UX8 phase + violation #22)
M pipeline/claim_matching.py  (B1: None instead of "")
M src/components/Tooltip.tsx
M src/pages/ClusterReport.tsx
M src/pages/Sources.tsx
M src/pages/Timeline.tsx
?? docs/implementation-rounds/70-ux7-cluster-timeline-copy.md
?? docs/implementation-rounds/71-ux7-followup.md
```

The 4 `src/` files are from prior UX7 changes (uncommitted).

---

## Compliance Table

| # | Requirement | Met? | Evidence |
|---|------------|------|----------|
| B1 | Fix pipeline/claim_matching.py:142 + db/claim_sources.py:18 | YES | :142 → None fallback; :18 → reject "" |
| B2 | Backfill 4 NULL rows, backup first | YES | 4 rows updated, backup at data/demo/backups/ |
| B3 | Fingerprint unchanged, no snapshots recomputed | YES | 378/10/358/17/13653 |
| B4 | Timeline header: sources·claims·days, 0 NULL | YES | 3·20·48 days, 0 NULL |
| Violation | #22 added to ledger | YES | STATUS.md:120 — fabricated "10 days" in UX7 |
| Build | npm run build PASS | YES | 470ms |
| Vitest | 12/3 baseline | YES | No regressions |

**ROUND OBJECTIVE:** NULL first_seen_at backfilled from variant articles, pipeline code fixed to never write empty string: **YES**

---

**Suggested commit:** `UX8: backfill NULL first_seen_at, reject empty-string in pipeline`
