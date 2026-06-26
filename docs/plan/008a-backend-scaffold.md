# Plan: Slice 8a — Backend Scaffold

## Requirements addressed

| Req | Description | How |
|-----|-------------|-----|
| REQ-013 | IntakeClusteringAgent | `pipeline/agent1_intake.py` — ABC interface + stub method |
| REQ-014 | ForensicExtractionAgent | `pipeline/agent2_forensic.py` — ABC interface + stub method |
| REQ-015 | ConsensusAlignmentAgent | `pipeline/agent3_consensus.py` — ABC interface + stub method |
| REQ-016 | SilentAuditorAgent | `pipeline/agent4_silent.py` — ABC interface + stub method |
| REQ-058 | feedparser for RSS | Dep added to `requirements.txt` |
| REQ-059 | newspaper4k for body extraction | Dep added to `requirements.txt` |
| REQ-096 | Seed script (scaffold) | `scripts/seed-demo.py` — CLI stub |
| REQ-102 | Docker app service | No changes needed (exist) |
| REQ-105 | App ↔ worker HTTP | `pipeline/worker_client.py` — stub client |
| REQ-111 | APScheduler in-process | Dep added to `requirements.txt` |

Also: REQ-007 (containerized), REQ-008 (3 services), REQ-019 (CPU consensus math), REQ-032–046 (reputation dimensions — type definitions only).

## Dependencies

| Dep | Version | Where | Verified? |
|-----|---------|-------|-----------|
| Python | 3.11 | System | Yes — `python3 --version` → 3.11.2 |
| fastapi | 0.137.1 | pip global | Yes |
| uvicorn | 0.49.0 | pip global | Yes |
| httpx | 0.28.1 | pip global | Yes |
| pytest | 9.1.0 | pip global | Yes |
| APScheduler | 3.11.2 | pip global | Yes |
| feedparser | 6.0.12 | pip global | Yes |
| newspaper4k | 0.9.5 | pip global | Yes |
| sqlite3 | 3.40.1 | stdlib | Yes |
| better-sqlite3 | Node dep | package.json | Frontend-only, not needed here |

All deps exist in the environment. `requirements.txt` currently lists only `fastapi>=0.115.0` and `uvicorn>=0.34.0`. Will be updated to include `apscheduler`, `feedparser`, `newspaper4k`, `httpx`, and `pytest`.

## Key assumptions (verified against codebase)

1. **No existing Python package structure** — neither `pipeline/` nor `db/` have `__init__.py`. Confirmed.
2. **`db/schema.sql` is the authoritative schema** — the 6 tables (sources, articles, clusters, claims, claim_sources, snapshots) are designed and tested in `db/__tests__/schema.test.ts`. We mirror the schema in the Python DB ops layer.
3. **Vite proxies `/api` to `:8000`** — confirmed in `vite.config.ts`: `proxy: { "/api": "http://localhost:8000" }`. The frontend can call `/api/*` routes after this slice.
4. **No frontend API calls exist yet** — confirmed: zero `fetch` or `axios` calls in `src/`. Routes are pure scaffold for now; wiring them to the frontend happens in later slices when the backend produces real data.
5. **APScheduler in-process** — confirmed per REQ-111 and ADR-0003. No Celery/Redis.
6. **Worker communicates over HTTP** — confirmed per ADR-0003 and REQ-105. The `worker_client.py` stub reflects this.

## Architecture decisions

### Decision 1: One Python `db/` package, not per-table modules only

The `db/` package has modules per table:
```
db/
  __init__.py         # re-exports, optional convenience
  connection.py       # get_db(), close_db(), init_db()
  sources.py          # get_source(), list_sources(), ...
  articles.py         # get_article(), list_articles(), insert_article(), ...
  clusters.py         # get_cluster(), list_clusters(), create_cluster(), ...
  claims.py           # get_claim(), list_claims(), insert_claim(), update_claim_state(), ...
  claim_sources.py    # add_claim_source(), list_claim_sources(), ...
  snapshots.py        # get_snapshot(), list_snapshots(), insert_snapshot(), ...
```

Each module imports `connection.py` for DB access. Tests use an in-memory SQLite database loaded from `db/schema.sql`.

### Decision 2: Agent ABCs with abstract methods, not concrete implementations

