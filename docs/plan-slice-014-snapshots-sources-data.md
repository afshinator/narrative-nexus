# Slice 014 — Snapshot Recomputation + Sources Page Data

## Problem

Only 5 of 37 sources show reputation data because snapshots were computed before the pipeline produced claims for all sources. Now that 11 sources have claims (1,098 CONSENSUS_ABSORBED, 907 with absorbed_at), the snapshot compute functions can produce r_orig, r_val, r_speed, and archetypes for all 11.

Additionally, the Sources page scatter plot never fetches data — it receives `scores={[]}` from the router. The Source Profile page has an API endpoint but only 5 sources have r_val in the snapshots table.

## What was verified

**Compute functions produce correct output for 11 sources:**

| Function | Sources with data | Sample |
|---|---|---|
| `compute_r_orig_raw` | 11 | BBC=100.0, WaPo=0.0 |
| `compute_r_val_raw` | 11 | BBC=80.0, WaPo=0.0 |
| `compute_r_speed_raw` | 8 (needs absorbed_at) | Fox=85.7, WaPo=0 |
| `percentile_rank` | 11 / 11 / 8 | Correct 0-100 mapping |
| `compute_panel_medians` | N/A | r_orig=50.0, r_val=50.0 |
| `get_archetype` | 11 | BBC=EARLY_BREAKER, NPR=CONSENSUS_FOLLOWER |

**Current snapshot state:**
- 44,326 rows (37 sources × 1,198 days)
- 1,646 have r_val (0.04%) — only 5 sources from seed
- Profile endpoint queries `WHERE source_id=? AND vertical=? ORDER BY date` — returns all rows
- Sources page receives `scores={[]}` from router — never populated

**Integration point:**
- `_compute_and_write_snapshots(conn)` in `pipeline/runner.py` already exists — computes all dimensions, writes one row per source for today
- `insert_snapshot()` uses `INSERT OR REPLACE` via UNIQUE(source_id, vertical, date) — overwrites existing row for today
- Profile endpoint already works — new snapshots would be picked up automatically

## Design

### 1. Run snapshot computation

One command: `_compute_and_write_snapshots(conn)` against the production DB. This:
1. Computes r_orig_raw, r_val_raw, r_speed_raw from all claims (11 sources → 11 with data)
2. Percentile ranks to 0-100
3. Assigns archetypes (EARLY_BREAKER, CONSENSUS_FOLLOWER, etc.)
4. Writes one snapshot row per source for today's date (37 rows, 11 with values)

The existing 44,326 seed rows stay untouched. The new row for today appends to the history.

### 2. Add Sources page API endpoint

`GET /api/scores?vertical=geopolitics` returns per-source `ReputationScore` objects from the latest snapshot. The `sourceId` field uses the source's `domain` (string, e.g. "reuters.com") so the frontend can match against `DEFAULT_SOURCES`.

Response shape:
```json
{
  "scores": [
    {"sourceId": "bbc.com", "vertical": "geopolitics", "R_orig": 100.0, "R_val": 80.0, "R_speed": 42.9, "R_frame": null, "R_edit": null, "R_correct": null},
    ...
  ]
}
```

Null dimensions (R_frame, R_edit, R_correct) stay null — frontend defaults them to 0.

### 2b. Sources page domain→id mapping

`DEFAULT_SOURCES.id` uses slugs ("reuters", "bbc") while DB returns domains ("reuters.com"). The Sources page builds a `Map<domain, id>` from `DEFAULT_SOURCES` on mount, then maps `score.sourceId` (domain) → `source.id` (slug) before looking up in `scoreMap`.

## What does NOT change
- Seed snapshots (44,326 rows) — untouched, they show historical trends
- Profile endpoint — already works, picks up new snapshot rows automatically
- `_compute_and_write_snapshots` function — unchanged, just invoked
- Schema — no changes

## Implementation order

1. ~~Run `_compute_and_write_snapshots` against nn.db~~ DONE — recomputed 2026-06-28, all 11 claim-bearing sources have real values (r_orig, r_val, r_speed). 26 non-claim sources have NULLs (frontend handles with `?? 0`).
2. Add `GET /api/scores` endpoint — JOIN sources.domain, latest snapshot per source (WHERE vertical=geopolitics)
3. Add backend tests for `/api/scores`
4. Wire Sources page: fetch `/api/scores`, build domain→id map, pass to scatter/table
5. Update Sources page tests
6. Full test suite, build verification

## Files touched

| File | Change |
|---|---|
| `app/main.py` | Add `/api/scores` endpoint (JOIN sources.domain, MAX(date) from snapshots) |
| `app/test_routes.py` | Add tests for scores endpoint |
| `src/pages/Sources.tsx` | Fetch scores, build domain→id map, pass to scatter/table |
| `src/__tests__/sources.test.tsx` | Update for data fetching + domain mapping |
| *(no pipeline changes — snapshot compute functions unchanged)* | |

## Test strategy

- Unit: `/api/scores` returns 11 sources with scores for geopolitics
- Unit: `/api/scores` returns empty array when no snapshots exist
- Unit: Sources page renders with fetched scores
- Integration: existing profile endpoint tests continue passing
- Manual: Sources page scatter plot shows 11 dots after recomputation

## Verification checklist

- [ ] `pytest -m "not network"` — all non-network tests pass
- [ ] `npm run build` — TypeScript compiles
- [ ] Manual: `_compute_and_write_snapshots` writes 37 rows to snapshots
- [ ] Manual: Sources page shows scatter plot with 11 source dots
- [ ] Manual: Source Profile radar shows real data for BBC, Guardian, etc.
- [ ] Manual: 26 sources show empty state (expected — no claims yet)
