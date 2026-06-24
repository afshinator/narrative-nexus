# Plan: Slice M1 — Review Fixes (ponytail edition)

Ladder applied. If it doesn't need to exist, delete it. If one line works, one line.

## Keep (6 items)

### HI-01: Light mode CSS
Move `--nn-*` tokens into `.dark {}`. One block cut-paste. No new code.
File: `src/index.css`

### HI-03: Error boundary
React class component, ~25 lines. Native platform feature. No deps.
File: `src/components/ErrorBoundary.tsx` (new)
File: `src/components/PageShell.tsx` (wrap `<Outlet />`)

### MI-01: Dead nav links — REVERTED
Changing to `#` broke React keys and tests. Ponytail re-evaluation: stub pages ARE valid pages — a stub is better UX than a broken link. Nav links stay as-is.
→ ponytail: reverted, no change needed.

### MI-03: Unify formatPercent
Delete local `formatPercent` from Settings.tsx. Rename shared in `format.ts` to `formatRate` (it expects 0–1 decimal). Add `formatPercent(n: number): string` → `${n}%`. Settings imports `formatPercent`. Pure, one-liner.
File: `src/pages/Settings.tsx`, `src/utils/format.ts`

### MI-07: Accessible switches
Add `aria-label={`Toggle ${source.name}`}` to each Switch. One attribute.
File: `src/pages/Panel.tsx`

### INC-04: Fix worker ports test assertion
The test asserts worker has no ports, but it SHOULD expose port 8001. Fix the test to check for port 8001.
File: `src/__tests__/docker/compose.test.ts`
File: `docker-compose.yml` (add `expose: ["8001"]` to worker)

## Delete / Skip (4 items)

### HI-02: Multi-stage Dockerfile — SKIP
Our workflow is `npm run build` → `docker compose build`. `dist/` exists before Docker runs. Adding a Node build stage is a 20-line refactor for a problem that doesn't exist in our workflow. Document the prerequisite in README instead.
→ ponytail: document, don't build.

### HI-04: Vertical filter UI — DELETE
No page reads `vertical` from the store. It's dead code. YAGNI. Remove `vertical`, `Vertical` type, `setVertical` from store. Re-add when a page actually filters by vertical.
→ ponytail: delete dead code, don't build UI for it.

### HI-06: Worker requirements — SKIP
Worker is a stub. Writing `requirements.worker.txt` for a stub is speculative. Add when the worker is actually built.
→ ponytail: skip.

### MI-02: Store subscription granularity — SKIP
`document.documentElement.style.setProperty` is a ~microsecond operation. The subscription fires on every state change but the work is trivial. Don't optimize without a profiler saying so.
→ ponytail: skip.

### INC-02: Vertical key casing — PARTIALLY GONE
After deleting `Vertical` type from store (HI-04), the casing mismatch between store and thresholds goes away. The remaining mismatch (threshold keys lowercase vs display Title Case) is a display concern — already handled by `VERTICAL_LABELS` mapping. No fix needed.
→ ponytail: already handled.

## Files changed

| File | Action | Lines |
|------|--------|-------|
| `src/index.css` | Move nn-* block into .dark {} | 0 new, cut-paste |
| `src/components/ErrorBoundary.tsx` | New | ~25 |
| `src/components/PageShell.tsx` | Wrap Outlet | +1 |
| `src/pages/Settings.tsx` | Delete local formatPercent, import shared | -3 +1 |
| `src/utils/format.ts` | Rename + add formatPercent | +2 |
| `src/pages/Panel.tsx` | Add aria-label to Switch | +1 |
| `src/store.ts` | Remove vertical, Vertical, setVertical | -5 |
| `docker-compose.yml` | Add expose: 8001 to worker | +1 |
| `src/__tests__/docker/compose.test.ts` | Fix worker ports assertion | ~3 |

Total: 9 files, ~37 lines changed. No new deps. No speculative code.
(MI-01 dead nav links reverted — no change to AppNav.tsx)

## Verification

1. `npm run build` exits 0
2. `npm run test` — all 72 tests pass
3. Light mode toggle renders correctly
4. Error boundary catches throw in dev
