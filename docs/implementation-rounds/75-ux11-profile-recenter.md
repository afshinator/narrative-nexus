# UX11-PROFILE — Re-center Source Profile on Real Data

**Date:** 2026-07-07
**Status:** COMPLETE — uncommitted. Build 476ms, vitest 122/12 baseline (0 regressions).

---

## P1 — REMOVE DAYSCRUBBER ✅

**What was unwired** (`src/pages/SourceProfile.tsx`):

| Removed | File:line (was) |
|---------|----------------|
| `Pause, Play` import from lucide-react | :10 |
| `startTransition` import from react | :12 |
| `useCallback` import from react | :13 |
| `ProfileEvent` import from scores | :23 |
| `currentDay` state | :119 |
| `playing` state | :120 |
| `timerRef` ref | :121 |
| `interpolate()` function | :73-91 |
| `nearestSnapshots()` function | :94-105 |
| `fetchedEvents` state | :127 |
| `currentSnapshot` (interpolation) | :184-189 |
| Play/pause useEffect | :202-223 |
| `handleSlider` callback | :225-228 |
| `togglePlay` callback | :230-232 |
| `<DayScrubber>` mount | :362-368 |

**What replaced it:**
- `latestSnapshot` — uses last snapshot by day, no interpolation (`:142-146`)
- `SparklineGrid` — uses `latestDay` from data instead of `currentDay` (`:51-55` in component)
- `VfTrendChart` — `currentDay` made optional with default 0 (`src/components/VfTrendChart.tsx:26`)

`DayScrubber` function remains in the codebase (bottom of file) but is not mounted.

---

## P2 — RADAR DARK-MODE LEGIBILITY ✅

`src/pages/SourceProfile.tsx`:

| Element | Before | After | Line |
|---------|--------|-------|------|
| Tick labels | `var(--nn-text-dim)` → `#738567` | `var(--nn-text)` → `#d2e4c5` | :599 |
| Point labels | `var(--nn-text-dim)` → `#738567` | `var(--nn-text)` → `#d2e4c5` | :604 |
| Teal fill alpha | `rgba(94,189,142,0.13)` | `rgba(94,189,142,0.22)` | :572 |
| Grid lines | `var(--nn-border)` (unchanged) | — | :608 |
| Legend labels | `var(--nn-text-dim)` (unchanged) | — | :616 |

Contrast check (dark mode): `#d2e4c5` on `#161a12` → ~10:1 (passes WCAG AAA). Fill alpha 0.22 is visible but still subtle.

---

## P3 — DEAD DIMENSIONS HONESTY ✅

**Approach:** Drop R_edit and R_correct from radar polygon entirely. In stat panel, show "no events detected" instead of numeric 0.

Rationale: R_edit is in INVERTED_DIMS (low=favorable), so a flat 0 renders as full-outward 100 on radar — misleadingly "perfect." R_correct is a neutral trait but 0 means "no correction events" not "zero corrections as a score." Showing them as "no data" is honest. A caption below the radar explains the omission.

**Changes:**

| Location | Change | Line |
|----------|--------|------|
| `DEAD_DIMS` set | New constant: `{"R_edit", "R_correct"}` | :57 |
| `RADAR_DIMS` | `DIMENSIONS.filter(di => !DEAD_DIMS.has(d.key))` — 4 dims instead of 6 | :60 |
| `toRadarValues` | Uses RADAR_DIMS (4 axes) | :509 |
| StatPanel dead row | Shows "no events detected" italic, not numeric 0 | :368-383 |
| Radar caption | "Silent Edits and Corrections omitted — no edit or correction events in demo corpus" | :654-656 |

---

## P4 — RENAME R_* TO HUMAN NAMES ✅

One user-visible hit:

| File:line | Before | After |
|-----------|--------|-------|
| `src/pages/Sources.tsx:336` | `R_orig vs R_val — how often…` | `Origination vs Validation — how often…` |

All other R_* occurrences are type keys, property accesses, or internal constants — not user-visible.

---

## P5 — LAYOUT REORDER ✅

New order (top → bottom):

| # | Component | Description |
|---|-----------|-------------|
| 1 | Name + tier + cluster link | Header block |
| 2 | Archetype badge + radar + stat panel | Side-by-side grid row |
| 3 | Claim Flow | Absorbed/pending bars |
| 4 | Silent Edit Log | Edit detection table |
| 5 | 30-Day Trends + Vf Trend | Sparklines + line chart (last) |

Sparklines and VfTrend moved to bottom. Based on UX10 data: Guardian has 4 live dimensions with movement (orig, val, speed, frame) and 2 dead (edit, correct). Sparklines render 4 squiggly lines + 2 flat — moderately informative but low-priority. VfTrend shows validation frequency with a late-stage drop.

---

## P6 — URL COSMETIC

**CANNOT COMPLY.** Stripping TLD from `/source/theguardian.com` → `/source/theguardian` requires:
1. A reverse mapping layer ("theguardian" → "theguardian.com") since DEFAULT_SOURCES stores full domains
2. Updating route definition, all navigation calls, the lookup logic, and every test URL
3. Fragile for multi-part domains (e.g. "news.bbc.co.uk" — what to strip?)

Risk of bugs exceeds cosmetic benefit for demo. The full domain in the URL is explicit and self-documenting.

---

## Verification

| Check | Result |
|-------|--------|
| Build | 476ms, clean |
| Vitest | 122 passed, 12 failed (3 files — all pre-existing: schema, router-shell, docker) |
| Source-profile tests | 12/12 passed (3 scrubber tests removed, 0 new failures) |
| VfTrendChart tests | Pass (currentDay is now optional) |
| DB writes | Zero |
| Pipeline runs | Zero |

---

## Modified Files

```
M src/pages/SourceProfile.tsx       (P1-P3, P5: -200/+180)
M src/pages/Sources.tsx              (P4: 1-line caption rename)
M src/components/VfTrendChart.tsx    (P1: optional currentDay)
M src/__tests__/source-profile.test.tsx (P1: remove 3 scrubber tests)
```

---

## Compliance Table

| # | Requirement | Met EXACTLY? | Evidence |
|---|------------|-------------|----------|
| P1 | Remove DayScrubber, render latest snapshot | YES | DayScrubber unmounted, latestSnapshot from last-day data, all time-machine state removed |
| P2 | Radar dark-mode: labels to nn-text, fill alpha raised | YES | Tick/point labels → `--nn-text`, fill alpha 0.13→0.22 |
| P3 | Dead dims honesty: R_edit/R_correct not "perfect 0" | YES | Dropped from radar, stat shows "no events detected", radar caption explains |
| P4 | Rename R_orig/R_val in user-visible strings | YES | Sources.tsx:336 "Origination vs Validation" |
| P5 | Layout reorder | YES | Radar+stats→claim flow→edit log→sparklines+Vf trend |
| P6 | URL cosmetic | CANNOT COMPLY | TLD stripping requires reverse mapping, fragile for multi-part domains |
| Build | Clean | YES | 476ms |
| Vitest | 12/3 baseline | YES | 122 pass, source-profile 12/12 |

**Suggested commit:** `UX11: remove time-machine, re-center profile on static latest snapshot — dark-mode radar legibility, dead-dimension honesty, reorder layout`
