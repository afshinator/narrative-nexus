# Round 128 — UX49: Archetype label rename on Sources page

**Date:** 2026-07-09
**Order:** UX49
**Status:** COMPLETE
**Branch:** main

## Red phase

Wrote 2 failing tests (`sources-page.test.tsx`) asserting new labels exist. Both failed on old code — "Unmatched Breaker" and "Late but Reliable" and "Consensus Echo" not found.

## Green phase

Updated 4 files:

| File | Change |
|------|--------|
| `src/pages/Sources.tsx` | Legend: 3 labels + 3 descriptions renamed |
| `src/components/ScatterPlot.tsx` | SVG quadrant labels: 3 renamed |
| `src/__tests__/sources-page.test.tsx` | SVG test + new legend test updated |
| `docs/design-tokens.md` | Color comments: 3 renamed |
| `docs/design-v1.2.md` | Spec: all 7 references renamed |
| `docs/design-v1.3.md` | Spec: all 7 references renamed |
| `docs/faq-demo-goal.md` | FAQ: 3 references renamed |

### Label mapping

| Old | New | Old desc | New desc |
|-----|-----|----------|----------|
| Noise Generator | **Unmatched Breaker** | breaks stories, rarely absorbed | breaks stories, uncorroborated |
| Selective but Accurate | **Late but Reliable** | late, reliable | late, tracks consensus |
| Consensus Follower | **Consensus Echo** | safe, uninformative | tracks the consensus |

"Early Breaker" label and description kept.

## Test results

```
✓ src/__tests__/sources-page.test.tsx (20 tests) — all passed
  Archetype legend labels > renders four archetype labels — passed
  Archetype legend labels > renders updated descriptions — passed
  renders four quadrant labels in the SVG — passed (UPPERCASE labels)
```

Full suite: 12 failed (baseline), 121 passed, 4 skipped. No new failures.

## Files Changed

```
src/pages/Sources.tsx              | 6 lines (3 labels + 3 descriptions)
src/components/ScatterPlot.tsx     | 3 lines (SVG quadrants)
src/__tests__/sources-page.test.tsx | 13 lines (new legend tests + SVG test update)
docs/design-tokens.md              | 3 lines (color comments)
docs/design-v1.2.md                | 7 lines (spec)
docs/design-v1.3.md                | 7 lines (spec)
docs/faq-demo-goal.md              | 3 lines (FAQ)
docs/STATUS.md                     | UX49 phase line
```
