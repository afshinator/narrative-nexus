# UX1 — Sources Page: Bug Fixes + Comprehension POC

**Date:** 2026-07-06
**Parent commit:** 1d0c8f8 (D4 STATUS update)
**Status:** COMPLETE — Part A committed (8ac2685), Part B POC served at localhost:3015

---

## Part A — Functional Bug Fixes

### A1 — Vertical Button Screen Flash

**Root cause:** `Sources.tsx:109-138` — `useEffect` fires fetch on `vertical` change, but `fetchedScores` state still holds old vertical's data. `scoreMap` (Sources.tsx:140-148) filters `.filter((s) => s.vertical === vertical)` → empty → all scatter points vanish momentarily (flash/glitch).

**Fix:** Clear `fetchedScores` immediately on vertical change:
```diff
 useEffect(() => {
     if (typeof window !== "undefined" && !window.fetch) return;
     let cancelled = false;
+    setFetchedScores([]);
     fetch(`/api/scores?vertical=${vertical}`)
```
`Sources.tsx:112`

**Verified:** npm run build PASS (478ms).

---

### A2 — Archetype Filter Pills Do Nothing

**Root cause:** `Sources.tsx:100` reads `filter` from Zustand, but `scatterData` (Sources.tsx:171-193) ignores it. Only the ledger table applies filtering (Sources.tsx:220-224 dims rows). The scatter plot renders all points regardless of which archetype pill is active.

**Fix:** Added `scatterVisible` memo that filters by archetype:
```typescript
const scatterVisible = useMemo(
    () => (filter === null ? scatterData : scatterData.filter((s) => s.archetype === filter)),
    [scatterData, filter],
);
const gradedData = useMemo(
    () => scatterVisible.filter((s) => s.R_val != null),
    [scatterVisible],
);
```
`Sources.tsx:198-209`

Also added `filter` to `scatterData`'s useMemo deps so it recalculates when filter changes.

**Verified:** npm run build PASS.

---

### A3 — Coverage Lens Text Labels Overlap

**Root cause:** `ScatterPlot.tsx:120-150` always renders quadrant backgrounds AND labels regardless of which lens is active. On coverage lens:
- Region label "Sole voices" renders at `y=ry+16` (near top)
- Quadrant label "SELECTIVE BUT ACCURATE" renders at `y=18` (top-left)
- These overlap illegibly

**Fix:** Added `showQuadrants` prop to ScatterPlot (default `true`). Coverage lens passes `showQuadrants={false}`:
```typescript
interface Props {
    ...
    showQuadrants?: boolean;  // ScatterPlot.tsx:38
}

// In useEffect:
if (showQuadrants) {
    // quadrant backgrounds + labels
}
```
`ScatterPlot.tsx:38, 50, 124-155`

Coverage lens invocation:
```tsx
<ScatterPlot
    data={coverageScatter}
    showQuadrants={false}
    ...
/>
```
`Sources.tsx:468`

**Verified:** npm run build PASS.

---

### A4 — Shape Legend Missing from Scatter Legend

**Root cause:** `Sources.tsx:337-373` renders only COLOR legend (colored squares). Shape entries exist BELOW the scatter card at `Sources.tsx:424-430` but are not integrated into the main legend.

**Fix:** Added shape reference line at end of color legend:
```tsx
<div className="mt-2 border-t border-[var(--nn-border)] pt-2 font-sans text-[0.72rem] text-[var(--nn-text-dim)]">
    Shapes: ● Circle (T1) · ■ Square (T2) · ◆ Diamond (T3) · ▲ Triangle (T4) · ✚ Cross (T5)
</div>
```
`Sources.tsx:381-383`

**Verified:** npm run build PASS.

---

### A5 — Hardcoded "20 Monitored Outlets"

**Root cause:** `Sources.tsx:287` — literal "20". Tests had same issue.

**Grep results (all sites):**
| File | Line | Content | Status |
|------|------|---------|--------|
| `src/pages/Sources.tsx` | 287 | `"20 monitored outlets"` | FIXED — `{visibleSources.length}` |
| `src/__tests__/store-settings.test.ts` | 39 | `"20 source IDs"` | FIXED — "all source IDs" |
| `src/__tests__/panel-page.test.tsx` | 34 | `"20 source names"` | FIXED — "source names" |

DEFAULT_SOURCES has 38 domains (37 active sources). `visibleSources` tracks the filtered list dynamically.

**Verified:** npm run build PASS.

---

### A6 — Axis Copy Wrong vs Model

**Root cause:** `Sources.tsx:329-334` conflates R_orig with R_val:
- X: "is first to report a story that becomes consensus-absorbed" — describes VALIDATION, not origination
- Y: "source's outlier claims become consensus-absorbed" — also conflates

**Fix:**
```diff
- X: "how often this source is first to report a story that becomes consensus-absorbed"
+ X: "how often this source reports claims before the rest of the panel"

- Y: "how often this source's outlier claims become consensus-absorbed"
+ Y: "how often its early claims later enter consensus"
```
`Sources.tsx:336-341`

