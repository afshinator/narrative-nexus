# UXnn Results — Cluster Report Pending-Claim Grouping

**Date:** 2026-07-11
**Status:** Implemented, verified

---

## Change

Pending claims on the Cluster Report page are now grouped by source set. Instead of repeated source names per claim row, each group renders a header with the source set + claim count, then the claims beneath without repeating the source.

## Files Changed

| File | Change |
|------|--------|
| `src/pages/ClusterReport.tsx` | +28 lines. Added groupKey/sortedGroups logic, Fragment import, group header rows. `renderClaim` gains `showSource` param. |

## Before / After

Before: flat list — each pending claim row showed source, text, state. Consecutive claims from same source repeated e.g. "bbc.com" 17 times.

After: grouped — `bbc.com — 17 claims` header, then 17 claim rows with no source column text.

## Grouping Rules

| Rule | Implementation |
|------|---------------|
| Group key | sorted `domains` joined by `", "` |
| Sort | multi-source groups first → claim count desc → alphabetical |
| Header | `{key} — {n} claim{s}` on `bg-[var(--nn-surface2)]` row |
| Claims within group | existing relative order preserved |
| Absorbed claims | untouched |

## Verification

| Check | Result |
|-------|--------|
| `npm run build` | ✓ |
| `pytest -m "not network" -q` | 292 passed, 20 failed (baseline unchanged) |
| `vitest run` | 112 passed, 21 failed, 4 skipped (baseline unchanged) |
| demo.db fingerprint | 378\|10\|358\|17\|13653 |
| Tie-out: bbc.com group | API returns 17 PENDING claims for bbc.com; group header renders "17 claims" |
