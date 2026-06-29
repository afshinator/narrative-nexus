# Slice 012 — Vf Trend Chart + Tier Average Radar Polygon

## Status of 5 deferred UI items

| # | Item | Status | Blocker |
|---|---|---|---|
| 1 | Timeline event markers | **Blocked** | No state transition timestamps (absorbed_at NULL). Agent 4 prints edits, no DB writes. |
| 2 | Vf trend chart | **Ready** | `r_val` exists in snapshots (1,646 rows, 5 sources). |
| 3 | Outlier waterfall | **Blocked** | 0 UNRESOLVED claims. Agent 3 only absorbs/pends, no rejection path. |
| 4 | Silent edit log | **Blocked** | No `silent_edits` table. Agent 4 writes to stdout only. |
| 5 | Tier average radar polygon | **Ready** | `r_orig`, `r_val` exist per source. Aggregatable by tier via JOIN. |

This slice implements items 2 and 5. Items 1, 3, 4 remain in `docs/deferred.md` with updated blocker descriptions.

## What exists

**SourceProfile page** (`src/pages/SourceProfile.tsx`, 630 lines):
- Full radar chart (6-axis, animated day scrubber, baseline overlay)
- 30-day sparkline grid (6 dimensions × SVG polylines)
- Stat panel (current values, deltas from day 0)
- Archetype badge
- Day scrubber with play/pause animation
- **Already accepts `tierAvg?: number[]` prop** — RadarChart renders a dashed "Tier avg" polygon overlay when provided. Zero data currently passed.
- Rendered at `/source/:domain` with **no props** — shows empty state.

**Sources page** (`src/pages/Sources.tsx`, 258 lines):
- Scatter plot, archetype pills, sortable score table. No radar.

**API:**
- `/api/snapshots?source_id=N&vertical=X` — returns raw DB rows (date strings, snake_case)
- No endpoint maps DB dates → frontend `day: 0–90` format
- No tier average endpoint

**Data (nn.db):**
- 44,326 snapshots, 37 sources, 1,198 days
- `r_val` non-null for 5 sources: CNN (1,198 days), BBC (425), theguardian (12), foxnews (8), npr (3)
- `r_orig` non-null for 5 sources: same pattern
- `r_speed`, `r_frame`, `r_edit`, `r_correct`: all NULL (not yet computed)
- Most sources have 0 r_val because snapshots were computed before articles existed

**Dependencies:** chart.js 4.5.1, react-chartjs-2 5.3.1 (already installed)

## Design

### 1. Backend: profile endpoint

New route `GET /api/sources/<source_id>/profile?vertical=geopolitics`:

Returns:
```json
{
  "snapshots": [
    {"day": 0, "R_orig": 75, "R_val": 60, "R_speed": null, ...},
    ...
  ],
  "tierAvg": [50, 55, 48, 52, 40, 45],
  "panelMedian": {"orig": 50, "val": 50}
}
```

Mapping:
- `source_id` (int) from URL param
- Query snapshots WHERE source_id=? AND vertical=? AND r_val IS NOT NULL ORDER BY date
- Map dates to sequential `day` integers starting from 0
- Compute `tierAvg`: average r_orig and r_val per dimension for sources in same tier
- Compute `panelMedian`: median r_orig and r_val across all active sources
- NULL dimensions → `null` in response (frontend handles missing)

### 2. Frontend: Vf trend chart component

New component in `src/components/VfTrendChart.tsx`:
- Line chart using chart.js `Line` (CategoryScale, LinearScale already needed — register)
- X-axis: day 0–90
- Y-axis: r_val 0–100
- Single line, teal color (`var(--nn-teal)`)
- Rendered on SourceProfile page below the sparkline grid
- Props: `snapshots: DailySnapshot[]`, `currentDay: number`
- Marks current day position with a vertical reference line or dot

### 3. Frontend: wire data to SourceProfile

- SourceProfile fetches `/api/sources/<id>/profile?vertical=<active>` on mount and vertical change
- Passes `snapshots`, `tierAvg`, `panelMedian` to existing components
- Existing empty-state rendering handles the loading/missing-data case
- Tier radar polygon appears automatically (RadarChart already renders it when tierAvg is provided)

### 4. Data coverage note

Full Vf trend data requires:
1. Body extraction completed (`extract_pending`) — running in background
2. Pipeline re-run (`run_daily_pipeline`) — recomputes snapshots from new articles

After both: all 37 sources will have r_val data. Until then, only 5 sources show trends.

## Files touched

| File | Change |
|---|---|
| `app/main.py` | Add `GET /api/sources/<source_id>/profile` endpoint |
| `src/data/scores.ts` | No changes (DailySnapshot, DIMENSIONS already correct) |
| `src/pages/SourceProfile.tsx` | Fetch data on mount + vertical change. Pass tierAvg. Import VfTrendChart. |
| `src/components/VfTrendChart.tsx` | New: line chart for Vf over time |
| `src/__tests__/source-profile.test.tsx` | Update tests for data fetching, tierAvg rendering |
| `src/__tests__/vf-trend-chart.test.tsx` | New: VfTrendChart component tests |
| `docs/deferred.md` | Update: mark items 2+5 done, update blockers for 1+3+4 |

## Implementation order

1. Backend: Add profile endpoint with date→day mapping + tierAvg + panelMedian
2. Backend: Add tests for profile endpoint
3. Frontend: Build VfTrendChart component
4. Frontend: Wire data fetching to SourceProfile, pass tierAvg
5. Frontend: Update existing tests, add VfTrendChart tests
6. Update `docs/deferred.md`

## Test strategy

- Backend: Test profile endpoint returns correct day mapping, tierAvg, panelMedian
- Backend: Test profile endpoint handles missing source_id, empty snapshots
- Frontend: Test VfTrendChart renders with data, empty state, marks current day
- Frontend: Test SourceProfile fetches on mount and vertical change
- Frontend: Test tierAvg polygon appears in radar when data provided
- Integration: `@pytest.mark.network` — live profile endpoint returns real data

## Verification checklist

- [ ] `pytest -m "not network"` — all non-network tests pass
- [ ] `pytest -m network` — profile endpoint returns real CNN data
- [ ] `npm run build` — TypeScript compiles
- [ ] `biome check src/` — no new frontend issues
- [ ] Manual: navigate to `/source/cnn.com` — Vf trend chart renders, tier radar overlay visible
- [ ] Manual: navigate to `/source/nonexistent.com` — "not found" still works
- [ ] `docs/deferred.md` updated: items 2+5 removed, 1+3+4 blockers clarified
