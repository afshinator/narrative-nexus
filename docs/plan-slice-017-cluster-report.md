# Slice 017 — Cluster Report Page

## Problem

Cluster Report page (`/cluster/:clusterId`) is an empty stub. Design doc calls for "3-zone forensic report (consensus summary / distortion matrix / forensic analysis)" but no distortion matrix is possible — zero claims have multiple sources (each claim attributed to exactly one source), and zero claims have convergence types.

Build a hackathon-ready version: cluster claim summary dashboard with source breakdown, claim list, and state distribution.

## What was verified

### Data reality

| Fact | Value |
|---|---|
| Total clusters | 656 |
| Best demo cluster | #880: 203 claims, 9 sources, 3 days (geopolitical) |
| Claims with >1 source | 0 / 3,345 — distortion matrix impossible |
| Convergence types | All NULL — forensic analysis limited |
| Mixed-state clusters | 4: #883 (34 claims), #904 (13), #905 (8), #890 (7) |
| All other clusters | Single-state (all PENDING or all ABSORBED) |

### Design doc

"3-zone forensic report (consensus summary / distortion matrix / forensic analysis). Version indicator. Config-change banner. Consensus-reality language throughout."

| Zone | Feasibility |
|---|---|
| Consensus summary | ✓ Absorbed/pending counts per source |
| Distortion matrix | ✗ No multi-source claims — no claim overlap to compare |
| Forensic analysis | ✗ No convergence types — no cross-source validation metadata |

### Existing infrastructure

| Endpoint | Returns |
|---|---|
| `/api/clusters` | Cluster list (id, title, vertical) |
| `/api/claims?cluster_id=X` | Claims for cluster (no source domain) |
| `/api/timeline/{cluster_id}` | Source-grouped claims with first_seen_at |

## Design

### 1. API endpoint: `GET /api/clusters/{cluster_id}/report`

Returns aggregate stats + claims with source domain for one cluster:

```json
{
  "cluster": {"id": 880, "title": "Cluster 4", "vertical": "geopolitics"},
  "summary": {
    "totalClaims": 203,
    "absorbed": 0,
    "pending": 203,
    "sourceCount": 9
  },
  "sources": [
    {"domain": "theguardian.com", "tier": 1, "claims": 47, "absorbed": 0, "pending": 47},
    {"domain": "washingtonpost.com", "tier": 2, "claims": 14, "absorbed": 0, "pending": 14},
    ...
  ],
  "claims": [
    {"id": 1421, "text": "...", "state": "PENDING", "domain": "theguardian.com", "created_at": "..."},
    ...
  ]
}
```

SQL: JOIN claims + claim_sources + sources, group by source for summary. Claim list is the flat JOIN result ordered by created_at.

### 2. Cluster Report page

Three sections matching the 3-zone design (adapted to available data):

```
┌─ Cluster 4 ──────────────────────────────────────────┐
│ consensus summary                                      │
│  203 claims · 9 sources · 0 absorbed · 203 pending    │
├───────────────────────────────────────────────────────┤
│ source breakdown                 claim list            │
│                                ┌──────────────────────│
│ theguardian.com       47        │ "Lebanon signed..."  │
│ washingtonpost.com    14        │ "Tehran said..."     │
│ foxnews.com            7        │ "Iran deployed..."   │
│ npr.org               12        │ "Trump said..."      │
│ ...                             │ ...                  │
├───────────────────────────────────────────────────────┤
│ forensic analysis                                      │
│  No convergence-type data (not yet computed by Agent 3)│
└───────────────────────────────────────────────────────┘
```

Ponytail: two-column layout. Left: source breakdown table. Right: claim list table. Forensic section shows placeholder text explaining the data limitation.

### 3. Nav link fix

Change `/cluster/abc123` → `/cluster/880` (best demo cluster).

## What does NOT change

- Timeline page — separate page, different view
- No new DB tables, no schema changes
- No chart libraries (ponytail: pure tables)
- `list_claims` function — unchanged, new endpoint handles JOIN
- Nav test: still checks for "Cluster Report" link text

## Known design doc adaptations

| Design doc | Plan | Rationale |
|---|---|---|
| 3-zone forensic report | 3 sections (summary, sources, analysis) | Data limitations prevent full forensic depth |
| Distortion matrix | Source breakdown table | Zero multi-source claims — no claim overlap to matrix |
| Forensic analysis | Placeholder text | Zero convergence types — no cross-source validation |
| Version indicator | Skipped | No version tracking in DB |
| Config-change banner | Skipped | No config change tracking |

## Grill-with-docs findings

| Decision | Result |
|---|---|
| Consensus summary data | ✓ 203 claims, 9 sources, absorbed/pending counts available |
| Distortion matrix feasibility | ✗ 0/3345 claims have >1 source — source table replaces matrix |
| Forensic analysis content | Placeholder: "No convergence-type data (not yet computed by Agent 3)" |
| New endpoint vs enhance /api/claims | New endpoint — avoids changing list_claims contract for all callers |
| Nav link change | /cluster/abc123 → /cluster/880 — nav test checks text, not URL |
| Claim ordering | Matches existing /api/claims pattern: ORDER BY created_at DESC |

## Adversarial review

| Attack | Result |
|---|---|
| Cluster with no claims? | Returns summary with zeros + empty claims array |
| Nonexistent cluster ID? | 404 via get_cluster check |
| Adding fields breaks existing /api/claims? | New endpoint, existing untouched |
| Nav test breaks from URL change? | Test checks link text + page content, not URL |
| 2843 clusters — which to demo? | 880 best (9 sources, 203 claims, geopolitical)

## Implementation order

1. Add `GET /api/clusters/{cluster_id}/report` endpoint (JOIN + aggregate)
2. Add backend tests
3. Replace ClusterReport stub with real component
4. Update nav link `/cluster/abc123` → `/cluster/880`
5. Full test suite, build, biome, visual check

## Files touched

| File | Change |
|---|---|
| `app/main.py` | Add `/api/clusters/{cluster_id}/report` endpoint |
| `app/test_routes.py` | Add tests for report endpoint |
| `src/pages/ClusterReport.tsx` | Replace stub with real component |
| `src/components/AppNav.tsx` | Update nav link cluster ID |

## Test strategy

- Unit: endpoint returns cluster with summary, sources, claims
- Unit: endpoint returns 404 for nonexistent cluster
- Unit: ClusterReport renders with mock data
- Existing: nav test still passes (checks for "Cluster Report" text)

## Verification checklist

- [ ] `pytest -m "not network"` — all non-network tests pass
- [ ] `npx vitest run` — all frontend tests pass
- [ ] `npm run build` — TypeScript compiles
- [ ] `npx biome check src/` — no new lint errors
- [ ] Manual: `/cluster/880` shows summary + source table + claim list
- [ ] Manual: `/cluster/99999` shows 404 error
- [ ] Manual: Nav link navigates to `/cluster/880`
- [ ] ponytail-review: no over-engineering
