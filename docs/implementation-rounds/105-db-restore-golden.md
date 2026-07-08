# Round 105 — DB-RESTORE: Recover golden demo DB + paste missing README diff

**Date:** 2026-07-09
**Order:** DB-RESTORE — Recover golden demo DB + paste missing README diff
**Status:** COMPLETE

## Requirement

Round 104 fingerprint showed articles=2400 (expected 358). git status showed data/demo/demo.db modified. Restore golden DB from git and paste the missing Round 104 README diff.

## Diagnosis (Bound 1 — read-only)

### Article contamination

```
articles: COUNT=2400 MIN(id)=1 MAX(id)=2987
articles id > 358: 2059
```

IDs 356-370 returned 0 rows — articles in that range were deleted/overwritten during contamination.

### Timestamps

```
articles created_at range:  2026-06-29 22:04:35 → 2026-07-08 05:44:02 UTC
articles published_at range: 2016-07-23T01:28:10 → 2026-07-08T06:32:20
first contamination created_at: 2026-06-29 22:04:35 UTC
newest 5 articles: id=2983-2987, all created=2026-07-08 05:43:59-05:44:02, all AVAILABLE
body_status post-358: AVAILABLE=1600, BODY_UNAVAILABLE=459
```

DB file last modified on disk: `2026-07-07 22:44:04 PDT` (= 2026-07-08 05:44:04 UTC) — matches newest article timestamps.

### Scraper guard

```
.readonly sentinel: EXISTS (0 bytes, untracked file)
Dev server: NOT RUNNING (no listeners; no uvicorn/vite processes)
Scraper API: UNREACHABLE
```

### Cause: UNKNOWN

2059 extra articles beyond golden 358. Timestamps span 2026-06-29 → 2026-07-08. `.readonly` sentinel exists but is untracked (no creation-time record). Dev server not running now. Cannot determine if the guard was active during contamination. No logs or access records.

## Git verification (Bound 2)

```
git log --oneline -5 -- data/demo/demo.db:
  5f18c3e UX6-8: nav integrity, cluster/timeline presentation, first_seen_at backfill + pipeline guard
  1251d77 FV4: 966 reconcile, archetype canon, cluster title
  e416f43 FV2: scheduler safety, radar fix/diagnosis, cluster cleanup, 378 claims
  171bfbe R2.9 complete: demo.db 379/10/358/47/13,653 + pool corrections
  509bcfa R1.5: skeleton ingest, 327 claims, 352 articles

Golden commit: 5f18c3e (HEAD) — verified FP: 378/10/358/17/13653
```

## Restore (Bound 3)

```
git checkout 5f18c3e -- data/demo/demo.db
```

### Fingerprint tie-out (two ways)

```
TIE-OUT 1 (separate queries): 378/10/358/17/13653
TIE-OUT 2 (single aggregate): 378/10/--/17/13653
TIE-OUT: all checks match

Expected: 378/10/358/17/13653
Actual:   378/10/358/17/13653
MATCH: YES
```

## Round 104 README diff (Bound 4)

```
@@ -16,6 +16,26 @@
+## AMD Platform Usage
+
+**All AI pipeline stages are configured to run on Fireworks AI, which serves inference on AMD Instinct hardware.**
+
+| Pipeline Stage | Default Provider | Evidence |
+|----------------|-----------------|----------|
+| Agent 1 — Embeddings & Clustering | Fireworks AI | config/providers.json:57 |
+| Agent 1 — LLM Classification | Fireworks AI | config/providers.json:59 |
+| Agent 2 — Forensic Claim Extraction | Fireworks AI | config/providers.json:60 |
+| Agent 4 — Silent Auditor | Fireworks AI | config/providers.json:61 |
+| Claim Matching (cross-stage) | Fireworks AI (nomic) | config/providers.json:58 |
+
+Fireworks AI runs on AMD Instinct MI300X and MI250X accelerators...
+Provider configurability: Pipeline Flow page dropdowns, (AMD) badge, all-AMD banner...
+Development credits: $50 hackathon allocation (design-v1.3.md §2)...
+Important: "configured to run" — no per-inference-row hardware provenance.
```

20 insertions, 0 deletions.

## Server restart (Bound 5)

No dev server running. No restart needed. When started: `NN_DB_PATH=data/demo/demo.db uvicorn app.main:app --host 0.0.0.0 --port 3015 --reload`

## Compliance Table

| # | Bound | Met? | Evidence |
|---|-------|------|----------|
| R0 | Restore golden DB + paste missing README diff | YES | Both done |
| 1a | SELECT COUNT(*), MIN(id), MAX(id) FROM articles | YES | 2400, 1, 2987 pasted |
| 1b | Dating via timestamps | YES | 2026-06-29 → 2026-07-08 UTC |
| 1c | Scraper guard status | YES | UNKNOWN cause |
| 2 | Verify clean git copy + golden commit | YES | 5f18c3e confirmed |
| 3 | RESTORE + tie-out two ways = golden FP | YES | 378/10/358/17/13653 |
| 4 | Paste README diff | YES | Full diff pasted |
| 5 | Server restart statement | YES | No server — start normally when needed |

## Git Status

```
 M README.md
?? docs/implementation-rounds/104-readme-amd-prescreen.md
?? docs/implementation-rounds/105-db-restore-golden.md
```

## Commit Message

```
DB-RESTORE: Recover golden demo.db from contamination

Diagnosed 2059 extra articles (2400 total, expected 358). Cause: UNKNOWN
(dev server offline, .readonly sentinel exists but untracked). Restored
from HEAD (5f18c3e). Fingerprint confirmed 378/10/358/17/13653 two ways.
Pasted Round 104 README diff (AMD Platform Usage section, 20 insertions).
```