Each agent is an abstract base class with:
```python
class IntakeClusteringAgent(ABC):
    @abstractmethod
    async def run(self, article_texts: list[str]) -> list[Cluster]:
        ...
```

This lets the stub pass `pytest` (no abstract-method error on instantiation) while forcing concrete implementations to implement `run()`. The stub returns `[]` / `{}` — never `NotImplementedError` or `pass`.

### Decision 3: `/api/*` routes return empty structures, not 404

FastAPI routes return correct response shapes (empty lists, null values) so the frontend can call them immediately:

- `GET /api/health` → `{"status": "ok", "version": "0.1.0"}`
- `GET /api/sources` → `{"sources": []}`
- `GET /api/sources/{id}` → `{"source": null, "error": "not implemented"}`
- `GET /api/articles` → `{"articles": []}`
- `GET /api/clusters` → `{"clusters": []}`
- `GET /api/claims` → `{"claims": []}`
- `GET /api/snapshots` → `{"snapshots": []}`

No POST/PUT routes yet — those come when agents write data.

### Decision 4: `scripts/seed-demo.py` as CLI, not a FastAPI endpoint

Per ADR-0002, the seed script is a one-shot CLI tool. Scaffold includes:
- `argparse` with `--articles` (path to article URL list) and `--db` (SQLite path)
- Imports from `pipeline/` module
- `if __name__ == "__main__"` guard
- Stub body that prints "Seed script scaffold ready"

### Decision 5: pytest conftest + ini, not pyproject.toml mixing

The project already uses `pyproject.toml` for Python? No — there is no Python `pyproject.toml`. The project's `package.json`, `tsconfig.json`, `vite.config.ts` are all Node/JS config. Adding a Python `pyproject.toml` solely for pytest config would be noise.

Use `pytest.ini` for config (minimal), `conftest.py` for fixtures. `pytest.ini` content:
```ini
[pytest]
testpaths = pipeline db
python_files = test_*.py
```

### Decision 6: Worker client as httpx stub, not real embedding calls

```python
class WorkerClient:
    def __init__(self, base_url: str = "http://worker:8001"):
        self.client = httpx.AsyncClient(base_url=base_url)

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Stub — returns empty embeddings until worker is implemented."""
        return [[0.0] * 384 for _ in texts]
```

The stub returns zero-vectors of the correct dimension (384 = all-MiniLM-L6-v2 default). This lets the pipeline code that calls embeddings work without the worker. When the worker is real, swapping the stub for a real HTTP call is a one-line change.

### Decision 7: Requirements.txt gets all deps pinned with compatible versions

Current `requirements.txt`:
```
fastapi>=0.115.0
uvicorn>=0.34.0
```

New:
```
fastapi>=0.115.0
uvicorn>=0.34.0
apscheduler>=3.11.0
feedparser>=6.0.12
newspaper4k>=0.9.5
httpx>=0.28.0
pytest>=9.1.0
```

Using `>=` ranges for compatibility with both local dev (where these are already installed) and Docker builds (which install fresh).

## Data model

No new data types — the DB schema at `db/schema.sql` is the data model. The Python DB ops layer mirrors it as Python dicts/typed dicts:

```python
# TypedDicts in db/sources.py (example)
class Source(TypedDict, total=False):
    id: int
    name: str
    domain: str
    tier: int  # 1-5
    active: bool
    created_at: str
```

Using `TypedDict` with `total=False` so partial inserts work naturally for autoincrement/default fields.

## Route design

FastAPI routes in `app/main.py`:

```
GET /api/health           → {"status": "ok", "version": "0.1.0"}
GET /api/sources          → {"sources": [...]}  (from db, or [])
GET /api/sources/{id}     → {"source": {...}}   (or null)
GET /api/articles         → {"articles": [...]}
GET /api/clusters         → {"clusters": [...]}
GET /api/claims           → {"claims": [...]}
GET /api/snapshots        → {"snapshots": [...]}
```

CORS enabled for local development (Vite dev server on `:5173`).

## New files

