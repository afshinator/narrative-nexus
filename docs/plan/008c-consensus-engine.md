# Plan: Slice 8c — Consensus Engine

## Requirements addressed

| Req | Description | How |
|-----|-------------|-----|
| REQ-019 | Consensus math on CPU (pure Python) | All modules use stdlib only |
| REQ-022 | Consensus baseline over Tier 1+2 | `consensus.py` computes threshold% of Tier 1+2 sources |
| REQ-023 | Claim enters baseline at threshold% | `consensus.py` classification logic |
| REQ-024 | Default thresholds 65/75/75 | `DEFAULT_THRESHOLDS` constant |
| REQ-026 | Stored with each cluster run | Snapshot computed and written per run |
| REQ-027–031 | Claim lifecycle states | `resolution.py` state machine (7/30/90 day) |
| REQ-032–037 | 6 reputation dimensions | `reputation.py` scoring from claims data |
| REQ-039–042 | Archetype assignment | `archetype.py` port of frontend logic |
| REQ-046 | Daily snapshots | `snapshots.py` compute + write per source×vertical |
| REQ-062 | BODY_UNAVAILABLE not penalized | Excluded from scoring |

## Assumptions verified (2026-06-26)

### 1. DB schema preparedness ✅
All needed tables exist: `claims` (state, absorbed_at), `claim_sources` (claim_id, source_id, first_seen_at), `snapshots` (6 dimensions, archetype, UNIQUE constraint), `sources` (tier, active), `clusters` (vertical). All needed CRUD functions exist in `db/`.

### 2. Formula computability ⚠️ (ambiguity — see below)

| Dimension | Computable from available data? | Input |
|-----------|-------------------------------|-------|
| R_orig | ✅ | `claim_sources` — which sources reported each claim |
| R_val | ✅ | `claims` — absorbed count / total originated |
| R_speed | ✅ | `claims.absorbed_at` − `claim_sources.first_seen_at` (median) |
| R_frame | ❌ | Needs NLP framing analysis (not yet built) |
| R_edit | ❌ | Needs SilentAuditorAgent output |
| R_correct | ❌ | Needs formal correction tracking |

**Decision needed:** For R_frame, R_edit, R_correct: compute as `None` (null in DB) until the respective agents produce data. The snapshot writer stores nulls, the frontend already handles nulls gracefully (dashes in stat panel, neutral color). Raise this during grill-with-docs.

### 3. Existing code that needs backend ports ✅
- `src/utils/archetype.ts` (13 lines) → `pipeline/archetype.py` — pure function, same logic
- `src/data/thresholds.ts` → `DEFAULT_THRESHOLDS` constant in `pipeline/consensus.py`
- `src/utils/polarity.ts` → not needed (polarity is a frontend render concern, not calculation)

### 4. Design doc rules are LOCKED ✅
- Resolution schedule: 7/30/90 day checks (design §4, LOCKED)
- Archetype assignment: R_orig/R_val vs panel median (design §4, LOCKED)
- Six dimensions defined (design §4, LOCKED)

### 5. No external dependencies needed ✅
Pure Python stdlib: `statistics.median`, `datetime`, `sqlite3`. No numpy, scipy, or math libraries needed.

### 6. Clusters are single-vertical ✅
DB schema has `clusters.vertical TEXT NOT NULL` (singular). ADR-0001's multi-vertical evaluation is deferred. 8c operates on one vertical per cluster. Simplifies computation.

## Architecture decisions

### Decision 1: Five modules with pure functions

```
pipeline/
  archetype.py   — get_archetype(r_orig, r_val, median_orig, median_val) → str
  consensus.py   — compute_baseline(cluster_id, threshold) → dict
  reputation.py  — score_source(source_id, vertical) → ReputationScore
  resolution.py  — run_resolution_checks() → list[dict] (updated claims)
  snapshots.py   — write_daily_snapshots() → int (count written)
```

Pure functions where possible. Each module imports from `db/` for data access. No shared state between modules.

### Decision 2: Reputation scoring formula

For R_orig: `count of claims where this source was the first reporter (earliest first_seen_at) / total claims in the cluster`. Expressed as percentile 0–100 relative to all sources in the same vertical.

For R_val: `count of originated claims that reached CONSENSUS_ABSORBED / count of originated claims × 100`.

For R_speed: `median(absorbed_at - first_seen_at)` in days, for absorbed claims only. Inverted to percentile where lower = higher score.

R_frame, R_edit, R_correct: `None` — not computable until NLP/auditor agents exist.

### Decision 3: Percentile computation

All scores are converted to 0–100 percentiles relative to all active sources in the same vertical. This normalizes across different verticals and source counts. Uses `statistics.median` for median, simple rank-based percentile for individual values.

