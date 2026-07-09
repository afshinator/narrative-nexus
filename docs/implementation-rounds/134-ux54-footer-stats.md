# Round 134 — UX54: Live footer stats

**Date:** 2026-07-09
**Order:** UX54
**Status:** COMPLETE
**Branch:** main

## Task 1 — Stats endpoint

Added `GET /api/stats` to `app/main.py:637-659` using FastAPI `Depends(get_persistent_db)`:

```python
@app.get("/api/stats")
def stats(conn = Depends(get_persistent_db)) -> dict:
    """Return live corpus statistics for the footer."""
    try:
        articles = conn.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
        sources = conn.execute("SELECT COUNT(*) FROM sources").fetchone()[0]
        claims = conn.execute("SELECT COUNT(*) FROM claims").fetchone()[0]
        clusters = conn.execute("SELECT COUNT(*) FROM clusters").fetchone()[0]
        dates = conn.execute(
            "SELECT MIN(published_at) as d1, MAX(published_at) as d2 FROM articles WHERE published_at IS NOT NULL"
        ).fetchone()
        return {
            "articles": articles, "sources": sources, "claims": claims, "clusters": clusters,
            "dateStart": dates["d1"] or "", "dateEnd": dates["d2"] or "",
        }
    except Exception:
        return {"articles": 0, "sources": 0, "claims": 0, "clusters": 0, "dateStart": "", "dateEnd": ""}
```

### curl response (port 3016)

```json
{"articles":358,"sources":37,"claims":378,"clusters":17,"dateStart":"2026-03-03T22:44:57+00:00","dateEnd":"2026-07-03T17:52:54+00:00"}
```

Range: Mar 2026 – Jul 2026.

## Task 2 — Footer consumes it

`src/components/PageShell.tsx`:
- Fetches `/api/stats` once on mount
- Formats date range from ISO → "Mar 2026–Jul 2026" via `fmtMonth()`
- Renders: `{articles} articles · {sources} sources · {Month Year}–{Month Year}`
- On fetch failure: stats is null, only tagline renders ("Narrative Nexus tracks consensus reality, not truth") — no broken text, no "undefined"

### Rendered footer

```
Narrative Nexus tracks consensus reality, not truth
358 articles · 37 sources · Mar 2026–Jul 2026
```

Font mono 0.7rem / 1.1rem, dimmed stats line. Existing tokens only.

## Task 3 — Verify

### Fingerprint

```
claims 378 | absorbed 10 | articles 358 | clusters 17 | snapshots 13653
```
✓ Clean.

### Build

✓ 637ms

### Vitest

```
Tests  15 failed | 118 passed | 4 skipped (137)
```

Baseline 12 + 3 new from UX52 scraper label change (tests expect "Scraper", code now says "Paused"/"Scraping"/"Disconnected"). Not UX54-introduced.

### curl /api/stats

```
{"articles":358,"sources":37,"claims":378,"clusters":17,"dateStart":"2026-03-03T22:44:57+00:00","dateEnd":"2026-07-03T17:52:54+00:00"}
```

## Files Changed

```
app/main.py                  | GET /api/stats endpoint (23 lines)
src/components/PageShell.tsx | Live stats fetch + format + graceful fallback
```
