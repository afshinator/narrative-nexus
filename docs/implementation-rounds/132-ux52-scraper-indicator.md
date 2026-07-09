# Round 132 — UX52: Nav scraper indicator — verify real, then polish

**Date:** 2026-07-09
**Order:** UX52
**Status:** COMPLETE
**Branch:** main

## Task 1 — Verify indicator is hooked up

### Code chain

```
Frontend: AppNav.tsx:23-31
  └─ useEffect([], fetch GET /api/scraper/status)
     └─ sets scraperRunning ∈ {null | true | false} from {running: bool}

Backend:  main.py:637-639
  └─ GET /api/scraper/status → request.app.state.scraper.status()

Scheduler: pipeline/scheduler.py:49-54
  └─ status() → {"running": self._running, ...}
     └─ _running is True when scraper loop is active, False when paused
```

### curl verification

```
$ curl -s http://localhost:3015/api/scraper/status
{"running":false,"last_run":null,"articles_inserted":0}
```

Scraper is paused — matches default startup state (`main.py:55` — "paused on startup").

### Verdict: STALE → now LIVE

**Was STALE** — frontend fetched ONCE at mount (empty `[]` dependency). If the user started/stopped the scraper in Settings, the nav indicator wouldn't update until page reload.

**Now LIVE** — added 30-second polling interval. Indicator tracks real scraper state with at most 30s lag. Cancellation guard prevents state updates after unmount.

## Task 2 — Polish

### Changes

**AppNav.tsx:**
- Replaced mount-only fetch with polling loop at 30s intervals
- Cancellation guard (`cancelled` flag in cleanup) prevents stale updates
- Replaced `animate-pulse` (Tailwind built-in, 1s fast blink) with custom `nn-scraper-breathe` (2.4s gentle opacity pulse, 1.0→0.45→1.0)
- Replaced generic "Scraper" label with context-sensitive text:
  - `null` → "Disconnected" (dim, no dot animation)
  - `false` → "Paused" (slate dot, static)
  - `true` → "Scraping" (teal dot, breathing animation)
- Added `transition-colors duration-200` on border/text for smooth state transitions
- Added `transition-[background-color] duration-200` on dot for smooth color changes
- Changed font from `font-mono` to `font-sans` for readability

**index.css:**
- New `@keyframes nn-scraper-breathe` animation (2.4s ease-in-out opacity cycle)
- `.nn-scraper-breathe` class applies it
- `prefers-reduced-motion` disables animation (`animation: none` on `.nn-scraper-breathe`)
- WCAG AA contrast maintained (teal `#5ebd8e` and slate `#90a882` on `--nn-nav-bg`)

### State descriptions

| State | Dot color | Animation | Label | Border |
|-------|-----------|-----------|-------|--------|
| Disconnected (null) | dim | none | "Disconnected" | default |
| Paused (false) | slate | none | "Paused" | slate/30 |
| Running (true) | teal | breathing | "Scraping" | teal/30 |

### Debug hardcode revert

```diff
-	const [scraperRunning, setScraperRunning] = useState<boolean | null>(true); // DEBUG
-	// useEffect(() => { ... }, []);  // commented out
+	const [scraperRunning, setScraperRunning] = useState<boolean | null>(null);
+	useEffect(() => { ... }, []);  // live code
```

Reverted. No debug state shipped.

## Task 3 — Verify

### Fingerprint

```
claims: 378 | absorbed: 10 | articles: 358 | clusters: 17 | snapshots: 13653
```
✓ Clean. No POST to /api/scraper/start or /stop issued.

### Build

✓ 490ms

### Vitest

```
Tests  12 failed | 121 passed | 4 skipped (137)
```
✓ Baseline 12, no new failures.

## Files Changed

```
src/components/AppNav.tsx | polling + animated indicator + state labels
src/index.css             | nn-scraper-breathe keyframes + reduced-motion disable
```
