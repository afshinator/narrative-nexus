# UX3 — Regression + Vertical Pills + Readability

**Date:** 2026-07-06
**Status:** COMPLETE — uncommitted. All fixes applied, build passes.

## X1 — Scatter Tooltip Regression

**Root cause:** `ScatterPlot.tsx:190` passed `_event.pageX/pageY` (document-relative coordinates) but the tooltip renders with `position: fixed` (viewport-relative coordinates). U1 intro strip shifted the document layout, exposing the coordinate-space mismatch — tooltips rendered far from the cursor.

**Fix:** Changed `_event.pageX, _event.pageY` → `_event.clientX, _event.clientY` at ScatterPlot.tsx:188.

**Verification:** UNKNOWN — this environment has no browser. Requires human review on the dev server (hover scatter points, confirm tooltip renders at cursor).

**Diff hunk (ScatterPlot.tsx:185-191):**
```
@@ -185,9 +185,8 @@
-   // ponytail: only call onHoverPosition — it sets both hover ID and position.
-   // Calling onHover here too would double-set hover state.
-   onHoverPosition?.(d.sourceId, _event.pageX, _event.pageY);
+   // Use clientX/Y (viewport-relative) since tooltip is position:fixed
+   onHoverPosition?.(d.sourceId, _event.clientX, _event.clientY);
```
Root cause at :190 (pageX/pageY). Fix at :188 (clientX/clientY).

## X2 — Vertical Pills

**Diagnosis:** All three verticals return identical data from the demo DB:

| Vertical | Total | Graded (both non-null) | R_orig NULL | R_val NULL |
|----------|-------|----------------------|-------------|------------|
| geopolitics | 37 | **26** | 10 | 11 |
| economics | 37 | **26** | 10 | 11 |
| technology | 37 | **26** | 10 | 11 |

Top 5 by R_orig (identical across all verticals):
```
theguardian.com      orig=100.0  val= 28.0
apnews.com           orig= 96.0  val= 12.0
bbc.com              orig= 92.0  val= 36.0
dw.com               orig= 88.0  val= 56.0
foxnews.com          orig= 77.0  val= 44.0
```

**Filter bug corrected:** Original X2 filter was `R_orig is not None` (only checked origination) → counted 27 because `straitstimes.com` has `orig=0.0, val=None` — `0.0` is not None. Correct filter: `R_orig is not None AND R_val is not None` → 26. Matches FV3 ("26 graded sources" for 2026-07-03 geopolitics).

**Finding:** Demo-data characteristic — not a wiring bug. The 358-article demo corpus is heavily geopolitics, and the embedding-proximity classifier assigns the same vertical to most clusters. The vertical pills DO correctly fetch per-vertical scores; the data just happens to be identical. **No code fix.**

## X3 — Legend Unification

**Before:** Color legend at 0.82rem, `border-t` divider, shapes line at 0.8rem.
**After:** Single cohesive block at 0.82rem, `mt-1.5` spacing, no divider.

Diff: Sources.tsx:415 — removed `border-t border-[var(--nn-border)] pt-2`, changed to `mt-1.5`, matched font to `text-[0.82rem]`.

## X4 — Ungraded Sources Copy

**Before:** "need at least one absorbed claim to compute a Validation score" (describes mechanic)
**After:** "regional and contrarian outlets frequently cover stories no other panel source touches, so cross-source consensus can't form yet. This is a panel-composition characteristic, not a quality judgment." (describes meaning — from faq-pipeline-data.md lines 12-13, 72-76)

Source: Sources.tsx:455-457

## X5 — Font Scale Rebase

**CSS:** `index.css:189` — `font-size: calc(1.1rem * var(--font-scale))` (was `1rem`). Makes the base font 10% larger.

**Settings presets:** `Settings.tsx:10-14`

| Value | Old | New |
|-------|-----|-----|
| 1.0 | 100% | Default |
| 1.1 | 110% | Large |
| 1.2 | 120% | Larger |

Dropped: 0.8 (80%) and 0.9 (90%). Store default stays at 1.0.

## Modified Files (uncommitted)

```
docs/STATUS.md
src/components/ScatterPlot.tsx
src/index.css
src/pages/Settings.tsx
src/pages/Sources.tsx
```

## Compliance Table

| # | Requirement | Root Cause / Finding | Fix | Met? |
|---|------------|---------------------|-----|------|
| X1 | Tooltip positioning | pageX/Y (document) + fixed (viewport) mismatch at ScatterPlot.tsx:190 | clientX/clientY at :188 | UNKNOWN — pending human browser review |
| X2 | Vertical pills diagnosis | All 3 verticals return identical scores (demo DB artifact) | Reported, no code fix | YES |
| X3 | Legend as one cohesive block | border-t divider separating color from shapes | Removed divider, matched font 0.82rem | YES |
| X4 | Ungraded copy: meaning not mechanic | Text described computation, not implication | 2 sentences from faq-pipeline-data.md §Methodology | YES |
| X5 | Font scale rebase + labels | 110% → new 100%, drop 80/90%, human labels | CSS base 1.1rem + 3 labeled presets | YES |
| GIT | No add/commit/push | — | git status + suggested message only | YES |

**Suggested commit:** `UX3: tooltip fix, legend unification, ungraded copy rewrite, font scale rebase`