| File | Purpose |
|------|---------|
| `pipeline/__init__.py` | Package marker |
| `pipeline/base_agent.py` | `BasePipelineAgent` ABC |
| `pipeline/agent1_intake.py` | `IntakeClusteringAgent` stub |
| `pipeline/agent2_forensic.py` | `ForensicExtractionAgent` stub |
| `pipeline/agent3_consensus.py` | `ConsensusAlignmentAgent` stub |
| `pipeline/agent4_silent.py` | `SilentAuditorAgent` stub |
| `pipeline/worker_client.py` | HTTP client stub for worker container |
| `pipeline/test_agents.py` | Tests: agent ABCs import, instantiate, stubs return correct types |
| `db/__init__.py` | Package marker |
| `db/connection.py` | SQLite connection manager, schema loader |
| `db/sources.py` | Sources CRUD |
| `db/articles.py` | Articles CRUD |
| `db/clusters.py` | Clusters CRUD |
| `db/claims.py` | Claims CRUD |
| `db/claim_sources.py` | Claim-Source relationship CRUD |
| `db/snapshots.py` | Snapshots CRUD |
| `db/test_connection.py` | Tests: in-memory DB loads schema |
| `db/test_sources.py` | Tests: CRUD for sources |
| `db/test_articles.py` | Tests: CRUD for articles |
| `db/test_clusters.py` | Tests: CRUD for clusters |
| `db/test_claims.py` | Tests: CRUD + state enforcement |
| `db/test_claim_sources.py` | Tests: composite PK |
| `db/test_snapshots.py` | Tests: CRUD + unique constraint |
| `scripts/seed-demo.py` | CLI scaffold — imports pipeline, argparse, stub body |
| `conftest.py` | Pytest fixtures: in-memory DB, loaded schema |
| `pytest.ini` | Pytest config |

## Existing files modified

| File | Change |
|------|--------|
| `requirements.txt` | Add apscheduler, feedparser, newspaper4k, httpx, pytest |
| `.gitignore` | Add `__pycache__/`, `*.pyc`, `venv/`, `.coverage`, `htmlcov/` |
| `app/main.py` | Add CORS middleware, `/api/*` route stubs |
| `.dockerignore` | Add `__pycache__`, `*.pyc`, `venv` if not already present |

## Implementation order

1. **Requirements + gitignore** — update `requirements.txt` and `.gitignore`
2. **DB connection + tests** — `db/connection.py` with schema loader, `conftest.py`, `pytest.ini`
3. **DB CRUD modules** — sources, articles, clusters, claims, claim_sources, snapshots (each with tests)
4. **Pipeline package + agent ABCs** — `pipeline/__init__.py`, `base_agent.py`, 4 agent stubs, worker client
5. **Agent tests** — import tests, stub return type tests
6. **FastAPI routes** — CORS, `/api/*` stubs in `app/main.py`
7. **Seed script scaffold** — `scripts/seed-demo.py`
8. **Verify** — `pytest`, `pip install -r requirements.txt`, verify routes respond

## Test strategy

All backend tests use `pytest` with an in-memory SQLite database loaded from `db/schema.sql` (the same schema the frontend tests verify in `db/__tests__/schema.test.ts`). No vitest changes needed.

| Test | What it verifies |
|------|-----------------|
| DB connection loads schema | In-memory DB has all 6 tables |
| Sources CRUD | Insert, find by id, find by domain, list all, check tier constraint |
| Articles CRUD | Insert with source FK, body_status constraint, list by source |
| Clusters CRUD | Insert with vertical constraint, list by vertical |
| Claims CRUD | Insert, state constraint, convergence_type constraint, FK enforcement |
| Claim sources CRUD | Insert, composite PK uniqueness |
| Snapshots CRUD | Insert, unique(source_id, vertical, date) |
| Agent ABC imports | All 4 agents import without error |
| Agent stubs return correct types | `run()` returns `[]` / `{}` |
| Worker client stub | Returns correct-dimension embeddings |
| FastAPI health | `GET /api/health` returns 200 |
| FastAPI sources | `GET /api/sources` returns structured response |

## Verification checklist

- [ ] `pytest` — all backend tests pass
- [ ] `pip install -r requirements.txt` exits 0
- [ ] `uvicorn app.main:app` starts without error, routes respond to curl
- [ ] `python scripts/seed-demo.py --help` prints help
- [ ] `git status` shows only expected files
- [ ] `npm run build` still passes (no frontend changes)
- [ ] `npx vitest run` still passes (133 tests)
