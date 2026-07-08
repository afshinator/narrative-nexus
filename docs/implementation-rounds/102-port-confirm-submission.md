# PORT-CONFIRM — Submission Container Only

**Round:** PORT-CONFIRM
**Date:** 2026-07-08
**Type:** Read-only. Submission container audit. NO code changes.

---

## S1 — App Port

**docker-compose.yml:22:**
```yaml
ports:
  - "8000:8000"
```

**Dockerfile.app:60:**
```dockerfile
EXPOSE 8000
```

**Dockerfile.app:62:**
```dockerfile
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Judge URL: **http://localhost:8000** — fixed, no variable, no range.

---

## S2 — FLAG: .readonly Sentinel Does NOT Ship

**Dockerfile.app copies (lines 45-58):**
```dockerfile
COPY app/      ./app/
COPY db/       ./db/
COPY pipeline/ ./pipeline/
COPY config/   ./config/
COPY --from=frontend /app/dist/ ./dist/
RUN mkdir -p /data
COPY data/demo/demo.db /data/nn.db
```

No `COPY .readonly` anywhere. No `touch .readonly` in entrypoint/CMD.

**Guard check location** (`app/main.py:558-563`):
```python
def _is_readonly() -> bool:
    return bool(
        os.environ.get("NN_READONLY")
        or os.path.exists(os.path.join(os.path.dirname(__file__), "..", ".readonly"))
    )
```

In the container: `os.path.dirname(__file__)` = `/app`, so the check resolves to `/app/../.readonly` = `/.readonly`. That file does not exist in the image → `_is_readonly()` returns `False`.

**Consequence:** A judge running `docker compose up` gets a live, unguarded scraper. The Pipeline page renders a functional green Play button. Clicking it fires `POST /api/scraper/start` → starts live RSS scraping into the baked demo DB.

**Fix required (not executed here — read-only round):** Add to `Dockerfile.app`:
```dockerfile
RUN touch /.readonly
```
Or:
```dockerfile
COPY .readonly /.readonly
```
Placed before the CMD line (line 62). The sentinel must be baked into the image so `_is_readonly()` returns `True` on any deployed instance.

---

## Compliance Table

| Requirement | Met? | Evidence |
|---|---|---|
| S1 — Port published | 8000:8000 | docker-compose.yml:22, Dockerfile.app:60,62 |
| S1 — Judge URL | http://localhost:8000 | Fixed, no variable |
| S2 — .readonly audit | FLAGGED | Not in Dockerfile.app, no entrypoint touch |
| S2 — Consequence | Unguarded scraper | _is_readonly() returns False in container |
| S2 — Fix path | Documented | COPY .readonly or RUN touch /.readonly |
