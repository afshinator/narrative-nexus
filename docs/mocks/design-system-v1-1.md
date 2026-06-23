# Narrative Nexus — Frontend Design System
**Version 1.0** | Aligned with spec v1.1

---

## 1. Tech Stack

| Layer | Choice | Rationale |
|---|---|---|
| Framework | React 18 (functional components + hooks) | Complex interactive state per page; chart/diagram components need lifecycle hooks |
| Build tool | Vite 5 | Fast HMR, minimal config, no CRA maintenance issues |
| Routing | React Router v6 | Client-side routing; FastAPI serves the static build |
| Layout / utilities | Tailwind CSS v3 | Spacing, grid, flex; does not own semantic color tokens |
| Design tokens | CSS custom properties on `:root` / `.dark` | Dynamic per-row archetype colors and polarity classes can't be Tailwind static classes |
| Data viz — scatter, radar | Chart.js 4 with custom canvas plugins | Proven; custom shape-per-format rendering already working |
| Data viz — pipeline flow | D3.js v7 | Node-edge animated diagram; nothing else handles this as well |
| Data viz — timeline | D3.js v7 | Day 0–90 animated horizontal layout |
| Data viz — simple charts | Recharts | Vf trend line, waterfall bars; integrates cleanly with React |
| State | Zustand with `persist` middleware | One store: theme, vertical, filter, font scale — all persisted to localStorage automatically |
| HTTP | fetch (native) or Axios | FastAPI `/api/*` endpoints |

### Tailwind + CSS vars integration pattern

CSS custom properties define *what* a color is semantically. Tailwind references them for *where* it's used structurally. Dynamic per-element coloring (archetype badges, polarity meter fills) is applied via `style={{ color: cssVar('--navy') }}` or inline style strings — not Tailwind classes.

```js
// tailwind.config.js
module.exports = {
  darkMode: 'class',  // toggled by adding .dark to <html>
  theme: {
    extend: {
      colors: {
        bg:       'var(--bg)',
        surface:  'var(--surface)',
        surface2: 'var(--surface2)',
        border:   'var(--border)',
        text:     'var(--text)',
        dim:      'var(--text-dim)',
        navy:     'var(--navy)',
        red:      'var(--red)',
        teal:     'var(--teal)',
        slate:    'var(--slate)',
        amber:    'var(--amber)',
      },
      fontFamily: {
        display: ['Space Grotesk', 'system-ui', 'sans-serif'],
        body:    ['IBM Plex Sans', 'system-ui', 'sans-serif'],
        mono:    ['IBM Plex Mono', 'monospace'],
      },
    },
  },
}
```

---

## 2. Color Tokens

### Dark mode (default / canonical)

```css
:root {
  /* Backgrounds */
  --bg:       #0c0f0b;   /* page background — deep warm dark green-black */
  --nav-bg:   #141810;   /* sticky nav band — one step lighter for zone distinction */
  --surface:  #161a12;   /* cards, panels */
  --surface2: #1f2619;   /* hover rows, alternate surfaces, input backgrounds */
  --border:   #2c3625;   /* all borders and dividers */

  /* Text */
  --text:     #d2e4c5;   /* primary text */
  --text-dim: #738567;   /* secondary labels, hints, metadata */

  /* Archetype colors — muted, readable on dark, no neon */
  --navy:     #7eb3e0;   /* Early Breaker */
  --navy-dim: rgba(126, 179, 224, 0.13);

  --red:      #d97878;   /* Noise Generator */
  --red-dim:  rgba(217, 120, 120, 0.13);

  --teal:     #5ebd8e;   /* Selective but Accurate */
  --teal-dim: rgba(94, 189, 142, 0.13);

  --slate:    #90a882;   /* Consensus Follower */
  --slate-dim:rgba(144, 168, 130, 0.13);

  /* Status / semantic */
  --amber:    #c49a42;   /* silent-edit flags, warnings, PENDING state */
  --green:    #5ebd8e;   /* favorable direction — same as --teal intentionally */
  --danger:   #d97878;   /* unfavorable direction — same as --red intentionally */
  --neutral:  #738567;   /* trait metrics (R_orig, R_correct), UNRATED states */
}
```

### Light mode

