# Panel Expansion — June 2026

**Date:** 2026-06-26
**Status:** Applied

## What changed

Added 3 sources to fill the Tier 2 gap: CNN, CBS News, ABC News. All US-based, all with working native RSS, all extract full article bodies.

| Source | Tier | Articles/poll | Extraction | Body quality |
|--------|------|---------------|------------|--------------|
| CNN | 2 | 69 | 3/3 | 9,258 chars avg — full articles |
| CBS News | 2 | 30 | 3/3 | 6,898 chars avg — full articles |
| ABC News | 2 | 25 | 2/3 | 2,298 chars avg — decent bodies |

## Why

PoC 1 and PoC 2 revealed that Tier 2 had 3 fully paywalled sources (NYT, Economist, Politico — 0% extraction) and 2 near-dead (Fox News 20%, WaPo summaries-only). With 300 of 416 Tier 2 articles coming from The Economist alone, and zero bodies from them, the "mainstream editorial" tier was broken.

The 3 new sources add 124 articles/poll with full body extraction — not a volume match for The Economist's 300, but real bodies beat metadata-only volume.

## Source counts

| | Before | After |
|---|--------|-------|
| Total panel | 20 | 23 |
| Tier 1 | 5 | 5 |
| Tier 2 | 5 | 8 |
| Tier 3 | 5 | 5 |
| Tier 4 | 3 | 3 |
| Tier 5 | 2 | 2 |
| Per poll (articles) | 1,196 | 1,321 |
| Working bodies/poll | ~400 | ~524 |

## Files changed

- `pipeline/scraper.py` — FEED_CONFIG: added cnn, cbs-news, abc-news
- `src/data/sources.ts` — DEFAULT_SOURCES: added CNN, CBS News, ABC News
- `pipeline/scheduler.py` — _ensure_sources: 20→23
- `pipeline/test_scraper.py` — test count: 20→23
- `src/__tests__/sources.test.ts` — test counts: 20→23, Tier 2 5→8
- `src/__tests__/sources-page.test.tsx` — scatter markers: 20→23

## What's still missing for "rich data"

The panel is functional. Consensus math works. But the app experience is sparse because:
- The Economist (300 articles, 25% of panel) produces zero bodies — no claims from the highest-volume source
- Tier 2 extraction is 32% overall — the remaining paywalls (NYT, Politico, Fox mostly) are structural
- 4 sources are metadata-only (Google News proxy) — titles and timestamps, no bodies

To get rich data: need API access to paywalled sources (NYT Developer API, Economist) or NewsAPI/Cortex/key-based aggregation. That's the next frontier.
