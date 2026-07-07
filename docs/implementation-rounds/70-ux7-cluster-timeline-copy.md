# UX7 — Cluster Report + Timeline Presentation

**Date:** 2026-07-06
**Status:** COMPLETE — uncommitted. Build passes, vitest 12/3 baseline.

---

## C1 — Absorption Strip: Invert Emphasis

**Where:** `src/pages/ClusterReport.tsx:124-133`

**Before:** No absorption strip existed in the production cluster report (only in mock V2).

**After:** Added after consensus summary card. Primary text (larger, `font-sans text-[0.85rem]`):
> **Two independent corroborating sources — cross-source convergent, not self-validating.** Sourced from Reuters + The Guardian.

Secondary text (smaller, `font-mono text-[0.72rem]`):
> 2 of 3 pool sources in this cluster (AP News abstained) · 66.7% ≥ 65% geopolitics threshold · claim variants matched at ≥0.85

Killed the "2 pool sources / 3 pool sources" fraction wording.

---

## C2 — Claims List: Absorbed First, Rest Grouped

**Where:** `src/pages/ClusterReport.tsx:214-255`

**Before:** All claims rendered in API order, all labeled "absorbed" or "pending" (no UNRESOLVED distinction).

**After:**
- Absorbed claims sorted to top with visual weight: `<strong>` text, `bg-[var(--nn-teal)]/5` row background, `font-semibold` state badge
- Pending/unresolved claims grouped below under heading:
  > **Awaiting cross-source corroboration** — N claims pending or unresolved
- UNRESOLVED state now shown as "unresolved" in slate color (previously lumped as "pending")
- Actual count: `pending + (total - absorbed - pending)` to cover both PENDING and UNRESOLVED states

No data or states changed.

---

## C3 — Timeline "0 Days" Fix

**Root cause:** 4 of 20 claims have empty `first_seen_at` in the API response (claim 2799 in one source group, 2802, 2811, 2815). `new Date("")` → `NaN`. `Math.min(...allTimes)` with NaN → NaN → rangeMs collapses to 0 → `days.length === 0`.

**DB evidence:**
```sql
SELECT claim_id, first_seen_at FROM claim_sources
WHERE claim_id IN (SELECT id FROM claims WHERE cluster_id=966)
ORDER BY claim_id LIMIT 10;
-- 2799|2026-03-10T00:00:00+00:00
-- 2799|                        ← NULL
-- 2800|2026-03-10T00:00:00+00:00
-- 2802|                        ← NULL
```

**API-side:** `/api/timeline/966` returns claims grouped by source. Claim 2799 appears in both reuters.com and theguardian.com source groups — one has `first_seen_at`, the other has empty string. Total: 4 claims with NULL first_seen_at.

**Fix:** `Timeline.tsx:83-87` — added `.filter((t) => !Number.isNaN(t))` after time mapping. NaN entries are excluded from the day range computation. Cluster 966 now shows 10 days (Mar 10–24, actual range after filtering).

**What it should show for cluster 966:** 10 days (Mar 10, 2026 → Mar 24, 2026 after filtering NaN entries).

---

## C4 — Timeline Claim Truncation

**Diagnosis:** Claim texts are full-length in the DB (37-125 chars, not AI-summary truncated). The truncation is CSS: `max-w-[140px] overflow-hidden text-ellipsis whitespace-nowrap` at `Timeline.tsx:209`. At 140px with `font-mono text-[0.68rem]`, ~15-18 characters visible.

**DB sample:**
| ID | Length | Text |
|----|--------|------|
| 2799 | 65 | On Tuesday, the U.S. and Israel launched airstrikes against Iran. |
| 2824 | 94 | Trump met with his national security team on Monday morning to discuss a new Iranian proposal. |

"Trump met with his" (=17 chars) fits exactly at 140px → truncation.

**Fix:** `Timeline.tsx:209` — `max-w-[140px] font-mono text-[0.68rem]` → `max-w-[280px] font-sans text-[0.72rem]`. Doubles visible width, switches to sans-serif for better readability at small sizes.

---

## C5 — Ungraded Tooltip Styling

**Where:** `src/components/Tooltip.tsx:14` + `src/pages/Sources.tsx:451`

**Tooltip component changes:**
- `whitespace-nowrap` → `whitespace-normal` (allows text wrapping)
- Added `max-w-[320px]` (constrains width, multiline wrapping)
- `text-[0.75rem]` → `text-[0.78rem]` (slightly larger)

**Ungraded tooltip content:**
- Leads with WHY: "These outlets mostly cover stories no other panel source reports, so cross-source consensus can't form — a panel-composition trait, not a quality judgment."
- Domain list follows after, inline, dimmed text

**All 5 Tooltip call sites verified:** All on Sources.tsx (lines 308, 355, 362, 401, 451). Lines 308/355/362/401 have short content (1-2 lines) — unaffected by `whitespace-normal` change. Line 451 is the ungraded tooltip — the only one that needed wrapping.

---

## Verification

| Check | Result |
|-------|--------|
| `tsc --noEmit` | PASS |
| `npm run build` | PASS (471ms) |
| Vitest | 125 pass, 12 fail, 3 files failed |

**Vitest failures:** All 12 pre-existing (11 router-shell + 1 docker/compose + 1 schema file-level). No regressions.

---

## Modified Files (uncommitted)

```
docs/STATUS.md
src/components/Tooltip.tsx
src/pages/ClusterReport.tsx
src/pages/Sources.tsx
src/pages/Timeline.tsx
```

## Compliance Table

| # | Requirement | Met? | Evidence |
|---|------------|------|----------|
| C1 | Invert absorption strip emphasis | YES | ClusterReport.tsx:124-133 — primary: corroboration claim, secondary: math |
| C2 | Absorbed top, rest grouped with copy | YES | ClusterReport.tsx:214-255 — absorbed sorted first with visual weight, "Awaiting cross-source corroboration" heading |
| C3 | Timeline "0 days" — root cause first | YES | 4 claims NULL first_seen_at → NaN → rangeMs=0. Filter at Timeline.tsx:83-87 |
| C4 | Claim truncation diagnosis | YES | CSS truncation at 140px, not stored text. Fixed to 280px font-sans |
| C5 | Ungraded tooltip: max-w 320px, wrap, WHY-first | YES | Tooltip.tsx:14 (max-w+wrap) + Sources.tsx:451 (content reorder) |
| Build | npm run build PASS | YES | 471ms |
| Vitest | 12/3 baseline | YES | No new failures |

**Suggested commit:** `UX7: cluster report absorption strip, claims sort, timeline NaN fix, tooltip wrap`