```css
html.light {
  --bg:       #eef0eb;
  --nav-bg:   #e0e4da;
  --surface:  #f7f8f5;
  --surface2: #e8ebe3;
  --border:   #d0d5c7;

  --text:     #1c2018;
  --text-dim: #717a68;

  --navy:     #2e4a7c;
  --navy-dim: rgba(46, 74, 124, 0.10);

  --red:      #8b2c28;
  --red-dim:  rgba(139, 44, 40, 0.10);

  --teal:     #276b52;
  --teal-dim: rgba(39, 107, 82, 0.10);

  --slate:    #5c6b5a;
  --slate-dim:rgba(92, 107, 90, 0.10);

  --amber:    #7a5217;
  --green:    #276b52;
  --danger:   #8b2c28;
  --neutral:  #717a68;
}
```

### Theme switching

```js
// src/hooks/useTheme.js
const [theme, setTheme] = useState(() =>
  localStorage.getItem('nn_theme') ?? 'dark'
);
useEffect(() => {
  document.documentElement.classList.toggle('light', theme === 'light');
  localStorage.setItem('nn_theme', theme);
}, [theme]);
```

Default is dark. Toggle lives in Settings page only — not in the nav or on any content page.

### Polarity color rule (normative)

This rule applies to every surface that renders a metric value. It must never be violated.

| Condition | Color token | Applies to |
|---|---|---|
| GRADED metric, favorable end | `--green` | Low Oi, low Sa, low Vf, high Rval, low Rspeed, low Redit |
| GRADED metric, middling | `--amber` | MED band labels, PENDING claim state |
| GRADED metric, unfavorable | `--danger` | HIGH band labels, UNRESOLVED state, high silent-edit count |
| TRAIT metric (no direction) | `--neutral` | R_orig, R_correct, UNRATED badge |
| Consensus-absorbed | `--teal` / `--green` | Absorption event markers, absorbed claim chips |
| Outlier pending | `--amber` | Pending claim chips, developing consensus bar |
| Unresolved | `--danger` | Terminal unresolved claim chips |

---

## 3. Typography

### Font families

```css
--font-display: 'Space Grotesk', system-ui, sans-serif;
--font-body:    'IBM Plex Sans', system-ui, sans-serif;
--font-mono:    'IBM Plex Mono', monospace;
```

**Space Grotesk** — page titles (h1), section headings (h2), nav brand, archetype labels, pulse strip numbers. Use weight 700 for headings, 500 for nav links.

**IBM Plex Sans** — all body copy, table row names, descriptions, tooltip prose, button labels, subheads. Use weight 400 for body, 500 for emphasized labels, 600 for column headers.

**IBM Plex Mono** — every numeric data value, metric labels (Oi / Vf / Sa), claim state tags, timestamps, LIVE PANEL badge, footer tagline, all code. Use weight 400 for values, 500 for labels.

### Type scale

All sizes are rem-based so the `--scale` multiplier (Section 6) applies throughout.

| Token | rem | Usage |
|---|---|---|
| `--fs-xs`  | 0.70rem | Eyebrows, footer tagline, column headers, legend labels |
| `--fs-sm`  | 0.82rem | Secondary labels, hints, table metadata |
| `--fs-base`| 0.90rem | Body text, table row content, tooltip prose |
| `--fs-md`  | 1.00rem | Nav links, primary UI labels |
| `--fs-lg`  | 1.15rem | Section headings (h2), card titles |
| `--fs-xl`  | 1.60rem | Sub-hero elements |
| `--fs-2xl` | 2.00rem | Page title (h1) |
| `--fs-data`| 1.90rem | Pulse strip numbers |

```css
:root {
  --scale: 1;
  --fs-xs:   calc(0.70rem * var(--scale));
  --fs-sm:   calc(0.82rem * var(--scale));
  --fs-base: calc(0.90rem * var(--scale));
  --fs-md:   calc(1.00rem * var(--scale));
  --fs-lg:   calc(1.15rem * var(--scale));
  --fs-xl:   calc(1.60rem * var(--scale));
  --fs-2xl:  calc(2.00rem * var(--scale));
  --fs-data: calc(1.90rem * var(--scale));
}
```

Font scale slider (Settings page): range 0.8–1.6, step 0.05. Persisted to `localStorage` key `nn_font_scale`. Applied as `document.documentElement.style.setProperty('--scale', value)` on load and on change.

### Line heights and weights

```css
--lh-tight:  1.25;   /* headings, big numbers */
--lh-base:   1.55;   /* body, table rows */
--lh-loose:  1.70;   /* long prose, onboarding copy */

--fw-normal:  400;
--fw-medium:  500;
--fw-semibold:600;
--fw-bold:    700;
```

---

## 4. Spacing & Layout

### Spacing scale (Tailwind-compatible)

These map to Tailwind's default spacing scale; listed here for clarity when writing custom CSS.