### Decision 4: Resolution state machine

```
Day 0:  claim inserted → PENDING
Day 7:  check — if ≥threshold% of Tier 1+2 sources have reported → CONSENSUS_ABSORBED
Day 30: check — if threshold crossed → CONSENSUS_ABSORBED
Day 90: PENDING → UNRESOLVED (terminal), or ABSORBED if threshold finally crossed
```

Convergence type: `CROSS_SOURCE_CONVERGENT` if ≥2 sources independently corroborated before absorption, `SELF_CONSISTENT` if only the origin source published consistent follow-up.

### Decision 5: Snapshot writing is batch, not incremental

`write_daily_snapshots()` iterates all active sources × all 3 verticals, computes scores for each, inserts one row per (source, vertical, today). Runs as a daily job (same APScheduler as scraper, separate job). UNIQUE constraint prevents duplicates.

### Decision 6: Consensus baseline over Tier 1+2 pool

For a given cluster + vertical + threshold (e.g., 65%): count how many distinct Tier 1+2 sources have reported any claim in this cluster. If ≥ threshold% of the Tier 1+2 pool, the cluster has a consensus baseline. Individual claims enter the baseline when ≥ threshold% of Tier 1+2 sources have reported that specific claim.

## New files

| File | Purpose |
|------|---------|
| `pipeline/archetype.py` | `get_archetype()` pure function — port of frontend logic |
| `pipeline/consensus.py` | `compute_baseline()`, `classify_claims()` — threshold math |
| `pipeline/reputation.py` | `score_source()` — 3 computable dimensions, 3 null stubs |
| `pipeline/resolution.py` | `run_resolution_checks()` — 7/30/90 day state machine |
| `pipeline/snapshots.py` | `write_daily_snapshots()` — batch score + insert |
| `pipeline/test_archetype.py` | Tests: archetype assignment matches frontend behavior |
| `pipeline/test_consensus.py` | Tests: baseline computation, claim classification |
| `pipeline/test_reputation.py` | Tests: scoring with synthetic claims data |
| `pipeline/test_resolution.py` | Tests: state transitions at each checkpoint |
| `pipeline/test_snapshots.py` | Tests: batch write, UNIQUE constraint, null handling |

## Existing files modified

| File | Change |
|------|--------|
| `pipeline/agent3_consensus.py` | Replace stub with real implementation using consensus.py + resolution.py |
| `app/main.py` | Add snapshot job to scheduler (separate from scrape job), add `/api/snapshots` already exists |

## Implementation order

1. **archetype.py** — pure function, no DB. Test against known inputs (match frontend).
2. **consensus.py** — baseline + classification. Test with synthetic claims.
3. **reputation.py** — scoring from claims data. Test with synthetic claims + sources.
4. **resolution.py** — state machine. Test with time-shifted fixtures.
5. **snapshots.py** — batch writer. Test with synthetic data.
6. **Wire agent3** — replace stub with real ConsensusAlignmentAgent.
7. **Verify** — pytest, existing tests, build.

## Test strategy

All tests use in-memory SQLite with synthetic data (no live RSS/network needed). Tests seed sources, articles, claims, and claim_sources with controlled values to verify exact outputs.

| Test | What it verifies |
|------|-----------------|
| archetype 4 quadrants | Each of 4 archetypes assigned correctly |
| archetype matches frontend | Same inputs → same outputs as TS version |
| baseline with 0 claims | Returns empty baseline |
| baseline at threshold | 65% of Tier 1+2 = 6.5 → 7 sources → 7/10 = 70% ≥ 65% → baseline exists |
| claim classification | PENDING → ABSORBED when threshold crossed |
| reputation R_orig | Correct count of first-reported claims |
| reputation R_val | Correct ratio of absorbed/originated |
| reputation R_speed | Median days computation correct |
| reputation null stubs | R_frame/R_edit/R_correct = None |
| resolution day 7 | Claims with ≥threshold sources → ABSORBED |
| resolution day 30 | Same check, later window |
| resolution day 90 | PENDING → UNRESOLVED if not absorbed |
| snapshots batch write | Correct row count, UNIQUE constraint enforced |
| snapshots null handling | Null dimensions stored without error |

## Verification checklist

- [ ] `pytest pipeline/test_archetype.py pipeline/test_consensus.py pipeline/test_reputation.py pipeline/test_resolution.py pipeline/test_snapshots.py` — 30+ tests pass
- [ ] `pytest -m "not network"` — all non-network tests pass (~150+)
- [ ] `vitest run` — 136 pass (no frontend changes)
- [ ] `tsc -b --noEmit` — clean
