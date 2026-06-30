# Slice 019 — ClusterReport + Timeline Frontend Tests

**Status:** Plan  
**Date:** 2026-06-30  
**Depends on:** Nothing (all deps exist — pages, API endpoints, test infrastructure)

---

## Scope

Add two test files covering the ClusterReport and Timeline pages. Both pages exist (~180 lines each), both API endpoints exist and are backend-tested (`app/test_routes.py`), but neither page has a frontend test file. All 9 other pages have tests.

---

## Files to create

1. `src/__tests__/cluster-report.test.tsx` — ~10 tests, ~120 lines
2. `src/__tests__/timeline.test.tsx` — ~10 tests, ~120 lines

No source code changes. No new dependencies. No API changes.

---

## Testing patterns (from existing pages)

- **Router:** `MemoryRouter` with `Routes` + `Route path="/clusters/:clusterId/report"` for param-based routes (pattern from `source-profile.test.tsx`)
- **Fetch mock:** `vi.stubGlobal("fetch", vi.fn(...))` returning `{ok, json}` objects (pattern from `pipeline-flow.test.tsx`)
- **No store reset needed** — neither ClusterReport nor Timeline imports from zustand store
- **vi.restoreAllMocks():** `beforeEach` calls `vi.restoreAllMocks()` to clean up `vi.stubGlobal("fetch", ...)` between tests (pattern from `pipeline-flow.test.tsx`)
- **Async:** `waitFor` for data-dependent assertions, `screen.getByRole/getByText` for DOM queries

---

## Test plan: cluster-report.test.tsx

### 1. Loading state
- **Given:** fetch hasn't resolved
- **Then:** Renders heading "Cluster Report" + "Loading…" text
- **Given:** fetch returns 404
- **Then:** Renders heading + "Cluster not found" error text

### 2. Error state
- **Given:** fetch rejects (network error)
- **Then:** Renders heading + "Failed to load" text

### 3. Data state — header
- **Given:** valid response with cluster title
- **Then:** Renders heading + cluster title

### 4. Consensus Summary card
- **Given:** valid response with summary stats
- **Then:** Renders claims count, sources count, absorbed count, pending count

### 5. Source Breakdown table
- **Given:** valid response with sources array
- **Then:** Renders "Source Breakdown" heading + table with source domains + tier badges + claim counts

### 6. Claims table
- **Given:** valid response with claims array
- **Then:** Renders "Claims" heading + table with claim text, source domain, state

### 7. Forensic Analysis placeholder
- **Given:** valid response
- **Then:** Renders "Forensic Analysis" heading + placeholder text about convergence data

---

## Test plan: timeline.test.tsx

### 8. Loading state
- **Given:** fetch hasn't resolved
- **Then:** Renders heading "Timeline" + "Loading…" text

### 9. Error state — 404
- **Given:** fetch returns 404
- **Then:** Renders heading + "Cluster not found" error text

### 10. Error state — network
- **Given:** fetch rejects
- **Then:** Renders heading + "Failed to load" text

### 11. Empty state
- **Given:** valid response with zero claims across all sources
- **Then:** Renders heading + cluster title + "No claims in this cluster."

### 12. Data state — header
- **Given:** valid response with claims
- **Then:** Renders heading + cluster title + summary line (sources count, claims count, days)

### 13. Source rows
- **Given:** valid response with 2 sources
- **Then:** Renders source domain labels + tier badges + claim count per source

### 14. Single-claim Timeline (rangeMs fallback)
- **Given:** cluster with exactly 1 claim
- **Then:** Renders without crash (rangeMs = 0 → falls back to `|| 1`)

### 15. positionPercent pure function
- **Given:** firstSeenAt within range
- **Then:** Returns 0% at range start, 100% at range end, correct mid-point

---

## Test data shapes (to use in mock fetch responses)

### ClusterReport mock data
```ts
{
  cluster: { id: 1, title: "Test Cluster", vertical: "geopolitics" },
  summary: { totalClaims: 5, absorbed: 3, pending: 2, sourceCount: 2 },
  sources: [
    { domain: "reuters.com", tier: 1, claims: 3, absorbed: 2, pending: 1 },
    { domain: "bbc.com", tier: 1, claims: 2, absorbed: 1, pending: 1 }
  ],
  claims: [
    { id: 1, text: "Claim one", state: "CONSENSUS_ABSORBED", absorbed_at: "2026-06-01T00:00:00Z", created_at: "2026-06-01T00:00:00Z", domain: "reuters.com" },
    { id: 2, text: "Claim two", state: "PENDING", absorbed_at: null, created_at: "2026-06-01T00:00:00Z", domain: "bbc.com" }
  ]
}
```

### Timeline mock data
```ts
{
  cluster: { id: 1, title: "Test Cluster" },
  sources: [
    { domain: "reuters.com", tier: 1, claims: [
      { id: 1, text: "Claim one", state: "CONSENSUS_ABSORBED", absorbed_at: "2026-06-01T00:00:00Z", first_seen_at: "2026-06-01T00:00:00Z", created_at: "2026-06-01T00:00:00Z" }
    ]},
    { domain: "bbc.com", tier: 1, claims: [
      { id: 2, text: "Claim two", state: "PENDING", absorbed_at: null, first_seen_at: "2026-06-02T00:00:00Z", created_at: "2026-06-02T00:00:00Z" }
    ]}
  ]
}
```

### Empty timeline mock data
```ts
{
  cluster: { id: 1, title: "Empty Cluster" },
  sources: []
}
```

---

## Verification checklist

1. `npm run build` — no regressions
2. `npx vitest run` — all tests pass (139 existing + ~20 new)
3. `npx oxlint src/__tests__/` — no lint errors
4. `ponytail-review` against the diff — no over-engineering

---

## Dependencies / assumptions

- `vitest`, `@testing-library/react`, `@testing-library/user-event`, `jsdom`, `react-router` — all already installed and used by existing tests
- No need to mock Chart.js (neither page uses it)
- Store reset needed — both pages may read from zustand store indirectly (onboarding, active sources). Reset to known state in beforeEach.
- `useParams<{ clusterId: string }>()` requires `MemoryRouter` with `initialEntries` pointing to a valid route with `:clusterId` param
