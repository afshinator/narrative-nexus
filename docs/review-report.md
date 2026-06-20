# Narrative Probe — Design Review

**Date:** 2026-06-20
**Mode:** Review
**Target:** `docs/mocks/index.html`
**Score:** 31/50

---

## TL;DR

The mock establishes a strong forensic/dark-terminal identity and the core interaction flow is navigable, but the scatter plot dominates the leaderboard at the expense of the table (the primary scanning tool), the archetype colors collide with the polarity color system, and interaction states are mostly absent. The foundation is solid — the fixes are targeted, not structural.

**Primary recommendation:** Swap the scatter plot and table positions on the leaderboard so the data table — the primary scanning instrument — is the first thing the user sees.

---

## Heuristic Scores

| # | Heuristic | Score | Key Finding |
|---|---|---|---|
| 1 | First impression | 6/10 | Strong genre identity but "Leaderboard" landing creates gamified tone mismatch |
| 2 | Hierarchy | 7/10 | Source profile and cluster report flow well; leaderboard prioritizes viz over data |
| 3 | Color voice | 6/10 | Archetype colors collide with polarity colors; meaningful signals blur together |
| 4 | Type voice | 7/10 | Inter + JetBrains Mono is a solid pair; sizes feel chosen ad-hoc rather than from a scale |
| 5 | Interaction feel | 5/10 | Table sorting and nav work; timeline dots not clickable, no loading/empty/error states, focus states missing |

---

## What's Working

- **Forensic genre identity** — The dark terminal palette (#0a0a0f), green/amber/red polarity, and monospace data values immediately communicate "analytical tool." The product name, tone, and visual language are aligned.
- **Scatter plot as concept anchor** — The 4-quadrant chart with labeled archetypes is the strongest design element. The axis descriptions (Validation Rate / Origination Rate) are clearly explained below it, making the core concept scannable.
- **Coverage Analysis zone structure** — The 3-zone layout (consensus → matrix → forensic) creates a clear narrative arc for the report. Warning banners, outlier cards, and pathway hints at the bottom make it feel like a real product.
- **Light/dark mode and font slider** — These aren't common in mockups and show attention to real user needs. The persistence via localStorage is correctly implemented.

---

## Priority Issues

### P1 — Archetype colors collide with polarity colors

**Evidence:** The four archetypes each have a color: Early Breaker = #00ff88 (green), Noise Generator = #ff4444 (red), Selective but Accurate = #00c8ff (blue), Consensus Follower = #ffaa00 (amber). The polarity system uses the exact same green/amber/red for metric cell coloring. On the scatter plot, an Early Breaker dot (green) in the bottom-right quadrant looks like a positive signal even though the source has low validation. A Consensus Follower dot (amber) in the top-right looks like a warning when it isn't one.

**Fix:** Use a separate, non-overlapping color encoding for archetypes. Four hues with equal lightness and chroma that don't overlap with the polarity palette — e.g., a desaturated set (blue-cyan, purple, teal, rose) that only appears on badges and scatter plot dots, never on metric cells.

### P1 — Scatter plot renders above the table on the leaderboard

**Evidence:** The leaderboard is the primary scanning surface. Users arrive to compare sources across 6 metrics. The scatter plot is supplementary — it shows the same data visually. Stacking it first means users scroll past a large chart every time they visit. The table, which is the actual working instrument, is below the fold.

**Fix:** Move the table above the scatter plot. Users scan data first, then optionally reference the visual. Or use a side-by-side layout on wider screens.

### P2 — Interactive elements lack states

**Evidence:** The chart's event listeners on the background register clicks at the wrong location. Chart.js tooltips don't show source names. The `onClick` handler on the scatter chart checks for items, but if you click on an empty area (most of it), nothing happens — there is no visual feedback. Focus states are absent throughout — tabbing through the interface provides no visible ring or outline. The Timeline dots have `title` attributes for hover text but no click behavior — the UX brief explicitly describes clicking timeline dots to navigate to coverage analysis.

**Fix:** Add visible focus rings (2-3px, 3:1 contrast). Make timeline dots clickable to navigate to the coverage analysis page. Implement loading/empty/error states for each chart container.

### P2 — Body type runs small

**Evidence:** Metric labels are 0.75rem, body text is 0.85rem, table cells are 0.82rem. The nav items at 0.8rem on a dark background with #e0e0e0 text are readable but tight. There's no visible type scale — sizes appear to be chosen independently.

**Fix:** Define a 3-step type scale (e.g., 0.75/0.875/1rem for product, 1.25rem for headings) and apply it consistently. Increase body minimum to 0.875rem.

### P2 — Stub pages communicate nothing useful

**Evidence:** The 4 stub pages (Pipeline Flow, Ad-Hoc, Panel, Onboarding) show "Contents TBD" with a brief description, but they don't indicate whether these are planned, in progress, or simply unfilled. The muted nav styling is correct, but landing on a blank page with no structure feels broken rather than "coming soon."

**Fix:** Give stub pages a minimal structural skeleton — even if the content is placeholder, show the page layout shape (left nav, content area, etc.) so the user understands the eventual information architecture.

---

## Recommended Next Modes

| Mode | Target | Why |
|---|---|---|
| `recolor` | Global | Resolve archetype/polarity color collision |
| `relayout` | Leaderboard | Swap scatter/table order |
| `interaction` | Global | Add focus rings, timeline click, chart click feedback |
| `typeset` | Global | Define and apply a type scale |
| `surface` | Stub pages | Give structural skeleton to Pipeline/Ad-Hoc/Panel/Onboarding |
