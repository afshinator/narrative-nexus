# Review Leftovers

Remaining suggestions and findings after resolving the 3 blocking issues from review-02.

---

## 🟡 Suggestion 4 — Consensus pool toggle guard

**File:** `src/pages/Panel.tsx:190-193`

Tier 1/2 sources (10 total, labeled "consensus pool") can all be deactivated with no minimum guard. A low-panel warning exists when total active drops below 12, but it conflates "total panel size" with "consensus pool depth." With 10 consensus-pool sources, it's possible to have 11 active (all 5 non-consensus + 6 consensus) and see no warning despite a thin consensus baseline.

**Options:**
- Lock the toggle when active consensus pool sources would drop below a minimum (e.g. 3 of 10).
- Or change the existing warning to track consensus pool count specifically rather than total panel size.

---

## 🟡 Suggestion 5 — Sources page ignores `activeSources` from store

**File:** `src/pages/Sources.tsx:63-115`

Both `scatterData` and `rows` use `DEFAULT_SOURCES` directly rather than filtering by `activeSources` from the Zustand store. A user who deactivates a source on the Panel page will still see it on the Sources page scatter and leaderboard. Either:

- Filter Sources page data by `activeSources` so Panel toggles have visible effect frontend-wide, or
- Document that deactivation is backend-only (for consensus computation).

The store is already subscribed: `Panel.tsx:46` reads `activeSources`. `Sources.tsx` only reads `archetypeFilter`.

---

## 🟡 Suggestion 6 — Dead export `formatDecimalAsPercent`

**File:** `src/utils/format.ts:2`

```ts
export function formatDecimalAsPercent(value: number, decimals = 1): string {
    return `${(value * 100).toFixed(decimals)}%`;
}
```

Zero imports across `src/`. The only percent formatter actually used is `formatPercent` (integer → string). Currently listed in fallow as intentional dead code — harmless but removable.

---

## 🔵 M1 — OnboardingDialog fragile state reset ordering

**File:** `src/components/OnboardingDialog.tsx:67-72`

```ts
function handleOpenChange(next: boolean) {
    if (!next) {
        setDontShow(false);     // resets state before reading it
        if (dontShow) setOnboardingComplete(true);
    }
    onOpenChange(next);
}
```

`setDontShow(false)` is called before the `if (dontShow)` check. This works today because React batches state updates and the closure still holds the old `dontShow` value. But it's fragile — a future React version or concurrent-mode edge case could break the ordering assumption.

**Fix (2-line reorder):**
```ts
if (!next) {
    if (dontShow) setOnboardingComplete(true);
    setDontShow(false);  // cleanup after check
}
```
