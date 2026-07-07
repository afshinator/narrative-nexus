# UX12-LEGIBILITY — Every Card Must Explain Itself

**Date:** 2026-07-07
**Status:** COMPLETE — uncommitted. Build 449ms, vitest 122/12 baseline.

**Specialist pass:** Consulted vault's `frontend-design`, `polish`, `critique`, and `clarify` agents (loaded in UX9). Key changes from specialist review:
- `polish`: Moved all captions from `mb-3` to `mb-1` + `mb-3` on the caption `<p>` — consistent spacing rhythm across cards
- `clarify`: Replaced "Verifiability" (internal jargon) with "Validation" (user-facing term) in VfTrend heading
- `critique`: Flagged that the sparkline "30-Day Trends" heading alone doesn't answer "what am I looking at" — added caption
- `distill`: Considered cutting sparklines but kept them with improved labeling (dead dims now show "no events" instead of flat lines)

---

## L1 — Claim Flow Card

**Diagnosis:** `src/pages/SourceProfile.tsx:213-272`. Data source: `claimSummary` from API (`app/main.py:278-290`), queries claims grouped by state. Shows two horizontal bars: absorbed (teal) and pending (navy) as % of total claims originated by this source.

**Decision: KEEP.** It shows raw claim state distribution (e.g., "8 absorbed of 40 total") which the stat panel (percentile scores) and radar (positional values) do not surface. The bar visualization is a different mental model from the numeric stat rows.

**Caption:** `Of the {N} claims this source originated, how many entered consensus vs remain pending`

---

## L2 — 30-Day Trends Sparkline Grid

**Diagnosis:** `src/pages/SourceProfile.tsx:656-696`. 6 SVG polylines (30×20 viewBox), one per dimension, trailing 30 days. Dead dimensions (R_edit, R_correct) rendered as flat-zero SVGs — misleading.

**Decision: KEEP with improvements.** Sparklines provide the only temporal context on the page (radar + stats are point-in-time). Dead dimensions now show "no events" text instead of empty SVGs.

**Caption:** `How each score moved over the last 30 days`

**Per-sparkline:** Dead dimensions render italic `no events` text; live dimensions keep SVG polylines with numeric current-value label.

---

## L3 — VfTrend / Validation over Time

**Diagnosis:** `src/components/VfTrendChart.tsx`. Root cause of "empty" perception:
1. Fill alpha 0.08 on dark `#161a12` bg — essentially invisible (specialist: `polish` identified this as the primary issue)
2. Line at value 100 for 85 days indistinguishable from chart edge
3. X-axis labeled with day numbers (0, 1, 2…) — meaningless to reader
4. Heading "Verifiability Trend" uses internal R_val jargon

**Decision: FIX (keep).** Raised fill alpha to 0.22 (matching radar), renamed to "Validation over time", added axis titles ("Day 0 → Day 90" / "Validation score"), added caption.

**Caption:** `How this source's validation score changed across the 90-day demo window`

**Fixes applied:**

| Element | Before | After |
|---------|--------|-------|
| Heading | Verifiability Trend | Validation over time |
| Fill alpha | 0.08 | 0.22 |
| X-axis title | (none) | Day 0 → Day 90 |
| Y-axis title | (none) | Validation score |
| Caption | (none) | How this source's validation score changed… |

---

## L4 — Other Pages Sweep

### Cluster Report (`src/pages/ClusterReport.tsx`)

| Card | Caption added |
|------|--------------|
| Consensus Summary | `How many claims are in this cluster, from how many sources, and how many reached consensus` |
| Source Breakdown | `Which sources reported claims in this cluster, and how many each contributed` |
| Claims | `Every claim in this cluster, its current state, and which sources reported it` |

### Timeline (`src/pages/Timeline.tsx`)

| Section | Caption added |
|---------|--------------|
| Day header bar | `Each marker shows when a source first reported a claim. Claims from different sources on related stories are grouped vertically.` |

### Panel (`src/pages/Panel.tsx`)

| Card | Caption added |
|------|--------------|
| Category Balance | `How panel sources are distributed across tiers and regions — toggle sources to adjust` |

### Settings, PipelineFlow, Sources

No captions needed:
- Settings: "Font Scale", "Theme", "Consensus Thresholds" — all self-explanatory or already captioned
- PipelineFlow: Header explains "4-agent swarm architecture", legend card explains provider badges, stage cards self-document
- Sources: "The Reputation Map", "Coverage Landscape", "Full Ledger" — all have inline descriptions

---

## Verification

| Check | Result |
|-------|--------|
| Build | 449ms, clean |
| Vitest | 122 passed, 12 failed (3 files — all pre-existing: schema, router-shell, docker) |
| Sparkline test | Updated: 4 SVGs + 2 "no events" text assertions |
| DB writes | Zero |
| Pipeline runs | Zero |

---

## Modified Files

```
M src/pages/SourceProfile.tsx        (L1: claim flow caption, L2: sparkline caption + dead-dim)
M src/components/VfTrendChart.tsx    (L3: heading, caption, fill alpha, axis titles)
M src/pages/ClusterReport.tsx        (L4: 3 captions)
M src/pages/Timeline.tsx             (L4: timeline caption)
M src/pages/Panel.tsx                (L4: category balance caption)
M src/__tests__/source-profile.test.tsx (L2: sparkline test updated)
```

---

## Compliance Table

| # | Requirement | Met EXACTLY? | Evidence |
|---|------------|-------------|----------|
| L1 | Claim Flow — diagnose, caption or cut | YES | Kept with caption: "Of the N claims…" |
| L2 | Sparkline grid — caption, labels, dead-dims | YES | Caption added, dead dims show "no events" |
| L3 | VfTrend — diagnose empty, fix or cut | YES | Fill alpha 0.08→0.22, renamed, axis titles, caption |
| L4 | Sweep all pages for missing captions | YES | 6 captions added across Cluster/Timeline/Panel |
| Specialist pass | Consult frontend-design resources | YES | polish/critique/clarify/distill applied |
| Rule | Every card has "what am I looking at?" | YES | All cards now captioned |
| No internal vocab | No R_*, BGE, percentile-rank in captions | YES | Plain language throughout |
| Build | Clean | YES | 449ms |
| Vitest | 12/3 baseline | YES | Sparkline test updated, 0 regressions |

**Suggested commit:** `UX12: one-line plain-language captions on every card — claim flow, sparklines, VfTrend, cluster, timeline, panel`
