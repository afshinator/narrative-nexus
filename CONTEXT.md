# Narrative Nexus — Domain Glossary

Decisions here are grouped into two categories:
- **UI conventions** — rendering rules, component behavior, UX patterns (this file)
- **Visual design** — colors, fonts, spacing, component styles — see `docs/design-tokens.md`
- **Architecture decisions** — system structure, execution model, page boundaries — see `docs/adr/0001` through `0004`

---

## Investigate Page Purpose

The Investigate page is NOT a dead-end wall. It shows stripped-frame article text (output of the Forensic Extraction Agent) for sources that covered the queried story, even though full claim-lifecycle state (consensus-absorbed/unresolved) is unavailable for ad-hoc queries. The snapshot banner warning remains — but the page still delivers useful raw material to the analyst.

## Onboarding UX

The onboarding walkthrough uses a **shadcn Dialog** (not an accordion panel). It is a 5-step walkthrough defining all five vocabulary terms from Section 1 of the spec. Stored in localStorage via `onboardingComplete` in the zustand store. The spec (REQ-093–095) overrides earlier taste preferences about accordion-based intro panels.

**Behavior:**
- Auto-opens on first visit (when `onboardingComplete` is `false`)
- Last step has a **"Don't show again" checkbox**
  - Checked + dismissed → `onboardingComplete = true`, never auto-shows again
  - Not checked + dismissed → stays `false`, auto-shows again next visit
- Re-accessible anytime from the `?` icon in the nav bar (regardless of `onboardingComplete` state)
- No Settings page toggle — the `?` icon is sufficient
- **TODO:** Each vocabulary term needs a unique icon (e.g. from lucide-react). These icons will appear both in the glossary dialog and on the Sources page as visual clues connecting terms to data points.

## Demo Strategy — No Demo Mode

*See ADR-0002 for full rationale.*

There is no demo mode. The app always works the same way. Before demo day, a seed script (`scripts/seed-demo.py`) processes ~80 curated article URLs (4 stories × ~20 sources) from the last 90 days through the real pipeline. The database records have timestamps matching the original publication dates, so 7d/30d/90d resolution checkpoints fire correctly. The app reads from SQLite as normal — it has no idea it's being demonstrated.

## Timeline vs Cluster Report Split

*See ADR-0004 for full rationale.*

The Timeline page handles **temporal sequencing**: horizontal Day 0–90 axis, claim dots positioned at their first-appearance day, CONSENSUS_ABSORBED vertical absorption line, UNRESOLVED dots fading at day 90, echo-mimic connections (dashed lines to origin source).

The Cluster Report page handles **per-claim classification**: convergence type table (CROSS_SOURCE_CONVERGENT vs SELF_CONSISTENT), consensus summary, distortion matrix.

They are linked via click-through: clicking a claim dot on the Timeline highlights it in the Cluster Report. Convergence badges do NOT appear on timeline dots — that would overcrowd the visualization.

## Sources Page Archetype Filtering

Archetype filter pills on the Sources page use dim-mode filtering (not hide-mode). Non-selected sources reduce to low opacity (~0.15) while selected sources remain at full opacity. This preserves quadrant context and reference frame. "All" restores full opacity to all sources.

Both the scatter plot markers and the leaderboard table rows follow the same dim-mode rule — filtered-out table rows remain in the DOM at opacity 0.15 so cross-linked hover works bidirectionally regardless of filter state.

## Radar Chart Polarity Inversion

On the radar chart (6 axes, percentile-oriented, outward = favorable), three graded dimensions have "lower is better" polarity. Their percentiles are inverted before plotting so outward = favorable is always true:

| Dimension | Raw polarity | Radar render |
|-----------|-------------|--------------|
| R_val | Higher = better | As-is (outward = favorable) |
| R_speed | Lower = better | Inverted (100 - percentile) |
| R_frame | Lower = better | Inverted (100 - percentile) |
| R_edit | Lower = better | Inverted (100 - percentile) |
| R_orig | Trait (neutral) | As-is, neutral color |
| R_correct | Trait (neutral) | As-is, neutral color |

Raw values still display in tooltips and tables — only the radar polygon position gets inverted. The color for trait dimensions remains `--nn-slate` regardless of percentile.

## Container Architecture (App vs Worker Split)

*See ADR-0003 for full rationale.*

The worker container has a single responsibility: **sentence-transformer embeddings on AMD GPU via ROCm.** The app sends raw article text to the worker over HTTP and gets embeddings back. All other compute runs in the app container: scraping, Fireworks API calls, consensus math, reputation scoring, BERTopic clustering (CPU), SQLite, static file serving.

The worker is deliberately thin — a GPU-accelerated embedding service and nothing else. This satisfies the AMD GPU requirement cleanly while keeping the app container GPU-free. On the Pipeline Flow page, the worker renders as a distinct node labeled "AMD GPU Pod (sentence-transformers)".

## Multi-Vertical Claims

*See ADR-0001 for full rationale.*

When a story matches multiple verticals, claims are evaluated against **each vertical's consensus threshold independently**. A claim enters the consensus baseline for a vertical if it clears that vertical's threshold. On the UI, clusters display which vertical(s) they were classified under so the user knows which threshold governs the display.

## Archetype Badge Colors

Each source archetype gets a semantic badge color, distinct from the polarity color scale:

| Archetype | Badge Color | Rationale |
|-----------|-------------|-----------|
| EARLY_BREAKER | `--nn-navy` | High origination + high validation — the prized category |
| SELECTIVE_ACCURATE | `--nn-teal` | Selective but reliable when they report |
| NOISE_GENERATOR | `--nn-red` | High origination but nothing validates |
| CONSENSUS_FOLLOWER | `--nn-slate` | Safe but uninformative |
| null (unclassified) | `--nn-text-dim` | Not enough data yet |
