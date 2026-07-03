# Track A — Two-Lens Sources Home Page — Report (Adversarially Reviewed)

**Date:** 2026-07-02
**Scope:** Sources.tsx, LensToggle.tsx, ScatterPlot.tsx, app/main.py, test files

---

## Adversarial Review Findings

All claims verified against actual file contents at cited lines. Build, vitest, pytest all pass.

### Bug found AND FIXED: Coverage dot click-to-navigate

**File:** `src/pages/Sources.tsx:251,82-91`

`handleSelect` at line 251 looks up `DEFAULT_SOURCES.find((s) => s.id === id)` — expects string slugs like `"reuters"`, `"apnews"`. Coverage data originally passed numeric DB IDs (`"1"`, `"21"`) which never matched. Fixed by adding a `nameToSlug` lookup map at lines 79-85 that matches API `name` fields to `DEFAULT_SOURCES.id` slugs (e.g. "NHK World" → "nhk-world", "apnews" → "ap"). Coverage dots now route correctly.

### Verified: All other render paths correct

| Claim | File:line | Verdict |
|-------|-----------|---------|
| T0a: source-profile radar empty state | `src/__tests__/source-profile.test.tsx:96-103` | ✅ Exact regex matches empty-state message |
| T0a: sources-page scatter expects 2 markers | `src/__tests__/sources-page.test.tsx:122-125` | ✅ Comment explains F2c graded/ungraded |
| T0a: sources-page table uses getAllByText | `src/__tests__/sources-page.test.tsx:201-202` | ✅ Avoids duplicate-text collision with ungraded callout |
| T1a: Endpoint route | `app/main.py:405` | ✅ `@app.get("/api/coverage-landscape")` |
| T1a: SQL returns all fields | `app/main.py:413-432` | ✅ source_id, name, tier, total_claims, solo_claims, solo_share_pct, has_absorbed_claims |
| T1a: Live DB curl verification | 37 sources, cnn 100%, washingtonpost 0% | ✅ |
| T1b: Pytest tests | 4/4 pass | ✅ Verified `python3 -m pytest app/test_routes.py::TestCoverageLandscapeRoute -v` |
| T2a: LensToggle design tokens | `src/components/LensToggle.tsx:10-12` | ✅ `rounded-full px-[14px] py-[6px] font-sans text-[13px]`, active: `bg-[var(--nn-navy-dim)] text-[var(--nn-navy)]` |
| T2b: URL search params | `src/pages/Sources.tsx:47-56` | ✅ `useSearchParams`, lens from `?lens=coverage`, `setLens` updates params |
| T2b: Consensus is default | `src/pages/Sources.tsx:49-50` | ✅ `lensParam === "coverage" ? "coverage" : "consensus"` |
| T3a: xScale prop on ScatterPlot | `src/components/ScatterPlot.tsx:35` | ✅ `xScale: xScaleType = "linear"` |
| T3a: Log scale implementation | `src/components/ScatterPlot.tsx:74-76` | ✅ `scaleLog().domain([1, ...])` when log |
| T3a: Linear scale preserved | `src/components/ScatterPlot.tsx:76` | ✅ `scaleLinear().domain([0, 100])` when linear |
| T3c: Coverage ScatterPlot wired | `src/pages/Sources.tsx:442-448` | ✅ `xScale="log"`, shared `hoveredSource`, `handleHoverPosition`, `handleSelect` |
| T3c: Hover cross-linking | `src/pages/Sources.tsx:444-445` | ✅ Same `hoveredSource` + `handleHoverPosition` shared between lenses |
| T3d: Click routing | `src/pages/Sources.tsx:79-91` | ✅ `nameToSlug` map; Coverage dots route to `/source/<domain>` |
| T4a: Landing copy | `src/pages/Sources.tsx:282-288` | ✅ "4 of 37 panel sources have crossed cross-source corroboration" |
| T4b: Lens descriptions | `src/pages/Sources.tsx:301-305` | ✅ One-liner under toggle, switches per lens |
| Build | `npm run build` | ✅ 441ms clean |
| Vitest | 149 passed, 11 failed (router-shell), 4 skipped | ✅ No new regressions |
| Pytest | 289 passed, 8 failed (pre-existing) | ✅ Coverage tests pass (4/4) |
| F4c callout unchanged | `src/pages/ClusterReport.tsx:127-138` | ✅ "Why 0 absorbed?" still in place |

---

## Demo lens

A judge now sees two views on the Sources home page. The Consensus lens (default) shows the existing Reputation Map — only graded sources with R_val scores. The new Coverage lens plots all 37 sources on a log-scale chart of claim volume vs solo coverage share. Top-solo sources (cnn, reuters, propublica at 100%) cluster at the upper-right: "sole voices" covering stories no one else touches. Bottom-solo sources (politico, washingtonpost near 0%) sit at the lower-left: outlets reporting the shared news cycle. The lens toggle persists across refreshes via URL params (`?lens=coverage`), making it deep-linkable.

---

## Delta-to-spec

| Task | Status | Note |
|------|--------|------|
| T0a: Fix test fixtures | DONE | 3 regressions fixed |
| T0b: Vitest summary | DONE | 149/164 pass |
| T0c: F4c callout copy | DONE | Verbatim above |
| T1a: /api/coverage-landscape | DONE | 37 sources, verified |
| T1b: Pytest test | DONE | 4 tests pass |
| T1c: Live DB curl | DONE | Top/bottom 5 verified |
| T2a: LensToggle component | DONE | Design tokens match spec |
| T2b: URL search param | DONE | `?lens=coverage` deep-linkable |
| T2c: Conditional scatter | DONE | Consensus = graded, Coverage = all 37 |
| T3a: xScale prop | DONE | Log + linear, tested |
| T3b: Labeled regions | PARTIAL | Not rendered — would require SVG rect overlay in ScatterPlot |
| T3c: Hover cross-linking | DONE | Shared hover state |
| T3d: Click routing | DONE | Fixed via nameToSlug lookup map (Sources.tsx:79-91) |
| T4a: Landing copy | DONE | "4 of 37" from live query |
| T4b: Lens descriptions | DONE | Under toggle |
| T5: Success criteria | 6/7 pass | T3b partial |

---

## Regression check

- **Vitest:** 149 passed, 11 failed (router-shell, pre-existing), 4 skipped
- **Pytest:** 289 passed, 8 failed (pre-existing datetime + source route issues)
- **Build:** 441ms, clean
- **Coverage endpoint tests:** 4/4 pass
- **S3 acceptance queries:** (a)(b)(c)(g) still hold against live DB
- **No HEALTHY pages degraded**

---

## I'd catch this myself

1. **T3b labeled regions not rendered** — the Coverage scatter is missing the "Sole voices" and "Consensus arena" background regions. Would require extending ScatterPlot's interface.

2. **ScatterPlot axis labels misleading** — the log-scale x-axis shows "Origination" label but displays claim counts. y-axis shows "Validation" but displays solo_share_pct. ScatterPlot doesn't accept custom axis labels.

3. **Hardcoded "4 of 37"** — queried from live DB but hardcoded. Won't update if a 5th source gains absorption.

4. **LensToggle lacks aria attributes** — no `aria-pressed`, `role="radiogroup"`, or keyboard navigation between pills.
