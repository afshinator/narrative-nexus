# Backend Slices — Overview

Three sequential slices to build the backend without waiting on API keys.

---

## Slice 8a — Backend Scaffold

**Goal:** Establish the Python package structure, agent interfaces, DB operations layer, and FastAPI route scaffold so all backend code has a home and can be tested.

**Scope:**

| Layer | What | Verification |
|-------|------|-------------|
| `pipeline/` package | `__init__.py`, `base_agent.py` with ABC, agent stubs (1–4), `worker_client.py` stub | `pytest` import tests |
| DB operations | `db/` Python package: `connection.py`, `sources.py`, `articles.py`, `clusters.py`, `claims.py`, `snapshots.py` — CRUD for all 6 tables per `db/schema.sql` | `pytest` tests against in-memory SQLite |
| FastAPI routes | CORS, `/api/health`, `/api/sources`, `/api/sources/{id}`, `/api/articles`, `/api/clusters`, `/api/claims`, `/api/snapshots` — route-only stubs returning 501/empty lists for now | `pytest` via `TestClient` |
| Requirements | Add `apscheduler` to `requirements.txt`, pin existing deps | `pip install -r requirements.txt` |
| Seed script scaffold | `scripts/seed-demo.py` — CLI stub with argparse, imports `pipeline/` module | `python scripts/seed-demo.py --help` |
| Pytest infra | `conftest.py`, `pytest.ini` with coverage config, fixture for test DB | `pytest` |
| .gitignore | Add `__pycache__`, `*.pyc`, `venv/`, `.coverage` | `git status` |

**Requires:** None (pure Python, zero API keys)
**Deliverable:** Backend structure testable in isolation. Frontend can call `/api/*` routes and get structured responses (empty but correct).

---

## Slice 8b — Scraper + Scheduler

**Goal:** The scraping stack per REQ-058/059 — RSS discovery via feedparser, article body extraction via newspaper4k, scheduled polling loop.

**Scope:**

| Component | What | Verification |
|-----------|------|-------------|
| RSS feed config | Map of source domain → RSS feed URLs for all 20 sources | Config file / dict |
| `pipeline/scraper.py` | `RSSPoller` class: fetch feed, parse entries, deduplicate by URL | `pytest` against test RSS fixtures |
| `pipeline/extractor.py` | `ArticleExtractor`: newspaper4k body extraction, body_status classification, paywall detection | `pytest` against known URLs or local fixtures |
| `pipeline/scheduler.py` | APScheduler integration: polling interval, backoff, error logging, writes to `articles` table | Integration test |
| DB writes | Scraped articles → `articles` table with source_id, url, title, body, body_status | Verify via direct DB query |

**Requires:** Slice 8a (DB ops layer, pipeline package)
**Deliverable:** RSS feeds polled, articles extracted, stored in SQLite. Visible via `/api/articles` endpoint.

---

## Slice 8c — Consensus Engine

**Goal:** Pure Python consensus math, reputation scoring, claim resolution, and archetype assignment — all testable without any LLM or API key.

**Scope:**

| Component | What | Verification |
|-----------|------|-------------|
| `pipeline/consensus.py` | Baseline computation (threshold% of Tier 1+2 pool), claim classification (CONSENSUS_ABSORBED / UNRESOLVED) | `pytest` with synthetic data |
| `pipeline/reputation.py` | 6-dimension scoring (R_orig, R_val, R_speed, R_frame, R_edit, R_correct) from snapshot data | `pytest` with known inputs → expected outputs |
| `pipeline/resolution.py` | 7/30/90-day check logic, state machine transitions, convergence type assignment | `pytest` with time-shifted fixtures |
| `pipeline/archetype.py` | Archetype assignment from R_orig/R_val vs panel median | `pytest` |
| `pipeline/snapshots.py` | Daily snapshot computation/writer, snapshot backfill | `pytest` |

**Requires:** Slice 8a (DB ops layer, pipeline package). Does NOT require Slice 8b (can operate on manually inserted data).
**Deliverable:** All consensus math and reputation scoring working and tested. When combined with real data from scraper + pipeline agents, produces correct scores end-to-end.

---

## Dependencies between slices

```
8a (scaffold) ──→ 8b (scraper + scheduler)
   │
   └──→ 8c (consensus engine)
```

8b and 8c are parallel — both depend on 8a but not on each other.
