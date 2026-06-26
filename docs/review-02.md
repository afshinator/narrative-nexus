# Adversarial Review 02

**Date:** 2026-06-26
**Scope:** Full codebase (`src/`) against `docs/design-v1.2.md`, `spec/requirements.md`, and `docs/design-tokens.md`.
**Method:** File-by-file read of all pages, components, data files, utils, store, and CSS. Cross-checked every requirement tag and design token.
**Status:** Found 3 blocking issues, 3 suggestions. 0 security issues, 0 correctness errors in analytical logic, 0 color token mismatches.

> Skips stub pages (ClusterReport, Timeline) per request.

---

## 🔴 Blocking

### 1. Scatter plot markers all rendered navy regardless of behavior archetype

**File:** `src/components/ScatterPlot.tsx:171`
**Spec:** `docs/design-v1.2.md` §6 (Sources) — "Shapes in the scatter encode outlet format; **color encodes behavior archetype**."
**REQ:** Implicit in REQ-085 (scatter plot with archetype filter pills).

All 20 markers on the scatter plot are hardcoded to `fill="var(--nn-navy)"` regardless of which quadrant they sit in:

```ts
// ScatterPlot.tsx:171
.attr("fill", "var(--nn-navy)")
```

A source sitting in the bottom-right (Noise Generator) red quadrant still renders as a navy dot. The four quadrant background tints are correct (navy/red/teal/slate at 9% opacity), but the actual data markers ignore archetype entirely. This undercuts the primary visual encoding of the landing page.

**Fix:** Derive each source's archetype from its R_orig/R_val against the panel median (already computed in `SourcesPage.tsx` as `panelMedian`) and pass a color down. Replace the hardcoded navy fill with:

```
EARLY_BREAKER → var(--nn-navy)
NOISE_GENERATOR → var(--nn-red)
SELECTIVE_ACCURATE → var(--nn-teal)
CONSENSUS_FOLLOWER → var(--nn-slate)
```

---

### 2. Investigate page stores empty results as completed analyses

**File:** `src/pages/Investigate.tsx:14-19`
**REQ:** REQ-118, REQ-119 (ad-hoc results should display extracted claims with cross-source matches).

`handleSubmit` pushes a result to the store with `claims: []` immediately, before any pipeline processing:

```ts
addAdHocResult({
    id: crypto.randomUUID(),
    query: trimmed,
    timestamp: Date.now(),
    claims: [],   // ← always empty, no backend connected
});
```

The UI then renders "No claims extracted yet. Pipeline analysis will populate results when the backend runs stages 1–3." This is technically honest but creates a poor UX pattern: every submit creates a permanent empty result in localStorage that must be manually cleared. A user submitting 5 URLs gets 5 empty cards that can't be dismissed individually (only "Clear Results" nukes all).

**Fix options (choose one):**
- (a) Don't store results unless claims are non-empty — gate on backend response.
- (b) Add individual result dismissal (a per-card × button).
- (c) Show a transient toast/shimmer instead of a persisted result card when claims are empty.

---

### 3. `pagehead` CSS class used but never defined

**Files:** `src/pages/Sources.tsx:142`, `src/pages/Settings.tsx:31`
**Spec:** `docs/mocks/sources.html:95` defines `.pagehead { display:flex; align-items:center; gap:12px; margin-bottom:6px }` in the mock HTML.

Both pages wrap their `<h1>` in:

```tsx
<div className="pagehead">
    <h1 className="font-heading ...">Sources</h1>
</div>
```

But no corresponding CSS exists in `src/index.css` or any Tailwind layer. The `pagehead` class is a no-op at runtime. The `margin-bottom: 6px` intended gap below the heading is missing — the `<p>` subtitle ends up closer to `<h1>` than the mock intends.

**Fix:**
- Define the class in `src/index.css` under `@layer utilities` or replace with standard Tailwind utilities (e.g., `flex items-center gap-3 mb-1.5`).

---

## 🟡 Suggestions

### 4. Tier 1/2 consensus pool sources are toggleable off with no guard

**File:** `src/pages/Panel.tsx:190-193`
**REQ:** REQ-047 (panel must distinguish consensus pool vs tracked).

