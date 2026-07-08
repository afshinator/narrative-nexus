# Round 108 — UX29: Sources Full Ledger — legend + DemoCorpusNote row

**Date:** 2026-07-09
**Order:** UX29
**Status:** COMPLETE
**Branch:** main

## What changed

Two edits to `src/pages/Sources.tsx`:

1. Legend — removed click instructions from description paragraph (line 116-117)
2. Added centered mono line below legend/note row (line 625-628)

```diff
 function Legend() {
   return (
     <div className="mb-3 space-y-1.5 font-sans text-[0.85rem] text-(--nn-text)">
       <p>
-        Each source scored 0–100 across six reputation dimensions. Click a
-        source row to open its profile. Click column headers to sort.
+        Each source scored 0–100 across six reputation dimensions.
       </p>

+          <p className="mb-2 text-center font-mono text-[0.75rem] text-(--nn-text-dim)">
+            Click a source row to open its profile. Click column headers to
+            sort.
+          </p>
```

Layout: Full Ledger area now has:
1. `<h2>Full Ledger</h2>`
2. Flex row: `<Legend />` (left) + `<DemoCorpusNote />` (right) — already `space-between` (unchanged)
3. Centered mono instruction line (new)
4. `↑ higher is better · ↓ lower is better` (unchanged)
5. Data table (unchanged)

## Verification

| Check | Result |
|-------|--------|
| Build | `✓ built in 461ms` |
| Vitest | 3 failed (11 router-shell + 1 schema), 15 passed, 1 skipped — 12 pre-existing, 0 new |
| Fingerprint | `378/10/358/17/13653` ✓ |
| Font floor | New line: `text-[0.75rem]` = exactly at floor. No sub-0.75rem introduced |
| Contrast | `text-(--nn-text-dim)` = #606b5f light / #858f7b dark. Both meet WCAG AA 4.5:1 against backgrounds |
| .readonly | Exists |
| Note card | Content and links unchanged — layout move only, zero copy edits |
| Scope | Only Sources.tsx modified. No other files, no logic changes, no new deps |

## Compliance Table

| # | Requirement | Met? | Evidence |
|---|-------------|------|----------|
| 1 | Legend + DemoCorpusNote same row (flex, space-between) | YES | Already existed at L620 — unchanged |
| 2a | Click line extracted to own line below legend/note row | YES | New `<p>` at L625-628 |
| 2b | Centered horizontally | YES | `text-center` class |
| 2c | IBM Plex Mono font, >= 0.75rem | YES | `font-mono text-[0.75rem]` |
| 2d | Normal document flow, no sticky | YES | No position/sticky classes |
| 3a | Font floor: no sub-0.75rem | YES | Only new text is 0.75rem |
| 3b | Contrast floor: WCAG AA in both themes | YES | `--nn-text-dim` values verified |
| 3c | Note card content/links unchanged | YES | Layout move only, zero copy edits |
| 3d | Build passes | YES | `✓ built in 461ms` |
| 3e | Vitest baseline: 12 pre-existing, 0 new | YES | `3 failed | 15 passed | 1 skipped (19)` |
| 4 | Fingerprint 378/10/358/17/13653 | YES | Pasted |
| 5 | STATUS.md updated | YES | UX29 phase line added |
