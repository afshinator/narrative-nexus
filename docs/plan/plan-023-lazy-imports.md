# Slice 023 — Lazy Pipeline Imports for Server Startup

## Problem

The FastAPI server crashes on startup because the module-level import chain
pulls in `sentence_transformers` and `torch`, which are not installed:

```
app/main.py → runner_scheduler (module-level import)
  → pipeline.runner (module-level import)
    → pipeline.vertical_classifier
      → from sentence_transformers import SentenceTransformer  ❌
```

The server cannot serve **any** API routes or frontend static files until
these ~800MB of dependencies are installed.

## Dependencies checked

| Package | Installed | Needed by |
|---------|-----------|-----------|
| scikit-learn | ✅ 1.9.0 | agent1_intake (DBSCAN) |
| numpy | ✅ 2.4.6 | various |
| scipy | ✅ 1.17.1 | scikit-learn dep |
| openai | ✅ 2.24.0 | embedding_client, agent2 |
| httpx | ✅ 0.28.1 | openai dep |
| vaderSentiment | ✅ 3.3.2 | framing.py |
| transformers | ✅ 5.12.1 | (installed but no torch backend) |
| sentence-transformers | ❌ | vertical_classifier, embedding_client |
| torch | ❌ | sentence-transformers dep |

All **other** requirements.txt packages are installed — only the
sentence-transformers + torch chain is missing.

## Approach: Lazy imports (Option 2)

Two minimal changes, no new dependencies:

### Change A — `pipeline/runner_scheduler.py`

Move `from pipeline.runner import run_daily_pipeline` inside `_job()`.

The `_job` function already has `try/except Exception` that logs errors.
When the job fires on first tick (immediately after scheduler start), the
import will fail with ModuleNotFoundError, be caught, and logged. The
scheduler will retry after 24h. The server will already be serving traffic.

### Change B — `pipeline/vertical_classifier.py`

Move `from sentence_transformers import SentenceTransformer` inside
`_get_model()`. The function already follows a lazy-load pattern with
module-level `_model: SentenceTransformer | None = None`. The import
just needs to move inside the function body.

This means the vertical classifier module can be imported without pulling
in sentence-transformers. When the pipeline actually runs and calls
`_get_model()`, it will fail with ModuleNotFoundError if
sentence-transformers isn't installed yet.

## Effect on pipeline

With these changes:
- **Server starts**, serves API routes, serves frontend ✅
- Pipeline scheduler starts in background, fires `_job()` once
- `_job()` imports `runner` → fails at sentence-transformers → caught by try/except
- `_job()` prints `[pipeline] daily run failed: No module named 'sentence_transformers'`
- Scheduler retries in 24h
- All API routes (sources, articles, clusters, claims, snapshots, profiles,
  scores, scraper control, provider config) work because they only use
  `db.*`, FastAPI, and configured LLM providers — no sentence-transformers

## Timeline — Two-phase deployment

### Phase 1 (now): Lazy imports
Make the two import changes → server starts → user can browse the site
with real DB data.

### Phase 2 (follow-up): Install sentence-transformers + torch
`pip install --break-system-packages sentence-transformers` with extended
terminal timeout (300s+). Once installed, restart the server and the
pipeline will run normally.

## Implementation steps

1. Patch `pipeline/runner_scheduler.py` — move import to `_job()`
2. Patch `pipeline/vertical_classifier.py` — move import to `_get_model()`
3. Start server → verify `/api/health` and `/api/sources`
4. Start frontend → verify it loads in browser
5. Run relevant tests to confirm no regression
6. Install sentence-transformers + torch (background, extended timeout)
7. Restart server → verify pipeline can start

## Verification checklist

- [ ] `curl http://localhost:8000/api/health` returns `{"status":"ok"}`
- [ ] `curl http://localhost:8000/api/sources` returns source list
- [ ] Frontend at `http://localhost:3015` loads without console errors
- [ ] All API routes respond (scores, clusters, claims, snapshots)
- [ ] Pipeline error is logged, not fatal — `process(action='log')` shows
      `[pipeline] daily run failed: ...`
- [ ] No test regressions: `vitest run`, `pytest`