| Token | px | Tailwind |
|---|---|---|
| space-1 | 4px  | `p-1`  |
| space-2 | 8px  | `p-2`  |
| space-3 | 12px | `p-3`  |
| space-4 | 16px | `p-4`  |
| space-5 | 20px | `p-5`  |
| space-6 | 24px | `p-6`  |
| space-8 | 32px | `p-8`  |

### Layout tokens

```css
--nav-height:    52px;
--page-max-w:    1340px;
--page-padding:  32px;       /* left/right on desktop */
--page-padding-y:28px;       /* top padding below nav */
--card-radius:   14px;       /* hero cards, ledger card */
--pill-radius:   999px;      /* all pill buttons and badges */
--badge-radius:  999px;      /* verdict badges */
--input-radius:  8px;        /* text inputs, Settings fields */
```

### Nav bar

```
height: var(--nav-height) = 52px
background: var(--nav-bg)
position: sticky; top: 0; z-index: 100
border-bottom: 1px solid var(--border)
padding: 0 28px
```

Brand mark: target/ring SVG icon + "Narrative Nexus" in Space Grotesk 700, 1.0em.
Active link: `color: var(--navy)`, `border-bottom: 2px solid var(--navy)`.
Stub links: 50% opacity, `cursor: default`, non-interactive.
Settings floats right after a flex spacer + 1px divider.

### Responsive breakpoints

Desktop-first. The demo runs on a laptop/external display. Mobile is not a hackathon requirement but don't make it actively broken.

```
sm:  640px   — pill wrapping, single-column pulse strip
md:  768px   — nav overflow-x: auto
lg:  1024px  — full layout target
xl:  1280px  — comfortable max for the scatter + ledger side by side (future)
```

---

## 5. Component Tokens

### Cards and panels

```css
.card {
  background:    var(--surface);
  border:        1px solid var(--border);
  border-radius: var(--card-radius);
  padding:       22px 24px;
}
```

### Verdict / archetype badges

Fully rounded pill. Background is the archetype color at 10% opacity (13% dark mode). Text is full archetype color.

```css
.badge {
  display:       inline-flex;
  align-items:   center;
  gap:           5px;
  padding:       4px 12px;
  border-radius: var(--badge-radius);
  font-family:   var(--font-mono);
  font-size:     var(--fs-xs);
  font-weight:   var(--fw-semibold);
  letter-spacing:.02em;
  white-space:   nowrap;
  /* Colors applied via inline style using --archetype-color and --archetype-dim */
}
```

### Filter pills

```css
.pill {
  display:       inline-flex;
  align-items:   center;
  gap:           6px;
  padding:       7px 16px;
  border-radius: var(--pill-radius);
  font-family:   var(--font-body);
  font-size:     var(--fs-sm);
  font-weight:   var(--fw-medium);
  border:        1px solid var(--border);
  background:    transparent;
  color:         var(--text-dim);
  cursor:        pointer;
  transition:    color 150ms, border-color 150ms, background 150ms;
}
.pill.active[data-arch="eb"] { border-color: var(--navy); color: var(--navy); background: var(--navy-dim); }
.pill.active[data-arch="ng"] { border-color: var(--red);  color: var(--red);  background: var(--red-dim); }
.pill.active[data-arch="sa"] { border-color: var(--teal); color: var(--teal); background: var(--teal-dim); }
.pill.active[data-arch="cf"] { border-color: var(--slate);color: var(--slate);background: var(--slate-dim); }
.pill.active[data-arch="all"]{ border-color: var(--text); color: var(--text); background: var(--surface2); }
```

### Meter bars (origination / validation columns)

```
height: 7px
width: 88px
background: var(--surface2)
border-radius: 4px
fill: archetype color of that row
median tick: 2px wide, 11px tall, var(--text-dim) at 50% opacity
```

### Pulse strip

```
4-column grid, 1px gap, background var(--border) (creates hairline dividers)
border-radius: 12px, overflow: hidden
each cell: var(--surface), padding 16px 20px
left border: 3px solid (archetype color or amber for flags, transparent for count)
numbers: Space Grotesk 700, var(--fs-data)
label: IBM Plex Sans 600, var(--fs-xs), uppercase, letter-spacing .05em, var(--text-dim)
sub: IBM Plex Sans 400, var(--fs-sm), var(--text-dim)
```

### Table

```
th: IBM Plex Sans 700, var(--fs-xs), uppercase, letter-spacing .05em, var(--text-dim)
    padding 8px 10px, border-bottom 2px solid var(--border), cursor pointer
td: padding 10px, border-bottom 1px solid var(--border), font-size var(--fs-base)
tr hover: background var(--surface2)
tr.linked: background var(--surface2)  (from scatter hover cross-link)
row enter: opacity 0→1 + translateY(3px→0), 350ms ease, staggered 25ms per row
           ONLY on first render — not on filter/sort changes
```

