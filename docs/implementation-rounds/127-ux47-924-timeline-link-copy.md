# Round 127 — UX47: 924 timeline link re-enable + Stories copy

**Date:** 2026-07-09
**Order:** UX47
**Status:** COMPLETE
**Branch:** main

FP START: 378/10/358/17/13653
FP END:   378/10/358/17/13653 ✓

## T1 — Verify 924 backfill persistence

```
$ git status data/demo/demo.db
On branch main
nothing to commit, working tree clean

$ git log -1 --oneline -- data/demo/demo.db
273e8d1 demo script

924 NULL count: 0
```

(a) The mutation is COMMITTED. File is tracked, working tree is clean, the last commit touching demo.db (`273e8d1`) contains the backfill (verified: extracted committed DB → NULL count=0).
(b) `git checkout` would roll back to `273e8d1` — the same commit we're already at.

## T2 — Re-enable Timeline link

Replaced hardcoded `story.id === 966` with API gate:

```tsx
// Before:
{story.id === 966 && (
  <Link to={`/timeline/${story.id}`}>View Timeline</Link>
)}

// After:
{story.distinctDays > 1 && story.emptyDateCount === 0 && (
  <Link to={`/timeline/${story.id}`}>View Timeline</Link>
)}
```

Added `distinctDays` and `emptyDateCount` to StoryData interface + fetchStory. Both now read from API `summary.distinctDays` / `summary.emptyDateCount`.

Both clusters pass the gate: 966 (distinctDays=6, empty=0), 924 (distinctDays=6, empty=0).

## T3 — Intro copy

Added scraping-to-news distinction:

> "...what the instrument is actually measuring. Article scraping was performed July 3–5, 2026; coverage windows below reflect when the news itself was published."

## T4 — Verify

| Check | Result |
|-------|--------|
| Build | `✓ built in 467ms` |
| Vitest | 12 failed (baseline), 119 passed, 4 skipped |
| FP | 378/10/358/17/13653 ✓ |
| 924 NULL count | 0 ✓ |
| 966 Timeline button | visible (gate passes) |
| 924 Timeline button | visible (gate passes, was hidden) |
| /timeline/924 | 20 sources, 233 claims, 6 dates, span 2026-06-24→2026-06-29 |

## Files Changed

```
src/pages/Stories.tsx | +4 fields (distinctDays, emptyDateCount), gate change (id===966 → real check), copy update
docs/STATUS.md        | UX47 phase line
```

## Compliance Table

| # | Requirement | Met? | Evidence |
|---|-------------|------|----------|
| T1a | git status/log pasted | YES | Clean working tree, commit 273e8d1 |
| T1b | NULL count = 0 | YES | Pasted |
| T1c | FP unchanged | YES | 378/10/358/17/13653 |
| T2a | Hardcoded id===966 removed | YES | Replaced with distinctDays>1 && emptyDateCount===0 |
| T2b | Gate fields read from API | YES | summary.distinctDays + summary.emptyDateCount |
| T3 | Intro copy clarifies scraping dates | YES | Diff pasted |
| T4a | Build + vitest + FP | YES | Build 467ms, 12 baseline |
| T4b | Both cards show Timeline button | YES | 966 + 924 both pass gate |
| T4c | /timeline/924 renders | YES | 20 sources, 233 claims, 6 dates |
| — | STATUS.md updated | YES | UX47 phase line |