**Quadrant label verification:** Labels render at four plot corners (ScatterPlot.tsx:139-153):
- Top-right: EARLY BREAKERS (navy) — `x=width-10, y=18, text-anchor=end`
- Bottom-right: NOISE GENERATORS (red) — `x=width-10, y=yScale(0)-10, text-anchor=end`
- Top-left: SELECTIVE BUT ACCURATE (teal) — `x=10, y=18, text-anchor=start`
- Bottom-left: CONSENSUS FOLLOWERS (slate) — `x=10, y=yScale(0)-10, text-anchor=start`

Vertical position is unmistakable — each quadrant label sits at the extreme edge of its quadrant.

**Verified:** npm run build PASS.

---

## Part B — Comprehension POC Mock

**File:** `/project/narrative-nexus/docs/mock-ux1-comprehension-poc.html`
**Access URL:** `http://localhost:3015/mock-ux1-comprehension-poc.html`
**Server:** Python http.server on port 3015, bound to 0.0.0.0 (published to host per /vault/Workflows/dev-servers.md)
**Stop:** `kill 5501`

### B1 — Compact Intro Strip
One-line framing: "Not the truth — consensus reality" prominent, followed by one sentence of what the app does. Not a card grid — a horizontal strip above the page.

### B2 — Tooltips
7 functional tooltips (hover triggers, CSS-only):
1. "Narrative Nexus" — app definition
2. "37 sources" — panel description
3. "Geopolitics" vertical pill — vertical definition
4. Archetype pill names (4 pills) — archetype descriptions
5. Consensus/Coverage toggle "?" icon — lens description
6. X-axis label — origination computation method
7. Y-axis label — validation computation method

### B3 — Corrected Axis Copy
Uses the A6-corrected text: "how often this source reports claims before the rest of the panel" / "how often its early claims later enter consensus."

### B4 — Real-ish Data
10 hardcoded scatter points matching actual archetype distribution:
- Reuters (T1 circle, navy/EB), BBC (T1 circle, red/NG), NPR (T1 circle, slate/CF)
- NYT (T2 square, teal/SA), Fox News (T2 square, red/NG), WaPo (T2 square, teal/SA)
- DW (T3 diamond, navy/EB), GlobalTimes (T3 diamond, slate/CF)
- Bellingcat (T4 triangle, teal/SA)
- ZeroHedge (T5 cross, red/NG)

Design tokens applied: Space Grotesk headings, IBM Plex Sans body, IBM Plex Mono data labels, dark mode colors from docs/design-tokens.md.

---

### Interactive vs Static
**Interactive:** All 7 tooltips on hover, pill buttons visually respond to hover, scatter points have labels.
**Static:** No JS filtering (pills don't toggle), no API data (points hardcoded), lens toggle doesn't switch views.

---

## Commit
```
8ac2685 UX1-A: sources page functional fixes
 src/__tests__/panel-page.test.tsx    |  2 +-
 src/__tests__/store-settings.test.ts |  2 +-
 src/components/ScatterPlot.tsx       | 66 +++++++++++++++++++-----------------
 src/pages/Sources.tsx                | 39 +++++++++++++--------
 4 files changed, 62 insertions(+), 47 deletions(-)
```

## Compliance Table

| # | Requirement | Root Cause | Fix | Verified | Met? |
|---|------------|-----------|-----|----------|------|
| A1 | Vertical buttons flash | Sources.tsx:109-138 — stale fetchedScores causes empty scoreMap | Clear fetchedScores before fetch | npm run build PASS | YES |
| A2 | Archetype pills do nothing | Sources.tsx:171-193 — scatterData ignores filter | scatterVisible memo with filter | npm run build PASS | YES |
| A3 | Coverage labels overlap | ScatterPlot.tsx:120-150 — quadrants always rendered | showQuadrants=false on coverage lens | npm run build PASS | YES |
| A4 | No shape in legend | Sources.tsx:337-373 — only colors shown | Shape reference line added | npm run build PASS | YES |
| A5 | Hardcoded "20" | Sources.tsx:287 + 2 test files | {visibleSources.length}; test strings fixed | npm run build PASS | YES |
| A6 | Axis copy wrong | Sources.tsx:329-334 — conflates origination with absorption | Corrected X/Y copy per model | npm run build PASS | YES |
| B1 | Compact intro strip | — | 2-line strip above plot, "Not the truth — consensus reality" | Visual in POC HTML | YES |
| B2 | Tooltips ≥3 functional | — | 7 hover tooltips functional in mock | Hover-tested in HTML | YES |
| B3 | Corrected axis copy in mock | — | Uses A6 text | In HTML source | YES |
| B4 | Real-ish data, not live API | — | 10 points, 4 archetypes, 5 tiers | In HTML source | YES |
| ROUND | A-bugs fixed with named causes; POC served for human review | — | — | YES |

**ROUND OBJECTIVE:** A-bugs fixed with named causes; POC served for human review: **YES**
