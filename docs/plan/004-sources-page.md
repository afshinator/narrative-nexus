# Plan: Slice 4 — Sources Page (Landing)

## Requirements addressed

| Req | Description | How |
|-----|-------------|-----|
| REQ-064 | Sticky nav bar with Sources link | Already exists (AppNav, index route) |
| REQ-065 | Sources page as landing page | Replace `src/pages/Sources.tsx` stub |
| REQ-085 | Scatter plot with archetype filter pills and sortable columns leaderboard | SourcesPage component — D3 scatter + HTML table + ArchetypePills |
| REQ-083 | Monospace font for all data values, labels, and codes | `font-mono` / `tabular-nums` on all data values |
| REQ-073 | CSS custom properties per design-tokens.md | Use existing `--nn-*` tokens (no new colors) |
| REQ-004 | Footer tagline on every page | Already on PageShell (inherited) |

Implicit from design-v1.2.md §6 (Sources page description):
- Cross-linked hover between table rows and scatter markers
- Shapes encode outlet format (tier → shape mapping in `shapes.ts`)
- Color encodes behavior archetype (navy/red/teal/slate per CONTEXT.md)

Implicit from design-v1.2.md §11 (success criteria):
- Four labeled quadrants on scatter (Early Breaker, Noise Generator, Selective but Accurate, Consensus Follower)

## Dependencies

| Dep | Version | Where | Verified? |
|-----|---------|-------|-----------|
| d3 | ^7.9.0 | `package.json` | Yes — `d3.select`, `d3.scaleLinear`, `d3.symbolCircle`, `d3.svgSymbol` all verified working via Node |
| react | ^19.2.7 | `package.json` | Yes — in use everywhere |
| zustand | ^5.0.14 | `package.json` | Yes — store already has `archetypeFilter` + `setArchetypeFilter` |
| lucide-react | ^1.21.0 | `package.json` | Yes — may use for sort direction arrows |

## Key assumptions (verified against codebase)

1. **Store has `archetypeFilter`** — confirmed in `src/store.ts` line 18. Type: `Archetype | null`. Setter: `setArchetypeFilter`. Will use this for filter pill state (persisted via zustand-persist).

2. **`shapes.ts` exists** — confirmed: `TIER_SHAPE` maps tier (1–5) to D3 symbol names (circle, square, diamond, triangle, cross). `getShapeForTier(tier)` exports a helper. Design doc says "shapes encode outlet format" — tiers are the outlet format grouping. No new shape coding needed.

3. **`archetype.ts` works** — confirmed: `getArchetype(rOrig, rVal, medOrig, medVal)` returns the correct `Archetype` string union. Will use this for badge display and scatter marker coloring.

4. **`polarity.ts` works** — confirmed: `getPolarityColor(dimension, percentile)` returns `--nn-teal` (≥66), `--nn-amber` (≥33), `--nn-red` (<33), or `--nn-slate` (trait dimensions). Ready for table value coloring.

5. **CSS tokens exist** — confirmed: all `--nn-navy`, `--nn-red`, `--nn-teal`, `--nn-slate`, `--nn-amber` defined in `src/index.css` for both light and dark modes. No new tokens needed.

6. **Card layout pattern** — confirmed from `Panel.tsx`: `rounded-[14px] border border-[var(--nn-border)] bg-[var(--nn-surface)] p-6`. Follow this pattern for the scatter card and leaderboard card.

7. **D3 available at runtime** — confirmed: `require('d3')` resolves, exports `select`, `scaleLinear`, `symbolCircle`, `svgSymbol`. No additional D3 sub-packages needed; the umbrella `d3` package bundles everything.

8. **`DEFAULT_SOURCES` has 20 entries with tier and region** — confirmed: 5 per tier (1–2), 5/3/3 for tiers 3/4/5. Source metadata (name, domain, tier) already available for table rows.

## Architecture decisions

### Decision 1: D3 over Chart.js for scatter plot

