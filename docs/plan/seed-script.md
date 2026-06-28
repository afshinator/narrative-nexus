# Plan: Demo Seed Script

**Slice:** Demo seed script — populate 90 days of historical data through the real pipeline
**Status:** Complete
**Date:** 2026-06-27
**Depends on:** Slice 12 (provider abstraction + Agents 1/2/4) — DONE

---

## 1. What this slice does

The existing database has 575 scraped articles from 37 sources spanning 2023–2026, with 252 articles having extractable body text. This slice runs the full 4-agent pipeline against that data, generates date-filtered daily reputation snapshots across the full time range, and produces a demo-ready database with real clusters, real claims, real consensus states, and real reputation time-series.

All pipeline code is shared with the live scheduler — no demo mode, no mock data, no static JSON.

**If the auto-generated demo data isn't compelling enough**, a second round can add hand-picked article URLs to seed specific stories. That's an escape hatch, not the primary plan.

## 2. What the seed script does

`scripts/seed-demo.py`:

1. **Load provider config** — from `config/providers.json` (same as live pipeline)
2. **Run Agent 1** — IntakeClusteringAgent on all articles with bodies. Produces clusters via DBSCAN + sentence-transformers embeddings
3. **Run Agent 2** — ForensicExtractionAgent on clustered articles. Extracts atomic claims via OpenCode Zen LLM
4. **Run Agent 3** — ConsensusAlignmentAgent on all clusters. Classifies claims into CONSENSUS_ABSORBED / UNRESOLVED states
5. **Run Agent 4** — SilentAuditorAgent. Detects edits by re-fetching + diffing
6. **Generate date-filtered daily snapshots** — for each day in the article date range, compute reputation values using only data up to that date. Produces real time-series the radar animation can scrub through

The seed script shares code with `pipeline/runner.py` — it calls the same agent classes. The snapshot loop is the only new logic.

## 3. Date-filtered snapshot generation (Option B)

Current `_compute_and_write_snapshots` in `runner.py` aggregates ALL data and writes one snapshot for today. For the demo, we need one snapshot per day with data filtered up to that date.

**Refactor needed:** Add optional `date_str` and `as_of_date` parameters to:
- `pipeline/runner.py:_compute_and_write_snapshots` — accepts `date_str` override (1 line)
- `pipeline/snapshots.py:compute_r_orig_raw` — add optional `as_of` filter to only include claims with `first_seen_at <= as_of`
- Same for `compute_r_val_raw` and `compute_r_speed_raw`

The seed script then loops over each day in the article date range and calls `_compute_and_write_snapshots(conn, date_str=day, as_of=day)`.

**Impact:** Each day's snapshot reflects only the data that existed on that date. The radar animation shows reputation evolving over time as more articles and claims accumulate.

## 4. The pipeline already handles article→claim date backdating

Agent 2 inserts claims with `created_at = datetime('now')` (SQLite default). For the demo, claim dates should match article publication dates so Agent 3's 7d/30d/90d checkpoints work correctly. The seed script reads each article's `published_at` and overrides `claims.created_at` and `claim_sources.first_seen_at` to match. This ensures claims appear on the timeline at the right dates.

**Refactor needed:** `db/claims.py:insert_claim` currently has no `created_at` override parameter. Add an optional `created_at` param (defaults to now, backward-compatible).

## 5. Files changed

| File | Change |
|------|--------|
| `scripts/seed-demo.py` | Rewrite — run pipeline on existing DB, generate date-filtered snapshots |
| `pipeline/runner.py` | Add `date_str` + `as_of` params to `_compute_and_write_snapshots` |
| `pipeline/snapshots.py` | Add `as_of` filter to `compute_r_orig_raw`, `compute_r_val_raw`, `compute_r_speed_raw` |
| `db/claims.py` | Add optional `created_at` param to `insert_claim` |
| `scripts/test_seed.py` | New — integration test with temp DB |
| `pipeline/test_snapshots.py` | Add tests for `as_of` filtering |
| `pipeline/test_runner.py` | Update for new `_compute_and_write_snapshots` signature |

## 6. What is NOT in scope

- **Hand-picked URL curation** — escape hatch for round 2, not this slice
- **Multi-vertical support** — all clusters are geopolitics (ponytail)
- **Demo DB backup** — manual `cp data/nn.db data/demo-backup.db`
- **Seeded DB in Docker image** — the seed script runs on the host before demo, not inside the container

## 7. Implementation order (TDD)

1. Add `created_at` override to `db/claims.py:insert_claim` + test
2. Add `as_of` filter to 3 snapshot compute functions + tests
3. Add `date_str` + `as_of` params to `_compute_and_write_snapshots` + test
4. Write seed script: pipeline agent calls with date overrides
5. Write seed script: date-filtered snapshot loop
6. Integration test: temp DB with 3 articles, verify clusters/claims/snapshots

## 8. Test strategy

- `pipeline/test_snapshots.py` — unit: `as_of` filter returns correct subsets
- `scripts/test_seed.py` — integration: 3-article temp DB, run seed, verify output
- Manual: `python scripts/seed-demo.py` against live `data/nn.db`, verify output
- Manual: open app, verify clusters/snapshots visible, radar animates

## 9. Verification checklist

- [ ] All pytest pass (including new snapshot and seed tests)
- [ ] `npm run build` + `vitest run` clean
- [ ] Seed script completes without errors against live DB
- [ ] DB has clusters, claims, snapshots after seed
- [ ] Pipeline Flow page shows provider dropdowns populated
- [ ] Source Profile radar chart has data
- [ ] Timeline shows articles distributed across date range
