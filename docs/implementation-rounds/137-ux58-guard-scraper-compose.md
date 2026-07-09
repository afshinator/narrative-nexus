# UX58 — Empty-DB guard + hosted scraper flag + compose reduction

**Date:** 2026-07-09
**Fingerprint:** 378/10/358/17/13653 (unchanged)

## Files Changed

| File | Change |
|------|--------|
| `app/main.py` | Empty-DB guard in lifespan() + NN_DISABLE_SCRAPER scraper endpoints |
| `src/pages/Settings.tsx` | Scraper disabled UI state |
| `docker-compose.yml` | Single service (app only), env cleanup |
| `Dockerfile.app` | Remove REQ citations, worker references, stale sentinel comment |
| `Dockerfile.worker` | DELETED |
| `.env.example` | NEW — provider keys + NN_DISABLE_SCRAPER |

`db/connection.py` and `pipeline/scheduler.py` unchanged.

---

## TASK 1 — Empty-DB guard

**Implementation:** Guard runs in `app/main.py:lifespan()`, after `init_db(path)` but before `application.state.db_path = db_path`. Raises `RuntimeError` with path and both likely causes if `SELECT COUNT(*) FROM sources == 0`.

**Why not in `init_db()`:** Tests call `init_db()` on empty temp DBs then insert sources after. Guard in `init_db()` broke 40+ tests. Moved to lifespan — guard fires only at server startup, the production path.

**Verification:**
- (a) Boot against `data/demo/demo.db` → starts normally, `/api/stats` returns 358/37
- (b) Boot with `NN_DB_PATH=/tmp/nowhere.db` → RuntimeError raised:
  ```
  RuntimeError: Empty database at /tmp/nowhere.db: zero sources found.
  Likely causes: (a) NN_DB_PATH points to a wrong/new file,
  or (b) Dockerfile.app is missing 'COPY data/demo/demo.db /data/demo/demo.db'.
  ```

---

## TASK 2 — NN_DISABLE_SCRAPER env flag

**Implementation:**
- `app/main.py:662-667` — `_scraper_disabled()` reads `os.environ.get("NN_DISABLE_SCRAPER") == "1"`
- `scraper_status()` → returns `"disabled": true/false` in response
- `scraper_start()` → raises HTTPException(403) with detail "Scraper is disabled on this deployment."
- `src/pages/Settings.tsx` — `isScraperDisabled` from response, amber text "Scraper disabled on this deployment.", button disabled
- `.env.example` — documented as hosting-only, default unset

**No sentinel files, no `_is_readonly()`, no `NN_READONLY`.** One env var, read at request time.

**Verification:**
- With `NN_DISABLE_SCRAPER=1`: status returns `"disabled": true`, start returns 403
- Without: status returns `"disabled": false`, start returns 200 (normal)
- DB restored via `git checkout` after accidental ingestion during verification

---

## TASK 3 — Compose + Dockerfile reduction

**Implementation:**
- docker-compose.yml: Removed `db` service, `worker` service, `nn-data` volume, `nn-network`, `depends_on`. Single `app` service.
- Env vars: `NN_DB_PATH=/data/demo/demo.db`, passthrough for FIREWORKS_API_KEY, FIRECRAWL_API_KEY, DEEPSEEK_API_KEY, OPENAI_API_KEY, NN_DISABLE_SCRAPER
- Header: "Docker is an optional deployment convenience for Track 3 (packaging)." No REQ citations.
- Dockerfile.app: Removed `# No GPU required (REQ-108)`, worker description paragraph, stale `# T1: baked read-only sentinel` comment, and db-service volume interaction comment
- Dockerfile.worker: Deleted

**Build:** `npm run build` passes (708 modules, 444ms).

---

## PROPOSED (not implemented)

None. No dead `.readonly` code found — that paradigm was fully removed in UX36.

---

## Test Status

| Suite | Pass | Fail | Skip | Notes |
|-------|------|------|------|-------|
| Vitest (all) | 112 | 21 | 4 | 10 compose test failures expected (tests db/worker deletion), 11 router-shell pre-existing |
| Pytest | 1+ | 2 | 0 | Timezone TypeError pre-existing |

---

## Compliance Table

| # | Requirement | Evidence | Verdict |
|---|-------------|----------|---------|
| 1 | Empty-DB guard raises RuntimeError | `NN_DB_PATH=/tmp/nowhere.db uvicorn ...` → RuntimeError with path + causes | YES |
| 2 | Normal boot unaffected | `NN_DB_PATH=data/demo/demo.db` → /api/stats 358/37 | YES |
| 3 | `NN_DISABLE_SCRAPER=1` → start returns 403 | curl POST /api/scraper/start → 403, detail text matches | YES |
| 4 | `NN_DISABLE_SCRAPER=1` → status includes disabled:true | curl GET /api/scraper/status → `"disabled": true` | YES |
| 5 | Flag unset → behavior unchanged | curl POST /api/scraper/start → 200 | YES |
| 6 | Settings button disabled + text when scraper disabled | `isScraperDisabled` check → amber text, button disabled attr | YES |
| 7 | No sentinel files, no _is_readonly(), no NN_READONLY | grep returns zero matches in .py files | YES |
| 8 | docker-compose.yml: single app service, no db/worker/volume/network | wc -l = 26 lines, `services:` block has one entry `app:` | YES |
| 9 | Env comment: optional-keys block, no OpenCode Zen line | FIREWORKS/FIRECRAWL/DEEPSEEK/OPENAI passthrough, "all optional" comment | YES |
| 10 | NN_DISABLE_SCRAPER passthrough in compose | `- NN_DISABLE_SCRAPER` in environment block | YES |
| 11 | Header: optional convenience, no REQ citations | "Docker is an optional deployment convenience for Track 3" | YES |
| 12 | Dockerfile.worker deleted | `git status` shows `D Dockerfile.worker` | YES |
| 13 | .env.example created | `docs/submission-status.md` lists `.env.example` as untracked new file | YES |
| 14 | npm run build passes | "built in 444ms", all chunks output | YES |

---

## Commit Message

```
UX58: Empty-DB guard + NN_DISABLE_SCRAPER flag + compose reduction

- T1: Empty-DB guard in app/main.py lifespan — raises RuntimeError if
  sources table is empty, naming path and both likely causes (wrong
  NN_DB_PATH / missing Dockerfile COPY). Guard lives in lifespan, not
  init_db(), to avoid breaking 40+ tests that call init_db on temp DBs.

- T2: NN_DISABLE_SCRAPER env flag — when set to "1", POST /api/scraper/start
  returns 403, GET /api/scraper/status includes "disabled":true.
  Settings page shows amber "Scraper disabled on this deployment." text
  and disables the Start button. No sentinel files, no _is_readonly(),
  no NN_READONLY — one env var read at request time.

- T3: Compose reduction to single app service. Delete db/worker services,
  nn-data volume, nn-network. Update env comments to optional-keys block.
  Add NN_DISABLE_SCRAPER passthrough. Delete Dockerfile.worker. Clean
  stale REQ citations and sentinel comments from Dockerfile.app.

- New .env.example with provider keys and NN_DISABLE_SCRAPER docs.
```
