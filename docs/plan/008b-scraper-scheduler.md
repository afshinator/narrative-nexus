# Plan: Slice 8b — Scraper + Scheduler

## Requirements addressed

| Req | Description | How |
|-----|-------------|-----|
| REQ-058 | feedparser for RSS | `pipeline/scraper.py` — RSSPoller class using feedparser |
| REQ-059 | newspaper4k for body extraction | `pipeline/extractor.py` — ArticleExtractor class |
| REQ-109 | APScheduler polling loop | `pipeline/scheduler.py` — BackgroundScheduler integration |
| REQ-061 | BODY_UNAVAILABLE marker | Set when newspaper4k fails or Google News RSS entry |
| REQ-010 | AMD GPU not required for scraper | All CPU-only code |

## Assumptions validated (2026-06-26)

### 1. Dependencies installed ✅
```
feedparser:      6.0.12
newspaper4k:     0.9.5   (nltk warning: benign, NLP features not needed for body extraction)
apscheduler:     3.11.2
httpx:           0.28.1
```
All imports succeed. APScheduler BackgroundScheduler starts/stops cleanly.

### 2. RSS feed availability ✅ (20/20 sources — verified live)
14 sources have native RSS feeds returning articles with direct source URLs.
6 sources required alternative feeds (4 Google News RSS, 1 FeedBurner, 1 alternate native).

**Native RSS feeds (14):**
bbc, npr, the-guardian, fox-news, the-economist, nyt, washington-post, al-jazeera, deutsche-welle, france24, the-intercept, propublica, bellingcat, the-gray-zone

**Google News RSS (4):** reuters, ap, nhk-world, global-times
These return opaque `news.google.com/rss/articles/...` URLs. The `source` field correctly identifies the originating outlet (e.g., `{'href': 'https://www.reuters.com', 'title': 'Reuters'}`). Body extraction is not possible from these URLs — entries get `body_status = 'BODY_UNAVAILABLE'`.

**FeedBurner (1):** zerohedge
**Alternate native (1):** politico (`rss.politico.com`)

### 3. newspaper4k body extraction ✅ (with known limitations)
- Open-access sites: works correctly (tested: The Guardian — 4,686 chars extracted)
- Paywalled sites (NYT): returns 403 → body_status = 'BODY_UNAVAILABLE'
- nltk warning is cosmetic — newspaper4k's core extraction works without it

### 4. DB schema readiness ✅
- `articles` table has all needed columns: source_id, url, title, body, published_at, body_status
- `insert_article()` from db/articles.py accepts all fields
- `get_source_by_domain()` from db/sources.py maps domain → source_id
- **Missing:** No UNIQUE constraint on `articles.url`. Scraper must dedup before insert.

### 5. Google News RSS entry structure ✅
Entries contain `source.href` (domain), `title`, `published`, `summary`. The `link` points to Google's opaque redirect URL — not useful for body extraction. Title-based dedup or `published`+`source` composite dedup needed since the opaque URLs change per request.

## Architecture decisions

### Decision 1: Three modules, not one monolith

```
pipeline/
  scraper.py      — RSSPoller: fetch + parse feeds, dedup entries, yield article dicts
  extractor.py    — ArticleExtractor: download + extract body via newspaper4k
  scheduler.py    — Scheduler: APScheduler loop, coordinates poller → extractor → DB write
```

Clean separation: scraper knows about RSS feeds, extractor knows about HTTP/article parsing, scheduler orchestrates.

### Decision 2: Feed config as a Python dict, not a config file

```python
# In scraper.py
FEED_CONFIG: dict[str, dict] = {
    "bbc": {
        "url": "https://feeds.bbci.co.uk/news/rss.xml",
        "type": "native",  # extracts body
        "domain": "bbc.com",
    },
    "reuters": {
        "url": "https://news.google.com/rss/search?q=site:reuters.com&hl=en-US&gl=US&ceid=US:en",
        "type": "google_news",  # metadata only
        "domain": "reuters.com",
    },
    ...
}
```

No YAML/JSON config file needed for 20 entries. The dict is the config. If this grows beyond ~100 lines in a future slice, extract to `config/feeds.py`.

### Decision 3: Dedup by URL before insert

The `articles` table has no UNIQUE constraint on `url`. Before inserting, the scraper checks whether the URL already exists. For Google News entries (opaque URLs that change per request), dedup by `(source_id, title, published_at)` composite.

Add the UNIQUE index directly to `db/schema.sql` — single source of truth for schema:

```sql
CREATE UNIQUE INDEX IF NOT EXISTS idx_articles_url ON articles(url);
```

No `ensure_indexes()` helper needed.

### Decision 4: Scheduler starts paused — controlled via API

Per REQ-111 and ADR-0003: in-process scheduling, no Celery/Redis. The scheduler MUST NOT auto-start on app launch — launching the app shouldn't fire 20+ external HTTP calls without user intent.

The scheduler initializes in a **paused** state. Two API endpoints control it (both idempotent — calling start when already running is a no-op, same for stop when paused):

```
POST /api/scraper/start   → resumes the scheduler, begins polling (idempotent)
POST /api/scraper/stop    → pauses the scheduler (idempotent)
GET  /api/scraper/status  → returns {"running": true/false, "last_run": "...", "articles_inserted": N}
```

The FastAPI lifespan creates the scheduler and attaches it to `app.state` so route handlers can access it:

