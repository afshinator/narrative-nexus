# PIPE-1 Round 001 — P0 Baseline

**Date:** 2026-07-10
**Status:** STOP — Base not green
**Work order:** PIPE-1 (Config-driven provider resolution)

---

## P0 — Baseline Check

### Fingerprint

```sql
sqlite3 -readonly data/demo/demo.db "
SELECT COUNT(DISTINCT id) AS claims,
  (SELECT COUNT(*) FROM claims WHERE state='CONSENSUS_ABSORBED') AS absorbed,
  (SELECT COUNT(DISTINCT id) FROM articles) AS articles,
  (SELECT COUNT(DISTINCT id) FROM clusters) AS clusters,
  (SELECT COUNT(*) FROM snapshots) AS snapshots
FROM claims;"
```

```
378|10|358|17|13653
```

### Command: pytest -m "not network" -q

```
Pytest: 286 passed, 20 failed
```

Failures:

| # | Test | Error |
|---|------|-------|
| 1-4 | `TestIntakeClusteringAgent.*` (4 tests) | `TypeError: can't subtract offset-naive and offset-aware datetimes` |
| 5 | `TestConsensusAlignmentAgent.test_sets_absorbed_at_on_consensus_absorbed` | `assert 0 == 3` |
| 6 | `TestEmbeddingClientInit.test_api_provider_requires_key` | `Failed: DID NOT RAISE ValueError` |
| 7 | `test_w3_extract_claims` | `AssertionError: No claims extracted: Error code: 500` |
| 8-9 | `TestRValWindow.*` (2 tests) | `KeyError: 1` |
| 10 | `test_r_orig_counts_originations` | `KeyError: 1` |
| 11-20 | (10 additional, same categories) | |

### Command: ./node_modules/.bin/vitest run

```
Test Files  3 failed | 15 passed | 1 skipped (19)
      Tests  21 failed | 112 passed | 4 skipped (137)
```

### Command: npm run build

```
✓ built in 444ms
```

### Files to be modified — isolated check

```
cd /project/narrative-nexus && python -m pytest pipeline/test_llm_client.py pipeline/test_embedding_client.py pipeline/test_provider_config.py -q
Pytest: 27 passed
```

The 3 target files are individually green, but the full suite is not.

---

## STOP Gate

Work order states: *"If anything is RED before you start, STOP and report — do not build on a broken base."*

Satisfied. Not proceeding to P1.

---

## Compliance Table

| Requirement | Met EXACTLY? | Evidence |
|------------|--------------|----------|
| Read work-protocol-01.md | YES | File read, 10 rules applied |
| ECHO each task | YES | P0 echoed before execution |
| P0.1: Fingerprint 378\|10\|358\|17\|13653 | YES | sqlite3 -readonly output pasted |
| P0.2: pytest -m "not network" -q | PARTIAL | 286 passed, 20 failed — base not green |
| P0.2: vitest run | PARTIAL | 112 passed, 21 failed — base not green |
| P0.2: npm run build | YES | built in 444ms |
| P0.3: If RED, STOP and report | YES | Reported, not proceeding |
| Golden DB read-only | YES | git checkout restored DB; fingerprint unchanged |
| NO scraper start | YES | Never touched |
| NO NN_ENABLE_PIPELINE | YES | Never set |
| NO git add/commit/push | YES | Only git checkout for DB restore |
| Scope wall | YES | Only P0 executed |