D3 chosen because:
- Per-point custom shapes (circle/square/diamond/triangle/cross) are native in D3 via `d3.symbol()` — Chart.js bubble chart only renders circles natively and needs custom `afterDraw` plugin to override
- Four quadrant overlays (`<rect>` elements) are trivial in D3 SVG — Chart.js needs a custom plugin
- Cross-linked hover is natural via DOM event listeners on individual SVG elements — Chart.js hover requires `chart.draw()` calls which risk flicker
- All other visualization pages (Timeline, Source Profile radar, Pipeline Flow) will use D3 — one rendering approach across the app
- `shapes.ts` already references D3 symbol type names

### Decision 2: Empty data state, one code path

There is no placeholder data module. The page starts with an empty array. The chart infrastructure (axes, quadrants, labels, median lines) always renders. The table headers always render. Data points populate when the database has data.

This is the same code path in all states:

| State | What renders | Data source |
|-------|-------------|-------------|
| Dev (no backend) | Axes, quadrants, labels, filter pills, table headers. Zero markers, zero rows. | Empty array — `const scores: ReputationScore[] = []` with comment explaining replacement when backend exists |
| Post-seed (demo) | Same infrastructure + 20 markers + populated table rows | Same query path, different result — DB has data from `scripts/seed-demo.py` (ADR-0002) |
| Live | Same | Same query path — DB has data from live scheduler |

When the backend exists, the empty array becomes a query (store/API/swr). The infrastructure code does not change. The rendering functions are already written to handle both empty and populated arrays — a scatter with zero markers renders quadrants and axes, a table with zero rows renders headers and an empty body.

**Why no placeholder scores module:**
- Placeholder values are indistinguishable from real pipeline output — the user can't tell the difference
- The project's "one code path, no demo mode" rule (ADR-0002) forbids conditional data sources
- `DEFAULT_THRESHOLDS` and `DEFAULT_SOURCES` are user-configurable settings and source metadata — not pipeline output. Scores are computed data, not configuration.

### Decision 3: Tier → shape encoding (not adding a format field)

The design doc says "shapes encode outlet format." The five tiers already group sources by outlet role:
- Tier 1 = Wire / Consensus Anchor (Reuters, AP, BBC, NPR, Guardian)
- Tier 2 = Mainstream Editorial (Fox News, Politico, Economist, NYT, WaPo)
- Tier 3 = International (Al Jazeera, DW, NHK, Global Times, France24)
- Tier 4 = Independent / Investigative (Intercept, ProPublica, Bellingcat)
- Tier 5 = Contrarian (ZeroHedge, Gray Zone)

Adding a `format` field to `Source` would create a secondary classification that parallels tier for all 20 sources. It adds a dimension to the data model without adding analytical value. If format classification becomes meaningful later, it can be added as a field on Source and `shapes.ts` can map from `source.format` instead of `source.tier` — a one-line change in the renderer.

### Decision 4: Store's `archetypeFilter` for filter state

The store already has `archetypeFilter: Archetype` and `setArchetypeFilter`. Using it means:
- Filter state persists across page visits (by nature of zustand-persist)
- No new store slice needed
- Other pages can read the filter if needed (e.g., Source Profile can show relevant context)

Local UI state (hovered source ID, sort key, sort direction) stays in the page component — it's transient view state, not application state.

### Decision 5: Vertical hardcoded to GEOPOLITICS for now

The subhead displays "GEOPOLITICS vertical." The store had a `vertical` filter that was deleted in M1 (YAGNI — no page used it). Multi-vertical filtering will be re-introduced when a vertical selector component exists, which is outside this slice's scope. The `ReputationScore` type includes a `vertical` field so the data model is ready for multi-vertical when needed.

### Decision 6: Table dim-mode matches scatter dim-mode

Per CONTEXT.md, the scatter uses dim-mode filtering (non-selected markers at ~0.15 opacity). The table follows the same rule — filtered-out rows remain in the DOM at opacity 0.15. This preserves cross-linked hover when a non-matching scatter marker is hovered (the corresponding table row is still present).

## Data model

### ReputationScore type

Defined inline in `SourcesPage.tsx` for now — extracted to a shared location when the backend exists and multiple pages consume it.

