# Narrative Alpha — Mock Screens Plan

## Goal

Create four interactive HTML/CSS mock screens based on the UX brief (`docs/ux-brief-01.md`), styled in the dark terminal / forensic intelligence console theme. No framework, no build step — plain HTML + CSS + JS. Chart.js (CDN) for the charts.

The user will review these to validate visual direction and UX flow before we derive the spec.

## Screens to Build (Core Journey)

1. **Leaderboard** — Table of ~20 sources with 6 metrics + scatter plot (origination × validation, 4 quadrants)
2. **Source Profile** — Radar chart, archetype tag, framing volatility line chart, outlier claim waterfall, silent edit log
3. **Cluster Forensic Report** — 3-zone report: consensus summary, source comparison matrix, forensic analysis
4. **Timeline** — Horizontal calendar with sources stacked vertically, consensus absorption line

## File Structure

```
docs/
  mocks/
    index.html                 # Nav hub — links to all 4 screens
    leaderboard.html            # Screen 1: Leaderboard (table + scatter)
    source-profile.html         # Screen 2: Source profile (radar, waterfall, log)
    cluster-report.html         # Screen 3: Cluster forensic report
    timeline.html               # Screen 4: Timeline view
    css/
      theme.css                 # Shared styles: dark terminal theme, typography, colors, components
    js/
      mock-data.js              # All mock data: sources, clusters, articles, metrics
      charts.js                 # Chart.js configs and rendering for each screen
      navigation.js             # Screen nav, footer, common behavior
```

## Visual Theme (from UX Brief §5)

