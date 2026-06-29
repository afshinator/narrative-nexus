# Slice 011 — Scraper Rewrite: Separate Polling from Body Extraction

## Problem

`ScraperScheduler.run_once()` interleaves RSS polling (~29s for all 37 feeds, measured) with per-article body extraction (HTTP fetch + newspaper4k parse, 0.2–7s each; newspaper4k default 7s timeout). With ~1,800 articles per cycle, best-case extraction is ~15 min, but paywalled/timeout sources push it past the 30-minute scheduler interval. The job never completes; it's killed mid-cycle by the next APScheduler tick.

Proof: the 7 sources with articles in nn.db are the first 7 in FEED_CONFIG iteration order (reuters, ap, bbc, npr, the-guardian, fox-news, cnn). Sources 8–37 have zero articles. Every feed returns valid entries when tested individually. Domain matching is perfect (37/37 match).

## Design

### Two-phase split

| Phase | What | Speed | When |
|---|---|---|---|
| 1. Poll + Insert | Parse all 37 RSS feeds, insert articles with empty body (deferred extraction) | ~29s | Every 30 min (APScheduler) |
| 2. Body Extraction | Fetch + parse article pages for rows with empty body, update body | 0.2–7s/article | Separate job or on-demand |

Phase 1 replaces `run_once()`. Phase 2 is a standalone function callable by the pipeline runner, a separate APScheduler job, or manually.

### How "pending extraction" is tracked (no schema change)

No new `body_status` value. The existing `body_status='AVAILABLE'` + `body=''` combination means "not yet extracted." This avoids SQLite CHECK constraint migration entirely.

| body_status | body | Meaning |
|---|---|---|
| `AVAILABLE` | non-empty text | Extraction succeeded |
| `AVAILABLE` | `''` or NULL | Not yet extracted (Phase 1 inserted, Phase 2 pending) |
| `BODY_UNAVAILABLE` | `''` | Extraction failed, or Google News source |

Phase 2 queries: `WHERE body_status='AVAILABLE' AND (body IS NULL OR body='')`.
Agent 1 unchanged: already reads `WHERE body_status='AVAILABLE' AND body IS NOT NULL AND body != ''`.

### Files touched

| File | Change |
|---|---|
| `pipeline/scraper.py` | `_normalize()`: native feeds emit body='' with status='AVAILABLE' (was: extract body inline) |
| `pipeline/extractor.py` | Add `extract_batch()` method for Phase 2 bulk extraction |
| `pipeline/scheduler.py` | `run_once()` → Phase 1 only (poll+insert). New `extract_pending()` for Phase 2. |
| `db/articles.py` | Add `list_pending_articles()` helper: `WHERE body_status='AVAILABLE' AND (body IS NULL OR body='')` |
| `pipeline/test_scheduler.py` | Update tests for new flow |
| `pipeline/test_extractor.py` | Add batch extraction tests |

**NOT touched:** `db/schema.sql` (no CHECK constraint change), `app/main.py` (API endpoints unchanged), `pipeline/agent1_intake.py`

### Flexibility for sample runs

```python
# Phase 1: poll subset of sources
scheduler.run_once(max_sources=3)  # only first 3 feeds

# Phase 2: extract limited batch
scheduler.extract_pending(limit=20)  # only 20 articles

# Standalone: poll without body extraction
from pipeline.scraper import RSSPoller
poller = RSSPoller()
for entry in poller.fetch("bbc"):  # single source
    print(entry["title"])
```

### What does NOT change

- API endpoints (`/api/scraper/start`, `/api/scraper/stop`, `/api/scraper/status`) — same interface
- Agent 1 — already reads `WHERE body_status='AVAILABLE' AND body IS NOT NULL`, ignores `BODY_PENDING`
- Seed script — doesn't touch the scraper
- Pipeline runner — orchestrates agents, not scraping
- FEED_CONFIG — all 37 sources unchanged

## Implementation Order

1. Scraper: change `_normalize()` — native feeds emit body='', status='AVAILABLE'; google_news stays body='', status='BODY_UNAVAILABLE'
2. DB helper: add `list_pending_articles()`
3. Extractor: add `extract_batch()` with configurable limit + timeout
4. Scheduler: rewrite `run_once()` as Phase 1 only, add `extract_pending()` for Phase 2
5. Update existing tests, add new tests
6. Integration test: full poll cycle completes <60s, inserts articles from all 37 sources

## Test Strategy

- Unit: `RSSPoller._normalize()` emits correct body_status per feed type
- Unit: `list_pending_articles()` returns correct rows
- Unit: `extract_batch()` handles success, timeout, partial failure
- Integration: `run_once()` with temp DB inserts articles from all 37 sources
- Integration: `extract_pending()` updates bodies in place
- Network: `@pytest.mark.network` — live test polls 3 sources, verifies Phase 1 completes <30s

## Verification Checklist

- [ ] `pytest -m "not network"` — all non-network tests pass
- [ ] `pytest -m network` — live poll test inserts articles from all 37 sources
- [ ] Manual: `python -c "from pipeline.scheduler import ScraperScheduler; s = ScraperScheduler('data/test_phase1.db'); s.run_once(); print(s.status())"` — completes <60s, articles from all sources
- [ ] DB after Phase 1: native-feed articles have body='' + body_status='AVAILABLE'
- [ ] DB after Phase 2: successfully extracted articles have non-empty body + body_status='AVAILABLE'; failed ones have body='' + body_status='BODY_UNAVAILABLE'
- [ ] Google News articles (reuters, ap, nhk, globaltimes) stay body='' + body_status='BODY_UNAVAILABLE'
- [ ] `npm run build` — TypeScript compiles (no frontend changes but verify no regressions)
- [ ] Existing live DB (nn.db, 868 articles) not corrupted — no schema migration needed