```ts
interface ReputationScore {
  sourceId: string;     // matches Source.id in DEFAULT_SOURCES
  vertical: string;       // e.g. "geopolitics"
  R_orig: number;       // 0–100, trait (no favorable direction)
  R_val: number;        // 0–100, graded (high = favorable)
  R_speed: number;      // days, graded (low = favorable)
  R_frame: number;      // stddev, graded (low = favorable)
  R_edit: number;       // count, graded (low = favorable)
  R_correct: number;    // count, trait (no favorable direction)
}
```

### Data flow

```
SourcesPage
├── const scores: ReputationScore[] = []
│   // Empty — replaced by store/API query when backend exists.
│   // Scatter and table rendering handle both empty and populated arrays.
├── Source metadata from DEFAULT_SOURCES (name, domain, tier)
│   // Always available — used for table rows regardless of score data
├── reads store.archetypeFilter (persisted)
├── filters: filterKey !== null ? scores.filter(...) : scores
├── computes archetype per source via getArchetype(rOrig, rVal, medOrig, medVal)
│   // Skipped when scores array is empty
├── renders ArchetypePills → onClick dispatches setArchetypeFilter
├── renders ScatterPlot → D3 SVG with:
│   ├── 4 quadrant rects (9% opacity archetype colors) — always rendered
│   ├── 4 quadrant labels — always rendered
│   ├── median dashed lines (X and Y) — rendered when scores.length > 0
│   ├── D3 axes (Origination Rate →, Validation Rate →) — always rendered
│   ├── per-source shape markers — rendered only when scores.length > 0
│   └── hover → setHoveredSource
└── renders leaderboard table → HTML:
    ├── sortable column headers — always rendered
    ├── per-row: source name + domain from DEFAULT_SOURCES, score columns from scores
    │   └── empty "—" for score columns when no matching score exists
    └── hover → setHoveredSource (cross-links to scatter)
```

## Files to create

| File | Content |
|------|---------|
| `src/components/ArchetypePills.tsx` | 5 filter pills (All + 4 archetypes) using store's `archetypeFilter` |
| `src/components/ScatterPlot.tsx` | D3 scatter plot SVG: quadrants, axes, shape markers, median lines, hover/click callbacks. Renders chart infrastructure even with empty data array. |

## Files to modify

| File | Change |
|------|--------|
| `src/pages/Sources.tsx` | Replace stub with full page: ReputationScore type, imports ArchetypePills + ScatterPlot, leaderboard table. Empty scores array with comment explaining replacement path. |

## Component architecture

### `ArchetypePills`

```
ArchetypePills({ onFilterChange?: (archetype: Archetype | null) => void })
├── reads store.archetypeFilter
├── 5 pill buttons: "All" + 4 archetypes
├── active state: colored border + background (archetype color at 10% opacity)
├── inactive state: border-neutral, text-dimmed
└── onClick → store.setArchetypeFilter (and call onFilterChange prop if provided)
```

Pattern matches Settings page pill presets (border, active highlight, monospace labels). Archetype colors follow CONTEXT.md badge colors.

### `ScatterPlot`

```
ScatterPlot({
  data: EnrichedSource[],
  hoveredId: string | null,
  onHover: (id: string | null) => void,
  onSelect: (id: string) => void
})
├── D3 `useRef` + `useEffect` pattern (SVG rendered imperatively into DOM node)
├── React-managed: data, hoveredId, callback props
├── D3-managed: scales, axes, quadrant rects, markers, labels, median lines
├── D3 updates: only re-render when data, dimensions, or hoveredId changes
├── Empty state: renders axes, quadrants, labels — no markers or median lines
├── Populated state: adds shape markers + median lines
├── Shapes: `getShapeForTier(source.tier)` returns D3 symbol type → `d3.symbol().size(...)`
├── Colors: archetype → CSS custom property via `getComputedStyle` / `getCssVar`
├── Hover: `mouseenter`/`mouseleave` on each shape `<path>` calls `onHover`
├── Click: shape `<path>` click calls `onSelect` (for navigation to Source Profile)
└── Responsive: `viewBox` on SVG, `ResizeObserver` on container div for resize handling
```

