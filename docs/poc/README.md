# PoC — Source Panel Investigation

**Date:** 2026-06-26
**Status:** Active — panel at 37 sources (14 added in slice 11)
**Scope:** Understand the source panel, fix what's broken, expand regional coverage to make data rich enough for production consensus math.

## One-sentence summary

The panel has 37 sources producing **1,821 articles/poll** with **1,004 working bodies** (55.1% richness). 939 bodies have 2,000+ chars. Firecrawl (keyless) can add +45 bodies from Politico and Times of Israel. Data is confirmed rich for production consensus math.

---

## PoC 1 — Source Distribution

**Question:** How many articles does each source produce, and is the distribution stable?

**Result:** 23 sources, 1,196 articles/poll (before expansion) → 1,321 (after). The Economist owns 25% of the panel (300/poll). 4 Google News sources are capped at 100 and are metadata-only. WaPo feed is dead (7 articles). NPR is sparse (10).

→ [Spec](poc-source-distribution.md) → [Results](poc-source-distribution-results.md)

---

## PoC 2 — Body Extraction Yield

**Question:** Can we extract article body text from each source?

**Result:** 77.5% overall extraction rate. Tier 1 (100%), Tier 3 (100%), Tier 5 (100%) work. Tier 2 is broken — 32% extraction, with NYT, Economist, Politico fully paywalled (0%). WaPo extracts but only RSS summaries (438 chars). Fox mostly paywalled (20%).

→ [Spec](poc-extraction-yield.md) → [Results](poc-extraction-yield-results.md)

---

## PoC 3 — Panel Expansion (US news gap)

**Question:** What sources can we add to replace the paywalled Tier 2 dead weight?

**Result:** Added CNN (69/poll, 9,258 chars), CBS News (30/poll, 6,898 chars), ABC News (25/poll, 2,298 chars). All native RSS, all extract. Panel went 20→23 sources, working bodies ~400→524/poll.

→ [Panel expansion doc](panel-expansion-2026-06.md)

---

## PoC 4 — Firecrawl Extraction

**Question:** Can Firecrawl cloud scraping extract bodies from paywalled sources that newspaper4k can't?

**Result:** Politico rescued (0% → 39k chars full article). WaPo rescued (438-char summaries → 5,856 chars real body). Economist gets 1 paragraph (+paywall gate). NYT and Fox News blocked. Firecrawl MCP registered and operational in keyless mode.

→ [Firecrawl results](poc-firecrawl-results.md)

---

## PoC 5 — Regional Source Expansion (IMPLEMENTED — slice 11)

**Question:** Can we fill regional gaps (Africa, LatAm, Caribbean, ME, Asia) with viable RSS + extractable sources?

**Result:** 45 candidate feeds tested. 16 found with working RSS + extractable bodies. 14 added to panel. Panel went 23→37 sources.

**Added by region:**

| Region | Sources | Tier |
|--------|---------|------|
| Africa | Premium Times, Vanguard, Punch, The Reporter (Ethiopia), Namibian, African Arguments | T3, T4 |
| Latin America | Buenos Aires Times, MercoPress | T3 |
| Caribbean | Jamaica Observer | T3 |
| Middle East | Times of Israel, Tehran Times | T3 |
| South Asia | The Hindu | T3 |
| SE Asia | Straits Times | T3 |
| Europe | Sputnik | T5 |

**Current panel composition:** T1:5 | T2:8 | T3:17 | T4:4 | T5:3 = 37

**Files changed:** `pipeline/scraper.py`, `src/data/sources.ts`, `pipeline/scheduler.py`, `pipeline/test_scraper.py`, `src/__tests__/sources.test.ts`, `src/__tests__/sources-page.test.tsx`

→ [Full candidate list & extraction test results](poc-regional-sources.md)

---

## File index

| File | Purpose |
|------|---------|
| [README.md](README.md) | This summary |
| [poc-source-distribution.md](poc-source-distribution.md) | PoC 1 spec — distribution survey |
| [poc-source-distribution-results.md](poc-source-distribution-results.md) | PoC 1 results — per-source counts |
| [poc-extraction-yield.md](poc-extraction-yield.md) | PoC 2 spec — extraction survey |
| [poc-extraction-yield-results.md](poc-extraction-yield-results.md) | PoC 2 results — per-source extraction rate |
| [panel-expansion-2026-06.md](panel-expansion-2026-06.md) | PoC 3 — US news gap expansion (20→23) |
| [poc-firecrawl-results.md](poc-firecrawl-results.md) | PoC 4 — Firecrawl scraping tests |
| [poc-regional-sources.md](poc-regional-sources.md) | PoC 5 — 45 feeds tested, 14 added |
| [poc-37-survey.md](poc-37-survey.md) | PoC 8 — 37-source panel distribution + extraction survey |
| [poc-backfill.md](poc-backfill.md) | PoC 9 — scaled-down backfill pipeline exploration |

**Data files:** `data/survey-37-2026-06-26.json` (distribution), `data/extraction-37-2026-06-26.json` (extraction)

**Scripts:** `scripts/survey-sources.py`, `scripts/survey-extraction.py`

---

## Key numbers (confirmed — PoC 8 survey)

| Metric | Value |
|--------|-------|
| Total sources | **37** |
| Articles/poll | **1,821** |
| Working bodies/poll | **1,004** |
| Rich bodies (2,000+ chars) | **939** |
| Dead articles (no body) | 817 |
| Richness ratio | **55.1%** |
| Tier breakdown | T1:5 T2:8 T3:17 T4:4 T5:3 |
| Regions covered | All 7 (NA, EU, ME, Asia, Africa, LatAm, SA) |
| Firecrawl upside | +45 bodies (Politico 30 + Times of Israel 15) |

---

## Remaining PoCs

- **PoC 6 — Content overlap:** How much do sources cover the same stories? Needed to calibrate consensus weights.
- **PoC 7 — Temporal drift:** Does the panel change over hours/days? Or is one poll representative?
- **PoC 8 — Expanded panel distribution survey:** Re-run survey to measure actual articles/poll with 37 sources.
- **Firecrawl integration:** Add Politico/WaPo Firecrawl extraction path to pipeline.
