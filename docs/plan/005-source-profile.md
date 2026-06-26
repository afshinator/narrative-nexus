# Plan: Slice 5 — Source Profile Page

## Requirements addressed

| Req | Description | How |
|-----|-------------|-----|
| REQ-086 | Source Profile page: radar chart (6 axes), archetype badge, 30-day sparklines | `SourceProfilePage.tsx` — Chart.js radar + inline SVG sparklines + archetype badge |
| REQ-066 | Nav links to Source Profile at `/source/:domain` | Already routed (App.tsx), stub replaced |
| REQ-004 | Footer tagline on every page | Already on PageShell (inherited) |
| REQ-082 | Polarity binding: color per dimension via `getPolarityColor` | Stat rows use `getPolarityColor()` for value coloring |
| REQ-083 | Monospace font for data values, labels, codes | IBM Plex Mono on all data: sparkline labels, stat values, day counter, event markers |
| REQ-038 | Trait dimensions R_orig + R_correct neutral color | `--nn-slate` on stat rows; CONTEXT.md neutral color on radar axes |

Implicit from design-v1.2.md §6 (Source Profile page description):
- Radar chart: 6 axes, percentile-oriented (outward = favorable), scaled 0–100
- Radar polarity inversion: R_speed, R_frame, R_edit inverted (100 − percentile per CONTEXT.md)
- Archetype badge with semantic color from CONTEXT.md
- 30-day sparklines — one per dimension showing trajectory
- Day 0–90 scrubber: slider + play/pause + timeline markers + event card
- Stat panel: 6 dimensions with current percentile, delta from day-0 baseline, color per polarity

Decisions from mock review session:
- **Vertical picker:** Pills (GEOPOLITICS / ECONOMICS / TECHNOLOGY), component-local state
- **Data display:** Stat panel (deltas) + 30-day sparkline grid — both
- **Extras deferred:** Vf trend, outlier waterfall, silent edit log → future slices

## Dependencies

| Dep | Version | Where | Verified? |
|-----|---------|-------|-----------|
| chart.js | ^4.5.1 | `package.json` | Yes — `type: 'radar'` confirmed via Context7 docs, supports 6+ labels, multiple datasets, fill, pointRadius |
| react-chartjs-2 | ^5.3.1 | `package.json` | Yes — React wrapper for Chart.js 4 |
| react-router | ^7.18.0 | `package.json` | Yes — `useParams()` for `:domain` route param |
| zustand | ^5.0.14 | `package.json` | Yes — store used for active sources lookup |
| lucide-react | ^1.21.0 | `package.json` | Yes — Play, Pause, SkipBack, SkipForward icons |
| shadcn | ^4.11.0 | `package.json` | Yes — Card, Badge pattern for layout |

## Key assumptions (verified against codebase)

1. **Chart.js radar handles 6 axes** — confirmed: Context7 docs show `labels: ['Eating', 'Drinking', 'Sleeping', 'Designing', 'Coding', 'Cycling', 'Running']` (7 labels) with multiple datasets. The `type: 'radar'` chart type supports arbitrary label counts.

2. **`react-chartjs-2` exports `<Radar>` component** — confirmed: `import { Radar } from 'react-chartjs-2'` for React wrapper.

3. **`DEFAULT_SOURCES` has domain field** — confirmed: `Source.domain` is a string like `"reuters.com"`. The route param is `:domain`. Source lookup is a one-liner inlined in the component: `DEFAULT_SOURCES.find(s => s.domain === domain)`. No separate export needed for a single call site.

4. **`getArchetype()` exists** — confirmed in `src/utils/archetype.ts`. Takes `(rOrig, rVal, medianOrig, medianVal)`. On Source Profile we provide single-source R_orig/R_val vs panel median (computed from available data or fallback to fixed values like the mock).

5. **`getPolarityColor()` exists** — confirmed in `src/utils/polarity.ts`. Returns CSS variable string for stat row coloring. Trait dims (R_orig, R_correct) return `var(--nn-slate)`.

6. **`VerticalThresholdKey` type exists** — confirmed in `src/data/thresholds.ts`: `"geopolitics" | "economics" | "technology"`. Reused for vertical picker labels.

7. **Card layout pattern** — confirmed from `Panel.tsx` and `Sources.tsx`: `rounded-[14px] border border-[var(--nn-border)] bg-[var(--nn-surface)] p-6`. Consistent across the app.

8. **CSS tokens exist** — all `--nn-navy`, `--nn-red`, `--nn-teal`, `--nn-slate`, `--nn-amber`, `--nn-text`, `--nn-text-dim`, `--nn-border`, `--nn-surface`, `--nn-surface2` defined. No new tokens needed.

