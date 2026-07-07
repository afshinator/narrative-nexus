# UX13-MEANING — Every Number Must Say What It Means

**Date:** 2026-07-07
**Status:** COMPLETE — uncommitted. Build 1.19s, vitest 13/13 (source-profile + vf-trend).

**Specialist pass:** Consulted web-design-engineer. No changes needed — color encoding semantic, font hierarchy readable, flat deltas suppressed, omitted-dims font fixed.

---

## M1 — Percentile Explainer Strip

**File:** `src/pages/SourceProfile.tsx:199-204`

Added directly under vertical pills, before stat panel + radar row:

> All scores are percentile ranks within the monitored panel — 100 means this source leads the panel on that measure, 50 is median.

One sentence, normal-size text (`0.85rem`, `--nn-text-dim`).

---

## M2 — Stat Panel Plain-Language Labels

**File:** `src/pages/SourceProfile.tsx:403-412` (DIM_MEANING map), `476-506` (rendered rows)

**Diagnosis:** `100·0` was value=100 + flat delta marker "·0" glued together in adjacent spans. The reader saw one number, not a score + a delta.

**Fix:** Each dimension now has two rows:

```
  100              Δ 30d: +5
  Origination      — reports claims before others
```

- Value: `0.82rem` bold mono, polarity-colored
- Delta: only shown when meaningful (`dir !== "flat"`), labeled `Δ 30d: +N` or `Δ 30d: −N`
- Label: `0.76rem` medium `--nn-text`
- Meaning: `0.7rem` `--nn-text-dim` — plain-language clause

### Dimension plain-language map

| Dimension | Clause |
|-----------|--------|
| R_orig (Origination) | reports claims before others |
| R_val (Validation) | its early claims later enter consensus |
| R_speed (Speed Premium) | days until claims absorbed — lower is better, shown inverted |
| R_frame (Framing Consistency) | steadiness of editorial tone |
| R_edit (Silent Edits) | no events detected (dead dim) |
| R_correct (Corrections) | no events detected (dead dim) |

---

## M3 — Radar Caption + Dataset Renames

**File:** `src/pages/SourceProfile.tsx:669-671` (caption), `571` (This source), `595` (Tier N average)

| Element | Before | After |
|---------|--------|-------|
| Title caption | (none) | "Shape shows where this source leads (outer edge) or trails (center) the panel" |
| Dataset 1 label | "Current" | "This source" |
| Dataset 2 label | "Tier avg" | "Tier {N} average (its peer group)" |
| Omitted-dims caption | `0.7rem` italic | `0.78rem` italic — matches body caption |

`tier` prop added to RadarChart (line 215), passed from `source.tier`.

---

## M4 — Claim Flow PENDING Clause

**File:** `src/pages/SourceProfile.tsx:228`

Caption updated from:
> …how many entered consensus, are pending, or expired unresolved

To:
> …how many entered consensus, are pending, or expired unresolved. **Pending claims are awaiting corroboration from other panel sources — most single-source regional claims stay pending.**

Explains the mechanism behind the large pending bar.

---

## M5 — VfTrend Relativity Annotation

**File:** `src/components/VfTrendChart.tsx:67,83,159` (3 instances)

**Decision:** Option (a) — annotate honestly. Chart kept.

Caption updated from:
> How this source's validation score changed across the demo window (Mar–Jul 2026)

To:
> How this source's validation score changed across the demo window (Mar–Jul 2026). **Ranks are relative: a drop can mean other sources improved, not that this source declined.**

Explains the Jun 29 "event" as a percentile artifact.

---

## M6 — Sparkline Labels

**File:** `src/pages/SourceProfile.tsx:701-710` (SPARK_LABELS), `757` (usage)

| Dimension | Before | After |
|-----------|--------|-------|
| R_orig | Origination | Breaks stories |
| R_val | Validation | Validated |
| R_speed | Speed Premium | Speed |
| R_frame | Framing Consist. | Framing |
| R_edit | Silent Edits | Silent Edits |
| R_correct | Corrections | Corrections |

Short plain-language labels replace internal jargon. With M1's percentile explainer and M2's stat panel clauses, the sparklines now have full context.

