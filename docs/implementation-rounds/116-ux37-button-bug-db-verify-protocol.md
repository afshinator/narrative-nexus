# Round 116 — UX37: UX36 followups

**Date:** 2026-07-09
**Order:** UX37
**Status:** COMPLETE
**Branch:** main

## Task 1 — Fix button state bug

**Root cause:** Copy text was static ("Paused by default") regardless of scraper state. When the scraper was running (stale pre-restart server state), this created a contradiction: text says paused, button says Stop.

**Fix:** Made the description text dynamic — shows different copy when running vs paused.

```diff
- Polls RSS feeds from 37 sources, ingests new articles, and rescans
- on a schedule. Paused by default — press Start to begin live
- collection.
+ {isRunning
+   ? "Polling RSS feeds from 37 sources, ingesting new articles, and rescanning on a schedule."
+   : "Polls RSS feeds from 37 sources, ingests new articles, and rescans on a schedule. Paused by default — press Start to begin live collection."}
```

Button labels and `isRunning` logic were already correct — only the static copy caused the mismatch.

## Task 2 — Verify DB restore

```
$ git status data/demo/demo.db
On branch main
nothing to commit, working tree clean

$ git log -1 --oneline -- data/demo/demo.db
5f18c3e UX6-8: nav integrity, cluster/timeline presentation, first_seen_at backfill + pipeline guard

FP: 378/10/358/17/13653
```

DB is clean — no modifications, restored from the correct commit (UX6-8, the golden fingerprint commit). Not git-lfs — plain SQLite file tracked in git.

## Task 3 — Verification-hygiene note

Added to STATUS.md BANNED section:
```
**Scraper endpoint hygiene (UX37):** Scraper endpoints (/api/scraper/start, /api/scraper/stop)
now execute under the one-DB paradigm. Any verification that hits these endpoints must run against
a scratch DB copy, never data/demo/demo.db. Restoration via git checkout is a fallback, not a plan.
```

## Task 4 — Violation #30

Logged in STATUS.md Prior Violations table:
```
| 30 | YES-on-failed-bound: FP unchanged claim while DB was mutated then restored |
```
Full description documents the UX36 mutation-recovery sequence and notes this is the same pattern as #24.

## Files Changed

```
src/pages/Settings.tsx   | Dynamic copy for running/paused states
docs/STATUS.md           | Phase line + hygiene note + Violation #30
```

## Compliance Table

| # | Requirement | Met? | Evidence |
|---|-------------|------|----------|
| 1 | Button state bug fixed | YES | Root cause: static copy. Fixed: dynamic copy via `isRunning` |
| 2a | git status clean | YES | `nothing to commit, working tree clean` |
| 2b | git log shows correct commit | YES | `5f18c3e UX6-8...` |
| 2c | Fingerprint pasted | YES | `378/10/358/17/13653` |
| 3 | Hygiene note added | YES | Diff pasted, in BANNED section |
| 4 | Violation #30 logged | YES | Diff pasted, in Prior Violations table |
| — | STATUS.md updated | YES | UX37 phase line |
