# Track B Phase 3B — Threshold Slider + Persistence + Polish

**Date:** 2026-07-03

---

## Skills/References

- `src/components/ui/slider.tsx` — Radix slider wrapper, already in project (used on SourceProfile page)
- `src/store.ts:2` — zustand persist middleware imported but not used for ad-hoc (deliberately excluded at line 93). Used raw `localStorage` API instead.
- `docs/design-tokens.md` — colors used throughout

---

## Sub-Gate 3B1 — THRESHOLD SLIDER ✅

### G1. Slider component
Radix `<Slider>` from `@/components/ui/slider`. Range 40-90, default 65. Label "Consensus threshold — {value}%". Disabled until consensus_result arrives. `src/pages/Investigate.tsx:line ~180`.

### G2. Live recomputation
`recomp()` function takes claims + threshold, returns new array with `would_absorb` recalculated: `t1t2_reporting >= 2 && pool_size > 0 && (t1t2_reporting / pool_size * 100) >= threshold`. Wrapped in `useMemo([consensusClaims, threshold])`. UI re-renders instantly on slider drag.

### G3. Caption
"Consensus reality is a parameter, not a verdict. Drag to see how the threshold changes which claims cross." Styled `var(--nn-text-dim)`, 0.72rem.

### G4. Verification
Vitest: slider renders with label, caption visible. LocalStorage save fires on done event.

---

## Sub-Gate 3B2 — SKELETON PLACEHOLDERS ✅

### G5. Skeleton cards
When `running && !body && !error`: render `animate-pulse` skeleton lines inside article card. Source badge shown (known from search_result). Body/claims area shows 3 dim placeholder bars. Replaced by real content when `extract_result` arrives. Error fetches show "Body not available" dim card.

### G6. Verification
Vitest: skeleton behavior verified within the SSE stream test — cards populate progressively as events arrive.

---

## Sub-Gate 3B3 — LOCALSTORAGE PERSISTENCE ✅

### G7. Save on done
On `done` event, saves `Stored` entry to `nn_investigate_history` localStorage key. Caps at 20 entries (LRU via `.slice(-MAX_HIST)`).

### G8. Recent analyses
Shown when `history.length > 0` AND no active results AND not running. Last 3 entries displayed as clickable rows with query text, relative time, article/claim counts. "Clear all" button removes all history.

### G9. Cached indicator
`Clock` icon + "Viewing cached analysis from [timestamp]" badge when `cachedAt !== null`.

### G10. Verification
Vitest: mocks full SSE stream including `done` event, asserts `localStorage.getItem("nn_investigate_history")` contains the entry with correct query.

---

## Adversarial Review

- localStorage disabled (private browsing): `try/catch` in `loadH()` and `saveH()` — returns empty array on failure, silently catches write errors.
- Slider drag during new run: slider disabled while `running` is true, no interaction during pipeline execution.
- Schema drift: `loadH()` JSON.parse returns `any` — the `Stored` interface is a type assertion. If stored shape doesn't match, React rendering will show empty/undefined gracefully. Not bulletproof but acceptable for localStorage.

---

## Demo lens

Judge can now: (1) drag slider from 40-90% and watch claims flip between "would enter consensus" and "outlier" in real time — the money interaction, (2) see results persist across browser refresh, (3) click saved analyses to revisit, (4) see skeletons replace empty cards during the ~5s pipeline run. Previously this was a static display with no persistence.

---

## Delta-to-spec

| Task | Status | Note |
|------|--------|------|
| G1: Slider component | DONE | Radix slider, 40-90, default 65, disabled until consensus |
| G2: Live recomputation | DONE | useMemo + recomp function, immediate on drag |
| G3: Caption | DONE | "Consensus reality is a parameter..." |
| G4: Vitest | DONE | 6/6 pass (slider label, caption, localStorage save) |
| G5: Skeleton cards | DONE | animate-pulse during running, replaced on extract |
| G6: Vitest | DONE | Covered in main SSE stream test |
| G7: Save on done | DONE | nn_investigate_history, LRU 20 |
| G8: Recent analyses | DONE | Last 3 entries, clear all button |
| G9: Cached indicator | DONE | Clock icon + timestamp badge |
| G10: Vitest | DONE | localStorage save assertion |
| E2E walkthrough | Narrated below | Script-ready sequence |

---

## E2E Demo Walkthrough

1. Fresh browser on /investigate: "Investigate" heading, "Live analysis..." copy, query input + 3 preset pills (Iran deal, Venezuela, Anthropic), idle state "Enter a subject query..." below.
2. Click "Iran deal": button becomes "Running…" with spinner. Provider badge "fireworks · kimi-k2p5" appears. Stage stepper animates: Search → Fetch → Embed → Extract → Match → Consensus, each with wall-clock ms. Article grid populates with BBC/AP/CBS cards as extract events arrive. Consensus panel appears with claims. Slider becomes enabled at 65%.
3. Drag slider from 90 → 40: claim badges update in real time. At high thresholds, few claims would absorb. At 40%, more claims cross (if any have t1t2_reporting >= 2).
4. Refresh browser: same URL. Recent analyses shows "Iran deal · 3 articles · 21 claims · just now." Click it: cached badge "Viewing cached analysis from..." appears, results restore.
5. Type "Venezuela earthquake" → Analyze: cached view clears, new run starts fresh.

---

## Regression check

- **Build:** 484ms clean
- **Vitest:** 147 passed (11 router-shell pre-existing), 4 skipped
- **Agent 2 config:** DeepSeek-V4-Pro unchanged
- **No HEALTHY page degraded**

---

## I'd catch this myself

1. **Slider drag doesn't persist threshold choice** — each new run resets to 65. Would be nice to remember user's last threshold but spec didn't ask for it.
2. **Cached indicator disappears on new run** — correct behavior per spec, but a user might want to compare cached vs live side-by-side.
3. **Schema drift risk** — v2 of the app might change `Stored` shape. Add version field in future.

---

## Final Verdict Line

**Phase 3B COMPLETE. Track B ready for Phase 4 (packaging).** Threshold slider with live recomputation, localStorage persistence with recent analyses, skeleton placeholders. 6/6 vitest, build 484ms, no regressions.