### Shape signature glyph (profile shape column)

5-axis mini radar polygon. 34×34px SVG. Outer pentagon in `var(--border)`, fill polygon in archetype color at 25% opacity, stroke at full color, 1.4px.

---

## 6. Data Visualization

### Scatter plot (Chart.js + custom canvas plugin)

```
canvas height: 580px (full available width)
Chart.js type: bubble
all points: transparent fill + 0 borderWidth (shapes drawn in afterDraw plugin)
point radius: 6 + sqrt(article_count) / 24 (volume encoding)

Quadrant tints:
  dark mode opacity: 0.09
  light mode opacity: 0.06
  colors: navy (top-right), red (bottom-right), teal (top-left), slate (bottom-left)

Dashed center lines:
  dark: rgba(255,255,255,.12)
  light: rgba(0,0,0,.10)
  dash: [4, 4], lineWidth: 1

Quadrant labels:
  font: 600 11.5px IBM Plex Sans
  color: matching archetype color
  position: corners (inside chart area, 10px inset)

Marker shapes (drawn in afterDraw):
  circle    → Wire / Public
  square    → Daily / Weekly print
  diamond   → Cable broadcast
  triangle  → Tabloid
  hexagon   → Digital-native
  fill: archetype color at 80% opacity (cc suffix)
  stroke: archetype color full, 1.5px

Flagged source (silent edits ≥ threshold):
  pulsing amber ring at r+5px, 0.3–0.45 opacity, 60ms redraw interval
  disable interval when no flagged sources in current filter

Hover from table row → draw highlight ring at r+7px, 2px, 0.8 opacity
Scatter hover → highlight matching table row via .linked class
```

### Radar chart (Source Profile, Chart.js or canvas)

```
6 axes: Origination Rate | Validation Rate | Speed Premium |
        Framing Consistency | Silent Edit Rate | Correction Rate
Axes: percentile-oriented — outward = favorable
      Origination and Correction are TRAIT axes (no favorable direction) —
      label at 30% opacity, "descriptive" marker, excluded from polygon
Polygons:
  current period: var(--teal), 2px stroke, 13% opacity fill
  baseline (day 0 or 30-day prior): var(--text-dim), 1.3px dashed stroke, no fill
  tier average: var(--neutral), 1.2px dashed stroke, no fill
Dots at vertices: 3px filled circle, var(--teal)
Grid rings: concentric polygons at 25/50/75/100, var(--border)
Axis lines: var(--border)
Labels: IBM Plex Mono var(--fs-xs), var(--text-dim) / var(--neutral) for trait axes
```

### Timeline (D3.js)

```
X axis: calendar days 0–90
Y axis: sources stacked (one lane per source)
Publication dot: 6–10px circle, archetype color
Outlier claim: dot + small claim chip below
Consensus absorption: vertical rule, var(--teal), label "CONSENSUS-ABSORBED"
Unresolved: dot fades to var(--text-dim) opacity .3 at day 90
Echo mimic: smaller dot (60% size) + dashed line connecting to origin dot
Animation: day 0 → 90 playback at ~60fps, play/pause button
```

### Pipeline flow (D3.js)

```
Layout: left-to-right, 8 stage nodes
Stage nodes: rounded-rect cards with stage name + AMD GPU / Fireworks badge
Particles: small circles travelling along bezier paths between stages
  color: var(--teal) for active, var(--amber) for queued/waiting
Live mode: particles represent real articles in pipeline (WebSocket or polling)
Replay mode: reconstruct from pipeline_run_log timing data
Stage click: side panel expands with description, throughput, last run timestamp
```

---

## 7. Motion

### Principles

Animation is purposeful, not decorative. The signature animated moments are:
1. **Pulse strip count-up** — numbers count from 0 on page load (700ms, cubic ease-out)
2. **Scatter entrance** — markers grow from 0 radius (700ms, easeOutBack — Chart.js built-in)
3. **Row entrance** — table rows fade + translateY on first render only, staggered 25ms
4. **Pulsing amber ring** — flagged sources on the scatter, continuous 60ms redraw
5. **Pipeline particles** — continuous flow, the page's ambient motion

### Timings

```css
--duration-instant: 100ms;   /* hover color changes */
--duration-fast:    150ms;   /* pill active, badge color */
--duration-base:    300ms;   /* most UI transitions */
--duration-enter:   350ms;   /* row entrance */
--duration-chart:   700ms;   /* scatter + radar entrance */
--duration-countup: 700ms;   /* pulse strip numbers */
```

