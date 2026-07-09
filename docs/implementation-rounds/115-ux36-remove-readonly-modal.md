# Round 115 — UX36: Remove .readonly guard + confirmation modals

**Date:** 2026-07-09
**Order:** UX36
**Status:** COMPLETE
**Branch:** main

FP START: 378/10/358/17/13653
FP END:   378/10/358/17/13653 (restored after accidental scraper start during curl verification)

## Task 1 — Remove .readonly guard

```
app/main.py:
  - Removed _is_readonly() function (lines 614-618)
  - Removed readonly check from scraper_status (line 610)
  - Removed guard from scraper_start (line 624)
  - Removed guard from scraper_stop (line 632)
  Endpoints now pass through directly to scheduler

Dockerfile.app:
  - Removed RUN touch /app/.readonly (line 61)

.gitignore / root:
  - rm -f .readonly — file absent from repo
```

Post-cleanup grep: ZERO hits for `readonly` / `.readonly` / `NN_READONLY` / `_is_readonly` in `app/`, `src/`, `Dockerfile.app`.

## Task 2 — Frontend: normal button

Settings.tsx:
- Removed `readonly?: boolean` from ScraperStatus interface
- Removed conditional `disabled` / `readonly` styling
- Button renders normally: "Start Scraper" (teal) or "Stop Scraper" (red)

PipelineFlow.tsx:
- Removed `readonly?: boolean` from ScraperStatusData interface

## Tasks 3-5 — Confirmation modals

Reused existing `Dialog` component from `@/components/ui/dialog` (Radix UI).

**Start modal:**
- Title: "Start live collection?"
- Body: "The scraper will begin polling RSS feeds from the 37 sources and ingesting new articles into this instance's database. New clusters, claims, and reputation snapshots will accumulate."
- Buttons: Cancel (secondary, closes) / Start (primary teal, fires POST /api/scraper/start)
- Props: `aria-modal="true"`, `role="dialog"` — inherited from Radix Dialog

**Stop modal:**
- Title: "Stop live collection?"
- Body: "Scraping will pause. Existing data remains — no articles or claims are removed. You can restart at any time."
- Buttons: Cancel (secondary) / Stop (primary red, fires POST /api/scraper/stop)

Implementation: `confirmAction` state = "start" | "stop" | null. Dialog opens when non-null, closes on Cancel/ESC/click-outside (Radix default).

## Curveballs

**Accidental DB mutation during curl verification:** `curl -X POST /api/scraper/start` against the running server (still old code, but .readonly was deleted) succeeded — scraper ingested 1,752 articles. DB went from 358 to 2,110 articles. Git checkout 5f18c3e restored golden fingerprint. Lesson: the guard removal worked too well — don't curl the running server until after restart.

## Task 6 — Vitest baseline

Fixed pipeline-flow test that broke in UX34: changed regex from `/polls RSS feeds, ingests/` to `/Scraper paused/` matching UX34's new copy. Also added `waitFor` for async render.

Returned to 12 failures (baseline):
```
FAIL  db/__tests__/schema.test.ts (1)      — pre-existing
FAIL  src/__tests__/router-shell.test.tsx (11)  — pre-existing
FAIL  src/__tests__/docker/compose.test.ts (1)  — pre-existing (intermittent)
```

## Verification

| Check | Result |
|-------|--------|
| Grep app/src/Dockerfile: readonly | ZERO hits |
| `.readonly` file | No such file or directory |
| curl POST /api/scraper/start | `{"status":"started"}` 200 |
| curl POST /api/scraper/stop | `{"status":"stopped"}` 200 |
| Build | `✓ built in 432ms` |
| Vitest | 12 failed (baseline), 119 passed, 4 skipped |
| FP | 378/10/358/17/13653 ✓ |

## Files Changed

```
app/main.py                  | -17 lines (guard removal)
Dockerfile.app               | -1 line (RUN touch .readonly)
.readonly                    | DELETED
src/pages/Settings.tsx       | rewritten (modal + button + interface)
src/pages/PipelineFlow.tsx   | -1 field (readonly removed from interface)
src/__tests__/pipeline-flow.test.tsx | test fix (copy match)
```

## Compliance Table

| # | Requirement | Met? | Evidence |
|---|-------------|------|----------|
| 1a | _is_readonly() removed | YES | app/main.py diff |
| 1b | Guard removed from start/stop/status | YES | Endpoints now pass through directly |
| 1c | Dockerfile.app clean | YES | RUN touch removed |
| 1d | .readonly deleted | YES | `ls -la .readonly` → No such file |
| 1e | Grep zero hits | YES | app/src/Dockerfile.app clean |
| 2a | Frontend readonly removed from interface | YES | Settings + PipelineFlow interfaces |
| 2b | Button normal appearance | YES | No disabled/readonly conditional |
| 3 | Start confirmation modal | YES | Dialog title/body/buttons per spec |
| 4 | Stop confirmation modal | YES | Dialog title/body/buttons per spec |
| 5 | Modal reusable + accessible | YES | Radix Dialog (aria-modal, focus trap, ESC) |
| 6a | Font floor ≥ 0.75rem | YES | Button 0.84rem, modal body 0.82rem |
| 6b | Contrast WCAG AA | YES | Existing token colors, white on teal/red |
| 7a | FP unchanged | YES | 378/10/358/17/13653 (restored) |
| 7b | Build passes | YES | `✓ built in 432ms` |
| 7c | Vitest baseline 12 | YES | 12 failed, 0 new |
| 7d | curl start 200 | YES | `{"status":"started"}` |
| 7e | curl stop 200 | YES | `{"status":"stopped"}` |
| 7f | .readonly absent | YES | Confirmed |
| — | STATUS.md updated | YES | UX36 phase line |
