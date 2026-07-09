# Round 118 — UX39: Timeline 966 date axis + claim label fixes

**Date:** 2026-07-09
**Order:** UX39
**Status:** COMPLETE
**Branch:** main

FP START: 378/10/358/17/13653
FP END:   378/10/358/17/13653 ✓

## Defect A — Date axis fix

**Root cause:** Timeline.tsx:121-128 generated one label for every calendar day in the span (49 labels for 48-day span). With ~20px spacing per label and ~55px label width, text overlapped.

**Fix:** Filter to only dates with claim data:

```tsx
const claimDates = [
    ...new Set(
        data.sources.flatMap(s =>
            s.claims.map(c => c.first_seen_at.split("T")[0]),
        ),
    ),
].sort();
const days = claimDates.map((d) => new Date(`${d}T00:00:00`));
```

Result: 49 labels → 6 labels for cluster 966. Readable, no overlap.

## Defect B — Claim label markers

**Problem:** Claim text rendered inline as `<span>` with 280px max-width, single-line truncation. Same-date claims overlapped. Long claims illegible.

**Fix:** Replaced claim spans with numbered dot markers + claims legend:

1. **Numbered dots:** Small 20px circles with claim index (1-20), positioned horizontally by first_seen_at. Absorbed claims: teal background. Same-date claims stacked vertically with 22px offset.

2. **Claims legend:** Table below timeline rows showing all claims chronologically sorted. Number, full text, source domain, date. Uses IBM Plex Mono for numbers, IBM Plex Sans for text.

3. **Hover tooltips preserved:** `title` attribute shows `#N: claim text`.

4. **Dynamic row height:** Each source row's height adapts to the maximum same-day claim count.

## Test fix

`timeline.test.tsx:149` — "reuters.com" now appears both in source row label AND legend. Changed `getByText` → `getAllByText` with count assertion.

## Verification

| Check | Result |
|-------|--------|
| Build | `✓ built in 436ms` |
| Vitest | 12 failed (baseline), 119 passed, 4 skipped |
| FP | 378/10/358/17/13653 ✓ |
| Date axis | 6 labels, no overlap |
| Claim rows | Numbered dots, no truncated text |
| Legend | Full claim text, numbered, sourced |

## Files Changed

```
src/pages/Timeline.tsx               | Major rewrite — dots + legend
src/__tests__/timeline.test.tsx      | getByText → getAllByText fix
```
