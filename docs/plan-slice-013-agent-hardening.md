# Slice 013 — Agent 3/4 Hardening

## Problem

Three deferred UI items are blocked by two small backend gaps:

| UI item | Blocker |
|---|---|
| Timeline event markers | `absorbed_at` is NULL on all CONSENSUS_ABSORBED claims |
| Outlier waterfall | 0 UNRESOLVED claims (state machine works but `absorbed_at` missing means no transition evidence) |
| Silent edit log | Agent 4 prints edits to stdout, no persistent `silent_edits` table |

## What was verified

**Agent 3 — `determine_state()` already correct:**
```
>>> determine_state(30, 65, 100)   → "UNRESOLVED"   ✓
>>> determine_state(70, 65, 100)   → "CONSENSUS_ABSORBED"  ✓
>>> determine_state(30, 65, 50)    → "PENDING"      ✓
```

**Agent 3 — `update_claim_state()` already accepts `absorbed_at`:**
```python
# db/claims.py:78-84
def update_claim_state(conn, claim_id, state, convergence_type=None, absorbed_at=None):
```
The parameter exists but Agent 3 never passes it. One-line fix.

**Agent 4 — no DB writes, no table:**
- `run()` does `print(f"[SilentAuditor] Edit detected: article={article_id}")` — line 105
- No `silent_edits` table in schema.sql
- No `db/silent_edits.py` module

## Design

### Agent 3 change: set `absorbed_at` on CONSENSUS_ABSORBED

In `agent3_consensus.py:_run()`, when state transitions to CONSENSUS_ABSORBED:

```python
if new_state != claim["state"]:
    absorbed = datetime.now(timezone.utc).isoformat() if new_state == "CONSENSUS_ABSORBED" else None
    update_claim_state(conn, claim["id"], new_state, absorbed_at=absorbed)
```

That's it. `determine_state()` already handles UNRESOLVED. Claims that are PENDING for >90 days AND below threshold will transition to UNRESOLVED on the next pipeline run.

### Agent 4 change: write to `silent_edits` table

**Connection management fix:** `run()` currently closes the DB connection in a `finally` block (line 79) before the article loop starts (line 87). To write edits to DB, the connection must stay open during the loop, or a separate connection is opened for writes. Simplest: move `conn.close()` to after the loop.

**New table** (`db/schema.sql`):
```sql
CREATE TABLE IF NOT EXISTS silent_edits (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    article_id  INTEGER NOT NULL REFERENCES articles(id),
    detected_at TEXT NOT NULL DEFAULT (datetime('now')),
    change_ratio REAL NOT NULL,
    stored_body_length INTEGER NOT NULL,
    fetched_body_length INTEGER NOT NULL
);
```

**New DB module** (`db/silent_edits.py`):
```python
def insert_silent_edit(conn, article_id, change_ratio, stored_len, fetched_len) -> int
```

**Agent 4 `run()` change:**
Replace `print()` with `insert_silent_edit(conn, ...)`. Also record `change_ratio` (1.0 - ratio from SequenceMatcher) instead of just a boolean.

**`_detect_edit` signature change:** Currently returns `bool`. Must change to return `(bool, float)` — `(is_edit, change_ratio)`. Existing tests in `test_agent4_silent.py` assert boolean returns (4 tests) — must update.

### After this slice

All 5 originally-deferred UI items become buildable:

| Item | Unblocked by | Data note |
|---|---|---|
| Vf trend | Slice 012 | r_val already exists |
| Tier radar | Slice 012 | Tier averages computable |
| Timeline markers | Agent 3 absorbed_at + Agent 4 silent_edits | Depends on pipeline producing absorption + edit events |
| Outlier waterfall | Agent 3 UNRESOLVED via `determine_state()` | Depends on clusters with pool_size ≥ 2 AND baseline below threshold, OR pool_size=0 clusters with old claims |
| Silent edit log | Agent 4 silent_edits table | Depends on articles whose bodies changed since scraping |

**Outlier waterfall data caveat:** If most clusters are single-source (pool_size=1), those claims absorb at 100% instead of becoming UNRESOLVED. Number of UNRESOLVED claims is an empirical outcome of pipeline clustering — can't be guaranteed from agent changes alone.

## Files touched

| File | Change |
|---|---|
| `pipeline/agent3_consensus.py` | Pass `absorbed_at` to `update_claim_state()` |
| `pipeline/agent4_silent.py` | Compute `change_ratio`, call `insert_silent_edit()` instead of `print()` |
| `db/schema.sql` | Add `silent_edits` table |
| `db/silent_edits.py` | New: `insert_silent_edit()`, `list_silent_edits()` |
| `pipeline/test_agent4_silent.py` | Update: verify DB writes, not stdout |
| `pipeline/test_agents.py` | Update: verify absorbed_at set on state transition |
| `db/test_silent_edits.py` | New: test CRUD for silent_edits |
| `docs/deferred.md` | Unblock items 1+3+4 |

## Implementation order

1. Schema: add `silent_edits` table
2. DB layer: `db/silent_edits.py` with `insert_silent_edit()`
3. DB tests: `db/test_silent_edits.py`
4. Agent 3: pass `absorbed_at` — update tests
5. Agent 4: compute `change_ratio`, write to DB — update tests
6. Update `docs/deferred.md`

## Test strategy

- Unit: `insert_silent_edit()` writes correct row, `list_silent_edits()` filters by article_id
- Unit: `_detect_edit()` returns `(bool, float)` — update 4 existing boolean-assertion tests
- Unit: Agent 3 `_run()` sets `absorbed_at` when state → CONSENSUS_ABSORBED (verify via `get_claim`)
- Unit: Agent 3 `_run()` transitions PENDING → UNRESOLVED when day≥90 and below threshold
- Integration: Agent 4 `run()` populates `silent_edits` table (mock extractor, verify row count + values)

## Verification checklist

- [ ] `pytest -m "not network"` — all non-network tests pass
- [ ] `npm run build` — TypeScript compiles (no frontend changes)
- [ ] `docs/deferred.md` updated: items 1,3,4 unblocked
- [ ] Manual: run pipeline, verify `absorbed_at` populated on CONSENSUS_ABSORBED claims
- [ ] Manual: verify `silent_edits` table has rows after Agent 4 runs