### Reduced motion

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { animation-duration: 0ms !important; transition-duration: 0ms !important; }
  .blip { animation: none !important; }
  /* pipeline particles: still rendered, not animated */
}
```

In Chart.js: `animation: { duration: reduceMotion ? 0 : 700 }`.
Pulse ring interval: disabled when `prefers-reduced-motion`.

---

## 8. Iconography

No icon library. All icons are inline SVG, drawn at 13–20px.

| Usage | Shape |
|---|---|
| Early Breaker pill | Lightning bolt path |
| Noise Generator pill | Three scattered circles |
| Selective but Accurate pill | Bullseye (circle + filled center) |
| Consensus Follower pill | Two overlapping circles |
| Nav brand mark | Concentric circles with dashed outer + filled center |
| LIVE PANEL badge | 6px pulsing dot |
| Silent-edit flag | 6px amber dot inline after source name |

Keep icons monochromatic — they inherit the surrounding element's `color` or receive the archetype color explicitly. No multi-color icons.

---

## 9. Persistent Footer

Every page, every screen size:

```
font-family: IBM Plex Mono
font-size: var(--fs-xs)
color: var(--text-dim)
text-align: center
padding: 28px 0
letter-spacing: .04em
content: "Narrative Nexus tracks consensus reality, not truth."
```

Ticker-tape animation: deferred stretch goal. Plain centered text for MVP.

---

## 10. Frontend Decisions — Confirmed

All decisions resolved. No open questions remain before building.

| # | Decision | Resolved |
|---|---|---|
| 1 | React Router: **history mode** | Clean URLs (`/sources`, `/cluster/abc`). Requires FastAPI catch-all route returning `index.html` for all non-`/api/*` paths — register it last in `app.py`. |
| 2 | Pipeline flow diagram: **D3.js v7** | Custom animated node-edge layout; React Flow would constrain animation control. |
| 3 | Global state: **Zustand** with `persist` middleware | One store file; `persist` replaces manual localStorage for theme + font scale. No Context providers. |
| 4 | Chart.js vs Recharts for radar: **Chart.js** | Canvas control needed for custom polygon drawing and axis exclusion logic. |
| 5 | Vite dev server proxy | `vite.config.js` proxies `/api/*` to `localhost:8000`. Set up day 1 of backend work. |
| 6 | Settings page controls: **shadcn/ui** | Sliders, toggles, selects. Already a dependency via Radix primitives. |
| 7 | Mobile: **graceful degradation** | Scatter + table stack vertically, nav scrolls horizontally. No responsive redesign. |
| 8 | Onboarding walkthrough: **shadcn/ui Dialog + Zustand step state** | 5-step vocabulary modal. No tour library — element highlighting is wrong shape for term definitions. Radix Dialog handles focus trap + escape key. `onboardingComplete` flag in Zustand store (persisted). Re-open from `?` icon in nav sets flag false. |

---

## 11. File Structure

```
src/
  components/
    layout/
      AppNav.jsx
      PageShell.jsx        ← sticky nav + page wrapper
      Footer.jsx
    charts/
      ScatterMap.jsx        ← Chart.js scatter + custom plugin
      RadarChart.jsx
      VfTrend.jsx           ← Recharts line
      OutlierWaterfall.jsx  ← Recharts stacked bar
      TimelineD3.jsx
      PipelineFlow.jsx
    ui/
      Badge.jsx             ← verdict / archetype badge
      Pill.jsx              ← filter pill
      MeterBar.jsx          ← origination / validation bar
      PulseStrip.jsx        ← 4-stat header row
      ShapeSig.jsx          ← 5-axis mini polygon
      StatCard.jsx          ← single metric with delta
      Tooltip.jsx
      Onboarding.jsx
  pages/
    Sources.jsx
    SourceProfile.jsx
    ClusterReport.jsx
    Timeline.jsx
    PipelineFlow.jsx
    Investigate.jsx
    Panel.jsx
    Settings.jsx
  hooks/
    useTheme.js
    useFontScale.js
    useVertical.js
    useSources.js           ← fetches /api/leaderboard
  utils/
    cssVar.js               ← getComputedStyle helper
    archetype.js            ← color + key lookups
    polarity.js             ← GRADED vs TRAIT, favorable direction
    format.js               ← number formatting, em-dash for n<5
  styles/
    tokens.css              ← all CSS custom properties (this doc → code)
    global.css
  App.jsx
  main.jsx
```