# UX10-DIAG — Source Profile Time-Machine Reality Check

**Date:** 2026-07-06
**Status:** DIAGNOSTIC ONLY — no code changes, no commits

---

## D1 — theguardian.com, Geopolitics, All 6 Dimensions

Source ID 5, vertical=geopolitics, 2026-03-03 → 2026-07-03 (122 snapshots, ~daily).

**Query:**
```sql
SELECT date, r_orig, r_val, r_speed, r_frame, r_edit, r_correct
FROM snapshots
WHERE source_id=5 AND vertical='geopolitics'
ORDER BY date;
```

**~10-day sample (plus inflection points):**

| Date | R_orig | R_val | R_speed | R_frame | R_edit | R_correct |
|------|--------|-------|---------|---------|--------|-----------|
| 2026-03-03 | 100 | — | — | — | 0 | 0 |
| 2026-03-10 | 86 | — | 100 | — | 0 | 0 |
| 2026-03-13 | 100 | — | 100 | — | 0 | 0 |
| 2026-03-16 | 100 | 100 | 100 | — | 0 | 0 |
| 2026-03-23 | 100 | 100 | 100 | — | 0 | 0 |
| 2026-04-03 | 100 | 100 | 100 | — | 0 | 0 |
| 2026-04-07 | 86 | 100 | 100 | — | 0 | 0 |
| 2026-04-16 | 88 | 100 | 100 | — | 0 | 0 |
| 2026-04-27 | 88 | 100 | 100 | 100 | 0 | 0 |
| 2026-05-07 | 88 | 100 | 100 | 100 | 0 | 0 |
| 2026-05-17 | 88 | 100 | 100 | 100 | 0 | 0 |
| 2026-05-27 | 88 | 100 | 100 | 100 | 0 | 0 |
| 2026-06-06 | 88 | 100 | 100 | 100 | 0 | 0 |
| 2026-06-16 | 88 | 100 | 100 | 100 | 0 | 0 |
| 2026-06-24 | 95 | 100 | 17 | 100 | 0 | 0 |
| 2026-06-25 | 96 | 100 | 19 | 60 | 0 | 0 |
| 2026-06-30 | 100 | 15 | 23 | 60 | 0 | 0 |
| 2026-07-03 | 100 | 28 | 23 | 60 | 0 | 0 |

**Min/Max/First/Last per dimension:**

| Dim | First non-null | Last value | Min | Max | Range |
|-----|---------------|------------|-----|-----|-------|
| R_orig | 100 (Mar 3) | 100 (Jul 3) | 86 | 100 | 14 pts |
| R_val | 100 (Mar 16) | 28 (Jul 3) | 15 | 100 | **85 pts** |
| R_speed | 100 (Mar 10) | 23 (Jul 3) | 17 | 100 | **83 pts** |
| R_frame | 100 (Apr 27) | 60 (Jul 3) | 60 | 100 | 40 pts |
| R_edit | 0 (Mar 3) | 0 (Jul 3) | 0 | 0 | 0 |
| R_correct | 0 (Mar 3) | 0 (Jul 3) | 0 | 0 | 0 |

---

## D2 — reuters.com, Geopolitics

Source ID 1. Same query.

**~10-day sample:**

| Date | R_orig | R_val | R_speed | R_frame | R_edit | R_correct |
|------|--------|-------|---------|---------|--------|-----------|
| 2026-03-03 | — | — | — | — | 0 | 0 |
| 2026-03-10 | 86 | — | — | — | 0 | 0 |
| 2026-03-16 | 86 | 0 | — | — | 0 | 0 |
| 2026-03-24 | 71 | 0 | — | — | 0 | 0 |
| 2026-04-07 | 71 | 0 | — | — | 0 | 0 |
| 2026-04-16 | 62 | 0 | — | — | 0 | 0 |
| 2026-04-27 | 62 | 0 | — | — | 0 | 0 |
| 2026-05-17 | 62 | 0 | — | — | 0 | 0 |
| 2026-06-16 | 62 | 0 | — | — | 0 | 0 |
| 2026-06-19 | 50 | 0 | — | — | 0 | 0 |
| 2026-06-23 | 75 | 0 | — | 0 | 0 | 0 |
| 2026-06-25 | 58 | 0 | — | 20 | 0 | 0 |
| 2026-06-26 | 36 | 0 | — | 0 | 0 | 0 |
| 2026-06-29 | 23 | 0 | — | 0 | 0 | 0 |
| 2026-07-03 | 23 | 0 | — | 0 | 0 | 0 |

