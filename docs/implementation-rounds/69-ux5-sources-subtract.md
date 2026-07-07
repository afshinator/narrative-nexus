# UX5 — Sources Page Subtraction

**Date:** 2026-07-06
**Status:** COMPLETE — uncommitted. Build passes, vitest 125/141 pass.

---

## S1 — Vertical Pills → Static Label

**Change:** Removed the 3 vertical picker pills (Geopolitics / Economics / Technology) and replaced with a single inert pill: "Vertical: Geopolitics (demo corpus)".

**Where:** `src/pages/Sources.tsx`

**Removed:**
- `VerticalPills` import (line 7) — still used in `SourceProfile.tsx`, component retained
- `VerticalThresholdKey` import (line 11) — no longer needed in Sources
- `VERTICAL_LABELS` import (line 11) — dead, removed
- `vertical` state and `setVertical` (line 44) — replaced with hardcoded `"geopolitics"` in fetch URL, scoreMap filter, and subtitle copy
- `[vertical]` dependency array (line 133) — changed to `[]`

**Added (Sources.tsx:325-328):**
```tsx
<span className="inline-flex items-center gap-1.5 rounded-full border border-[var(--nn-navy)]
  bg-[color-mix(in_srgb,var(--nn-navy)_10%,transparent)] px-4 py-1.5
  font-heading text-[0.78rem] font-semibold text-[var(--nn-navy)]">
    Vertical: Geopolitics (demo corpus)
</span>
```
Inert `<span>` — no onClick, no state, no interactive styling. Styled like the active pill state.

**Test update:** `sources-page.test.tsx` — "Vertical filter" describe block (3 tests: renders pills, default active, click updates) replaced with "Vertical label" (1 test: renders static label text).

**Hardcoded references to `vertical` resolved:**
| Line | Before | After |
|------|--------|-------|
| fetch URL | `/api/scores?vertical=${vertical}` | `/api/scores?vertical=geopolitics` |
| scoreMap filter | `.filter((s) => s.vertical === vertical)` | `.filter((s) => s.vertical === "geopolitics")` |
| subtitle | `<Tooltip>{VERTICAL_LABELS[vertical]} vertical</Tooltip>` | `— Geopolitics vertical` |
| VerticalPills | `<VerticalPills vertical={vertical} onChange={setVertical} />` | Removed |

---

## S2 — Corpus Provenance → Footer

**Change:** Corpus provenance line moved from Sources page body into the sitewide footer.

**Where:** `src/components/PageShell.tsx:14-20`

**Before:**
```tsx
<footer className="py-9 text-center font-mono text-[1.1rem] tracking-[0.04em] text-[var(--nn-text)]">
    Narrative Nexus tracks consensus reality, not truth
</footer>
```

**After:**
```tsx
<footer className="py-9 text-center font-mono text-[1.1rem] tracking-[0.04em] text-[var(--nn-text)]">
    Narrative Nexus tracks consensus reality, not truth
    <br />
    <span className="text-[0.7rem] text-[var(--nn-text-dim)]">
        Demo corpus: 358 articles · 37 sources · Mar–Jul 2026
    </span>
</footer>
```

**Note:** No corpus provenance line was present in the Sources page body (the mock v2 had one but it was never ported to production). Verified — no removal needed from Sources.tsx.

---

## S3 — Ungraded Sources Strip → One-Line + Tooltip

**Change:** Reduced the multi-line ungraded callout to one line with a tooltip.

**Where:** `src/pages/Sources.tsx:449-455`

**Before:**
```tsx
<span>N sources not yet graded</span>
— regional and contrarian outlets frequently cover stories...
This is a panel-composition characteristic, not a quality judgment.
[domain1, domain2, domain3, ...]  // 11 domains rendered inline
```

**After:**
```tsx
<Tooltip content={`Regional and contrarian outlets... Ungraded: ${names.join(", ")}`}>
    <span>N sources not yet graded ⓘ</span>
</Tooltip>
```

**Design decision:** The 11-domain list goes into the tooltip rather than being dropped entirely. The full X4 panel-composition copy and domain names are accessible on hover without cluttering the page body.

---

## S4 — No SQL or Debug Text

**Confirmed:** The query appendix card that appeared in mock V2 was never part of the app code (`src/`). It existed only in `docs/mocks/demo-direction-mock-v2.html`. The Sources page has no SQL output, debug text, or evidence apparatus.

---

## S5 — Near-Consensus Exhibit Deferred

**Not implemented.** Deferred pending separate human decision. No code exists for this component.

---

## Verification

| Check | Result |
|-------|--------|
| `tsc --noEmit` | PASS — no errors |
| `npm run build` | PASS (455ms) |
| Vitest | 125 pass, 12 fail |
| New test failures | 0 (3 vertical-pill tests replaced with static-label test) |
| Pre-existing failures | 12: 11 router-shell + 1 docker/compose |

**Vitest summary line:**
```
Test Files  3 failed | 15 passed | 1 skipped (19)
Tests  12 failed | 125 passed | 4 skipped (141)
```

Failing files: `db/__tests__/schema.test.ts` (better-sqlite3 stale), `src/__tests__/router-shell.test.tsx` (11 tests), `src/__tests__/docker/compose.test.ts` (volume removed). All pre-existing.

---

## Modified Files (uncommitted)

```
 M docs/STATUS.md
 M src/__tests__/sources-page.test.tsx
 M src/components/PageShell.tsx
 M src/components/ScatterPlot.tsx
 M src/index.css
 M src/pages/Settings.tsx
 M src/pages/Sources.tsx
```

## Compliance Table

| # | Requirement | Met? | Evidence |
|---|------------|------|----------|
| S1 | Vertical pills → static label | YES | Sources.tsx:325-328 — inert `<span>` pill |
| S2 | Corpus provenance → footer | YES | PageShell.tsx:16-19 |
| S3 | Ungraded strip → one-line + tooltip | YES | Sources.tsx:449-455 — domain list in tooltip |
| S4 | No SQL/debug text renders | YES | Confirmed — query card was mock-only |
| S5 | Near-consensus deferred | YES | Not implemented |
| Build | npm run build PASS | YES | 455ms |
| Vitest | 125/141 pass, no new failures | YES | 3 old tests replaced, 0 regressions |

**ROUND OBJECTIVE:** Sources page shows scatter + leaderboard with minimal chrome; all removed apparatus gone; build passes: **YES**

---

**Suggested commit:** `UX5: subtract — remove vertical pills, corpus provenance→footer, ungraded→one-liner`