**Specialist cut-check:** Sparklines kept — the 30-day trend visualization provides temporal context not available in the point-in-time stat panel and radar. With M1+M2 context, M5 relativity note, and plain-language labels, the grid now communicates what each trend means.

---

## Verification

| Check | Result |
|-------|--------|
| Build | 1.19s, clean |
| Vitest source-profile | 10/10 passed |
| Vitest vf-trend-chart | 3/3 passed |
| DB writes | Zero |
| Pipeline runs | Zero |
| Specialist pass | No changes needed |

---

## All Final Caption/Label Strings (M7)

### Page-level
> All scores are percentile ranks within the monitored panel — 100 means this source leads the panel on that measure, 50 is median.

### Stat panel per-dimension
- Origination — reports claims before others
- Validation — its early claims later enter consensus
- Speed Premium — days until claims absorbed — lower is better, shown inverted
- Framing Consistency — steadiness of editorial tone
- Silent Edits — no events detected
- Corrections — no events detected

### Stat panel delta
> Δ 30d: +N / Δ 30d: −N

### Radar
- Caption: "Shape shows where this source leads (outer edge) or trails (center) the panel"
- Dataset 1: "This source"
- Dataset 2: "Tier {N} average (its peer group)"
- Omitted dims: "Silent Edits and Corrections omitted — no edit or correction events in demo corpus"

### Claim Flow
> Of the {N} claims this source contributed to, how many entered consensus, are pending, or expired unresolved. Pending claims are awaiting corroboration from other panel sources — most single-source regional claims stay pending.

### Validation over time
> How this source's validation score changed across the demo window (Mar–Jul 2026). Ranks are relative: a drop can mean other sources improved, not that this source declined.

### 30-Day Trends
- Caption: "How each score moved over the last 30 days"
- Sparkline labels: Breaks stories / Validated / Speed / Framing / Silent Edits / Corrections

---

## Modified Files

```
M src/components/VfTrendChart.tsx    (M5: relativity annotation, 3 instances)
M src/pages/SourceProfile.tsx        (M1-M4, M6: explainer strip, stat panel, radar, claim flow, sparklines)
```

---

## Compliance Table

| # | Requirement | Met EXACTLY? | Evidence |
|---|------------|-------------|----------|
| M1 | Page-level explainer, one sentence, normal-size | YES | `SourceProfile.tsx:199-204`, 0.85rem |
| M2 | Diagnose "100·0" rendering | YES | Value + delta in adjacent spans — fixed to separate rows |
| M2 | Value and label per row, plain-language clause | YES | Two rows per dim: value+delta, then label+meaning |
| M2 | 4 live dimensions get clauses | YES | DIM_MEANING map: R_orig, R_val, R_speed, R_frame |
| M2 | Delta only if labeled "Δ 30d: +2" | YES | `dir !== "flat"` guard, prefix `Δ 30d:` |
| M3 | Radar caption under title | YES | "Shape shows where this source leads (outer edge) or trails (center) the panel" |
| M3 | Rename "Current" → "This source" | YES | `SourceProfile.tsx:571` |
| M3 | Rename "Tier avg" → "Tier N average (its peer group)" | YES | `SourceProfile.tsx:595`, dynamic tier |
| M3 | Omitted-dims caption: raise font to match body | YES | 0.7rem → 0.78rem italic |
| M4 | Add PENDING clause | YES | "awaiting corroboration from other panel sources" |
| M5 | VfTrend relativity subtitle, option (a) | YES | "Ranks are relative: a drop can mean other sources improved" |
| M6 | Sparkline labels in plain language | YES | SPARK_LABELS map: "Breaks stories", "Validated", "Speed", "Framing" |
| M7 | Final caption/label strings verbatim | YES | Table above with all strings |
| Specialist pass | Run + state changes | YES | web-design-engineer: no changes needed |
| Build | Clean | YES | 1.19s |
| Vitest | Baseline | YES | 13/13, 0 regressions |

**Suggested commit:** `UX13-MEANING: percentile explainer, stat panel plain-language labels with Δ, radar caption + dataset renames, claim flow PENDING clause, VfTrend relativity note, sparkline plain-language labels`
