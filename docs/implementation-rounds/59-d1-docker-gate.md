# D1 — Docker Clean-Checkout Gate (+2 Fixes)

**Date:** 2026-07-06
**Commit:** `30014a5` (fixes) + amended with this doc

---

## X1 — Cluster Report Absorbed Count Fix

### Problem

`app/main.py:437` computed `total_absorbed` as a per-source sum:

```python
total_absorbed = sum(s["absorbed"] for s in sources)
```

This double-counted merged claims: claim 2799 appears in claim_sources under both reuters and theguardian, so the GROUP BY per source produced absorbed=1 for each, summing to 2. Unique absorbed = 1.

### Fix

```python
total_absorbed = conn.execute(
    "SELECT COUNT(DISTINCT id) FROM claims "
    "WHERE cluster_id = ? AND state = 'CONSENSUS_ABSORBED'",
    (cluster_id,),
).fetchone()[0]
```

### Diff

```
-    total_absorbed = sum(s["absorbed"] for s in sources)
+    # Count DISTINCT absorbed claims (avoid per-source double-count from
+    # claim_sources JOIN — a merged claim appears under multiple sources).
+    total_absorbed = conn.execute(
+        "SELECT COUNT(DISTINCT id) FROM claims "
+        "WHERE cluster_id = ? AND state = 'CONSENSUS_ABSORBED'",
+        (cluster_id,),
+    ).fetchone()[0]
```

### Verification

```
$ curl -s http://localhost:8000/api/clusters/966/report | jq .summary
{
  "totalClaims": 20,
  "absorbed": 1,        ← was 2
  "pending": 7,
  "sourceCount": 3
}
```

---

## X2 — Archetype Null Contract

### Problem

`_get_latest_archetype()` returned the stored archetype even when r_orig or r_val was NULL. The /api/sources endpoint enforced the null contract (NULL r_orig/r_val → archetype=null), but the profile endpoint didn't.

### Fix

```python
row = conn.execute(
    "SELECT archetype, r_orig, r_val FROM snapshots "
    "WHERE source_id = ? AND vertical = ? "
    "ORDER BY date DESC LIMIT 1",
    (source_id, vertical),
).fetchone()
if not row:
    return None
# Null contract: if r_orig or r_val is NULL, archetype is null
if row["r_orig"] is None or row["r_val"] is None:
    return None
return row["archetype"]
```

### Diff

```
-    row = conn.execute(
-        "SELECT archetype FROM snapshots ..."
-    ).fetchone()
-    return row["archetype"] if row else None
+    row = conn.execute(
+        "SELECT archetype, r_orig, r_val FROM snapshots ..."
+    ).fetchone()
+    if not row:
+        return None
+    if row["r_orig"] is None or row["r_val"] is None:
+        return None
+    return row["archetype"]
```

### Verification

```
$ curl -s http://localhost:8000/api/sources/7/profile?vertical=geopolitics | jq .archetype
null           ← politico (all NULL snapshots)
```

---

## D1a — Git Clone (PASS)

```
$ git clone /project/narrative-nexus /tmp/nn-clean
Cloning into '/tmp/nn-clean'...
done.

$ cd /tmp/nn-clean && git branch --show-current
revise01

$ git log --oneline -3
1251d77 FV4: 966 reconcile, archetype canon, cluster title
f7617be FV3: archetype API + render verification
49e8a1c STATUS update: FV1+2 complete, violations 19-20, 378/10/358/17/13653
```

Clean clone at HEAD `1251d77` (pre-D1 fixes). Files present: Dockerfile.app, Dockerfile.worker, docker-compose.yml.

---

## D1b — Docker Build (CANNOT COMPLY)

```
$ docker compose build app
docker not found
$ which podman → not found
$ which nerdctl → not found
```

**CANNOT COMPLY: no container runtime installed.** Docker, podman, nerdctl all absent from this environment.

### Static Analysis of Dockerfile.app

Even if docker were available, the build would fail:

```
COPY dist/ ./dist/    ← dist/ does not exist in git or working tree
```

`dist/` is not tracked in git (`git ls-files dist/` → empty). The frontend must be built first: `npm install && npm run build` before `docker compose build`.

---

## D1c — Docker Run (CANNOT COMPLY)

No container runtime — cannot start services, cannot curl endpoints.

---

## D1d — DB Source Investigation (Analysis Only)

### How the DB arrives in the container

Relevant lines from `docker-compose.yml`:

```yaml
app:
  volumes:
    - nn-data:/data
  environment:
    - NN_DB_PATH=/data/nn.db

db:
  image: busybox
  volumes:
    - nn-data:/data
  command: ["sh", "-c", "mkdir -p /data && touch /data/.ready && tail -f /dev/null"]

volumes:
  nn-data:
```

Relevant lines from `Dockerfile.app`:

```dockerfile
COPY app/     ./app/
COPY db/      ./db/
COPY pipeline/ ./pipeline/
COPY config/  ./config/
COPY dist/    ./dist/
RUN mkdir -p /data
```

### Answer

| Mechanism | Present? |
|-----------|----------|
| Baked into image (COPY in Dockerfile) | **No** — Dockerfile copies app/, db/, pipeline/, config/, dist/ — never data/demo/ |
| Mounted from host | **No** — compose mounts an empty Docker volume `nn-data` |
| Fetched from git | **No** — `data/demo/demo.db` is tracked in git but no step in Dockerfile or compose copies it |
| Initialized by app on startup | **Yes** — `init_db()` creates empty tables at `/data/nn.db` |

**Finding:** The container serves an EMPTY database. The golden demo DB (378 claims, 10 absorbed, 358 articles, 17 clusters, 13,653 snapshots) is not available to the container by any path in the current Dockerfile or compose configuration. `app/main.py:44` reads `NN_DB_PATH` (default `data/nn.db`), and `init_db()` at line 46 creates tables but no data.

### Required to fix

Two changes needed:
1. Add `RUN npm install && npm run build` (or `COPY dist/` after pre-building) for the frontend
2. Add `COPY data/demo/demo.db /data/nn.db` in Dockerfile.app, OR mount `./data/demo/demo.db:/data/nn.db` in compose, OR add an init script

---

## Commit

```
30014a5 D1: X1 absorbed count fix (DISTINCT), X2 archetype null contract

app/main.py | 15 insertions(+), 3 deletions(-)
```

---

## Compliance Table

| # | Requirement | Met? | Evidence |
|---|---|---|---|
| **X1** | Cluster report absorbed count → DISTINCT | YES | `COUNT(DISTINCT id)` replaces sum. 966: 2→1. |
| **X1** | Diff pasted | YES | Above. |
| **X1** | API response showing absorbed=1 | YES | `curl .../966/report` → `"absorbed": 1`. |
| **X2** | Archetype null contract in profile | YES | NULL r_orig/r_val → null. politico→null. |
| **X2** | Diff pasted | YES | Above. |
| **X2** | Politico profile showing null | YES | `curl .../7/profile` → `"archetype": null`. |
| **D1a** | git clone to fresh dir | YES | `/tmp/nn-clean`, revise01, HEAD 1251d77. |
| **D1b** | docker compose build | CANNOT COMPLY | No docker/podman/nerdctl. Static analysis: dist/ missing, build would fail. |
| **D1c** | docker compose up + curl | CANNOT COMPLY | No container runtime. |
| **D1d** | DB source confirmed | YES (analysis) | demo.db not baked/mounted/fetched. Container starts empty. |
| **ROUND** | Clean-checkout container builds, runs, serves golden DB | CANNOT COMPLY | Docker not available. Analysis: build fails (no dist/), DB absent. |

---

## STOP
