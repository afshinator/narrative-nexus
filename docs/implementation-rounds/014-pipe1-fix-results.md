# PIPE-1-FIX Results — Golden DB Isolation in Test Suite

**Date:** 2026-07-10
**Status:** Complete
**Work order:** PIPE-1-FIX

---

## Headline

`app/test_routes.py::TestScraperRoutes.test_start_stop` wrote to `data/demo/demo.db` every time the full pytest suite ran. The `client` fixture created `TestClient(app)` with no `NN_DB_PATH` override, so the app lifespan defaulted to `data/demo/demo.db`. The scraper test then called `POST /api/scraper/start` → RSS polls → INSERT INTO golden DB. This is how the golden DB has been repeatedly contaminated across multiple rounds (including PIPE-1, where 358 articles became 2,137).

This is FIXED. The test suite can no longer touch the golden DB.

## Root Cause

Resolution chain:

```
client fixture (test_routes.py:25): TestClient(app)  — no NN_DB_PATH
  → app lifespan (main.py:45): os.environ.get("NN_DB_PATH", "data/demo/demo.db")
    → db_path = "data/demo/demo.db"
      → init_db(data/demo/demo.db)
      → ScraperScheduler(data/demo/demo.db)
        → test_start_stop (line 120): POST /api/scraper/start
          → scraper.start() → RSS → INSERT INTO golden DB
```

## Fix

`app/test_routes.py:22-39` — `client` fixture now accepts `tmp_path`, copies `data/demo/demo.db` to a temp file, and sets `NN_DB_PATH` to the copy. All writes (scraper, init_db, anything) hit the temp copy. `tmp_path` teardown deletes it.

Diff: +14 / -5 lines.

## Verification

| Check | Before | After |
|-------|--------|-------|
| Fingerprint | 378\|10\|358\|17\|13653 | 378\|10\|358\|17\|13653 |
| `pytest -m "not network" -q` | 292 passed, 20 failed | 292 passed, 20 failed |
| Diff failing tests vs baseline | — | EMPTY |
| `git diff data/demo/demo.db` | clean | clean |
| `git checkout` needed? | — | NO |

Zero new failures. Golden DB untouched. No restore needed. The scraper test runs isolated against a per-test temp copy.

## Prior Contamination Events (this session)

| Event | Article count before | Article count after | Cause |
|-------|---------------------|--------------------|-------|
| PIPE-1 P0 baseline capture | 358 | 5,455,872 bytes | `client` fixture → lifespan → init_db connection overhead |
| PIPE-1 P4 regression run | 358 | 2,137 | `test_start_stop` started scraper against golden DB |
| PIPE-1-FIX F4 run | 358 | **358** | FIXED — temp copy isolates all writes |

## Files Changed

| File | Change |
|------|--------|
| `app/test_routes.py` | `client` fixture: copy golden DB to tmp_path, set NN_DB_PATH |
