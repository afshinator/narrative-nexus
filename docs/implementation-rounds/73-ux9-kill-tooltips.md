# UX9 — Kill Dotted-Underline Tooltips on Sources Page

**Date:** 2026-07-06
**Status:** COMPLETE — uncommitted. Build 449ms, vitest 125/12 baseline.

---

## Requirement (ECHO)

Critique found 7 tooltips on Sources page hiding important conceptual info behind hover with CSS-only positioning that overflows viewport. Fix: remove all `<Tooltip>` wrappers, move content inline. No data changes, no new dependencies.

---

## Evidence

### Diff
```
src/pages/Sources.tsx | 28 +++++++++++-----------------
 1 file changed, 11 insertions(+), 17 deletions(-)
```

**5 locations changed:**

1. **Import removed** (line 6): `import Tooltip from "../components/Tooltip";` — deleted. Zero other files import Tooltip.

2. **"37 monitored outlets"** (line ~308): tooltip wrapper removed. Content now inline:
   ```
   {visibleSources.length} outlets across 5 tiers: wire services, mainstream
   editorial, international, investigative, contrarian — Geopolitics vertical
   ```
   Dropped `— design-v1.2 §5` internal reference.

3. **X-axis label** (line ~355): `<Tooltip>` wrapper removed. `Origination (0–100)` now plain text. Inline description already present: `— how often this source reports claims before the rest of the panel.` Dropped `— design-v1.2 §4 (R_orig)`.

4. **Y-axis label** (line ~362): `<Tooltip>` wrapper removed. `Validation (0–100)` now plain text. Inline description already present. Dropped `— design-v1.2 §1`.

5. **Archetype legend** (line ~401): `<Tooltip content={item.tip}>` wrapper removed from the `.map()` loop. Each archetype label (`{item.label}`) keeps its color, with `— {item.desc}` inline descriptions preserved.

6. **Ungraded callout** (line ~451): tooltip wrapper replaced with two `<p>` elements — count line + always-visible explanation line. Dropped comma-separated wall of 9 source names from the tooltip content.

### Build
```
$ npm run build
✓ built in 449ms
```
Exit 0. No warnings.

### Vitest
```
Test Files  3 failed | 15 passed | 1 skipped (19)
     Tests  12 failed | 125 passed | 4 skipped (141)
```

Sources-specific tests:
```
✓ src/__tests__/sources-page.test.tsx (18/18 passed)
✓ src/__tests__/sources.test.ts (5/5 passed)
```

3 failing files are all pre-existing:
- `db/__tests__/schema.test.ts` — better-sqlite3 removed (D3)
- `src/__tests__/router-shell.test.tsx` — 11 tests, router link patterns (pre-existing)
- `src/__tests__/docker/compose.test.ts` — nn-data volume removed (D2)

**Zero new failures.**

### Grep: Tooltip import now unused site-wide
```
$ rg "import Tooltip" src/
(no matches)
```

---

## Compliance Table

| # | Requirement | Met EXACTLY? | Evidence |
|---|------------|-------------|----------|
| 1 | Remove all Tooltip wrappers from Sources page | YES | Diff shows 5 locations, 7 tooltip instances removed |
| 2 | Move panel composition inline | YES | "37 outlets across 5 tiers: wire services…" |
| 3 | Move axis descriptions inline (already had inline text) | YES | Origination/Validation plain text, inline desc preserved |
| 4 | Remove archetype tooltip wrappers (redundant with inline desc) | YES | `— {item.desc}` already present, Tooltip wrapper removed |
| 5 | Ungraded explanation always visible | YES | Two `<p>` elements, explanation below count |
| 6 | No data changes | YES | Zero DB writes, zero API changes |
| 7 | Build passes | YES | 449ms, exit 0 |
| 8 | Vitest — no regressions | YES | Sources tests 23/23 pass, 12 failures all pre-existing |

---

## PROPOSED (not done)

- Same treatment could apply to other pages using Tooltip — but none do. Tooltip.tsx is now dead code (0 imports site-wide). Consider removing the component file in a cleanup pass.

---

**Suggested commit:** `UX9: kill dotted-underline tooltips on Sources — info now inline, no off-screen overflow`
