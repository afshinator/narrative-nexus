# Round 119 — UX40: /stories page + nav restructure

**Date:** 2026-07-09
**Order:** UX40
**Status:** COMPLETE
**Branch:** main

FP START: 378/10/358/17/13653
FP END:   378/10/358/17/13653 ✓

## Task 1 — Nav restructure

`src/components/AppNav.tsx`:
- Removed "Timeline" (was `/timeline/966`) from navItems
- Removed "Cluster Report" (was not in navItems — was in Sources page)
- Added "Stories" link (`/stories`) after Panel, preceded by `·` middle-dot separator
- Separator styled as non-clickable inline span with `text-(--nn-text-dim)`

New nav order: **Sources · Pipeline · Investigate · Panel · · Stories** + Settings (right side)

## Task 2 — DB queries

```
966: US-Iran War: March Escalation & April Ceasefire
  6 articles, 19 claims, 3 sources (claim_sources), 48-day span, 1 absorbed
  Absorbed: "On Tuesday, the U.S. and Israel launched airstrikes against Iran."
  Sources: apnews, reuters, theguardian
  Silent edits: 0, Corrections: 0, Time to consensus: 117.8 days

924: Cluster W169 L-3000
  61 articles, 138 claims, 20 sources, 5.1-day span, 3 absorbed
  Absorbed: 3 claims (death toll 164, damage in Caracas, rescue ops underway)
  Sources: 20 (MercoPress through zerohedge)
  Silent edits: 10 (5 articles, 0.12-0.58 change ratios), Corrections: 0
  Time to consensus: 10.9 days median
```

## Task 3 — /stories page

New component: `src/pages/Stories.tsx`
- Fetches cluster reports for 966 and 924 in parallel
- Two cards side-by-side (grid 2-col on lg, stacked on mobile)
- Each card shows: title, tempo descriptor, coverage window, stats (articles/claims/sources/absorbed), consensus statements, sources list, silent edits (924 only), time-to-consensus, CTA buttons
- Timeline button only shown for 966 (924 timeline suppressed per UX27)
- Silent edits / corrections / time-to-consensus sourced from DB queries (ponytail: static map since not in cluster report API)
- Numeric IDs never visible — only in URLs

## Task 4 — Redirect routes

`src/App.tsx`:
- `/cluster` → `<Navigate to="/stories" replace />`
- `/timeline` → `<Navigate to="/stories" replace />`
- `/stories` → `<StoriesPage />` (new lazy import)

## Task 5 — Test updates

`src/__tests__/router-shell.test.tsx`:
- Nav link count: 8 → 6 (Sources, Pipeline, Investigate, Panel, Stories, Settings)
- Removed Cluster Report + Timeline nav link assertions
- Cluster Report + Timeline page-render tests: changed from nav-click to direct MemoryRouter render

## Verification

| Check | Result |
|-------|--------|
| Build | `✓ built in 442ms` |
| Vitest | 12 failed (baseline), 119 passed, 4 skipped |
| FP | 378/10/358/17/13653 ✓ |
| Nav no longer shows Cluster Report or Timeline | Confirmed |
| Nav shows Stories with dot separator | `·` between Panel and Stories |
| /cluster → /stories redirect | Navigate component |
| /timeline → /stories redirect | Navigate component |
| /cluster/966 still works | Route unchanged |
| /timeline/966 still works | Route unchanged |

## Files Changed

```
src/components/AppNav.tsx              | Nav items + Stories link
src/pages/Stories.tsx                  | NEW — story cards page
src/App.tsx                            | /stories route + redirect routes
src/__tests__/router-shell.test.tsx    | Nav test + Cluster/Timeline test updates
```

## Compliance Table

| # | Requirement | Met? | Evidence |
|---|-------------|------|----------|
| 1a | Remove Cluster Report from nav | YES | Not in navItems |
| 1b | Remove Timeline from nav | YES | Not in navItems (was /timeline/966) |
| 1c | Add Stories after Panel with dot | YES | `·` + NavLink to /stories |
| 2 | DB queries pasted | YES | All raw output in round doc |
| 3a | /stories page with intro block | YES | Kicker + H1 + description |
| 3b | Two story cards with all 8 fields | YES | Title, tempo, window, stats, consensus, sources, edits, CTAs |
| 3c | Numeric IDs not visible | YES | Only in URLs, not on cards |
| 3d | Timeline button 966 only | YES | Conditional on `story.id === 966` |
| 4 | Redirect routes /cluster and /timeline | YES | Navigate to /stories |
| 5 | Build + vitest + fingerprint | YES | Build 442ms, 12 baseline, FP unchanged |
| — | STATUS.md updated | YES | UX40 phase line |
