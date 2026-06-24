# Plan: Slice 2 — Docker + DB Foundation

## Requirements addressed

| Req | Description | How |
|-----|-------------|-----|
| REQ-007 | Containerized with docker-compose.yml at project root | `docker-compose.yml` |
| REQ-008 | At least 3 services: app, worker, db | Service definitions |
| REQ-102 | App service for FastAPI server | `app:` service |
| REQ-103 | Worker service for AMD GPU pod | `worker:` service |
| REQ-104 | Database service or volume with SQLite | SQLite volume mount on app |
| REQ-105 | App and worker communicate over HTTP | Network config |
| REQ-106 | Fireworks API calls originate from app | Documented in compose comments |
| REQ-107 | Worker uses ROCm base image + sentence-transformers | `worker:` image |

## Design (from docs/design-v1.2.md §8)

Three services:
- **app** — FastAPI server, scheduler, API endpoints, frontend static serving. Python 3.12, port 8000. SQLite volume. No GPU.
- **worker** — AMD GPU pod. ROCm base image. sentence-transformers. Exposes HTTP endpoint for embedding requests.
- **db** — SQLite file on a named volume mounted to app. No separate container needed (SQLite is file-based).

Network: `nn-network` (bridge). App exposes port 8000. Worker internal only.

## SQLite schema

Tables (in `db/schema.sql`):

| Table | Purpose | Key columns |
|-------|---------|-------------|
| `sources` | Source panel registry | id, name, domain, tier, active, created_at |
| `articles` | Scraped article storage | id, source_id, url, title, body, published_at, body_status |
| `clusters` | Story clusters | id, vertical, title, created_at |
| `claims` | Extracted factual claims | id, article_id, cluster_id, text, state, convergence_type, absorbed_at |
| `claim_sources` | Which sources published each claim | claim_id, source_id, first_seen_at |
| `snapshots` | Daily reputation snapshots | id, source_id, vertical, date, r_orig, r_val, r_speed, r_frame, r_edit, r_correct, archetype |

Design decisions:
- SQLite WAL mode (per REQ-112)
- `body_status` enum: AVAILABLE, BODY_UNAVAILABLE (per REQ-061)
- `state` enum: PENDING, CONSENSUS_ABSORBED, UNRESOLVED (per REQ-027–029)
- `convergence_type`: CROSS_SOURCE_CONVERGENT, SELF_CONSISTENT (per REQ-030–031)
- Foreign keys enforced. Timestamps default to CURRENT_TIMESTAMP.

## Assumptions requiring validation (Phase 3.5) — ✅ VALIDATED

1. **`better-sqlite3`** — installed, in-memory DB creation works (`CREATE TABLE` succeeds). Can test schema DDL without Docker.
2. **`docker-compose.yml`** — minimal draft created at project root. Structure validates: exactly 3 services (app, worker, db), has `networks:` and `volumes:` sections. YAML syntax valid.

   Docker `compose up` cannot be tested in this environment (Docker not installed), but the file structure, service count, and key properties match REQ-102–107.

## Files to modify

| File | Content |
|------|---------|
| `docker-compose.yml` | 3 services + network + volume |
| `db/schema.sql` | CREATE TABLE statements + indexes |
| `db/__tests__/schema.test.ts` | In-memory SQLite schema validation |

## Verification

1. **Structural validation** — `npm run test:docker` runs `src/__tests__/docker/compose.test.ts` (15 tests). Validates YAML, 3 services, ports, networks, volumes. No Docker needed.
2. **Integration test** — `npm run test:docker` runs `src/__tests__/docker/integration.test.ts` (4 tests). On a host with Docker: `compose up`, verify 3 services running, check nn-network and nn-data volume, `compose down`. Skips automatically when Docker unavailable.
3. **Schema validation** — `npm run test` runs `db/__tests__/schema.test.ts` against in-memory SQLite. Verify all 6 tables create without errors, columns match spec.
4. `npm run build` exits 0 (no TS changes expected)
5. `npm run test` — existing 38 tests + new schema tests pass
