# Slice 027 — R_frame Snapshot Wiring

**Plan date:** 2026-07-01
**Depends on:** Backfill complete — all 2,028 articles have llm_score, lexical_score, sentiment_score in `article_framing`.

## What

Wire R_frame (framing consistency) into daily snapshot computation. This is the 6th and final radar dimension — ships the full hexagon.

## Verified facts

| Claim | Status | Evidence |
|---|---|---|
| All 2,028 articles have LLM scores | ✅ | `SELECT COUNT(*) FROM article_framing WHERE llm_score IS NOT NULL` = 2028 |
| 37 sources have scored articles | ✅ | `COUNT(DISTINCT source_id)` = 37 |
| LLM score variance ranges 0.55–7.75 across sources | ✅ | Highest: tehrantimes (7.75), Lowest: theintercept (0.55) |
| `write_daily_snapshots()` already accepts `r_frame` param | ✅ | `snapshots.py:255` — optional `dict[int, float \| None]` |
| `_compute_and_write_snapshots()` uses 5 of 6 dimensions | ✅ | `runner.py:155-214` — r_frame not yet computed |
| 30 snapshot tests exist, r_edit added in slice 018 | ✅ | `test_snapshots.py` — all pass |

## Implementation

### 1. `compute_r_frame_raw()` — new function in `pipeline/snapshots.py`

```python
def compute_r_frame_raw(conn, *, as_of=None) -> dict[int, float | None]:
    """Stddev of LLM framing scores per source. Lower = more consistent.

    If as_of is provided, only articles published <= as_of are counted.
    Returns {source_id: stddev}. None when a source has <2 scored articles.
    """
```

SQL pattern (matching `compute_r_edit_raw`):
- JOIN article_framing → articles → sources
- GROUP BY source_id, compute `STDEV(llm_score)` (SQLite doesn't have STDEV — compute via `SQRT(AVG(x²) - AVG(x)²)`)
- Filter with optional as_of on `articles.published_at`
- Return NULL for sources with <2 scored articles (can't compute variance)

### 2. Wire into `_compute_and_write_snapshots()` — `runner.py`

Add after r_correct_raw (line 176):
```python
r_frame_raw = compute_r_frame_raw(conn, as_of=as_of)
```

Add after r_correct percentile (line 185):
```python
r_frame_raw = compute_r_frame_raw(conn, as_of=as_of)
r_frame = percentile_rank({k: v for k, v in r_frame_raw.items() if v is not None})
# Frontend handles inversion (src/utils/polarity.ts INVERTED_DIMS includes R_frame).
# DB stores raw percentiles — high stddev = high percentile = inconsistent.
```

Add to `write_daily_snapshots()` call (after r_correct, line 211):
```python
r_frame=r_frame,
```

### 3. Add `compute_r_frame_raw` to runner imports (line 24)

### 4. Tests — 3 new tests in `test_snapshots.py`

| Test | What it checks |
|---|---|
| `test_r_frame_raw_stddev` | Stddev computed correctly for sources with >=2 scored articles |
| `test_r_frame_raw_null_edge_case` | Source with <2 scored articles returns None |
| `test_r_frame_end_to_end` | Raw → percentile → invert → write → query matches expected values |

### 5. Test fixture: add `article_framing` rows to the `db` fixture

Need to insert `article_framing` rows for test articles to compute framing scores. Pattern: `INSERT INTO article_framing (article_id, llm_score, lexical_score, sentiment_score) VALUES (...)`.

## Files changed

| File | Change | Lines |
|---|---|---|
| `pipeline/snapshots.py` | Add `compute_r_frame_raw()` | ~25 |
| `pipeline/runner.py` | Import + wire into snapshot loop | ~5 |
| `pipeline/test_snapshots.py` | 3 new tests + fixture update | ~60 |

## Assumptions

1. R_frame uses **LLM score only** (not lexical or sentiment). The other scorers are supplementary — LLM score is the primary framing signal per design doc §3.
2. **Stddev is the consistency metric** — per design doc §4: "low stddev is favorable."
3. **Invert percentile rank** — raw stddev gets percentile-ranked, then inverted (100 − pct) so high R_frame = consistent.
4. **as_of filter** uses `articles.published_at` (same as other dimensions use `claims.created_at`).

## Verification checklist

- [ ] `npm run build` passes
- [ ] `rtk pytest pipeline/test_snapshots.py -v` — all tests pass (33 total after +3)
- [ ] `rtk pytest -m "not network"` — no regressions
- [ ] Live DB: `SELECT COUNT(*) FROM snapshots WHERE r_frame IS NOT NULL` > 0
- [ ] Frontend: Source Profile radar shows full hexagon (6 dimensions)
