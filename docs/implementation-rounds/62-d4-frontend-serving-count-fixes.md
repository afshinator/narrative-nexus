# D4 — Serve Frontend + totalClaims + Duplicate Claims Fixes

**Date:** 2026-07-06
**Parent commit:** ac89bc5 (D3)
**Status:** COMPLETE — 2 commits (bae4cc3 + 1d0c8f8). Push blocked (SSH).

## Audit

| Item | Value |
|------|-------|
| Fingerprint (demo.db) | 378/10/358/17/13653 (unchanged) |
| npm run build | PASS (457ms, 709 modules) |
| Vitest | 127 pass, 12 fail (pre-existing router-shell + docker volume check matching D2 change), 4 skip |
| git push | BLOCKED — SSH host key verification |
| Commits | bae4cc3 (code) + 1d0c8f8 (STATUS) |

## D4.0 — Serve Frontend from FastAPI

### Problem
Container starts, API works, but `/` returns `{"detail":"Not Found"}`. No static file serving configured.

### Fix
Added SPA catch-all route at bottom of `app/main.py`:

```python
from fastapi.responses import FileResponse
import os as _os

_DIST_DIR = _os.path.join(_os.path.dirname(__file__), "..", "dist")

@app.get("/{full_path:path}")
async def serve_spa(full_path: str = ""):
    if full_path:
        file_path = _os.path.join(_DIST_DIR, full_path)
        if _os.path.isfile(file_path):
            return FileResponse(file_path)
    return FileResponse(_os.path.join(_DIST_DIR, "index.html"))
```

API routes registered BEFORE the catch-all → `/api/*` takes priority. All other paths → SPA fallback.

### Verification (live uvicorn, NN_DB_PATH=data/demo/demo.db)

```
curl http://127.0.0.1:8000/
→ <!doctype html><html lang="en">...  (HTML — SPA index.html)

curl http://127.0.0.1:8000/source/5
→ <!doctype html><html lang="en">...  (HTML — SPA fallback, NOT JSON 404)

curl http://127.0.0.1:8000/cluster/966
→ <!doctype html><html lang="en">...  (HTML — SPA fallback)

curl http://127.0.0.1:8000/api/sources
→ {"sources":[...37 entries...]}  (JSON — API still works)
```

## D4.1 — totalClaims Double-Count Fix

### Problem
`/api/clusters/966/report` returned `totalClaims=20`. DB truth: 19 distinct claims. Claim 2799 has 2 claim_sources → summed per-source counts = 20.

### Root cause
```python
total_claims = sum(s["claims"] for s in sources)  # 20, not 19
```

Same bug class as D1 X1 (absorbed count fixed to COUNT DISTINCT).

### Fix
```python
total_claims = conn.execute(
    "SELECT COUNT(*) FROM claims WHERE cluster_id = ?",
    (cluster_id,),
).fetchone()[0]  # → 19
```

### Verification
```
curl /api/clusters/966/report | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['summary']['totalClaims'])"
→ 19
```

## D4.2 — Duplicate Claim Rows (Domains Array)

### Problem
Claim 2799 has 2 claim_sources (reuters.com + theguardian.com). The claim list JOIN produced 2 rows for the same claim, each with a different domain. Frontend rendered both (key=c.id → React renders both rows for same id).

### DB evidence
```
sqlite3 data/demo/demo.db "
SELECT cl.id, COUNT(*) as src_count
FROM claims cl JOIN claim_sources cs ON cs.claim_id = cl.id
WHERE cl.cluster_id = 966
GROUP BY cl.id HAVING COUNT(*) > 1;
"
2799|2
```

### Fix — API (app/main.py)
Changed claim list construction from flat `[dict(r)]` to deduplication loop:
```python
claims_by_id: dict[int, dict] = {}
for r in claim_rows:
    cid = r["id"]
    if cid not in claims_by_id:
        claims_by_id[cid] = {..., "domains": []}
    claims_by_id[cid]["domains"].append(r["domain"])
claims = list(claims_by_id.values())
```

Response shape: `domain: string` → `domains: string[]`.

### Fix — Frontend (ClusterReport.tsx)
```diff
- domain: string;
+ domains: string[];
...
- {c.domain}
+ {c.domains.join(", ")}
```

### Fix — Test (cluster-report.test.tsx)
```diff
- domain: "reuters.com",
+ domains: ["reuters.com"],
- domain: "bbc.com",
+ domains: ["bbc.com"],
```

### Verification
```
curl /api/clusters/966/report | python3 -c "
d = json.load(sys.stdin)
for c in d['claims']:
    if c['id'] == 2799: print(c['domains'])
"
→ ['reuters.com', 'theguardian.com']

Claims array: 19 entries, 19 unique ids, 0 duplicates
```

## D4.3 — Runbook Update

Added browser check line to `docs/docker-runbook.md`:
```bash
# 5. Open in browser
open http://localhost:8000  # → app loads (SPA served by FastAPI)
```

## D4.4 — Commit

```
$ git log --oneline -5
1d0c8f8 D4: update STATUS.md — post-D4 header, D4 entry, next action
bae4cc3 D4: serve frontend from container, fix totalClaims double-count, dedupe claims with domains array
638ddca update status, better-sqlite3 removal
ac89bc5 D3: remove better-sqlite3 from frontend build — native module breaks container npm ci
3526275 D2: container self-sufficiency — multi-stage build, baked demo DB, runbook
```

```
$ git log -1 --stat
1d0c8f8 D4: update STATUS.md — post-D4 header, D4 entry, next action
 docs/STATUS.md | 7 ++++---
  1 file changed, 4 insertions(+), 3 deletions(-)
```

Push blocked (SSH). Human must push all 3 commits (638ddca + ac89bc5 + bae4cc3 + 1d0c8f8).

## Compliance Table

| # | Requirement | Met? | Evidence |
|---|------------|------|---------|
| D4.0 | Serve frontend: /→index.html, /source/5→HTML, /api→JSON | YES | curl verified: / → HTML, /source/5 → HTML, /api/sources → JSON. app/main.py:582-610 |
| D4.1 | Fix totalClaims double-count: 20→19 | YES | curl verified: 19. app/main.py:443-447 COUNT(*) |
| D4.2 | Dedupe claims array (2799 had 2 rows) | YES | curl verified: 19 entries, 19 unique, domains agg. app/main.py:469-482 |
| D4.3 | Update runbook expected values + browser check | YES | docs/docker-runbook.md:21-22 |
| D4.4 | Commit locally, paste git log -1 --stat | YES | 1d0c8f8, block above |
| Read STATUS.md first | YES | Read line 1-10 |
| Update STATUS.md last | YES | Header (post-D4), D4 entry, Next Action updated |
