# Slice 016 — Source Profile: Silent Edit Log + Outlier Waterfall

## Problem

SourceProfile page is missing two design-doc sections: silent edit log (41 edits in DB, all on 2026-06-30) and outlier waterfall (claim origination → absorption breakdown). The DayScrubber event markers are hardcoded to `events=[]` — no real data flows in.

## What was verified

### Silent edits (DB)

| Fact | Value |
|---|---|
| Total | 41 rows |
| By source | BBC 28, Guardian 4, Fox 2, 7 others (1 each) |
| Temporal spread | All on 2026-06-30 (batch run — single day) |
| Fields | change_ratio (0.12–0.98), stored/fetched body length, article URL |
| JOIN path | silent_edits → articles → sources |

Best demo source: BBC (28 edits) via `/source/bbc.com`.

### Outlier waterfall (DB)

| Fact | Value |
|---|---|
| Convergence types | ALL NULL — cannot do convergence-type breakdown |
| Claim states per source | BBC: 404 absorbed / 181 pending / 585 total; Guardian: 230/231/461 |
| What's possible | Simple bar/bullet: "X absorbed · Y pending · Z total" |

Design doc says "outlier waterfall with convergence-type breakdown" — adapted to absorbed-vs-pending breakdown since convergence types don't exist.

### SourceProfile page

| Section | Status |
|---|---|
| Radar | Implemented |
| StatPanel | Implemented |
| SparklineGrid | Implemented |
| VfTrendChart | Implemented |
| DayScrubber | Implemented (but events=[] hardcoded) |
| Silent edit log | **Missing** |
| Outlier waterfall | **Missing** |

Profile endpoint returns: `snapshots`, `tierAvg`, `panelMedian`. No `events` or `edits` or `claimSummary`.

## Design

### 1. Extend profile endpoint

Add three fields to `GET /api/sources/{source_id}/profile` response:

```json
{
  "snapshots": [...],
  "tierAvg": [...],
  "panelMedian": {...},
  "events": [
    {"day": 87, "type": "SILENT_EDIT", "title": "Article edited by 33%", "detail": "abc..."},
    {"day": 90, "type": "CLAIM_ABSORBED", "title": "12 claims absorbed", "detail": ""}
  ],
  "edits": [
    {"id": 1, "change_ratio": 0.33, "stored_length": 15039, "fetched_length": 7944,
     "article_url": "...", "article_title": "...", "detected_at": "..."}
  ],
  "claimSummary": {
    "total": 585,
    "absorbed": 404,
    "pending": 181
  }
}
```

**Events** (`ProfileEvent[]`): Aggregate — one event per type, not one per row. BBC has 404 absorbed claims; showing 404 dots on the DayScrubber would be unreadable. Instead, emit one event per type at the appropriate day:

```python
# ponytail: aggregate events to avoid cluttering the scrubber
events = []
if absorbed_count > 0:
    events.append({"day": event_day, "type": "CLAIM_ABSORBED",
                    "title": f"{absorbed_count} claims absorbed", "detail": ""})
if edit_count > 0:
    events.append({"day": event_day, "type": "SILENT_EDIT",
                    "title": f"{edit_count} edits detected", "detail": ""})
```

Day is computed as `(event_date - first_snapshot_date) / (last_snapshot_date - first_snapshot_date) * DAY_MAX`, clamped to [0, DAY_MAX]. For current data, all events fall at day 90.

**Edits** (`silent_edits` rows): Full edit log for the source. Each row has change_ratio, lengths, article info.

**claimSummary**: Simple counts of claims attributed to this source.

### 2. Silent edit log section

Add below DayScrubber. Table layout:

```
┌─ Silent Edit Log ────────────────────────────────────┐
│ Article                  │ Change │ Stored → Fetched │
│ "Rosatom will hold..."   │  33%   │ 15,039 → 7,944   │
│ "Monday, June 29..."     │  98%   │    622 → 1,546   │
└──────────────────────────────────────────────────────┘
```

Each row links to the article URL. change_ratio shown as percentage with color coding (green <10%, amber 10-30%, red >30%).

### 3. Outlier waterfall section

Add above Sparklines. Mini bar visualization:

