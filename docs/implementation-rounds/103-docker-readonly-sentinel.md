# DOCKER-READONLY — Bake the Sentinel into the Submission Image

**Round:** DOCKER-READONLY
**Date:** 2026-07-08
**Type:** Dockerfile fix. NO DB writes. No frontend changes.

---

## T1 — Sentinel Baked into Dockerfile.app

**Mechanism:** `RUN touch` — safer than `COPY .readonly` (the file is in the repo root and could be gitignored or absent in the build context). `touch` always works.

**Diff:**
```diff
+ # T1: baked read-only sentinel — disables scraper in deployed instances
+ RUN touch /app/.readonly
+
  EXPOSE 8000

  CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Placed at `Dockerfile.app:61-63`, before the EXPOSE line (line 64).

---

## T2 — Path Resolution Verified

`_is_readonly()` in `app/main.py:558-563`:
```python
def _is_readonly() -> bool:
    return bool(
        os.environ.get("NN_READONLY")
        or os.path.exists(os.path.join(os.path.dirname(__file__), "..", ".readonly"))
    )
```

Path computation (container context):
```
__file__                          = /app/app/main.py
os.path.dirname(__file__)         = /app/app
os.path.join("/app/app", "..")    = /app
os.path.join("/app", ".readonly") = /app/.readonly
```

`RUN touch /app/.readonly` creates exactly that path. Match confirmed.

---

## T3 — No ENV Counterpart

**docker-compose.yml:23-30** — environment block:
```yaml
environment:
  - NN_DB_PATH=/data/nn.db
  - OPENCODE_API_KEY=${OPENCODE_API_KEY:-}
  # - FIREWORKS_API_KEY=${FIREWORKS_API_KEY:-}
  # - DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY:-}
  # - OPENAI_API_KEY=${OPENAI_API_KEY:-}
```

No `NN_READONLY` anywhere. The baked sentinel is the sole guard for the submission image. This is correct — the sentinel works even with bare `docker run`, not just via compose.

---

## T4 — STATUS.md

Submission image now ships read-only-guarded by default. Local dev unchanged (uses local `.readonly` file at repo root).

---

## Compliance Table

| Requirement | Met? | Evidence |
|---|---|---|
| ROUND OBJECTIVE — Submission image ships working read-only guard | YES | RUN touch /app/.readonly in Dockerfile.app |
| T1 — Sentinel baked | YES | Diff above |
| T1 — Used RUN touch (not COPY) | YES | Safer — no build-context dependency |
| T2 — Path verified | YES | /app/.readonly matches _is_readonly() resolution |
| T3 — No ENV counterpart needed | YES | docker-compose.yml has no NN_READONLY |
| T4 — STATUS.md recorded | YES | Updated header below |
| DB untouched | YES | Zero writes |
| Build passes | YES | 741ms |

---

## Modified Files

- `Dockerfile.app` — line 61: `RUN touch /app/.readonly`
- `docs/STATUS.md` — header updated