**Important implementation note:** D3 in React requires the imperative DOM approach — an empty `<svg ref={svgRef}>` that D3 populates in `useEffect`. React does NOT manage the individual SVG elements inside the scatter. The dependencies array controls re-renders: `[data, hoveredId]` plus a resize signal. The quadrant rects, axes, and labels render once and persist regardless of data. Markers and median lines update when data changes.

### Leaderboard table (in SourcesPage, not a separate component)

The table is purely HTML — no D3. It's built with standard React JSX in `SourcesPage` for simplicity (the Panel page uses the same pattern). Columns:

| Column | Content | Sortable? |
|--------|---------|-----------|
| Source | Name + domain, shape glyph (SVG) — from `DEFAULT_SOURCES` | Yes (by name) |
| Verdict | Archetype badge pill — computed when scores exist, otherwise empty | Yes (by archetype group) |
| R_orig | Meter bar + median marker + value — from scores, otherwise "—" | Yes (numeric) |
| R_val | Meter bar + median marker + value — from scores, otherwise "—" | Yes (numeric) |
| R_speed | Value with unit (e.g., `3.2d`) or "—" | Yes |
| R_frame | Value with unit (e.g., `σ 0.14`) or "—" | Yes |
| R_edit | Count, colored: teal (≤2), amber (≤8), red (>8) — or "—" | Yes |
| R_correct | Count, neutral — trait dimension — or "—" | Yes |

**Source metadata (name, domain, tier) always comes from `DEFAULT_SOURCES`** regardless of whether scores exist. The table shows all 20 source rows with score columns filled or showing "—" based on whether a matching `ReputationScore` exists for that sourceId.

Hover behavior:
- `onMouseEnter` row → `setHoveredSource(sourceId)` (passed to ScatterPlot as `hoveredId`)
- `onMouseLeave` row → `setHoveredSource(null)`
- `onClick` row (or specific source name cell) → navigate to `/source/{domain}`

**Dim-mode on filtered rows:** When an archetype filter is active, non-matching rows get opacity 0.15 (`className="opacity-15"`). All 20 rows remain in the DOM so cross-linked hover always works — hovering a dimmed scatter marker finds its matching table row.

**Empty state:** When `scores.length === 0`, all score columns show "—". The table still renders 20 rows with source names and domains. The scatter renders quadrants, axes, and labels without markers.

## Verification

1. `npm run build` exits 0
2. `npm run test` — all existing 77 tests pass + new Sources page tests
3. `npm run lint` — no new oxlint errors
4. **Scatter plot renders with empty data** — SVG present with quadrant rects, axes, quadrant labels. No markers, no median lines. No errors in console.
5. **Leaderboard renders with empty data** — 20 rows with source name + domain + shape glyph. Score columns show "—". Sortable headers.
6. **Archetype filter pills render** — 5 pills present, "All" active by default, clicking toggles active state
7. **Scatter plot renders with populated data** — same SVG, adds shape markers at correct positions, median lines appear
8. **Leaderboard renders with populated data** — score columns fill with values, meter bars render, archetype badges appear
9. **Dim-mode filtering** — non-matching scatter markers and table rows reduce to opacity 0.15 (per CONTEXT.md)
10. **Cross-linked hover** — hovering table row highlights matching scatter marker (ring); hovering scatter marker highlights table row (`.linked` class)
11. **Archetype badges** — correct colors per CONTEXT.md (navy for Early Breaker, red for Noise Generator, teal for Selective but Accurate, slate for Consensus Follower)
12. **Shapes by tier** — Tier 1 = circle, Tier 2 = square, Tier 3 = diamond, Tier 4 = triangle, Tier 5 = cross
13. **6 dimension columns** — all six R_* columns present, correct polarity coloring where applicable
14. **No new colors** — all styling uses existing `--nn-*` CSS custom properties
15. **Monospace data** — all values use `font-mono` with `tabular-nums`
16. **Responsive** — scatter SVG scales to container width; table scrolls horizontally on narrow viewports
17. **Footer tagline** — present via PageShell (not duplicated in SourcesPage)
18. **No placeholder data module** — `src/data/scores.ts` does not exist. No false scores in the codebase.
