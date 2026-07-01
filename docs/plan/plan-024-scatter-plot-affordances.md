# Slice 024 — Sources Page Scatter Plot Affordances

## Problem

The "Reputation Map" scatter plot on the Sources page is the homepage's centerpiece. Three gaps make it indecipherable to a first-time visitor:

1. **No tooltip on hover** — hovering a marker dims other dots but shows no source name, scores, or archetype. The hover state connects to the Full Ledger table row below, which is non-obvious.
2. **No axis labels** — tick marks at bottom (0–100) and left (0–100) have no titles. User doesn't know what "R_orig" and "R_val" represent.
3. **No centralized legend** — quadrant labels exist (EARLY BREAKERS, etc.) at 11.5px, and ArchetypePills sit above the card, but there's no visual key tying colors/shapes to meaning directly on or near the plot.

## Design principles (from project + skills)

- **Progressive disclosure** (frontend-design): quadrant labels + legend teach first glance; tooltip reveals detailed data
- **Match existing visual vocabulary** (web-design-engineer): use `--nn-*` tokens, Space Grotesk headings, IBM Plex Mono for data, 14px card radius
- **No new dependencies** (ponytail): D3 is already loaded; React state already tracks `hoveredSource`; ArchetypePills already renders colored archetype names
- **Color carries meaning** (frontend-design): the legend must tie `--nn-navy` → EARLY BREAKER, `--nn-red` → NOISE GENERATOR, etc.

## Implementation

### 1. Tooltip on hover (`src/components/ScatterPlot.tsx` + `src/pages/Sources.tsx`)

**ScatterPlot changes:**
- Extend `onHover` to pass `(sourceId, mouseX, mouseY)` triples so the parent knows cursor position
- Extend mouseenter handler on D3 markers to include `d3.pointer(event)` for viewport-relative coords
- Add a new prop: `onHoverPosition: (id: string | null, x: number, y: number) => void`

**Sources.tsx changes:**
- Track `tooltipPos: {x: number, y: number} | null` in state
- Render a floating `<div>` tooltip when `hoveredSource` is set, absolutely positioned at mouse offset
- Tooltip content: source name (IBM Plex Sans, 600), R_orig + R_val values (IBM Plex Mono, tabular-nums), archetype badge

Tooltip styling per design tokens:
- `bg-[var(--nn-surface)]`, `border border-[var(--nn-border)]`, `rounded-[8px]`, `px-3 py-2`
- `pointer-events-none`, `z-50`
- Transition opacity 150ms for smooth appearance

### 2. Axis labels (`src/components/ScatterPlot.tsx`)

Add two D3 `<text>` elements to the SVG:

- **X-axis label:** centered below the `xAxis` group, text "Origination", fill `--nn-text-dim`, font-family Space Grotesk, 11px, weight 500
- **Y-axis label:** rotated 90°, positioned to the left of the `yAxis` group, text "Validation"

This matches the existing D3 text pattern already used for quadrant labels (lines 107–145 in ScatterPlot.tsx).

### 3. In-card legend (`src/pages/Sources.tsx`)

Add a compact legend row between the scatter plot title and the `<ScatterPlot>` component. Four colored squares/badges in a row:

```
▮ Early Breaker  ▮ Noise Generator  ▮ Selective but Accurate  ▮ Consensus Follower
```

Each square uses the archetype color (navy/red/teal/slate) with 10% opacity background + matching text. Font: IBM Plex Sans, 0.78rem, `var(--nn-text-dim)`.

This ties the ArchetypePills (above the card) to the scatter plot (inside the card) in a way that's visually obvious without being heavy.

## Files touched

| File | What changes |
|------|------------|
| `src/components/ScatterPlot.tsx` | New `onHoverPosition` prop, mouse-position in D3 events, axis label `<text>` elements |
| `src/pages/Sources.tsx` | Tooltip state + rendering, in-card legend row |
| `src/__tests__/sources.test.tsx` | Tooltip visibility test, legend rendering test |

## Test strategy

- Tooltip renders when `hoveredSource` is set, hides when null
- Legend renders all 4 archetype labels with correct color classes
- Axis labels exist in the SVG (could test via container query)
- No test changes for existing behavior (dim-mode, click-to-navigate)

## Verification checklist

- [ ] Hovering a scatter dot shows tooltip with source name + R_orig + R_val
- [ ] Tooltip follows mouse position, disappears on mouseout
- [ ] X axis shows "Origination" label below tick marks
- [ ] Y axis shows "Validation" label left of tick marks
- [ ] Legend row shows 4 archetypes with correct colors
- [ ] No visual regressions: quadrant labels, dim-mode, Full Ledger row highlight
- [ ] `npm run build` passes
- [ ] `vitest run` passes
- [ ] `biome check src/` clean