The Panel correctly labels Tier 1/2 as "consensus pool" but offers no protection against deactivating all 10 consensus-pool sources. If a user turns every Tier 1+2 source off, the analytical model becomes undefined — the consensus baseline has no input.

Consider either:
- Locking the toggle for sources when total active consensus pool would drop below a minimum (e.g. 3 of 10).
- Or showing a warning dialog: "You're about to disable most of the consensus pool — analysis may be unreliable."

This is not a spec violation (the spec says "activate/deactivate sources" without locks), but it's a real UX risk in production use.

---

### 5. Sources page ignores `activeSources` from store

**File:** `src/pages/Sources.tsx:63-76`, `src/pages/Sources.tsx:79-115`

Both `scatterData` and `rows` use `DEFAULT_SOURCES` directly rather than filtering by `activeSources` from the Zustand store. A user who deactivates sources on the Panel page will still see every source on the home page scatter and leaderboard.

If deactivation is intended only for back-end consensus computation, this is correct behavior. But the current UX suggests toggling a source off has no visible effect anywhere in the frontend. If the intent is for deactivation to affect the front-end display, the Sources page is out of sync.

---

### 6. `formatDecimalAsPercent` is exported but never imported

**File:** `src/utils/format.ts:2`

```ts
export function formatDecimalAsPercent(value: number, decimals = 1): string {
    return `${(value * 100).toFixed(decimals)}%`;
}
```

Zero imports across `src/`. The only percent formatter actually used is `formatPercent` (integer → string). Harmless dead code, but worth removing or documenting as available for future use.

---

## Verified Correct (cross-checked)

These areas checked out against spec and tokens:

| Check | Status |
|---|---|
| Footer tagline on every page (REQ-001/REQ-004) | ✅ `PageShell.tsx:15` — correct IBM Plex Mono, exact text |
| 20 default sources match spec tiers (REQ-048–053) | ✅ `sources.ts` — all 20, correct domains, tiers, regions |
| Font families loaded (REQ-084) | ✅ `index.css:4-12` — Space Grotesk 400–700, IBM Plex Sans 400–600, IBM Plex Mono 400–500 |
| Monospace on data values (REQ-083) | ✅ All table cells, stat panel, badges use `font-mono` |
| Default thresholds (REQ-024) | ✅ `thresholds.ts` — geopolitics 65, economics 75, technology 75 |
| Archetype assignment logic (REQ-039–042) | ✅ `archetype.ts` — correct 4-way split vs panel median |
| Trait dimensions in neutral color (REQ-038) | ✅ `polarity.ts:8` — R_orig and R_correct return `var(--nn-slate)` |
| Nav bar sticky, all 8 links present (REQ-064) | ✅ `AppNav.tsx` — Sources, Source Profile, Cluster Report, Timeline, Pipeline, Investigate, Panel, Settings |
| Onboarding: 6 vocabulary terms (REQ-003, REQ-095) | ✅ `OnboardingDialog.tsx` — all 6 terms from spec §1 defined |
| Pipeline: AMD GPU + Fireworks API labeling (REQ-089) | ✅ `PipelineFlow.tsx:24-46` — red badge for AMD GPU, navy for Fireworks |
| Investigate: snapshot banner + read-only (REQ-090, REQ-122) | ✅ `Investigate.tsx:36-41` — amber banner with correct copy |
| Ad-hoc results persist in localStorage (REQ-120) | ✅ `store.ts:86` — `persist` middleware on `nn-store` key |
| Font scale dynamically applied (implicit REQ-092) | ✅ `main.tsx:19-24` — subscribe handler sets `--font-scale` on `<html>` |
| Docker Compose: 3 services (REQ-007/REQ-008/REQ-102–104) | ✅ `docker-compose.yml` — app + worker + db (busybox volume holder) |
| Design token colors match tokens doc | ✅ Light and dark mode `--nn-*` values in `index.css` match `docs/design-tokens.md` exactly |

---

## Summary

- **3 blocking** — scatter marker color (visual spec deviation), Investigate empty-result UX, missing `pagehead` CSS class
- **3 suggestions** — consensus pool toggle guard, activeSources not used on Sources page, one unused export
- **0 security issues**, **0 logic errors** in archetype assignment, polarity color mapping, or threshold handling
- **0 color token mismatches** between CSS and design-tokens.md
