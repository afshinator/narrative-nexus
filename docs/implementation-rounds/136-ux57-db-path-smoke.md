# UX57 — DB path fix + rebuild smoke script

**Date:** 2026-07-09
**FP:** 378/10/358/17/13653 (unchanged — no DB writes)
**Status:** COMPLETE (T4 proposal-only)

## Summary

Container booted with empty DB. Root cause: Dockerfile.app line 58 copied `data/demo/demo.db` to `/data/nn.db`, but docker-compose.yml sets `NN_DB_PATH=/data/demo/demo.db`. The app found no file at NN_DB_PATH, `sqlite3.connect()` silently created an empty file, and `init_db()` loaded schema into it — zero error, zero warning. The golden DB sat unused at `/data/nn.db` inside the image.

## Task 1 — Fix Dockerfile.app line 58

### Before
```
COPY data/demo/demo.db /data/nn.db
```

### After
```
COPY data/demo/demo.db /data/demo/demo.db
```

`docker-compose.yml` sets `NN_DB_PATH=/data/demo/demo.db`. The COPY destination must match.

### Evidence

```
$ git diff Dockerfile.app
-COPY data/demo/demo.db /data/nn.db
+COPY data/demo/demo.db /data/demo/demo.db
```

Verification of golden DB at `/data/nn.db` inside existing image (done on human's machine, pre-fix):
```
claims 378 / articles 358 / clusters 17 / snapshots 13653 / absorbed 10
```

## Task 2 — Sweep for nn.db references

### Raw grep output

```
./docs/workflow-gaps-01.md:57:- **C01 (API uses :memory: DB):** Every test uses an in-memory SQLite database. No test starts the FastAPI app with a real `data/nn.db` file and hits `/api/sources` to verify the route reads from the persistent store. The bug would be caught in 60 seconds by running `uvicorn` and making one curl call.
./docs/design-v1.3.md:10:- §3 §4 §7: Legacy nn.db-era snapshot/R_frame counts corrected to demo.db fingerprint (378/10/358/17/13,653).
./docs/design-v1.3.md:444:- **Note:** Prior v1.3 changelog entries reference nn.db-era counts (44,955 snapshots). These are corrected in the post-v1.3 amendments. The demo DB fingerprint is 378/10/358/17/13,653.
./docs/STATUS.md:21:**Phase:** DIAGNOSTIC — Demo DB is a near-subset of production (B): 341/358 demo articles (95.3%) harvested from production via harvest_story.py; 17 independently ingested URLs. Clusters re-derived — only 7/17 titles overlap. Production DB not present as data/nn.db but nn-backup-2026-07-03-1151.db matches FAQ fingerprint. FP: 378/10/358/17/13653.
./docs/STATUS.md:166:| Live data/nn.db writes | Recon phase only. Writes to /tmp copies. |
./pipeline/test_investigate.py:41:    before = _db_counts("data/nn.db")
./pipeline/test_investigate.py:45:    after = _db_counts("data/nn.db")
./pipeline/test_investigate.py:56:    before = _db_counts("data/nn.db")
./pipeline/test_investigate.py:58:    after = _db_counts("data/nn.db")
./pipeline/test_investigate.py:87:    before = _db_counts("data/nn.db")
./pipeline/test_investigate.py:92:    after = _db_counts("data/nn.db")
./pipeline/test_investigate.py:121:    before = _db_counts("data/nn.db")
./pipeline/test_investigate.py:126:    after = _db_counts("data/nn.db")
./pipeline/test_investigate.py:172:    before = _db_counts("data/nn.db")
./pipeline/test_investigate.py:174:    after = _db_counts("data/nn.db")
./pipeline/test_investigate.py:213:    before = _db_counts("data/nn.db")
./pipeline/test_investigate.py:215:    after = _db_counts("data/nn.db")
./.gitignore:49:data/nn.db
./scripts/tune_clustering.py:102:    db = sqlite3.connect("data/nn.db")
./scripts/dryrun_claim_matching.py:3:Runs against a COPY of data/nn.db so the production DB is untouched.
./scripts/dryrun_claim_matching.py:19:    src = _PROJ / "data" / "nn.db"
./scripts/t4a_final_groups.py:6:conn = sqlite3.connect("file:data/nn.db?mode=ro", uri=True)
./scripts/seed_demo.py:5:    python scripts/seed-demo.py [--db data/nn.db]
./scripts/seed_demo.py:49:        help="Path to SQLite database (default: data/nn.db)",
./scripts/_deepseek_backfill_300.py:17:DB = str(_PROJ / "data" / "nn.db")
./scripts/_fireworks_backfill_300.py:17:DB = str(_PROJ / "data" / "nn.db")
./scripts/backfill_framing.py:8:  python scripts/backfill_framing.py [--delay 0.5] [--limit 100] [--db data/nn.db]
./scripts/backfill_framing.py:35:                        help="Database path (default: data/nn.db)")
./scripts/y3_verify.py:27:conn = sqlite3.connect("file:data/nn.db?mode=ro", uri=True)
./scripts/y3_verify.py:41:conn3 = sqlite3.connect("file:data/nn.db?mode=ro", uri=True)
./scripts/backfill_corrections.py:8:  python scripts/backfill_corrections.py [--db data/nn.db]
./scripts/backfill_corrections.py:24:                        help="Database path (default: data/nn.db)")
./scripts/t4a_story_groups.py:6:conn = sqlite3.connect("file:data/nn.db?mode=ro", uri=True)
./scripts/backfill_snapshots.py:7:Usage: python3 scripts/backfill_snapshots.py --db data/nn.db --since 2026-04-01 [--until 2026-07-04]
./scripts/cleanup_empty_clusters.py:14:def delete_empty_clusters(db_path: str = "data/nn.db") -> int:
./scripts/cleanup_empty_clusters.py:45:    db = sys.argv[1] if len(sys.argv) > 1 else "data/nn.db"
./scripts/t4a_extra_groups.py:5:conn = sqlite3.connect("file:data/nn.db?mode=ro", uri=True)
./scripts/ingest_urls.py:9:Usage: python3 scripts/ingest_urls.py [--db data/nn.db] [--csv path/to/urls.csv]
./scripts/t4a_groups.py:6:conn = sqlite3.connect("file:data/nn.db?mode=ro", uri=True)
./scripts/legacy/harvest_story.py:5:  python3 scripts/harvest_story.py --source data/nn.db --db data/demo/demo.db \\
./scripts/legacy/harvest_story.py:102:    parser.add_argument("--source", default="data/nn.db", help="Source DB path")
./scripts/x2_pairwise.py:30:conn = sqlite3.connect("file:data/nn.db?mode=ro", uri=True)
./scripts/reset_claim_state.py:15:db_path = "data/nn.db"
./scripts/z1z2_gap.py:28:conn = sqlite3.connect("file:data/nn.db?mode=ro", uri=True)
./scripts/w1w2_sweep.py:117:    conn3 = sqlite3.connect("file:data/nn.db?mode=ro", uri=True)
./scripts/v2a_db_search.py:24:    conn = sqlite3.connect("data/nn.db")
```

### Analysis

- **`/data/nn.db` (container path):** Only Dockerfile.app line 58 — now fixed.
- **`data/nn.db` (host path):** 30+ references. All are documentation (historical nn.db-era notes), dev scripts with nn.db defaults (production DB, not demo), or `.gitignore`. No runtime code path reads `/data/nn.db` — the app reads `NN_DB_PATH` from env.
- **`pipeline/test_investigate.py`:** 12 hardcoded `data/nn.db` references. This is the only code path not using `NN_DB_PATH`. Listed under PROPOSED.

PROPOSED (not done):
- `pipeline/test_investigate.py`: hardcoded `data/nn.db` should use env var or `NN_DB_PATH` default (`data/demo/demo.db`)

## Task 3 — Verify scripts/smoke.sh

Script already exists with correct content.

### Evidence

```
$ ls -la scripts/smoke.sh
-rw-r--r-- 1 afshin afshin 2841 Jul  9 23:16 scripts/smoke.sh
```

```
$ head -20 scripts/smoke.sh
#!/usr/bin/env bash
# Narrative Nexus — container rebuild + smoke test
# Run from repo root on the host. Exits nonzero on first failure.
set -euo pipefail

EXPECT_ARTICLES=358
EXPECT_SOURCES=37
HOST_DB="data/demo/demo.db"

echo "== 0. Host DB fingerprint (before) =="
python3 - <<EOF
...
```

75 lines, 6 verification steps:
1. Host DB fingerprint check (378/358/17/13653/10)
2. `docker compose down && docker compose build app && docker compose up -d`
3. `/api/stats` response check (articles=358, sources=37)
4. SPA HTML served
5. In-container DB fingerprint at `/data/demo/demo.db`
6. Host DB verified untouched after container shutdown

## Task 4 — Loud-failure guard (PROPOSAL ONLY)

### Problem

`app/main.py:44-47` (lifespan):
```python
db_path = os.environ.get("NN_DB_PATH", "data/demo/demo.db")
os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
init_db(db_path)
```

`init_db()` → `sqlite3.connect(path)` silently creates an empty file if the path doesn't exist, then loads schema. If `NN_DB_PATH` points to the wrong location (e.g., `/data/demo/demo.db` when the golden DB is at `/data/nn.db`), the app boots with zero sources and zero errors.

### Proposed guard

Add to `db/connection.py:init_db()` after `load_schema(conn)`:

```python
# Loud-failure guard: refuse to boot with an empty database.
# sqlite3.connect() silently creates empty files — if the path is wrong,
# the app would boot with zero sources and the bug stays hidden.
n = conn.execute("SELECT COUNT(*) FROM sources").fetchone()[0]
if n == 0:
    raise RuntimeError(
        f"FATAL: database at {path} has zero sources rows. "
        f"Wrong NN_DB_PATH or missing COPY in Dockerfile."
    )
```

This catches the empty-DB case for all callers (FastAPI lifespan, scripts, tests).

## Files modified

| File | Change |
|------|--------|
| `Dockerfile.app` | Line 58: COPY destination `/data/nn.db` → `/data/demo/demo.db` |

## Compliance table

| # | Requirement | Met? | Evidence |
|---|------------|------|----------|
| T1 | Fix Dockerfile.app line 58 | YES | `COPY data/demo/demo.db /data/nn.db` → `COPY data/demo/demo.db /data/demo/demo.db` |
| T2 | Sweep for nn.db references | YES | Grep output above. No runtime code path reads `/data/nn.db`. `pipeline/test_investigate.py` hardcoded `data/nn.db` listed under PROPOSED. |
| T3 | Verify scripts/smoke.sh | YES | 75 lines, 2.8KB, 6 verification steps, chmod 644 |
| T4 | Propose loud-failure guard | YES | Proposal in `db/connection.py:init_db()` — check sources row count after schema load, raise RuntimeError if zero. Not implemented. |

## Commit message

```
UX57: fix Dockerfile.app DB path, add smoke script, propose empty-DB guard

- Dockerfile.app line 58: COPY dest /data/nn.db → /data/demo/demo.db
  (matches NN_DB_PATH in docker-compose.yml — container was booting empty)
- Swept for nn.db references: 30+ in scripts/docs, 1 code path flagged
  (pipeline/test_investigate.py hardcodes data/nn.db — PROPOSED fix)
- scripts/smoke.sh: 6-step container rebuild + fingerprint verification
- Proposed loud-failure guard in db/connection.py:init_db() — refuse to
  start when sources table has zero rows (silent-empty DB masking)
```