**Min/Max:** R_orig 23–86, R_val flat 0, R_speed all NULL, R_frame 0–20, R_edit/R_correct flat 0.

---

## D3 — Guardian Movement Analysis

Movements >2 pts vs prior snapshot:

| Date | Dim | Change | From→To | Determinable cause |
|------|-----|--------|---------|-------------------|
| Mar 10 | R_orig | −14 | 100→86 | UNKNOWN — panel composition shift? No claim absorbed on this date (first absorption Mar 13 per claim_sources) |
| Mar 10 | R_speed | NULL→100 | —→100 | First speed data appears. Cause UNKNOWN. |
| Mar 13 | R_orig | +14 | 86→100 | CONFOUNDED — 1 claim with first_seen_at=Mar 13 absorbed, but R_orig is a percentile rank; another source likely moved |
| Mar 16 | R_val | NULL→100 | —→100 | First validation data. Cause: claims began entering consensus. 7 of 8 absorbed claims have NULL first_seen_at — dates UNKNOWN |
| Apr 7 | R_orig | −14 | 100→86 | UNKNOWN — no new claims on this date |
| Apr 16 | R_orig | +2 | 86→88 | UNKNOWN |
| Apr 27 | R_frame | NULL→100 | —→100 | First framing consistency data. R_frame = stddev percentile — cause UNKNOWN |
| Jun 24 | R_orig | +7 | 88→95 | CONFOUNDED — other sources shifting in percentile rank |
| Jun 24 | R_speed | −83 | 100→17 | CONFOUNDED — large percentile shift, other panel sources' speed changed |
| Jun 25 | R_frame | −40 | 100→60 | CONFOUNDED — percentile rank shift from other sources |
| Jun 26 | R_frame | +40 | 60→100 | CONFOUNDED — percentile rank shift back |
| Jun 27 | R_frame | −9 | 100→91 | CONFOUNDED |
| Jun 28 | R_frame | −16 | 91→75 | CONFOUNDED |
| Jun 29 | R_frame | −15 | 75→60 | CONFOUNDED |
| Jun 30 | R_val | −85 | 100→15 | **CONFOUNDED** — R_val is a percentile rank. Guardian's raw validation didn't drop; OTHER sources moved up, pushing Guardian's percentile down. The 7 NULL-date claims may have been absorbed earlier than this date, but we can't determine when. |
| Jul 1 | R_val | +6 | 15→21 | CONFOUNDED — percentile shift |
| Jul 3 | R_val | +8 | 21→28 | CONFOUNDED — percentile shift |

**Key finding:** Nearly all movements in the last 10 days of the timeline (Jun 24–Jul 3) are CONFOUNDED — they're percentile-rank oscillations from OTHER panel sources shifting, not theguardian.com itself changing. The R_val crash from 100→15 on Jun 30 is almost certainly NOT theguardian getting worse — it's the rest of the panel getting better (more claims absorbed across other sources), pushing theguardian's percentile down.

**Event timeline hardcoded:** All events (CLAIM_ABSORBED, SILENT_EDIT) map to day 90 regardless of actual date. `app/main.py:293-296`: "All edits/absorptions on 2026-06-30, after snapshots end at 2026-06-28. Map to day 90." This is a deliberate ponytail — the demo DB has no dated event data.

---

## D4 — Radar Legibility in Dark Mode

**Radar chart color values** (`src/pages/SourceProfile.tsx`):

| Element | CSS var | Dark mode value | Light mode value | File:line |
|---------|---------|-----------------|------------------|-----------|
| Tick labels | `--nn-text-dim` | `#738567` | `#717a68` | :614 |
| Point labels (axis names) | `--nn-text-dim` | `#738567` | `#717a68` | :618 |
| Grid lines | `--nn-border` | `#2c3625` | `#d0d5c7` | :621 |
| Angle lines | `--nn-border` | `#2c3625` | `#d0d5c7` | :622 |
| Legend labels | `--nn-text-dim` | `#738567` | `#717a68` | :629 |
| Chart background | `--nn-surface` | `#161a12` | `#f7f8f5` | :653 |
| Teal area fill | hardcoded | `rgba(94,189,142,0.13)` | hardcoded | :567 |
| Teal border | `--nn-teal` | `#5ebd8e` | `#276b52` | :566 |

