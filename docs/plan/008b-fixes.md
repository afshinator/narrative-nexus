# Plan: Slice 8b Fixes

Adversarial review findings against 8b implementation.

## 🔴 Bug 1: All sources seeded as tier 1

**File:** `pipeline/scheduler.py:102-103`

`_ensure_sources()` inserts every source with `tier=1`. The actual tiers are 1–5 per `src/data/sources.ts`. Consensus math in 8c depends on Tier 1+2 identification for the baseline pool.

**Verification:** Ran `_ensure_sources` logic against in-memory DB — all 20 sources get tier=1.

**Fix:** Add `tier` field to `FEED_CONFIG` entries in `scraper.py`. `_ensure_sources` reads the tier from config. Requires a schema migration: `ALTER TABLE sources ADD COLUMN tier` is already in the schema (tier column exists), so no migration needed — just pass tier from config.

## 🔴 Bug 2: data/ directory not created

**File:** `app/main.py:22`

`sqlite3.connect("data/nn.db")` fails with `OperationalError` if `data/` doesn't exist. The directory is not created anywhere.

**Verification:** Confirmed `data/` doesn't exist on disk.

**Fix:** Add `os.makedirs(os.path.dirname(db_path), exist_ok=True)` in the lifespan before creating the scheduler. One line.

## 🟡 Suggestion: datetime.utcnow() deprecated

**File:** `pipeline/scraper.py:58`

Works on Python 3.11 but removed in 3.12+. Forward-compat fix: replace with `datetime.now(timezone.utc)`.

## Implementation order

1. Add `tier` field to `FEED_CONFIG` in `scraper.py` (20 entries, one int each)
2. Update `_ensure_sources` in `scheduler.py` to read tier from config
3. Add `os.makedirs` in `app/main.py` lifespan
4. Replace `datetime.utcnow()` with `datetime.now(timezone.utc)` in `scraper.py`
5. Add test: `_ensure_sources` preserves correct tiers
6. Verify: `pytest`, `vitest`, build

## Test strategy

| Test | What it verifies |
|------|-----------------|
| `test_ensure_sources_preserves_tiers` | Inserted sources have correct tier values matching FEED_CONFIG |

## Verification checklist

- [ ] `pytest -m "not network"` — 121+ tests pass (1 new)
- [ ] `vitest run` — 136 pass
- [ ] `tsc -b --noEmit` — clean