| Element | Value |
|---|---|
| Background | `#0a0a0f` |
| Positive/good | `#00ff88` |
| Warning/medium | `#ffaa00` |
| Alert/bad | `#ff4444` |
| Data values | Monospace (JetBrains Mono or system monospace) |
| Prose | Sans-serif (Inter or system UI) |
| Data value size | `font-size: 0.875rem` |
| Metric label size | `font-size: 0.75rem`, uppercase, muted (#888) |

Footer on every page: *"Narrative Alpha tracks consensus reality, not truth."*

### Navigation Bar (new — top of every screen)

A persistent horizontal nav bar lists all 7 sections of the app, so the full information architecture is visible even on non-mocked pages:

```
[ Leaderboard ] [ Source Profile ] [ Cluster Report ] [ Timeline ] [ Pipeline Flow ] [ Ad-Hoc ] [ Panel ]
```

- Mocked pages: styled as active links in green `#00ff88`
- Non-mocked pages: styled in muted `#555` with `(coming)` suffix, cursor shows a tooltip: "Mock coming in next iteration"
- Current page is highlighted with a subtle underline/border accent

This ensures the evaluator sees the complete app and knows every section is planned.

### Pathway hints on mocked pages

Where natural, non-mocked pages are referenced from mocked content:
- **Leaderboard**: The "Filter by topic vertical" dropdown includes a note: *"Manage your panel in Panel Settings"* (subtle gray link to Panel page, which shows as `(coming)`)
- **Cluster Report**: A button in Zone 3: *"Run ad-hoc investigation on this topic"* → links to Ad-Hoc page (shows as `(coming)`)
- **Source Profile**: A small help icon `(?)` in the header → re-opens onboarding walkthrough (`(coming)`)
- **Pipeline Flow**: Mentioned in context as an aside on the Cluster Report — *"See how this cluster flowed through the pipeline"* → links to Pipeline Flow page (`(coming)`)


## Mock Data Design

### Sources (18 outlets)

Real outlet names, realistic metrics:

| Source | Archetype | Origination | Validation | Silent Edits | Category | Country |
|---|---|---|---|---|---|---|
| Reuters | Early Breaker | 92 | 88 | 0 | Wire | UK |
| AP News | Early Breaker | 85 | 82 | 0 | Wire | US |
| BBC News | Selective but Accurate | 65 | 78 | 2 | Public | UK |
| Bloomberg | Early Breaker | 78 | 75 | 1 | Wire | US |
| The Guardian | Selective but Accurate | 55 | 70 | 3 | Daily | UK |
| The New York Times | Consensus Follower | 45 | 72 | 4 | Daily | US |
| The Washington Post | Consensus Follower | 40 | 68 | 5 | Daily | US |
| The Wall Street Journal | Selective but Accurate | 60 | 80 | 1 | Daily | US |
| CNN | Consensus Follower | 50 | 62 | 6 | Cable | US |
| Fox News | Noise Generator | 82 | 35 | 12 | Cable | US |
| MSNBC | Consensus Follower | 48 | 58 | 4 | Cable | US |
| Daily Mail | Noise Generator | 75 | 30 | 15 | Tabloid | UK |
| Breitbart | Noise Generator | 88 | 22 | 20 | Digital | US |
| Al Jazeera | Selective but Accurate | 58 | 72 | 2 | Digital | QA |
| The Economist | Selective but Accurate | 62 | 85 | 0 | Weekly | UK |
| NPR | Selective but Accurate | 48 | 76 | 1 | Public | US |
| Newsmax | Noise Generator | 80 | 18 | 18 | Digital | US |
| Axios | Early Breaker | 72 | 74 | 0 | Digital | US |

### Metrics thresholds for green/amber/red coloring

| Metric | Green (≥) | Amber (≥) | Red (<) |
|---|---|---|---|
| Origination Rate | 70 | 50 | 50 |
| Validation Rate | 70 | 50 | 50 |
| Consensus Accuracy | 75 | 55 | 55 |
| Source Reliability | 75 | 55 | 55 |
| Framing Consistency | 70 | 50 | 50 |
| Silent Edit Count | ≤2 | ≤8 | >8 |

### Clusters (3 clusters)

Cluster 1 (well-covered): "Nakatomi Space Treaty negotiations" — 12 sources, consensus reached day 14
Cluster 2 (divergent): "Aurora energy project environmental review" — deep split, reality fracture
Cluster 3 (single-source): "Hadal trench microbe discovery" — 1 source broke it, consensus-absorbed day 67

Each cluster: title, ID, article count, consensus status, absorption date, 5-8 articles with publish dates.

### Silent Edits (for source profile)

8 edit events across severity levels, with date, article title, diff description.

### Outlier Claims (for source waterfall)

10 claims breaking down into:
- Consensus-absorbed: 3
- Cross-source convergent: 2
- Self-consistent: 2
- Unresolved: 3

## Per-Screen Layout

### 1. Leaderboard

- **Scatter plot** (600×400): X = Origination Rate, Y = Validation Rate, 4 labeled quadrants, colored dots by archetype
- **Table**: 6 metric columns, sortable by click, green/amber/red cell coloring, source names link to profile
- Filter by archetype badge pills above the table
- Footer: "Narrative Alpha tracks consensus reality, not truth."

### 2. Source Profile

- **Header row**: Source name, archetype badge, country, article count, edit log count
- **Radar chart** (400×400): 6 axes, current + previous month, 0-100 scale
- **Framing volatility line chart**: 12 months, threshold lines, color-coded by severity
- **Outlier claim waterfall**: Stacked horizontal bars by outcome type
- **Silent edit log**: Table with date, severity badge, article, description, action buttons
- "← Back to Leaderboard" link

### 3. Cluster Report

- **Header**: Title, version badge, date range, article count
- **Zone 1**: Consensus narrative blurb with qualifier
- **Zone 2**: Source matrix table with omission index bars, volatility badges, BODY_UNAVAILABLE markers
- **Zone 3**: Warning banners, outlier claim cards, reality fracture indicator

### 4. Timeline

- X-axis: 90-day span, clickable to cluster report
- Y-axis: 12 source names
- Article dots positioned by date, colored by source
- Outlier claims = diamond markers
- Consensus absorption = vertical dashed line
- Hover tooltip

## Implementation

- Pure static HTML, open from filesystem
- Chart.js v4 from CDN
- No build step, no server
- Simple `<a>` navigation between screens

## Files to Create (9 total)

| File | Lines (est.) |
|---|---|
| `docs/mocks/index.html` | 60 |
| `docs/mocks/leaderboard.html` | 150 |
| `docs/mocks/source-profile.html` | 180 |
| `docs/mocks/cluster-report.html` | 160 |
| `docs/mocks/timeline.html` | 130 |
| `docs/mocks/css/theme.css` | 200 |
| `docs/mocks/js/mock-data.js` | 250 |
| `docs/mocks/js/charts.js` | 200 |
| `docs/mocks/js/navigation.js` | 40 |
