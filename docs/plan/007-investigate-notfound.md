# Plan: Slice 7 — Investigate + NotFound Pages

## Requirements addressed

### Investigate

| Req | Description | How |
|-----|-------------|-----|
| REQ-090 | Snapshot banner about ad-hoc reports | Static info card with exact design doc text |
| REQ-117 | Accept article URL or pasted text as query input | Search form with textarea + submit button |
| REQ-118 | Display extracted atomic claims from stages 1-3 | Results section showing claims with metadata |
| REQ-119 | Display cross-source matches and consensus comparison per claim | Each claim shows matching source count + consensus pool % |
| REQ-120 | Persist results in localStorage via zustand persist | Store slice `adHocResults` with persist middleware |
| REQ-121 | No writes to reputation tables or database | Results are store-only, not routed through API |
| REQ-122 | Read-only analysis through stages 1-3 | Pipeline stages labeled on results, no stage 4 |
| REQ-070 | Nav link to Investigate page | Already routed (App.tsx), stub replaced |

### NotFound

| Req | Description | How |
|-----|-------------|-----|
| (implicit) | Catch-all 404 page | Already routed as `*` in App.tsx, stub replaced |
| (implicit) | Link back to app | Link to `/` (Sources page) |

## Design doc references

From `docs/design-v1.2.md` §6 (updated):

> **Investigate** — Ad-hoc forensic query tool. Accepts an article URL or pasted text. Runs through pipeline stages 1–3 (Intake & Clustering → Forensic Extraction → Consensus Alignment) as a read-only analysis. Displays extracted atomic claims, cross-source matches, and consensus baseline comparison inline. Results persist in localStorage and survive navigation, refresh, and browser restarts. Snapshot banner: "Claim resolution states are not available for ad-hoc reports." Does not write to reputation tables. Does not require database persistence for results.

NotFound has no design doc section — standard 404 pattern.

## Dependencies

| Dep | Version | Where | Verified? |
|-----|---------|-------|-----------|
| react | ^19.2.7 | package.json | Yes |
| react-router | ^7.18.0 | package.json | Yes — routes exist |
| zustand | ^5.0.14 | package.json | Yes — persist middleware already configured |
| lucide-react | ^1.21.0 | package.json | Yes — Search, Send, FileText, ExternalLink icons |

No new dependencies.

## Key assumptions (verified against codebase)

1. **Routes exist** — App.tsx:23 `/investigate`, App.tsx:26 `*` (NotFound). Nav link at AppNav.tsx:13.

2. **zustand persist already configured** — store.ts uses `persist` middleware with `name: "nn-store"`. Adding `adHocResults` array will be auto-persisted to localStorage. Same pattern as existing fields.

3. **No mock files** — `docs/mocks/` contains no investigate or not-found mocks. Design from scratch using existing page patterns.

4. **CSS tokens exist** — all `--nn-*` variables defined. Card pattern: `rounded-[14px] border border-[var(--nn-border)] bg-[var(--nn-surface)] p-6`.

5. **Existing router-shell test** — line 73-79 tests navigate to `/investigate` and checks for stub text "Investigate". Will update to heading role.

6. **No backend** — search form is interactive but results come from empty store array. Honest empty states, no fabricated data. One code path.

## Data model

### New store types

```ts
interface AdHocClaim {
  text: string;               // extracted claim text
  sources: string[];          // source IDs with matching claims
  consensusPct: number | null;  // % of consensus pool matching (null = no baseline)
}

interface AdHocResult {
  id: string;                 // crypto.randomUUID()
  query: string;              // original URL or pasted text
  timestamp: number;          // Date.now()
  claims: AdHocClaim[];
}
```

### Store changes

Add to `StoreState`:
```ts
adHocResults: AdHocResult[];
addAdHocResult: (result: AdHocResult) => void;
clearAdHocResults: () => void;
```

Default: `adHocResults: []`. zustand persist middleware handles localStorage serialization automatically.

## Investigate page layout