## Architecture decisions

### Decision 1: Chart.js over D3 for radar chart

Chart.js chosen because:

- **Built-in radar type** — `type: 'radar'` handles circular axis layout, concentric grid rings, axis labels at correct angles, multiple polygon datasets with fill. D3 would require drawing all of this from scratch (~150 lines of SVG math).
- **Already installed** — Chart.js 4.5.1 and react-chartjs-2 5.3.1 are in `package.json`. The README specifically says "Chart.js 4 (radar)".
- **Multiple dataset support** — Three datasets (current day, day-0 baseline, tier average) with independent colors, fills, and line styles. Native to Chart.js radar.
- **Morphing = re-render** — Scrubbing the day slider changes the chart `data` prop, causing react-chartjs-2 to re-render. Smooth 150ms transition built into Chart.js.
- **Consistency note:** D3 was chosen for scatter in Slice 4 because scatter needs per-point custom shapes and quadrant overlays. Radar has neither — it's a fixed-axis polygon chart, which is exactly Chart.js's domain.

### Decision 2: Inline SVG over D3 for sparklines

Inline SVGs chosen because:

- **Minimalism** — 6 sparklines, each is an `<svg viewBox="0 0 30 20"><polyline points="..." /></svg>`. No D3 select/scale/axis machinery needed for a 30×20 mini-chart.
- **Data path is just a string** — `points` prop computed once from the data array. No runtime DOM manipulation.
- **Grid layout** — 2×3 or 3×2 CSS grid, each cell contains one sparkline SVG. Container always renders; polyline empty (no `points` attribute) when data is empty.

### Decision 3: Component-local vertical state, not store

The vertical picker (GEOPOLITICS / ECONOMICS / TECHNOLOGY pills) uses component-local state (`useState<VerticalThresholdKey>`). This is different from the Sources page archetype filter, which uses the store.

Reasoning:
- The vertical selection is **page-local context**, not a cross-page preference. No other page needs to know "the user was looking at ECONOMICS on the Source Profile."
- Changing the page (navigating to another source) resets the vertical — this is correct UX.
- If we later add deep-linking (`/source/:domain/:vertical`), the route param can seed the initial state.

**Data filtering:** When the vertical changes, all computed data (radar datasets, stat row values, sparkline points) filter to `snapshots.filter(s => s.vertical === selectedVertical)`. Use `useMemo` keyed on both `[snapshots, selectedVertical, currentDay]` to avoid re-filtering on every scrub tick — the filtered array is stable across day changes within the same vertical.

### Decision 4: Empty data state — one code path

Same principle as Sources page (slice 4 plan, decision 2). No placeholder data module. The page infrastructure always renders. Data populates when the backend produces it.

| State | What renders | Data source |
|-------|-------------|-------------|
| Dev (no backend) | Radar axes/rings/labels, stat row labels, archetype badge (unclassified/null), sparkline grid containers, day scrubber controls, event card placeholder. No data points — radar shows empty scale, stat rows show "—" per ADR-0002. | Empty daily snapshots array |
| Post-seed (demo) | Same infrastructure + radar polygons + stat values + sparkline data + event markers | Same query path, DB has data from `scripts/seed-demo.py` (ADR-0002) |
| Live | Same | Same query path, DB has data from live scheduler |

When the backend exists, the empty array becomes a store/API query. Infrastructure code does not change.

## Data model

### DailySnapshot (new type)

```ts
// Each row = one source × one vertical × one day
interface DailySnapshot {
  sourceId: string;
  vertical: string;
  day: number;          // 0–90
  R_orig: number;       // 0–100 percentile
  R_val: number;
  R_speed: number;
  R_frame: number;
  R_edit: number;
  R_correct: number;
}
```

### ProfileEvent (new type)

```ts
// Timeline event marker on the day scrubber
interface ProfileEvent {
  day: number;
  type: "CLAIM_ABSORBED" | "SILENT_EDIT" | "CLAIM_UNRESOLVED";
  title: string;
  detail: string;
}
```

### Props

```ts
interface Props {
  snapshots?: DailySnapshot[];  // All days for this source, filtered to selected vertical
  events?: ProfileEvent[];
  tierAvg?: number[];          // 6-element array, tier average per dimension
  panelMedian?: { orig: number; val: number };  // Cross-source panel median for archetype — defaults to {orig: 50, val: 50} when not provided
}
```

## Route extraction

