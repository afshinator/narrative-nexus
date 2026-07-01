# Slice 024b — Sources Page Scatter Plot Affordances (revised)

Supersedes `plan-024-scatter-plot-affordances.md` (partially implemented, contains bugs).

## What was found during review

**Design critique** (critique + clarify skills): 4 issues
**Code review** (frontend-developer agent): 20 issues including 1 critical bug

## Priority items for this slice

| # | Source | What | Severity |
|---|--------|------|----------|
| 1 | Code review #9 | `useMemo` uses `visibleSources.map` (function ref) — source toggle broken | Critical — functional regression |
| 2 | Design #1 | Axis labels faint, inside chart noise — move outside, use `--nn-text` | High — UX |
| 3 | Design #2 | "Origination"/"Validation" unexplained jargon — need definition near chart | High — UX |
| 4 | Design #3 | Legend identifies colors but not archetype meaning — add one-line explanations | Medium — UX |
| 5 | Code review #2 | No accessibility on scatter markers (no aria, no keyboard) | High — a11y |

Items #1-4 directly address the three UX problems you reported. Item #5 is a high-severity a11y gap found during review.

## Implementation

### 1. Fix `useMemo` dependency bug (`src/pages/Sources.tsx:131,171`)

**Root cause:** Lines 131 and 171 use `visibleSources.map` in dependency arrays:
```tsx
[scoreMap, panelMedian, visibleSources.map]  // .map is a function, never changes
```
When the Panel page toggles sources, `visibleSources` returns a new array but the `useMemo` never recomputes because `.map` is a constant function reference.

**Fix:** Replace `visibleSources.map` with `visibleSources`:
```tsx
[scoreMap, panelMedian, visibleSources]
```

### 2. Redesign axis labels

**Current state:** HTML `<span>` elements inside chart container, `text-[var(--nn-text-dim)]` (#738567), competing with D3 visual noise.

**Fix:** Remove the `<span>` labels from the ScatterPlot component. Replace with a compact HTML legend row below the chart title (extends existing legend area) that reads:
```
X-axis: Origination (0–100) — how often this source is first to report a story that becomes consensus-absorbed
Y-axis: Validation (0–100) — how often this source's outlier claims become consensus-absorbed
```
Font: IBM Plex Sans, 0.78rem, `text-[var(--nn-text)]` (#d2e4c5) for high contrast.

This kills three birds — fixes placement (outside chart), fixes contrast, and fixes jargon.

### 3. Add archetype explanations to legend

**Current state:** Legend row shows 4 colored squares + names but no meaning.

**Add:** Per-archetype one-liner:
```
▮ Early Breaker — high origination + high validation (consistently breaks stories that become consensus-absorbed)
▮ Noise Generator — high origination, low validation (frequently first, rarely becomes consensus-absorbed)
▮ Selective but Accurate — low origination, high validation (late to stories but reliable)
▮ Consensus Follower — low origination, low validation (safe but uninformative)
```
Font: IBM Plex Sans, 0.75rem. Placed below the existing legend row or on a second line. Colors for archetype names use `--nn-navy`, `--nn-red`, `--nn-teal`, `--nn-slate` respectively.

### 4. Tooltip tweaks

Keep the tooltip as-is (name + "Origination N · Validation N") but ensure it references the same terminology as the legend.

### 5. Accessibility on scatter markers

Add `role="button"`, `tabIndex={0}`, `aria-label={`${d.name}, Origination ${Math.round(d.R_orig)}, Validation ${Math.round(d.R_val)}`}` to D3 markers. Add `keydown` handler for Enter/Space.

This is a one-line change in the D3 `.on()` chain.

## Files touched

| File | Changes |
|------|---------|
| `src/pages/Sources.tsx` | Fix `useMemo` deps, redesign legend/axis labels area, tooltip tweaks |
| `src/components/ScatterPlot.tsx` | Remove HTML axis labels, add aria attrs + keyboard to markers |
| `src/__tests__/sources-page.test.tsx` | Update axis label test (labels move to card content), add a11y test |

## Verification checklist

- [ ] X-axis label reads "Origination (0–100) — how often..."
- [ ] Y-axis label reads "Validation (0–100) — how often..."
- [ ] Both labels use `--nn-text` (not `--nn-text-dim`)
- [ ] Archetype legend includes one-line explanations
- [ ] Source toggle from Panel page updates scatter plot (critical bug fix)
- [ ] Scatter markers have `role="button"`, `tabIndex`, `aria-label`
- [ ] `npm run build` + `vitest run` + `biome check src/` pass
