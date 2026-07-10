# 001 — GEMMA-1: Gemma 4 E4B Integration

**Round:** GEMMA-1 (Work Order, reissue)
**Date:** 2026-07-10
**Status:** BLOCKED at T2 (STOP GATE A — no deployment found)

---

## T1 — Baseline Fingerprint

**ECHO:** Golden DB fingerprint before any work.

```
sqlite3 "file:data/demo/demo.db?mode=ro" "SELECT ..."
378|10|358|17|13653
```

PASS — matches expected `378|10|358|17|13653`.

```
ls data/demo/
demo.db  4.5M
demo.db-shm  32.0K
demo.db-wal  0B
```
WAL/SHM are SQLite artifacts from read-only open — normal, expected.

---

## T2 — Discover Deployment Model String

**ECHO:** Query Fireworks API for gemma deployments.

Account ID discovered via `GET /v1/accounts`: `accounts/afshinator-b1hiwmnhr`

### Attempt 1: Deployments endpoint

```
curl -s -H "Authorization: Bearer [REDACTED]" \
  "https://api.fireworks.ai/v1/accounts/afshinator-b1hiwmnhr/deployments"
```

**Response:**
```json
{
    "deployments": [],
    "nextPageToken": "",
    "totalSize": 0
}
```

### Attempt 2: DeployedModels endpoint

```
curl -s -H "Authorization: Bearer [REDACTED]" \
  "https://api.fireworks.ai/v1/accounts/afshinator-b1hiwmnhr/deployedModels"
```

**Response:**
```json
{
    "deployedModels": [],
    "nextPageToken": "",
    "totalSize": 0
}
```

### Attempt 3: Model catalog search for "gemma"

Searched `GET /v1/models` data array for any model ID containing "gemma".

**Response:** `[]` — zero gemma models in the Fireworks inference catalog.

### STOP GATE A — No deployment exists

Zero deployments, zero deployed models, zero gemma catalog entries. The on-demand deployment either:
- Has not been created yet (human needs to deploy via Fireworks dashboard)
- Was created under a different account
- Was undeployed and not re-deployed after the repo re-clone

---

## T3 — Raw Smoke Inference

**NOT DONE** — blocked on T2 gate.

## T4 — Add Provider Entry

**NOT DONE** — blocked on T2 gate.

## T5 — Pipeline Gemma Pass

**NOT DONE** — blocked on T2 gate.

## T6 — Evidence File + Undeploy Reminder

**NOT DONE** — blocked on T2 gate.

---

## Compliance Table

| task/constraint | met EXACTLY? | evidence pointer |
|---|---|---|
| T1 — Baseline fingerprint | YES | `378\|10\|358\|17\|13653` matches expected |
| T2 — Discover model string | CANNOT COMPLY | All 3 API endpoints return empty/zero results |
| T3 — Raw smoke inference | NOT DONE | blocked on T2 gate |
| T4 — Add provider entry | NOT DONE | blocked on T2 gate |
| T5 — Pipeline Gemma pass | NOT DONE | blocked on T2 gate |
| T6 — Evidence file + reminder | NOT DONE | blocked on T2 gate |
| HC1 — Golden DB read-only | YES | fingerprint unchanged; read-only mode used |
| HC2 — Don't change defaults block | YES | not touched |
| HC3 — Don't re-run pipeline | YES | not triggered |
| HC4 — FIREWORKS_API_KEY from env | YES | key exists in `~/.hermes/.env`, used for API calls |
| HC5 — Scope wall T1-T6 | YES | nothing beyond T1-T2 attempted |

---

## Proposed (not done)

- Human must create the on-demand Gemma 4 E4B deployment via Fireworks dashboard at https://fireworks.ai before re-issuing this order.
- After deployment, the model string should be discoverable via the `deployments` or `deployedModels` endpoints (or visible in the Fireworks dashboard UI).
