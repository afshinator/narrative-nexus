# Plan — 009: Pipeline Flow Scraper Controls + Header Status Indicator

**Date:** 2026-06-26
**Status:** Plan
**Depends on:** Slice 8b (backend scraper/scheduler endpoints)
**Depended on by:** None

## Scope

Add scraper start/stop toggle to the Pipeline Flow page and a running/paused status indicator to the app header. Both consume existing backend endpoints from Slice 8b. Pure frontend wiring — zero backend changes.

## Assumptions validated

1. **`POST /api/scraper/start` exists** — `app/main.py:105`. Calls `request.app.state.scraper.start()`. Returns `{"status": "started"}`.
2. **`POST /api/scraper/stop` exists** — `app/main.py:111`. Calls `request.app.state.scraper.stop()`. Returns `{"status": "stopped"}`.
3. **`GET /api/scraper/status` exists** — `app/main.py:100`. Returns `request.app.state.scraper.status()` → `{"running": bool, "last_run": str|null, "articles_inserted": int}`.
4. **Scheduler state is accessible** — `ScraperScheduler.status()` is a pure dict, no side effects. `start()` and `stop()` are idempotent.
5. **No auth required** — API has CORS middleware for `localhost:5173`, no auth tokens. Direct `fetch` calls work.
6. **Vite proxy** — Vite dev server proxies `/api/*` to `localhost:8000`. Production serves from same origin. `fetch("/api/scraper/status")` works in both environments.

## Architecture decisions

1. **No new store state.** Local `useState` in PipelineFlow and AppNav. Scraper status is runtime state, not user preference — no reason to persist.
2. **No polling interval.** Fetch on mount + after toggle action. POST response updates state immediately. AppNav fetches once on mount — brief inconsistency after toggle is acceptable.
3. **Toggle button: single button.** "Start" when paused, "Stop" when running. Idempotent. Disable for 500ms after click to prevent double-taps.
4. **Toggle placement:** one card between legend and animated diagram on PipelineFlow page. Button + status line ("Running · 142 articles · last run 14:30").
5. **Status indicator: colored dot in AppNav.** 8px circle next to brand, `var(--nn-teal)` when running, `var(--nn-slate)` when paused. No dot when fetch fails (backend unreachable).
6. **POST error feedback:** inline text next to toggle button. Brief message ("Start failed — retrying…") that auto-clears after 3s. No toast library — `useState` + `setTimeout`.
7. **Independent state.** PipelineFlow and AppNav fetch independently. Brief inconsistency after toggle is acceptable — AppNav catches up on next mount.
8. **API base URL: `/api/scraper`.** Relative paths, no environment-specific config.

## Implementation order

1. Add scraper toggle + status display to `src/pages/PipelineFlow.tsx`
2. Add status indicator dot to `src/components/AppNav.tsx`
3. Write tests
4. Remove resolved items from `docs/deferred.md`

## Test strategy

- **Pipeline Flow toggle:** mock `global.fetch`, verify start button sends POST to `/api/scraper/start`, stop button sends POST to `/api/scraper/stop`, status display shows running/paused state and article count, error message appears on failed POST and clears after timeout
- **AppNav indicator:** mock `global.fetch`, verify dot renders with correct color for running vs paused state, verify dot is hidden when fetch fails
- **No backend tests** — endpoints already tested in `app/test_routes.py`

## Verification checklist

- [ ] `npm run build` passes
- [ ] `vitest run` passes (all existing + new tests)
- [ ] `biome check src/` — no new issues
- [ ] `pytest -m "not network"` passes (no backend changes, regression check)
- [ ] Visual check: toggle button on PipelineFlow page, status dot in header
- [ ] ponytail-review against diff