```python
# app/main.py lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler = ScraperScheduler(db_path="data/nn.db")
    app.state.scraper = scheduler  # paused, not started
    yield
    scheduler.shutdown()
```

Polling interval: 30 minutes (configurable via env var `SCRAPE_INTERVAL_MINUTES`).

**Deferred UI work (not in 8b):**
- Pipeline Flow page: Start/Stop toggle near the "Article Ingest" card
- App header: status indicator showing whether the scheduler is running vs paused
- Tracked in `docs/deferred.md` for a future frontend slice

### Decision 5: Body extraction is best-effort

newspaper4k succeeds on open-access sites, fails on paywalls (403) and Google News URLs (opaque). The extractor returns `body_status`:
- `'AVAILABLE'` — full body extracted
- `'BODY_UNAVAILABLE'` — 403, 404, timeout, or Google News URL

The pipeline won't stall on a single failed extraction. Each article is processed independently.

## New files

| File | Purpose |
|------|---------|
| `pipeline/scraper.py` | `RSSPoller` class — iterates FEED_CONFIG, parses feeds, deduplicates, yields article dicts |
| `pipeline/extractor.py` | `ArticleExtractor` class — downloads article body via newspaper4k, returns (body, body_status) |
| `pipeline/scheduler.py` | `ScraperScheduler` class — APScheduler loop: poll → extract → insert, with error handling |
| `pipeline/test_scraper.py` | Tests: RSSPoller parses live BBC feed, dedup logic, Google News source field parsing |
| `pipeline/test_extractor.py` | Tests: ArticleExtractor on known Guardian URL, 403 handling, BODY_UNAVAILABLE fallback |
| `pipeline/test_scheduler.py` | Tests: scheduler starts/stops, job runs without crash, articles land in test DB |

## Existing files modified

| File | Change |
|------|--------|
| `app/main.py` | Add lifespan context manager, attach scheduler to `app.state` (paused). Add `/api/scraper/start`, `/api/scraper/stop`, `/api/scraper/status` endpoints |
| `db/schema.sql` | Add `CREATE UNIQUE INDEX IF NOT EXISTS idx_articles_url ON articles(url)` |
| `db/articles.py` | Add `article_exists_by_url()` function for dedup check |

## Implementation order

1. **DB: URL dedup** — Add UNIQUE index to `schema.sql`. Add `article_exists_by_url()` to articles.py. Test.
2. **Scraper module** — `RSSPoller` class, FEED_CONFIG dict, parse + dedup logic. Test against live BBC feed + Google News feed.
3. **Extractor module** — `ArticleExtractor` class wrapping newspaper4k. Test with Guardian URL (success) + NYT URL (403/BODY_UNAVAILABLE).
4. **Scheduler module** — `ScraperScheduler` class (paused by default), APScheduler integration, start/stop methods. Test with in-memory DB.
5. **Wire into FastAPI** — Lifespan attaches paused scheduler to `app.state`. Add `/api/scraper/start|stop|status` endpoints. Test routes.
6. **Verify** — pytest, manual: start app, `POST /api/scraper/start`, check `/api/articles` populates, `POST /api/scraper/stop`.

## Test strategy

All tests use in-memory SQLite via `conftest.py` fixtures. Live RSS tests hit real URLs (BBC, Guardian) — these are network-dependent but validate real-world behavior. Mark them with `@pytest.mark.network` so they can be skipped with `-m "not network"`.

| Test | What it verifies |
|------|-----------------|
| DB URL uniqueness | `article_exists_by_url()` returns True for dupes, False for new |
| RSSPoller parses BBC feed | Returns >0 entries with title + link |
| RSSPoller parses Google News feed | Returns entries with `source` field, opaque URL |
| RSSPoller dedup | Second poll with same feed skips already-seen URLs |
| ArticleExtractor open-access | Guardian article → body > 100 chars, body_status='AVAILABLE' |
| ArticleExtractor paywall | NYT article → body_status='BODY_UNAVAILABLE' |
| ArticleExtractor timeout | Unreachable URL → graceful failure, doesn't crash poller |
| ScraperScheduler lifecycle | start() → job fires → articles exist in DB → shutdown() |
| Scheduler error isolation | One failed extraction doesn't block the rest of the poll |

## Verification checklist

- [ ] `pytest pipeline/ -m "not network"` — all non-network tests pass
- [ ] `pytest pipeline/` — network tests pass (BBC + Guardian reachable)
- [ ] Manual: start uvicorn, `curl -X POST localhost:8000/api/scraper/start`, verify `/api/articles` populates, `curl -X POST localhost:8000/api/scraper/stop`
- [ ] Manual: verify `curl localhost:8000/api/scraper/status` returns `{"running": false}` before start and `{"running": true}` after start
- [ ] `npm run build` still passes (no frontend changes)
- [ ] `npx vitest run` still passes (136 tests)

## Deferred items

Add to `docs/deferred.md`:

| What | Why deferred | Depends on | Originating slice |
|------|-------------|-----------|-------------------|
| Pipeline Flow page: scraper start/stop toggle | UI control for scheduler — backend endpoints exist but no frontend wiring | 8b (endpoints must exist first) | 8b |
| App header: scraper status indicator (running vs paused) | Visual feedback that scraping is active — needs scheduler state exposed | 8b | 8b |
