# UX55 — Footer stats not rendering + font floor violation + vitest baseline repair

**Date:** 2026-07-09
**FP:** 378/10/358/17/13653 (start and end)
**Status:** COMPLETE

## Summary

UX54 shipped a live footer stats line but in the human's browser NO stats rendered — only the tagline. The endpoint worked via curl, so the frontend fetch was failing and the graceful fallback was silently hiding it. Additionally the stats line was at 0.7rem (below the 0.75rem font floor) and 3 vitest failures from the UX54 PageShell change were left unfixed (15 total vs 12 baseline).

## Task 1 — Failing fetch diagnosis and fix

### Diagnosis

Root cause: the running uvicorn process (PID 15947, started Wed Jul 8 19:01:26) predated the UX54 commit that added the `/api/stats` endpoint to `app/main.py`. The `--reload` flag did not pick up the change. The SPA catch-all route `/{full_path:path}` matched `/api/stats` and returned `dist/index.html` with HTTP 200 and `content-type: text/html`. The frontend `fetch("/api/stats")` received HTML, `r.json()` threw, and the `.catch(() => setStats(null))` silently hid the failure.

Evidence — before fix (stale server):
```
$ curl -s -D - http://localhost:3015/api/stats | head -5
HTTP/1.1 200 OK
content-type: text/html; charset=utf-8
content-length: 717
<!doctype html>
```

Evidence — after fix (fresh restart):
```
$ curl -s http://localhost:3015/api/stats
{"articles":358,"sources":37,"claims":378,"clusters":17,"dateStart":"2026-03-03T22:44:57+00:00","dateEnd":"2026-07-03T17:52:54+00:00"}
```

### Fixes applied

1. **Killed stale uvicorn and restarted** — `kill 15947` then `uvicorn app.main:app --host 0.0.0.0 --port 3015 --reload`

2. **Added console.warn on fetch failure** (`src/components/PageShell.tsx:30-32`):
   ```tsx
   .catch((err: unknown) => {
       console.warn("Footer stats fetch failed — endpoint may be unreachable", err);
       setStats(null);
   });
   ```
   Prevents silent fallback from hiding broken endpoints in the future.

3. **Fixed vite proxy port mismatch** (`vite.config.ts:16`):
   ```
   -"/api": "http://localhost:8000"
   +"/api": "http://localhost:3015"
   ```
   STATUS.md dev server runs on 3015; proxy was pointing to 8000. Would fail in `npm run dev` mode.

## Task 2 — Font floor

### Before
Stats line at `text-[0.7rem]` (11.2px) — below the 0.75rem (12px) font floor per design law 2.

### After
Raised to `text-[0.75rem]` (12px) — meets floor exactly.

Tagline at `text-[1.1rem]` (17.6px) — already above floor, confirmed.

Evidence (built JS):
```
$ grep -o 'text-\[0\.75rem\].*articles' dist/assets/index-*.js | grep -o 'text-\[0\.[0-9]*rem\]'
text-[0.75rem]
```

## Task 3 — Vitest baseline repair

### Diagnosis

UX54 added `fetch("/api/stats")` to PageShell (line 27). The 3 scraper status indicator tests in `router-shell.test.tsx` stubbed global fetch with `vi.fn().mockResolvedValueOnce(...)` — a single-response mock. When PageShell called fetch a second time (for `/api/stats`), the mock returned `undefined`, causing `Cannot read properties of undefined (reading 'then')`. The React error boundary caught it, the scraper-status-dot element never rendered, and all 3 tests failed.

Evidence — before fix (partial):
```
× shows a teal dot when scraper is running  → Unable to find [data-testid="scraper-status-dot"]
× shows a slate dot when scraper is paused   → Cannot read properties of undefined (reading 'then')
× shows a dim dot when status fetch fails     → Cannot read properties of undefined (reading 'then')
```

### Fix

Replaced single-response mocks with a `mockFetch()` helper that routes by URL (`src/__tests__/router-shell.test.tsx:137-154`):

```tsx
function mockFetch(scraperResponse: object | Error) {
    const mock = vi.fn().mockImplementation((url: string) => {
        if (url === "/api/scraper/status") {
            if (scraperResponse instanceof Error) return Promise.reject(scraperResponse);
            return Promise.resolve({ ok: true, json: () => Promise.resolve(scraperResponse) });
        }
        // /api/stats — return valid stats to avoid PageShell crash
        return Promise.resolve({ ok: true, json: () => Promise.resolve({
            articles: 358, sources: 37, claims: 378, clusters: 17,
            dateStart: "2026-03-03", dateEnd: "2026-07-03",
        }) });
    });
    vi.stubGlobal("fetch", mock);
}
```

### Result

Full vitest run:
```
Test Files  3 failed | 15 passed | 1 skipped (19)
Tests  12 failed | 121 passed | 4 skipped (137)
```

12 failures = baseline (11 router-shell + 1 docker compose volume mount + 1 db/schema). 3 scraper tests pass.

## Task 4 — Verification

| Check | Result |
|-------|--------|
| FP start | 378/10/358/17/13653 |
| FP end | 378/10/358/17/13653 |
| `npm run build` | PASS (708 modules, 905ms) |
| `/api/stats` response | `{"articles":358,"sources":37,"claims":378,"clusters":17,"dateStart":"2026-03-03T22:44:57+00:00","dateEnd":"2026-07-03T17:52:54+00:00"}` |
| Footer rendered text | "358 articles · 37 sources · Mar 2026–Jul 2026" |
| Stats font size | 0.75rem (meets floor) |
| Tagline font size | 1.1rem (above floor) |
| console.warn in built JS | 1 occurrence of "Footer stats fetch failed" |
| Vite proxy target | localhost:3015 |
| Vitest failures | 12 (baseline) |

## Files modified

| File | Change |
|------|--------|
| `src/components/PageShell.tsx` | +console.warn on fetch failure; 0.7rem→0.75rem |
| `src/__tests__/router-shell.test.tsx` | mockFetch helper routing by URL for dual-endpoint mocking |
| `vite.config.ts` | proxy target 8000→3015 |
| `docs/STATUS.md` | UX55 phase line; violations #31 and #32 |

## Prior Violations logged

- **#31 — Shipped below font floor (design law 2):** UX54 shipped footer stats line at 0.7rem (11.2px), below the 0.75rem (12px) font floor. Fixed: raised to text-[0.75rem].
- **#32 — Shipped with untested test breakage (vitest baseline drift):** UX54 added fetch("/api/stats") to PageShell without updating the 3 scraper status indicator tests. Single-response fetch mock returned undefined for the second call, crashing PageShell. 3 new failures shipped unnoticed (15 total vs 12 baseline). Fixed: mockFetch helper routes by URL.

## Commit message

```
UX55: fix footer stats fetch (stale backend), font floor (0.7→0.75rem), vitest repair (15→12)

- Restarted uvicorn (predated UX54, /api/stats returned HTML via SPA catch-all)
- Added console.warn on fetch failure in PageShell (silent fallback proofing)
- Fixed vite proxy port 8000→3015 to match dev server
- Raised footer stats line from text-[0.7rem] to text-[0.75rem] (design law 2)
- Fixed 3 scraper status tests: mockFetch helper routes by URL to serve both
  /api/scraper/status and /api/stats (single-response mock → undefined crash)
- FP unchanged: 378/10/358/17/13653
```
