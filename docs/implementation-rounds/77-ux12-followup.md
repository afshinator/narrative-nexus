# UX12-FOLLOWUP — VfTrend Dates + Claim Flow Unresolved Bar

**Date:** 2026-07-07
**Status:** COMPLETE — uncommitted. Build 450ms, vitest 122/12/4 baseline.

---

## F1 — VfTrend Calendar Dates

**Diagnosis:** VfTrendChart used sequential day-index labels (0, 1, 2…), meaningless to the reader. Caption said "90-day demo window" but actual span is 2026-03-03 → 2026-07-03 = 123 days. X-axis title "Day 0 → Day 90" was factually wrong.

**What the chart actually plots:** All available snapshots for the source+vertical (up to 180, per backend LIMIT). For source 1 (reuters) geopolitics: 123 snapshots, all passed to VfTrendChart `snapshots` prop via `filtered` in SourceProfile.tsx:350.

**Fixes:**

| File | Change |
|------|--------|
| `app/main.py:224` | Added `"date": row["date"]` to snapshot response dict (date already in SELECT) |
| `src/data/scores.ts:20-21` | Added `date: string` to DailySnapshot interface |
| `src/components/VfTrendChart.tsx:24-27` | `fmtDate()` helper: ISO "2026-03-03" → "Mar 3" |
| `src/components/VfTrendChart.tsx:67` | Labels: `snapshots.map(s => fmtDate(s.date))` (was `String(s.day)`) |
| `src/components/VfTrendChart.tsx:89-98` | Removed x-axis `title` block (was "Day 0 → Day 90") |
| `src/components/VfTrendChart.tsx:40,57,133` | Caption: "demo window (Mar–Jul 2026)" (was "90-day demo window") |
| `src/__tests__/vf-trend-chart.test.tsx:18` | `date: "2026-03-03"` added to `makeSnapshot` |

---

## F2 — UNRESOLVED Claims Bar

**Diagnosis:** Claim Flow card only rendered two bars (Absorbed teal, Pending navy). DB has 11 UNRESOLVED claims across 3 sources (reuters: 3, apnews: 4, theguardian: 4). The card's `total` included unresolved claims but no bar displayed them — bars didn't sum to total. Caption "entered consensus vs remain pending" omitted the third state.

**Fix:** Added third bar (slate, `var(--nn-slate)`) conditional on `unresolved > 0`.

| File | Change |
|------|--------|
| `app/main.py:284` | `claim_summary` now `{"total":0, "absorbed":0, "pending":0, "unresolved":0}` |
| `app/main.py:292-293` | `elif r["state"] == "UNRESOLVED": claim_summary["unresolved"] = r["cnt"]` |
| `src/pages/SourceProfile.tsx:37` | `ClaimSummary` interface: +`unresolved: number` |
| `src/pages/SourceProfile.tsx:92,121` | Defaults + fallback: +`unresolved: 0` |
| `src/pages/SourceProfile.tsx:221` | Caption: "...entered consensus, are pending, or expired unresolved" |
| `src/pages/SourceProfile.tsx:274-294` | Third bar: slate color, `unresolved > 0` guard |
| `src/pages/SourceProfile.tsx:270` | "originated" → "contributed to" (matches `claim_sources` JOIN, not `originating_source_id`) |

---

## Data Verification

```
Snapshots for source 1 geopolitics: 123
First: 2026-03-03, Last: 2026-07-03

Claim summary for source 1 (reuters):
  CONSENSUS_ABSORBED: 1
  PENDING: 3
  UNRESOLVED: 3
```

---

## Verification

| Check | Result |
|-------|--------|
| Build | 450ms, clean |
| Vitest | 122 passed, 12 failed (3 files: schema, router-shell, docker — all pre-existing), 4 skipped |
| VfTrend test | 3/3 passed |
| Python import | OK (app.main routes verified) |
| DB writes | Zero |
| Pipeline runs | Zero |

---

## Modified Files

```
M app/main.py                          (F1: +date in snapshot; F2: +unresolved in claim_summary)
M src/data/scores.ts                   (F1: +date to DailySnapshot)
M src/components/VfTrendChart.tsx      (F1: fmtDate, labels, caption, removed x-axis title)
M src/pages/SourceProfile.tsx          (F2: +unresolved bar, caption, "contributed to")
M src/__tests__/vf-trend-chart.test.tsx (F1: +date to makeSnapshot)
```

---

## Compliance Table

| # | Requirement | Met EXACTLY? | Evidence |
|---|------------|-------------|----------|
| F1 | Replace day-number labels with calendar dates | YES | `fmtDate("2026-03-03")` → "Mar 3"; Chart.js auto-selects ticks |
| F1 | Remove "Day 0 → Day 90" x-axis title | YES | `scales.x.title` block deleted |
| F1 | Caption: "Mar–Jul 2026" across demo window | YES | 3 caption strings updated |
| F1 | Confirm what chart plots: all or subset? | YES | All 123 snapshots passed; backend limits to 180 |
| F2 | Does card render UNRESOLVED? file:line | YES (it didn't → now does) | `SourceProfile.tsx:274-294` — slate bar, `unresolved > 0` guard |
| F2 | Caption matches what chart shows | YES | "entered consensus, are pending, or expired unresolved" |
| Build | Clean | YES | 450ms |
| Vitest | Baseline unchanged | YES | 122/12/4 |

**Suggested commit:** `UX12-followup: VfTrend x-axis → calendar dates, Claim Flow +unresolved bar (slate), "originated" → "contributed to"`
