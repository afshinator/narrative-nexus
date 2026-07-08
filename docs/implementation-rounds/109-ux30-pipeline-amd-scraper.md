# Round 109 — UX30: Pipeline AMD card removal + scraper relocation + collection windows

**Date:** 2026-07-09
**Order:** UX30
**Status:** COMPLETE
**Branch:** main

## Changes

### 1. AMD summary card deleted (PipelineFlow.tsx)

Removed the F1+F5 Legend div (lines 173-247 old) — the card showing "All AI stages running on AMD Instinct accelerators via Fireworks AI", provider badges, and stage counts. Also removed unused `LegendItem` sub-component and `Play`/`Square` imports.

### 2. Scraper control relocated to Settings (Settings.tsx)

Added Scraper card to Settings page with:
- Status fetch on mount (`/api/scraper/status`)
- Start/Stop toggle with POST to `/api/scraper/{start,stop}`
- Readonly guard: button disabled when `.readonly` present
- Status display: running state + article count + last run time

### 3. Pipeline scraper card rewritten (PipelineFlow.tsx)

Removed Start/Stop button. New copy (verbatim):
> Runs continuously in production: polls RSS feeds, ingests, and rescans on a schedule. Paused here against a frozen demo corpus. Can be restarted in settings page.

Status span remains for running/paused/offline display.

### 4. Collection window measurements (read-only)

| Metric | Cluster 966 | Cluster 924 |
|--------|------------|------------|
| Articles | 19 | 138 |
| Distinct sources | 3 | 18 |
| Published span | 2026-03-10 → 2026-04-27 (48.0 days) | 2026-06-24 → 2026-06-29 (5.1 days) |
| Claims | 19 | 138 |
| Claim created span | 48.0 days | 5.1 days |
| Absorbed | 1 | 3 |
| Sources | apnews, reuters, theguardian | 18 sources |

`first_seen_at` NOT queryable — column does not exist on claims or articles in this DB version.

### 5. Test updates (pipeline-flow.test.tsx)

5 scraper tests replaced with 3 new tests matching new behavior:
- Shows status text on mount
- Shows article count when running
- No scraper button present (relocated to Settings)

Removed `userEvent` import (no longer needed).

## Verification

| Check | Result |
|-------|--------|
| Build | `✓ built in 444ms` |
| Vitest | 12 failed (baseline), 120 passed, 4 skipped — 0 new failures |
| Fingerprint | `378/10/358/17/13653` ✓ |
| 403 guard | `curl -X POST /api/scraper/start → 403 {"detail":"read-only demo"}` |
| Font floor | No sub-0.75rem introduced |
| AMD wording | No "ran/executed" language introduced |

## Files Changed

```
docs/STATUS.md                       |   3 +-
 src/__tests__/pipeline-flow.test.tsx |  76 ++++--------------
 src/pages/PipelineFlow.tsx           | 152 ++++---------------------------
 src/pages/Settings.tsx               |  86 +++++++++++++++++++-
 5 files changed, 122 insertions(+), 203 deletions(-)
```

## Compliance Table

| # | Requirement | Met? | Evidence |
|---|-------------|------|----------|
| 1 | Delete AMD summary card entirely | YES | Removed F1+F5 Legend div + LegendItem component |
| 2 | Relocate scraper control to Settings | YES | Full scraper card in Settings.tsx with guard |
| 3 | Rewrite Pipeline scraper card copy | YES | Verbatim copy applied, button removed |
| 4a | Cluster 966: article span, sources, claims | YES | 48 days, 19 articles/3 sources, 19 claims |
| 4b | Cluster 924: article span, sources, claims | YES | 5.1 days, 138 articles/18 sources, 138 claims |
| 4c | first_seen_at query | PARTIAL | Column absent in this DB version — UNKNOWN |
| 5a | 403 guard confirmed | YES | `curl POST → 403 {"detail":"read-only demo"}` |
| 5b | Font floor | YES | No sub-0.75rem introduced |
| 5c | Contrast floor | YES | New text uses existing tokens |
| 5d | Build passes | YES | `✓ built in 444ms` |
| 5e | Vitest baseline | YES | 12 failed (baseline), 0 new |
| 5f | Fingerprint 378/10/358/17/13653 | YES | Pasted |
| — | STATUS.md updated | YES | UX30 phase + UX28 P3 resolved |
