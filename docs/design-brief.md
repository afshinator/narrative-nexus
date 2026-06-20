# Narrative Probe — Design Brief

## Product Concept

Narrative Probe is a dashboard that tracks how ~20 news outlets relate to *consensus reality* — the version of events most of the panel agrees on. It measures which outlets break stories early that later become the consensus view, which generate claims that never stick, and whose coverage most closely aligns with the mainstream account.

**The system never says a source is "right" or "wrong."** It shows data across six independent metrics. The user makes their own judgment.

**Target users:**
- **Primary:** Analysts (journalists, OSINT researchers, policy analysts) who need to understand the media landscape
- **Secondary:** Hackathon judges / demo visitors who need to grasp the core idea in under 2 minutes

**Key constraint:** "Narrative Probe tracks consensus reality, not truth." — this phrase appears in the footer of every page and as a qualifier on the coverage analysis report.

## Current Mock Status

7 pages in the nav (4 functional, 3 stubs):

### Functional Pages

**1. Sources (landing page)** — Table of 18 sources with 6 sortable, color-coded metrics (Origination Rate, Validation Rate, Consensus Accuracy, Source Reliability, Framing Consistency, Silent Edits). Above the table: archetype filter pills (All / Early Breaker / Noise Generator / Selective but Accurate / Consensus Follower). Below the table: scatter plot with X=Origination Rate, Y=Validation Rate, 4 labeled quadrants mapping to the 4 archetypes. Each dot is clickable to view that source's profile. An intro accordion panel explains the product concept (collapsible, re-openable).

**2. Source Profile** — Header with source name, archetype badge, country/category. Stat row with 5 metrics. Grid of 2 charts: radar chart (6 axes, current vs previous month) + framing volatility line chart (12 months, threshold lines for low/medium/high). Below: outlier claim waterfall (10 claims across 4 outcome types: consensus-absorbed, cross-source convergent, self-consistent, unresolved) + silent edit log (8 events, 3 severity levels, with Confirm Significant / Mark False Positive buttons). Recent stories section linking to coverage analysis.

**3. Coverage Analysis** — 3-zone report layout:
- Zone 1: Consensus narrative blurb with qualifier
- Zone 2: Source comparison matrix (articles count, omission index bar, framing volatility badge, notable divergence notes)
- Zone 3: Warning banners (Reputation Alert, Reality Fracture Detected), outlier claim cards, navigation links to Timeline, Pipeline Flow (stub), and Ad-Hoc (stub)

**4. Timeline** — 90-day horizontal timeline. Sources stacked vertically on Y axis. Article dots positioned by date, colored by source archetype. Outlier claims as diamond markers. Vertical dashed line for consensus absorption (Day 14). Legend below.

### Stub Pages (layout skeleton only, content placeholder)
- Pipeline Flow (animated diagram concept)
- Ad-Hoc Investigation (search + forensic report concept)
- Panel Management (source catalog with toggles concept)
- Onboarding (5-step walkthrough concept)

## Visual Direction (current v3 mock)

**Register:** Product UI / analytical tool

**Default theme:** Light mode. Dark mode inverts the palette.

**Color palette:**
- Background: warm cream #f5f3ee
- Surface: white #ffffff
- Surface 2: warm light gray #ece8e0
- Border: #d8d4cc
- Text: near-black #1c1a16
- Text muted: warm gray #7a7568
- Accent / Primary: deep navy #1e3a5f (nav links, active states, badges)
- Positive: forest green #2d6a4f (good metric scores, consensus-absorbed)
- Warning: amber #b8860b (moderate scores)
- Alert: deep red #b91c1c (bad scores, noise generator)
- Archetype badge colors: navy (Early Breaker), teal (Selective but Accurate), slate (Consensus Follower), red (Noise Generator)
- Dark mode: navy → #60a5fa, forest → #34d399, amber → #fbbf24, red → #f87171 on #0c0b12 background

**Typography:**
- Headings: DM Serif Display, serif (1.5rem h1, 1.1rem h2)
- Body: DM Sans, sans-serif
- Data values: JetBrains Mono, monospace
- Metric labels: 0.75rem, uppercase, letter-spaced

