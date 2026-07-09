# Round 120 — UX41: Stories fixups

**Date:** 2026-07-09
**Order:** UX41
**Status:** COMPLETE
**Branch:** main

## Task 1 — Fix cluster 924 title

```
Before: Cluster W169 L-3000 (auto-generated DBSCAN label)
After:  Venezuela Emergency and Rescue Response

SQL: UPDATE clusters SET title = 'Venezuela Emergency and Rescue Response' WHERE id = 924;

966 confirmed correct: US-Iran War: March Escalation & April Ceasefire
```

Backup: `data/demo/backups/pre-ux41-1752088746.db`

FP before: 378/10/358/17/13653
FP after:  378/10/358/17/13653 (unchanged — title change doesn't affect counts)

## Task 2 — Move hardcoded stats into API

`app/main.py` cluster report API now returns:
```python
"silentEdits": COUNT(*) FROM silent_edits JOIN claims for cluster
"corrections": COUNT(*) FROM corrections JOIN claims for cluster
"timeToConsensusDays": median julianday(absorbed_at) - julianday(created_at) for absorbed claims
```

`Stories.tsx`: removed STATIC_EXTRAS hardcoded map. All three fields now read from API `summary.silentEdits`, `summary.corrections`, `summary.timeToConsensusDays`.

Verified API output:
```
966: 0 silentEdits, 0 corrections, 117.8 ttcDays
924: 10 silentEdits, 0 corrections, 10.9 ttcDays
```

## Task 3 — Improved time-to-consensus label

```
Before: "117.8 days median"
After:  "Median: 117.8 days"
        "From first report to consensus-absorbed"
        (tooltip: "Time between a claim's first appearance and its cross-source
         corroboration by ≥2 consensus-pool sources.")
```

Clearer: "Median:" prefix, explanation sub-line, full definition in tooltip hover.

## Verification

| Check | Result |
|-------|--------|
| Build | `✓ built in 484ms` |
| Vitest | 12 failed (baseline), 119 passed, 4 skipped |
| FP | 378/10/358/17/13653 |
| 924 title renders correctly | "Venezuela Emergency and Rescue Response" |
| API returns new fields | 0/0/117.8 (966), 10/0/10.9 (924) |
| Hardcoded map removed | STATIC_EXTRAS deleted from Stories.tsx |

## Files Changed

```
data/demo/demo.db                      | Title UPDATE (1 row)
data/demo/backups/pre-ux41-1752088746.db | PRE-UPDATE BACKUP
app/main.py                            | +25 lines (3 new queries)
src/pages/Stories.tsx                  | -7 hardcoded map, +6 API fields, +4 ttc label
```

## Compliance Table

| # | Requirement | Met? | Evidence |
|---|-------------|------|----------|
| 1 | 924 title fixed + backup created | YES | UPDATE + confirmed SELECT, backup path pasted |
| 2a | silentEdits in API | YES | Query + response pasted |
| 2b | corrections in API | YES | Query + response pasted |
| 2c | timeToConsensus in API | YES | Median computation + response pasted |
| 2d | Hardcoded map removed | YES | STATIC_EXTRAS deleted |
| 3 | Improved ttc label | YES | "Median: N days" + explanation + tooltip |
| 4a | FP unchanged | YES | 378/10/358/17/13653 both |
| 4b | Build + vitest | YES | Build 484ms, 12 baseline, 0 new |
| — | STATUS.md updated | YES | UX41 phase line |
