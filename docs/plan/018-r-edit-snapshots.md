# Slice 018 — Wire R_edit into Snapshot Computation

**Plan date:** 2026-06-30
**Spec ref:** REQ-036 [desired] — "The system must track reputation dimension R_edit Silent Edit Rate"
**Status:** Plan → needs user approval before Assumption Validation

---

## 1. What This Is

Wire the 4th reputation dimension (R_edit — Silent Edit Rate) into the daily snapshot computation. Agent 4 already runs and writes real data (89 silent_edits rows). The `compute_r_edit` function exists and is tested. The frontend is fully prepared (R_edit in INVERTED_DIMS, null handling, polarity colors). The only gap is that `_compute_and_write_snapshots` never computes or passes `r_edit` — so all 44,363 snapshots have `r_edit=NULL`.

After this slice, the Source Profile radar chart goes from 3 live dimensions (triangle) to 4 (quadrilateral).

---

## 2. Verified Facts (traced against actual code)

### 2.1 What already works

| Layer | File | Status |
|---|---|---|
| Silent edit detection | `pipeline/agent4_silent.py` | Runs, writes 89 rows to `silent_edits` table |
| Raw computation function | `pipeline/reputation.py:39` — `compute_r_edit(edit_count, article_count)` | Exists, tested (3 tests in `test_reputation.py`) |
| DB write path | `db/snapshots.py:17` — `r_edit` column accepted by `insert_snapshot` | Column exists, stores NULL by default |
| API serves edits per source | `app/main.py:182-192` — JOINs silent_edits → articles → source | Live, tested |
| Frontend radar | `src/pages/SourceProfile.tsx:475-480` — inverts R_edit, handles null | Ready |
| Frontend polarity | `src/utils/polarity.ts:5` — R_edit in INVERTED_DIMS | Ready |
| Frontend edit log | `src/pages/SourceProfile.tsx:344-366` — renders silent edit table | Ready |

### 2.2 The exact gap

`pipeline/runner.py:194-203` — `_compute_and_write_snapshots` calls `write_daily_snapshots()` with only 5 positional args: `r_orig`, `r_val`, `r_speed`, `archetypes`. The optional params `r_edit` (and `r_frame`, `r_correct`) default to `None` → become `{}` → `.get(sid)` returns `None` → stored as NULL.

### 2.3 Data path for r_edit computation

```
silent_edits (article_id, detected_at, change_ratio)
    → JOIN articles (id, source_id)
    → GROUP BY source_id → edit_count per source
    → Divide by article_count per source → raw ratio
    → percentile_rank() → 0-100
    → write_daily_snapshots(r_edit=...)
```

### 2.4 Polarity verification

R_edit is "Graded — low is favorable" (design doc §4). `percentile_rank` sorts ascending: lowest value → rank 0. Frontend inverts: `100 - percentile`. Net result: source with 2% edit rate → percentile ~0 → inverted to 100 → teal (favorable). Source with 10% → percentile ~100 → inverted to 0 → red. Correct.

### 2.5 as_of filter behavior

Existing raw functions (r_orig_raw, r_val_raw, r_speed_raw) accept optional `as_of` ISO string for date-filtered historical snapshots (used by seed script). For r_edit, this means filtering `silent_edits.detected_at <= as_of`. The `detected_at` column uses `datetime('now')` default (space-separated, e.g. `2026-06-30 00:03:00`). SQLite string comparison works correctly against ISO `as_of` because both start with the date portion in descending order.

Article count denominator: count all articles per source (no date filter, matching the pattern in r_orig_raw which doesn't filter articles by date).

---

## 3. Changes

### 3.1 `pipeline/snapshots.py` — Add `compute_r_edit_raw()`

New function following the exact pattern of `compute_r_orig_raw`/`compute_r_val_raw`/`compute_r_speed_raw`:

```python
def compute_r_edit_raw(conn, *, as_of=None) -> dict[int, float | None]:
    """Silent edit rate per source — edits/articles ratio.
    Returns {source_id: ratio} where ratio = edit_count / article_count.
    None when a source has zero articles."""
```

SQL:
```sql
SELECT a.source_id, COUNT(se.id) as edit_count
FROM silent_edits se
JOIN articles a ON a.id = se.article_id
WHERE (as_of filter on se.detected_at)
GROUP BY a.source_id
```

Then cross-reference with article count per source from `list_sources` + article count query.

### 3.2 `pipeline/runner.py` — Wire r_edit into `_compute_and_write_snapshots`

At line 171 (after `r_speed_raw` computation), add:
```python
r_edit_raw = compute_r_edit_raw(conn, as_of=as_of)
```
At line 176 (after `r_speed` percentile rank), add:
```python
r_edit = percentile_rank({k: v for k, v in r_edit_raw.items() if v is not None})
```

At line 195-203 (`write_daily_snapshots` call), add:
```python
r_edit=r_edit,
```

### 3.3 `pipeline/test_snapshots.py` — Add test + update existing

**New test:** `test_redit_raw_counts_edits_per_source` — inserts silent_edits rows into fixture DB, verifies edit counts and ratios.

**Update:** `test_write_daily_snapshots` — pass `r_edit` with real data instead of `r_edit={}`, assert rows have non-None r_edit values.

### 3.4 No changes to these files

- `pipeline/reputation.py` — `compute_r_edit` function unchanged (used elsewhere for ad-hoc computation, not in snapshot pipeline)
- `db/silent_edits.py` — no changes
- `db/snapshots.py` — no changes  
- `app/main.py` — no changes (API already serves r_edit)
- `src/pages/SourceProfile.tsx` — no changes
- `src/utils/polarity.ts` — no changes
- `scripts/seed_demo.py` — imports `_compute_and_write_snapshots` from runner, benefits automatically

---

## 4. Implementation Order (TDD)

1. **RED** — Add `test_redit_raw_counts_edits_per_source` to `test_snapshots.py` (will fail — function doesn't exist yet)
2. **RED** — Update `test_write_daily_snapshots` to expect r_edit populated (will fail — code doesn't pass r_edit yet)
3. **GREEN** — Add `compute_r_edit_raw` to `snapshots.py`
4. **GREEN** — Wire r_edit computation + pass to `write_daily_snapshots` in `runner.py`
5. **REFACTOR** — None needed (ponytail: no abstractions)

---

## 5. Test Strategy

| Test | What it verifies |
|---|---|
| `test_redit_raw_counts_edits_per_source` | New — JOIN path, edit counting, ratio computation, None for zero-article sources |
| `test_write_daily_snapshots` (updated) | r_edit stored non-None when data exists |
| `test_run_daily_pipeline_writes_snapshots` | Existing — should still pass, r_edit now populated |
| `test_run_daily_pipeline_empty_db` | Existing — should still pass, r_edit=None when no data |

---

## 6. Verification Checklist

- [ ] `pytest pipeline/test_snapshots.py -x -q` — all tests pass
- [ ] `pytest pipeline/test_runner.py -x -q` — all tests pass
- [ ] `pytest pipeline/test_reputation.py -x -q` — no regressions
- [ ] `npm run build` — no regressions
- [ ] `vitest run` — 139 passed (no frontend changes)
- [ ] Manual: start app with real DB, open a Source Profile page, verify R_edit shows a value (not "—") on radar chart
- [ ] Manual: verify R_edit percentile shown in correct polarity color (low edit rate = teal)
