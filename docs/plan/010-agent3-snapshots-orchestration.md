# Plan — 010: Agent 3 Hardening + Daily Snapshots + Pipeline Orchestration

**Date:** 2026-06-26
**Status:** Plan
**Depends on:** Slice 8c (consensus engine — agent 3, consensus.py, resolution.py)
**Depended on by:** Timeline, Vf chart, waterfall, edit log, tier avg (all 5 blocked items)

## Scope

Three related pieces, all pure Python/DB — zero API keys needed:

1. **Agent 3 hardening** — run on ALL clusters instead of one, apply resolution schedule
2. **Daily snapshot computation** — compute R_orig, R_val, R_speed per source per vertical per day from claim data. Write to snapshots table.
3. **Pipeline orchestration** — a runner that sequences agent 3 → snapshot computation, integrated with APScheduler

## Assumptions validated

### Agent 3 state machine is correct
- `determine_state()` in `pipeline/resolution.py` — baseline ≥ threshold → CONSENSUS_ABSORBED, day ≥ 90 → UNRESOLVED, else PENDING. Design §4 [LOCKED]. No changes needed.
- `compute_baseline_pct()` in `pipeline/consensus.py` — correct per review-03 H03 fix.
- Agent runs on ONE cluster_id today (`run(cluster_id=...)`). Missing: loop over all clusters.

### R_orig is computable from claim data
- `claim_sources` has `first_seen_at` timestamp. For each claim, sort by `first_seen_at` — first source = originator.
- Count origins per source per vertical. Join through claims → clusters for vertical. Pure SQL.

### R_val is computable from claim data
- Claims originated by source where `state = CONSENSUS_ABSORBED` / total originated. Pure SQL.

### R_speed is computable from claim data
- For absorbed claims originated by source: median of `(absorbed_at - created_at)` in days. Pure date math.

### R_frame, R_edit, R_correct are NULL
- Design doc §3 Data Format Contracts: "Dimensions not yet computable until their respective agents are built." NULL is correct.

### Archetype is a pure function
- `pipeline/archetype.py:get_archetype()` — matches TS `src/utils/archetype.ts` exactly. 5 tests exist in `pipeline/test_archetype.py`. No changes needed.

### Snapshots CRUD exists
- `db/snapshots.py` — `insert_snapshot()`, `list_snapshots()`, `get_source_vertical_snapshot()`. All tested. No changes needed.

### APScheduler already runs scraper
- `ScraperScheduler` in `pipeline/scheduler.py` uses APScheduler. Can add a second job for daily pipeline run.

## Architecture decisions

1. **Agent 3 runs on all clusters.** Add `run_all()` method that lists all clusters and calls `_run()` for each. Keep `run(cluster_id)` for single-cluster use (tests, ad-hoc).
2. **Snapshot computation is a standalone module.** `pipeline/snapshots.py` — pure functions: compute R_orig, R_val, R_speed per source per vertical, compute archetype, compute panel medians, write snapshots. No agent subclass — this is data aggregation, not an AI agent.
3. **Pipeline runner is a function, not a class.** `pipeline/runner.py` — `run_daily_pipeline(db_path)` calls agent 3, then snapshot computation. Scheduled via APScheduler. No state, no class — one function.
4. **Resolution schedule is the runner's concern.** Runner calls agent 3 daily. Agent 3's `determine_state()` handles the 90-day forced UNRESOLVED. No separate 7/30/90 day scheduling — daily run naturally re-evaluates claims. Claims that cross threshold get absorbed on the day they do.
5. **APScheduler job: daily at midnight.** Create a standalone `BackgroundScheduler` for the pipeline — do not couple to ScraperScheduler. Separate concerns. The function `run_daily_pipeline(db_path)` is scheduled directly, no wrapper class needed.
6. **R_orig/R_val are 0–100 percentiles.** Per `src/data/scores.ts` type definitions. For each source, compute raw value, then percentile-rank against all active sources in that vertical. Same pattern as frontend `interpolate` in `src/utils/scores.ts`.
7. **R_speed defaults to NULL** when a source has no absorbed claims (median of empty set is undefined). Design doc §3: nullable fields are NULL, not 0.
8. **No new database tables.** Snapshots table already has all columns needed.

## Implementation order

1. Create `pipeline/snapshots.py` — pure computation functions (R_orig, R_val, R_speed, archetype, medians)
2. Add `run_all()` to `ConsensusAlignmentAgent`
3. Create `pipeline/runner.py` — `run_daily_pipeline(db_path)` function
4. Schedule pipeline job (standalone BackgroundScheduler, daily at midnight UTC)
5. Write tests (TDD)
6. Update CLAUDE.md slice status

## Test strategy

- **Snapshot computation:** mock DB with known claim data, verify R_orig/R_val/R_speed values, verify archetype assignment, verify NULL for R_frame/R_edit/R_correct, verify percentile ranking
- **Agent 3 run_all:** mock DB with multiple clusters, verify all clusters processed, verify state transitions
- **Pipeline runner:** mock agent + snapshot, verify sequence order (agent first, then snapshots)
- **Scheduler integration:** verify job is added, verify it calls runner
- **No network tests** — pure data computation

## Verification checklist

- [ ] `pytest -m "not network"` passes (all existing + new)
- [ ] `vitest run` passes (no frontend changes, regression check)
- [ ] `biome check src/` — clean
- [ ] `npm run build` passes
- [ ] ponytail-review against diff
- [ ] Adversarial review (algorithmic code — per vault Knowledge, this IS algorithmic)