```ts
// In SourceProfilePage
const MOBILE_BREAKPOINT = 900; // single-column below this width

const { domain } = useParams();
const source = useMemo(() => DEFAULT_SOURCES.find(s => s.domain === domain), [domain]);

// ponytail: vertical defaults to geopolitics. When multi-vertical Sources page exists,
// add an optional :vertical? route segment and initialize from it:
//   const [vertical, setVertical] = useState<VerticalThresholdKey>(
//     (urlVertical as VerticalThresholdKey) || 'geopolitics'
//   );
const [vertical, setVertical] = useState<VerticalThresholdKey>('geopolitics');
```

If `source` is undefined (bad URL), show a "Source not found" state with a link back to Sources.

## Page layout

```
┌────────────────────────────────────────────────────┐
│ PageShell (AppNav + footer — inherited)            │
├────────────────────────────────────────────────────┤
│                                                    │
│  Reuters  Tier 1 · Wire · reuters.com              │
│                                                    │
│  [GEOPOLITICS] [ECONOMICS] [TECHNOLOGY]   ◄── pills│
│                                                    │
│  ┌────── Stat Panel ─────┐  ┌─── Radar Chart ───┐  │
│  │ [EARLY BREAKER] badge │  │                    │  │
│  │                        │  │  6-axis radar     │  │
│  │ Origination    58  ·   │  │  Current day      │  │
│  │ Validation     75  ▲15 │  │  Day 0 baseline   │  │
│  │ Speed          68  ▲18 │  │  Tier avg         │  │
│  │ Framing        62  ▲2  │  │                    │  │
│  │ Silent Edits   50  ▼20 │  │                    │  │
│  │ Corrections    56  ·   │  │                    │  │
│  └────────────────────────┘  └────────────────────┘  │
│                                                    │
│  ┌──── 30-Day Sparklines ───────────────────────┐  │
│  │ Origination  ───/\/───  58                   │  │
│  │ Validation   ────/───   75                   │  │
│  │ Speed        ───/───    68                   │  │
│  │ Framing      ──/\/\/──  62                   │  │
│  │ Silent Edits ───/\──    50                   │  │
│  │ Corrections  ───────    56                   │  │
│  └──────────────────────────────────────────────┘  │
│                                                    │
│  ┌──── Day Scrubber ───────────────────────────┐  │
│  │ [▶ Play] ═══●════════●══════●═══════════ Day 45 │
│  │                                              │  │
│  │ DAY 30  Claim resolves UNRESOLVED.           │  │
│  │ A second outlier claim from early in the     │  │
│  │ period never reached consensus...             │  │
│  └──────────────────────────────────────────────┘  │
│                                                    │
└────────────────────────────────────────────────────┘
```

## Radar chart details

### Axis labels

Six dimensions rendered as radar axis labels. Order (per CONTEXT.md radar polarity table):
1. Origination Rate (trait — neutral color)
2. Validation Rate (graded — teal/amber/red)
3. Speed Premium (graded, inverted)
4. Framing Consistency (graded, inverted)
5. Silent Edit Rate (graded, inverted)
6. Correction Rate (trait — neutral color)

Trait dimension axis labels rendered in `var(--nn-slate)` to distinguish from graded dimensions.

### Three datasets

| Dataset | Line style | Fill | Color | Purpose |
|---------|-----------|------|-------|---------|
| Current day | Solid, 2px | 13% opacity | `var(--nn-teal)` | Active profile at selected day |
| Day 0 baseline | Dashed, 1.3px | None | `var(--nn-text-dim)` 55% opacity | Reference point |
| Tier average | Dashed, 1.2px | None | `var(--nn-slate)` | Panel context |

### Scale

Fixed 0–100 percentile scale. Uses **hard bounds** `min: 0, max: 100` (not `suggestedMin`/`suggestedMax`). Hard bounds force the scale to render even with empty datasets — verified: Chart.js radar with `min:0, max:100` renders axes, labels, and concentric rings with zero data points. The `suggested*` variants require at least one data point to compute scale range and fail with empty datasets. Concentric rings at 25, 50, 75, 100.

### Polarity inversion

Before passing data to the Chart.js dataset, apply CONTEXT.md inversion:
```
R_speed_inverted = 100 - R_speed
R_frame_inverted = 100 - R_frame
R_edit_inverted  = 100 - R_edit
```

R_orig and R_correct pass through unchanged (trait dimensions, `--nn-slate`).
R_val passes through unchanged (already "higher = better").

### Empty state rendering

When `snapshots.length === 0`:
- Radar renders with axis labels, concentric rings, tick marks
- All three datasets are empty arrays `[]` — Chart.js draws no polygons
- Legend renders (dataset labels visible, no lines drawn)
- This communicates "infrastructure is ready, waiting for data"