**Layout:**
- Sticky top nav bar (52px) with 7 nav items, brand in serif, light/dark toggle, font size slider
- Max-width 1400px centered content
- 24px grid gap in 2-column layouts
- No card borders — chart containers use subtle box-shadow instead
- Table: header with background, row hover highlights in navy tint
- Footer: centered, italic, "Narrative Probe tracks consensus reality, not truth."

## Navigation Flow

Sources (landing) → click source name/dot → Source Profile → click story card → Coverage Analysis → click timeline link → Timeline
Pathway hints also connect to stub pages (Pipeline Flow, Ad-Hoc, Panel, Onboarding)

## Data

- 18 sources (real outlet names: Reuters, AP News, BBC, Bloomberg, Guardian, NYT, WaPo, WSJ, CNN, Fox News, MSNBC, Daily Mail, Breitbart, Al Jazeera, Economist, NPR, Newsmax, Axios)
- 4 archetypes assigned to sources
- 3 clusters for coverage analysis (Nakatomi Space Treaty, Aurora Energy, Hadal Trench)
- Metrics on 0-100 scale with green/amber/red thresholds per metric
- Silent edit log: 8 events across minor/moderate/major severity
- Outlier claims: 10 claims across 4 outcome categories


---

## Font size recommendations

```
/* ==========================================================================
   NARRATIVE PROBE — TYPOGRAPHY THEME SCALES
   ========================================================================== */

/* 1. ARCHIVAL EDITORIAL (Current v3) 
   Classical, premium digital journalism scale with clear contrast. */
:root[data-theme="archival-editorial"] {
  --font-heading: 'DM Serif Display', serif;
  --font-body: 'DM Sans', sans-serif;
  --font-mono: 'JetBrains Mono', monospace;

  --fs-tiny: 0.7rem;
  --fs-small: 0.75rem;
  --fs-body: 0.85rem;
  --fs-subtitle: 0.9rem;
  --fs-h2: 1.1rem;
  --fs-stat: 1.2rem;
  --fs-h1: 1.5rem;
}

/* 2. TACTICAL INTEL (OSINT Terminal) 
   High-density command center scale. Compressed headers, prioritized data. */
:root[data-theme="tactical-intel"] {
  --font-heading: 'Inter', system-ui, sans-serif;
  --font-body: 'Inter', system-ui, sans-serif;
  --font-mono: 'SF Mono', monospace;

  --fs-tiny: 0.65rem;
  --fs-small: 0.7rem;
  --fs-body: 0.75rem;
  --fs-subtitle: 0.8rem;
  --fs-h2: 0.9rem;
  --fs-stat: 1.4rem;
  --fs-h1: 1.1rem;
}

/* 3. CLINICAL LEDGER (Bureaucratic Registry) 
   Extreme structural scale contrast. Massive indices, microscopic labels. */
:root[data-theme="clinical-ledger"] {
  --font-heading: 'Neue Haas Grotesk', Arial, sans-serif;
  --font-body: 'Neue Haas Grotesk', Arial, sans-serif;
  --font-mono: 'JetBrains Mono', monospace;

  --fs-tiny: 0.6rem;
  --fs-small: 0.65rem;
  --fs-body: 0.85rem;
  --fs-subtitle: 0.95rem;
  --fs-h2: 1.3rem;
  --fs-stat: 2.5rem;
  --fs-h1: 2.2rem;
}

/* 4. SIGNAL FIELD (Spectrum & Diffusion) 
   Modern, spacious SaaS scale. High breathing room and geometric clarity. */
:root[data-theme="signal-field"] {
  --font-heading: 'Plus Jakarta Sans', sans-serif;
  --font-body: 'Plus Jakarta Sans', sans-serif;
  --font-mono: 'Geist Mono', monospace;

  --fs-tiny: 0.75rem;
  --fs-small: 0.8rem;
  --fs-body: 0.9rem;
  --fs-subtitle: 1.0rem;
  --fs-h2: 1.2rem;
  --fs-stat: 1.6rem;
  --fs-h1: 1.75rem;
}
```