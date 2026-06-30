# Slice 015 — Timeline Page (Per-Cluster Claim Cascade)

## Problem

The Timeline page (`/timeline/:clusterId`) is an empty stub. The design doc calls for a "Horizontal Day 0–90 animation per claim" but the DB has 3 days of claim data (June 27-29), no state transition log, and all 907 absorptions happened in one batch run (June 30).

Build a hackathon-ready version: per-cluster claim timeline grouped by source, showing when each claim first appeared.

## What was verified

### Data availability

| Claim | Result |
|---|---|
| Claim-bearing clusters with multi-source coverage | 10 clusters, best: #880 (203 claims, 9 sources) |
| first_seen_at distribution | 23 days (June 2026), good spread |
| absorbed_at distribution | Single day (June 30) — all in one batch |
| State transitions (intermediate states) | None — only PENDING → CONSENSUS_ABSORBED |
| Convergence types | All NULL |
| claim_sources JOIN | 2,642 rows, covers all claims |
| Cluster #880 demo quality | 9 sources, 3 days, geopolitical topic (Iran-US) |

### Design doc

Design doc §Timeline: "Horizontal Day 0–90 animation per claim. Echo-mimic dots. CONSENSUS-ABSORBED vertical line. UNRESOLVED claims fade at Day 90."

What we adapt: 3 days of data, no UNRESOLVED claims, no intermediate states. Per-claim first_seen timeline with source grouping replaces the 90-day animation.

### Integration points

- `list_claims()` returns claim rows (no source/domain JOIN)
- No existing `/api/timeline` endpoint
- Nav link points to `/timeline/abc123` (hardcoded — needs cluster ID)
- ClusterReportPage is a separate empty stub (leave it)

## Design

### 1. API endpoint: `GET /api/timeline/{cluster_id}`

Returns claims in a cluster, enriched with source domain and first_seen_at, sorted by first_seen_at:

```json
{
  "cluster": {"id": 880, "title": "Iran-US Strait of Hormuz tensions"},
  "sources": [
    {
      "domain": "theguardian.com",
      "tier": 1,
      "claims": [
        {
          "id": 1421,
          "text": "Lebanon and Israel signed a 14-point framework...",
          "state": "PENDING",
          "absorbed_at": null,
          "first_seen_at": "2026-06-27T15:07:00",
          "created_at": "2026-06-27T15:07:00"
        },
        ...
      ]
    },
    ...
  ]
}
```

Claims grouped by source, ordered by first_seen_at within each group. Sources ordered by earliest first_seen_at.

SQL:
```sql
SELECT cs.first_seen_at, s.domain, s.tier,
       cl.id, cl.text, cl.state, cl.absorbed_at, cl.created_at
FROM claims cl
JOIN claim_sources cs ON cs.claim_id = cl.id
JOIN sources s ON s.id = cs.source_id
WHERE cl.cluster_id = ?
ORDER BY cs.first_seen_at
```

Python groups by source domain.

### 2. Timeline page component

Replace the `<div>Timeline</div>` stub. Layout:

```
┌─ Cluster 4: Iran-US Strait of Hormuz tensions ────────────┐
│ Jun 27 ─────────── Jun 28 ─────────── Jun 29 ─────────────│
│                                                             │
│ theguardian.com (Tier 1, 47 claims)                         │
│   [claim] [claim] [claim] [claim] [claim] ...             │
│                                                             │
│ washingtonpost.com (Tier 2, 14 claims)                     │
│            [claim] [claim] [claim] ...                     │
│                                                             │
│ foxnews.com (Tier 2, 7 claims)                             │
│                       [claim] [claim] ...                  │
│                                                             │
│ ... (9 sources total)                                       │
└─────────────────────────────────────────────────────────────┘
```

Each source row is a horizontal scroll of compact claim cards, positioned at their approximate `first_seen_at` offset. Cards show truncated claim text. Source header shows domain + tier badge. All claims in this cluster are PENDING — no absorption line (data reality).

Design doc alignment:

| Design doc spec | Adaptation |
|---|---|
| Horizontal Day 0–90 animation | Horizontal 3-day layout with claim cards positioned by first_seen_at |
| Echo-mimic dots (dashed connection to origin) | Source-grouped rows — conveys "same origin" via row grouping |
| CONSENSUS-ABSORBED vertical line | Skipped — demo cluster has zero absorbed claims (all in single-source clusters) |
| UNRESOLVED claims fade at Day 90 | Skipped — no unresolved claims in DB |

Why cluster 880 over others:
- Cluster 883 (3 sources, 9 absorbed) has only 1 day of data
- Cluster 880 (9 sources, 203 claims) has 3 days — best cross-source cascade demo
- No multi-source cluster has BOTH multi-day spans AND absorbed claims (data limitation)

Ponytail: pure CSS flexbox, no animation library, no chart.js. Source rows scroll horizontally.

### 3. Nav link fix

Change hardcoded `/timeline/abc123` → `/timeline/880` (best demo cluster).

## What does NOT change
- ClusterReportPage stub (leave as-is)
- No new DB tables, no schema changes
- No chart.js dependency (ponytail: pure CSS flexbox)
- No new npm packages
- Nav test: still checks for "Timeline" link text and page content — both preserved
- ProfileEvent type in scores.ts (used by SourceProfile day scrubber, not Timeline page)

## Implementation order

1. Add `GET /api/timeline/{cluster_id}` endpoint (JOIN claims + claim_sources + sources, group by domain)
2. Add backend tests (returns grouped claims, 404 for nonexistent cluster)
3. Replace Timeline page stub with real component
4. Update nav link `/timeline/abc123` → `/timeline/880`
5. Update tests (nav test expects "Timeline" text — already passes with stub)
6. Full test suite, build, biome, visual check

## Files touched

| File | Change |
|---|---|
| `app/main.py` | Add `/api/timeline/{cluster_id}` endpoint (SQL JOIN + Python grouping) |
| `app/test_routes.py` | Add tests for timeline endpoint |
| `src/pages/Timeline.tsx` | Replace stub with real component |
| `src/components/AppNav.tsx` | Update hardcoded cluster ID |

## Test strategy

- Unit: endpoint returns grouped claims for cluster 880
- Unit: endpoint returns 404 for nonexistent cluster
- Unit: Timeline component renders with mock data
- Integration: nav link points to cluster 880
- Manual: `/timeline/880` shows 9 source groups with claims

## Verification checklist

- [ ] `pytest -m "not network"` — all non-network tests pass
- [ ] `npx vitest run` — all frontend tests pass
- [ ] `npm run build` — TypeScript compiles
- [ ] `npx biome check src/` — no new errors
- [ ] Manual: Timeline page loads at `/timeline/880`
- [ ] Manual: 9 source groups visible, claims positioned by first_seen_at
- [ ] Manual: Nav link navigates to `/timeline/880`
- [ ] Manual: Cluster 404 shows error state
- [ ] ponytail-review: no over-engineering