**Contrast check (dark mode):**
- `#738567` text on `#161a12` background → contrast ratio ~4.5:1 (passes WCAG AA for normal text, marginal for small text)
- Tick labels at 9px font, point labels at 10px mono — both meet WCAG AA at this ratio
- The axis labels ("Origination," "Validation," etc.) are rendered by Chart.js's `pointLabels` — NOT standard HTML text. Chart.js renders them on a canvas with `fillText()`. The color `var(--nn-text-dim)` resolves to `#738567` which on the dark `#161a12` background is **legible but low-contrast** — it reads as "dim text" against a near-black card.

**Why it's hard to read:** Not a contrast failure per se, but `#738567` is a muted olive-gray on a near-black `#161a12` background. At 10px mono font, the text lacks visual punch. The issue is perceptual, not technical — the radar text intentionally uses the "dim" color from the design system, which was tuned for light-mode readability (`#717a68` on `#f7f8f5`) and doesn't carry the same presence in dark mode.

**Hardcoded fill color** (`rgba(94,189,142,0.13)` at line 567): The alpha value 0.13 was chosen for light mode. On dark `#161a12`, it renders as a very subtle green tint — almost invisible. No equivalent dark-mode override exists.

---

## D5 — Profile Page Layout Inventory (Top to Bottom)

From `src/pages/SourceProfile.tsx` return JSX (line 254):

| # | Component | File:line | Description |
|---|-----------|-----------|-------------|
| 1 | `<h1>` source name | :258-259 | "The Guardian" heading |
| 2 | Tier + domain line | :262-264 | "Tier 3 · theguardian.com" |
| 3 | Cluster link | :265-269 | "View cluster → US-Iran War…" deep-link |
| 4 | `<VerticalPills>` | :272 | Geopolitics selector (pill buttons) |
| 5 | Grid row: `<StatPanel>` + `<RadarChart>` | :275-287 | Side-by-side on lg screens |
| 5a | — StatPanel: archetype badge, 6 dim stat rows with deltas | :442-531 | Left column, 280px |
| 5b | — RadarChart: radar with 3 datasets (current/baseline/tier avg) | :533-668 | Right column, fills remaining space |
| 6 | `<SparklineGrid>` | :290-294 | 6 sparklines, one per dimension |
| 7 | `<VfTrendChart>` | :297 | Validation frequency trend line chart |
| 8 | Claim Flow card | :300-359 | Absorbed/pending bar chart + counts |
| 9 | **`<DayScrubber>`** ← **PLAY CONTROL** | :362-368 | **Slider + Play/Pause button + event markers + event card** |
| 10 | Silent Edit Log table | :371-435 | Article edit detection log |

**Play control position:** The DayScrubber sits at position 9 of 10 — BELOW the radar, stat panel, sparklines, VfTrend, and claim flow. When the user presses Play, the timed animation advances `currentDay` from 0→90, interpolating between snapshots. The radar, stat panel, sparklines, and VfTrend all re-render based on `currentDay`. But the user has to scroll past 4 major visualization sections to even FIND the play button.

---

## Key Findings

1. **Guardian moves mostly in the last 10 days, and nearly all movements are CONFOUNDED** — they're percentile-rank oscillations from other sources shifting, not theguardian itself changing. The R_val crash from 100→15 is misleading: it's the PANEL getting better, not theguardian getting worse.

2. **R_edit and R_correct are flat 0 for ALL sources, ALL dates** — two of six radar dimensions are dead data.

3. **R_speed is NULL for reuters entirely** — only 4 of 6 dimensions have data for some sources.

4. **Events are hardcoded to day 90** — the timeline scrubber shows one event blob at the far right. No dated events exist in the demo DB. Pressing Play animates through 90 days of interpolated percentile noise with no narrative.

5. **Radar text uses `--nn-text-dim`** — legible but visually recessive in dark mode. The teal fill is hardcoded with a light-mode alpha value, rendering nearly invisible on dark backgrounds.

6. **Play button is at the BOTTOM of the page** — user has to scroll past 4 visualization sections to find it, then watch as ALL of them animate simultaneously with no clear indication of WHAT changed or WHY.
