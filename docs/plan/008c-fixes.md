# Plan: Slice 8c Fixes

Adversarial review findings against 8c implementation.

## 🔴 Bug 1: Reputation scores computed globally, not per-vertical

**File:** `pipeline/snapshots.py:63-108`

`_query_claim_stats` queries all claims regardless of vertical. The snapshot writer inserts identical scores for all 3 verticals. Design doc defines scores per source × vertical.

**Verification:** Ran `write_daily_snapshots` with 1 source — all 3 verticals got identical `r_orig=0.0, r_val=0.0, r_speed=0.0`.

**Fix:** Add `vertical` parameter to `_query_claim_stats`. Join through `clusters` table to filter claims by vertical:

```sql
FROM claim_sources cs
JOIN claims c ON c.id = cs.claim_id
JOIN clusters cl ON cl.id = c.cluster_id
WHERE cl.vertical = ? AND cs.source_id = ?
```

Call `_query_claim_stats` per-vertical in the loop.

## 🔴 Bug 2: Agent hardcoded to in-memory DB

**File:** `pipeline/agent3_consensus.py:20`

`get_db(":memory:")` always creates a fresh empty DB. Agent cannot work with real data. Pattern should match `ScraperScheduler` which accepts `db_path` parameter.

**Verification:** `grep` confirms line 20 is the only call: `conn = get_db(":memory:")`.

**Fix:** Add `db_path` parameter to `__init__`, default `":memory:"` for test compatibility. Replace hardcoded string with `get_db(self.db_path)`.

## 🔴 Bug 3: Hardcoded threshold ignores cluster vertical

**File:** `pipeline/agent3_consensus.py:54`

`threshold=75` hardcoded. Geopolitics clusters should use 65 per design defaults. Cluster's `vertical` field is available but not consulted.

**Verification:** Line 54 reads `determine_state(pct, threshold=75, ...)`. The `cluster_id` parameter is available but cluster vertical is never queried.

**Fix:** Add `DEFAULT_THRESHOLDS = {"geopolitics": 65, "economics": 75, "technology": 75}` constant. Query cluster vertical from DB, look up threshold.

## 🟡 Dead import: classify_claim

**File:** `pipeline/agent3_consensus.py:3`

`classify_claim` imported but never called. `compute_baseline_pct` IS used (line 47). Remove the unused import.

## Implementation order

1. Add `DEFAULT_THRESHOLDS` constant to `pipeline/consensus.py` (or new `pipeline/thresholds.py`)
2. Add `db_path` to `ConsensusAlignmentAgent.__init__`
3. Fix `_query_claim_stats` to accept `vertical` parameter, join through clusters
4. Fix agent3 to query cluster vertical, look up threshold
5. Remove dead `classify_claim` import
6. Update tests: test per-vertical scoring, test threshold lookup
7. Verify: pytest, vitest, tsc

## Test strategy

| Test | What it verifies |
|------|-----------------|
| `test_per_vertical_scoring` | Two sources with claims in different verticals get different scores |
| `test_agent_respects_cluster_vertical_threshold` | Geopolitics cluster uses 65, economics uses 75 |
| `test_agent_db_path` | Agent works with non-default DB path |

## Verification checklist

- [ ] `pytest -m "not network"` — 157+ tests pass (3 new)
- [ ] `vitest run` — 136 pass
- [ ] `tsc -b --noEmit` — clean