## Stat panel details

Six rows, each showing:
1. Dimension label (e.g. "Validation Rate")
2. `(trait)` annotation for R_orig and R_correct (muted, smaller)
3. Current percentile value (IBM Plex Mono, tabular-nums)
4. Delta from day-0 baseline: ▲ for improvement, ▼ for deterioration, · for < 1pt change

Day-0 baseline is extracted as `snapshots.find(s => s.day === 0)` from the current vertical's filtered data. If no day-0 snapshot exists, deltas show "—".

Coloring per `getPolarityColor()`:
- ≥ 66 percentile → `var(--nn-teal)` (favorable)
- ≥ 33 percentile → `var(--nn-amber)` (neutral watch)
- < 33 percentile → `var(--nn-red)` (unfavorable)
- Trait dimensions → `var(--nn-slate)` (neutral, no polarity)

**Delta arrows** are colored by direction (not polarity), matching the reputation.html mock: ▲ green, ▼ red, · dim. This keeps the arrow's job simple ("which way did it move?") while the value color carries the polarity signal ("is that good or bad?").

Empty state: labels render, values show `—` (em dash) per ADR-0002.

## Sparkline details

### Implementation

6 inline SVG sparklines in a 2×3 or 3×2 CSS grid. Each sparkline:

```tsx
<svg viewBox="0 0 30 20" className="h-5 w-full">
  <polyline
    fill="none"
    stroke="var(--nn-slate)"
    strokeOpacity={0.7}
    strokeWidth={1.2}
    points={pointsString}
  />
</svg>
```

The sparkline color uses `--nn-slate` — the system's neutral/no-polarity token (already used for trait dimensions on the radar per CONTEXT.md). At 70% opacity it's visible against `--nn-surface` without competing with the stat panel's teal/amber/red polarity colors. Olive-tinted per the brand, not a dead gray.

The `points` string is computed from the trailing 30 days of snapshot data for each dimension, relative to the current scrubber position: **(currentDay − 30) through currentDay**. When currentDay < 30, show days 0 through currentDay (all available data). When no data exists, omit the `points` attribute — polyline renders invisibly. No axes, no labels (the sparkline column header identifies the dimension).

### Layout

Two-column CSS grid below the radar/stat panel row:
```
Origination sparkline  │  Validation sparkline
Speed sparkline        │  Framing sparkline
Silent Edits sparkline │  Corrections sparkline
```

Each cell: dimension label (left, mono) + sparkline SVG (center) + current value (right, mono).

### Empty state

Sparkline SVGs render with no `points` attribute on the `<polyline>` — invisible lines. Labels and value placeholders render.

## Day scrubber details

### Controls row

```
[▶ Play] [══════●══●══════●══════] Day 45
```
- Play/Pause button: Space Grotesk 700, 0.82rem, teal background
- Range input: `<input type="range" min={0} max={90} step={1}>`, flex-1, styled with CSS accent-color
- Day counter: IBM Plex Mono, "Day N" format

### Timeline markers

Small dots along the track at event days. Clicking a dot jumps to that day. Color:
- CLAIM_ABSORBED → `var(--nn-teal)` fill + border
- SILENT_EDIT → `var(--nn-amber)` border
- CLAIM_UNRESOLVED → `var(--nn-amber)` border

Dots before current day → filled. Dots after → outlined only.

### Event card

Below the scrubber row. Shows the nearest event at or before the current day:

```
DAY 30  Claim resolves UNRESOLVED.
A second outlier claim from early in the period never reached consensus by the 90-day check. Counts toward this source's Scatter-Shot Anomaly Factor.
```

Empty state: "Drag the slider, hit play, or click a marker to jump to a moment."

### Play animation

Clicking Play advances the slider by 0.6 days every 40ms from current position to day 90. Clicking Pause (or reaching day 90) stops. Moving the slider manually stops playback. Implemented with `useRef` interval (not requestAnimationFrame — 40ms is sufficient for this visual).

**Performance note (Vercel best-practices):** During animation, wrap the `setCurrentDay` call in `startTransition` (React 19) so slider track position updates at full speed while radar/stats re-renders are deprioritized. The radar chart component should be `React.memo` with a `compare` function that skips updates when the percentile values haven't changed by ≥ 1pt. This prevents expensive Canvas re-renders on fractional day changes (e.g., 45.0 → 45.6 → 46.2 where radar polygon is visually identical).

## Archetype badge