```
┌─ Claim Flow ─────────────────────────────────────────┐
│ Absorbed ████████████████████░░░░░ 404 (69%)         │
│ Pending  █████████░░░░░░░░░░░░░░░ 181 (31%)          │
│ Total claims originated: 585                          │
└──────────────────────────────────────────────────────┘
```

Ponytail: CSS-only bar (div with percentage width), no chart library.

### 4. Wire DayScrubber events

Already implemented — just pass real events from API. `events` field (currently `[]`) gets populated from the profile response. Event dots appear on day scrubber: teal for CLAIM_ABSORBED, amber for SILENT_EDIT.

## What does NOT change
- Radar, StatPanel, SparklineGrid, VfTrendChart — untouched
- No new endpoints (extend existing `/api/sources/{id}/profile`)
- No new npm packages
- No schema changes
- SourceProfile test: existing tests check for radar/sparkline — unaffected

## Known design doc adaptations

| Design doc | Plan | Rationale |
|---|---|---|
| "convergence-type breakdown" | Absorbed-vs-pending breakdown | All convergence types are NULL in DB |
| "human review UI" for silent edits | Read-only table | No review workflow implemented; display-only for hackathon |
| Day 0–90 event markers | Aggregated events at day 90 | 404 individual dots would overwhelm scrubber; one dot per type |

## Grill-with-docs findings

| Decision | Result |
|---|---|
| Endpoint extension vs new routes | Extend profile — ponytail, no new routes ✓ |
| Day mapping for events | 90.2 → clamp to 90. Verified against actual snapshot range ✓ |
| Claim counting (DISTINCT vs raw) | claim_sources PK prevents dupes, but use DISTINCT for correctness |
| Event aggregation | Changed: one event per type, not one per row (404 dots = unreadable) |
| Section ordering | Outlier waterfall after VfTrend, edit log after waterfall (matches design doc order) |
| Component `events` prop | Already wired — just populate from API (simpler than planned) |
| Empty states | Source with 0 edits → "No silent edits detected"; 0 claims → "No claims attributed" |

## Adversarial review findings

| Attack | Result |
|---|---|
| Source with edits but no snapshots? | 0 sources — safe |
| Day calculation overflow? | 90.2 → clamped to 90 — safe |
| Source with 0 claims? | Some sources have 0 — claimSummary shows zeros |
| Adding fields breaks existing profile tests? | Tests check for `snapshots`/`tierAvg`/`panelMedian` — extra fields ignored |

## Implementation order

1. Extend profile endpoint: add `events`, `edits`, `claimSummary` queries after existing snapshot/tierAvg queries
2. Add backend tests for new fields
3. Add silent edit log component section to SourceProfile
4. Add outlier waterfall section to SourceProfile
5. Wire events into DayScrubber (replace `events=[]`)
6. Full test suite, build, biome, visual check

## Files touched

| File | Change |
|---|---|
| `app/main.py` | Add 3 SQL queries to profile endpoint (edits, claim summary, events) |
| `app/test_routes.py` | Add assertions for new profile response fields |
| `src/pages/SourceProfile.tsx` | Add EditLog + OutlierWaterfall sections, wire events from API |

## Test strategy

- Unit: profile endpoint includes edits for source with silent edits
- Unit: profile endpoint includes claimSummary with absorbed/pending counts
- Unit: profile endpoint includes events for source with edits/absorptions
- Unit: SourceProfile renders edit log when edits present
- Unit: SourceProfile renders claim summary when data present
- Unit: SourceProfile passes events to DayScrubber
- Existing: profile snapshot/tierAvg tests continue passing

## Verification checklist

- [ ] `pytest -m "not network"` — all non-network tests pass
- [ ] `npx vitest run` — all frontend tests pass
- [ ] `npm run build` — TypeScript compiles
- [ ] `npx biome check src/` — no new lint errors
- [ ] Manual: `/source/bbc.com` shows silent edit log (28 edits)
- [ ] Manual: `/source/bbc.com` shows claim waterfall (404 absorbed / 181 pending)
- [ ] Manual: DayScrubber has event dots for edits and absorptions
- [ ] Manual: Source with no edits (e.g. dw.com) shows empty states
- [ ] ponytail-review: no over-engineering