```
┌──────────────────────────────────────────────────────────┐
│ PageShell (AppNav + footer — inherited)                  │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  Investigate                                             │
│  Ad-hoc forensic query tool                              │
│                                                          │
│  ┌──── Snapshot Banner ──────────────────────────────┐  │
│  │ ⚠ Claim resolution states are not available for   │  │
│  │   ad-hoc reports. This analysis runs stages 1–3   │  │
│  │   of the pipeline in read-only mode.              │  │
│  └───────────────────────────────────────────────────┘  │
│                                                          │
│  ┌──── Query ────────────────────────────────────────┐  │
│  │                                                    │  │
│  │  [Paste article URL or text...              ]      │  │
│  │                                        [Submit]     │  │
│  │                                                    │  │
│  └────────────────────────────────────────────────────┘  │
│                                                          │
│  ┌──── Results ─────────────────────────────────────┐  │
│  │                                                    │  │
│  │  Empty state (no queries yet):                     │  │
│  │    "Submit an article URL or paste text to run     │  │
│  │     a forensic analysis through pipeline           │  │
│  │     stages 1–3."                                   │  │
│  │                                                    │  │
│  │  With results:                                     │  │
│  │    ┌── Claim 1 ─────────────────────────────┐     │  │
│  │    │ "The event occurred at 3:45 PM..."     │     │  │
│  │    │ Stage 2: Forensic Extraction           │     │  │
│  │    │ Matches: 3 sources · 45% consensus     │     │  │
│  │    │ Sources: Reuters, AP, BBC              │     │  │
│  │    └────────────────────────────────────────┘     │  │
│  │    ┌── Claim 2 ─────────────────────────────┐     │  │
│  │    │ ...                                    │     │  │
│  │    └────────────────────────────────────────┘     │  │
│  │                                                    │  │
│  │  [Clear Results]                                   │  │
│  │                                                    │  │
│  └────────────────────────────────────────────────────┘  │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

## Investigate implementation details

### Snapshot banner
- Amber-tinted warning card at top of page
- Exact text from design doc: "Claim resolution states are not available for ad-hoc reports."
- Supplemental: "This analysis runs pipeline stages 1–3 in read-only mode."

### Search form
- Textarea (not single-line input) — articles can be long text
- Placeholder: "Paste an article URL or full text..."
- Submit button with Send/Search icon
- On submit: creates an empty `AdHocResult` with the query and no claims (backend does extraction, frontend just stores)
- Without backend: results array stores the query but claims array is empty — honest state

### Results area
- When `adHocResults.length === 0`: show empty state message
- When `adHocResults` has entries: show list of past queries (most recent first)
- Each query result card shows: query text (truncated), timestamp, claim count (0 without backend)
- "Clear Results" button removes all results from store
- Individual result cards are not deletable (simpler, same as session persistence)

### Results persist behavior
- zustand persist middleware handles localStorage serialization
- Results survive: in-app navigation, page refresh, browser close/reopen
- No per-query delete — only "Clear All"
- No per-result expansion/collapse in initial implementation (ponytail: add when needed)

## NotFound page layout

```
┌──────────────────────────────────────────────────────────┐
│ PageShell (AppNav + footer — inherited)                  │
├──────────────────────────────────────────────────────────┤
│                                                          │
│                    Page not found                        │
│     The page you're looking for doesn't exist.           │
│                                                          │
│                 ← Back to Sources                        │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

Simple centered layout, matching the app's design tokens. Link back to `/`.

## New files

| File | Purpose |
|------|---------|
| `src/pages/Investigate.tsx` | Full page component (replaces stub) |
| `src/pages/NotFound.tsx` | Full page component (replaces stub) |
| `src/__tests__/investigate.test.tsx` | Test suite |
| `src/__tests__/not-found.test.tsx` | Test suite |

## Existing files modified

| File | Change |
|------|--------|
| `src/store.ts` | Add `AdHocResult`, `AdHocClaim` types, `adHocResults` state, `addAdHocResult` and `clearAdHocResults` actions |
| `src/__tests__/router-shell.test.tsx` | Update Investigate nav test from `getByText` to heading role |

No route changes needed. No nav changes needed.

## Implementation order

1. **Store types + actions** — Add `AdHocResult`/`AdHocClaim`, state, and actions to store.ts
2. **NotFound page** — Simple 404 with heading, message, link home. Trivial — one test cycle.
3. **Investigate page shell + banner** — Heading, subtitle, snapshot banner card
4. **Investigate search form** — Textarea + submit button, stores query on submit
5. **Investigate results area** — Displays past queries from store, empty state, clear button
6. **Tests** — Store tests, page tests for both pages
7. **Update router-shell test** — Investigate nav test updated

## Test strategy

### Store tests

| Test | What it verifies |
|------|-----------------|
| adHocResults defaults to empty array | Initial state |
| addAdHocResult appends result | Action works |
| clearAdHocResults clears array | Action works |

### Investigate page tests

| Test | What it verifies |
|------|-----------------|
| Renders page heading | "Investigate" heading present |
| Renders snapshot banner | Exact text from design doc |
| Renders search textarea | Textarea element present |
| Renders submit button | Submit button present |
| Submitting stores query | Query appears in results after clicking submit |
| Shows empty state when no results | Placeholder message visible |
| Shows past queries in results | Stored results render |
| Clear results button works | Results cleared from store |
| Integrates with nav | Existing router-shell test updated |

### NotFound page tests

| Test | What it verifies |
|------|-----------------|
| Renders "Page not found" heading | Heading present |
| Renders link back to Sources | Link to `/` present |
| Renders descriptive message | User-friendly message present |

## Verification checklist

- [ ] `npm run build` exits 0
- [ ] `npx vitest run` — all tests pass (existing 119 + new tests)
- [ ] `npx biome check src/` — no new errors
- [ ] Dev server: Investigate page renders at `/investigate`
- [ ] Dev server: NotFound renders for unknown route
- [ ] Search form accepts text, submit stores to localStorage
- [ ] Results persist across page navigation
- [ ] Snapshot banner shows correct text

## Deferred items

- **Per-claim cross-source details** — needs backend stage 3 output
- **Per-result deletion** — not in spec, add when needed
- **Result expansion/collapse** — not in spec, add when backend produces claim data
- **Pipeline stage progress animation** — not in spec, add when backend runs stages