- Computed via `getArchetype(currentR_orig, currentR_val, panelMedian.orig, panelMedian.val)` where `panelMedian` defaults to `{ orig: 50, val: 50 }` when not provided.
- If no data available: shows null archetype — "Unclassified" text, `var(--nn-text-dim)` color, no background
- If data: semantic color per CONTEXT.md (navy/teal/red/slate), background at 10% opacity of that color
- Badge updates instantly when day scrubber changes (archetype is computed from current day's R_orig and R_val)

## Store changes

No store changes needed. Vertical picker state is component-local. The store's `activeSources` is used for the source lookup only.

## New files

| File | Purpose |
|------|---------|
| `src/pages/SourceProfile.tsx` | Full page component (replaces stub) |
| `src/pages/__tests__/source-profile.test.tsx` | Test suite |
| `src/data/scores.ts` | Shared score types: `ReputationScore` (extracted from Sources.tsx), `DailySnapshot`, `ProfileEvent`, dimension definitions array |

## Existing files modified

| File | Change |
|------|--------|
| `src/pages/Sources.tsx` | Remove local `ReputationScore` interface, import from `src/data/scores.ts` |

## Deferred items

See `docs/deferred.md` for the consolidated list across all slices. This plan adds:
- Timeline event markers — deferred until backend pipeline produces event data
- Vf trend chart, outlier waterfall, silent edit log, tier average polygon — deferred until backend pipeline

## Implementation order


**Component structure (Vercel best-practices):** Each section is a named sub-component in the same file — not inline JSX. `<StatPanel>`, `<RadarChart>`, `<SparklineGrid>`, `<DayScrubber>`. This prevents a single component tree from re-rendering en masse on scrub ticks and follows the `rerender-memo` rule. `RadarChart` uses `React.memo` with a custom comparator.

1. **Data types + helper** — `DailySnapshot`, `ProfileEvent` types, dimension definitions array in `src/data/scores.ts`
2. **Source lookup + vertical pills** — Route param extraction, vertical picker with component-local state, source-not-found fallback
3. **Stat panel** — 6 stat rows with polarity coloring, delta arrows, empty state
4. **Radar chart** — Chart.js `<Radar>` with 3 datasets, polarity inversion, axis labels, empty state, `React.memo`
5. **Sparkline grid** — 6 inline SVGs, data path computation, empty state
6. **Day scrubber** — Slider, play/pause with `startTransition`, timeline markers, event card
7. **Wire it together** — All sections update when day or vertical changes
8. **Tests** — Render tests for each section, interaction tests for scrubber, empty state tests

## Test strategy

**Important:** Chart.js requires a Canvas context, which jsdom does not provide. Mock `react-chartjs-2` in the test file:

```ts
vi.mock('react-chartjs-2', () => ({
  Radar: () => <canvas data-testid="radar-chart" aria-label="radar chart" />
}));
```

This lets tests verify the Radar component is mounted without requiring actual Canvas rendering. The visual verification checklist (dev server) confirms real rendering.

| Test | What it verifies |
|------|-----------------|
| Source not found | Renders "Source not found" for invalid `:domain` param |
| Source found | Renders source name, tier, domain from `DEFAULT_SOURCES` |
| Vertical pills render | 3 pills: GEOPOLITICS, ECONOMICS, TECHNOLOGY |
| Vertical pill click | Clicking a pill changes the active vertical, updates stat labels |
| Stat panel renders | 6 stat rows with dimension labels |
| Stat panel empty state | Values show "—" when no data |
| Archetype badge renders | Badge visible with correct archetype text |
| Archetype badge empty state | Shows "Unclassified" when no data |
| Radar chart renders | Canvas element with `data-testid="radar-chart"` present in DOM |
| Sparkline grid renders | 6 SVG sparklines with correct labels |
| Day scrubber renders | Slider, play button, day counter visible |
| Play animation starts | Clicking Play advances the day counter (use `vi.useFakeTimers()`) |
| Timeline markers render | Event dots at correct positions |
| Event card shows | Event detail for the nearest event at current day |
| Event card empty state | Placeholder text when no events |
| Link back to Sources | Navigation link to `/` present |

## Verification checklist

- [ ] `npm run build` exits 0
- [ ] `npm test` — all tests pass (existing 91 + new source-profile tests)
- [ ] TypeScript: no errors from `tsc --noEmit`
- [ ] Dev server: page renders at `/source/reuters.com`
- [ ] Empty state: radar axes visible, stat labels visible, no data points
- [ ] Vertical pills: clicking changes the pill highlight
- [ ] Day scrubber: slider moves, day counter updates
- [ ] Play button: animation advances the day
- [ ] Responsive: layout adjusts below 900px (single column)
