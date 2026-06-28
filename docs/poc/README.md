# PoC — Source Panel Investigation

**Date:** 2026-06-27
**Status:** Complete — panel at 37 sources, pipeline end-to-end verified
**Scope:** Understand the source panel, fix what's broken, expand regional coverage.

## One-sentence summary

37 sources producing **1,821 articles/poll** with **1,004 working bodies** (55.1% richness). 939 bodies have 2,000+ chars. Firecrawl (keyless) can add +45 bodies from Politico and Times of Israel. Data is confirmed rich for production consensus math.

---

## PoC 1 — Source Distribution

**Question:** How many articles does each source produce, and is the distribution stable?

**Result:** 23 sources, 1,196 articles/poll (before expansion). The Economist owns 25% (300/poll). 4 Google News sources capped at 100, metadata-only. WaPo feed dead (7 articles).

→ [Spec](poc-source-distribution.md) → [Results](poc-source-distribution-results.md)

---

## PoC 2 — Body Extraction Yield

**Question:** Can we extract article body text from each source?

**Result:** 77.5% overall. Tier 2 is broken at 32% — NYT, Economist, Politico fully paywalled (0%). WaPo gives RSS summaries only (438 chars). Tiers 1, 3, 4, 5 all >93%.

→ [Spec](poc-extraction-yield.md) → [Results](poc-extraction-yield-results.md)

---

## PoC 3 — Panel Expansion (US gap)

**Question:** What sources can replace the paywalled Tier 2 dead weight?

**Result:** Added CNN (69/poll, 9k chars), CBS News (30/poll), ABC News (25/poll). All native RSS, all extract. Panel 20→23.

→ [Panel expansion doc](panel-expansion-2026-06.md)

---

## PoC 4 — Firecrawl Extraction

**Question:** Can Firecrawl cloud scraping extract bodies from paywalled sources?

**Result:** Politico rescued (0% → 39k chars). WaPo rescued (438 → 5,856 chars). Economist still gated. NYT and Fox blocked. Firecrawl MCP registered, keyless.

→ [Firecrawl results](poc-firecrawl-results.md)

---

## PoC 5 — Regional Source Expansion

**Question:** Can we fill regional gaps with viable RSS + extractable sources?

**Result:** 45 candidates tested, 14 added. Panel 23→37. **Added:** Africa (6), LatAm (2), Caribbean (1), ME (2), South Asia (1), SE Asia (1), Europe/Sputnik (1).

→ [Full candidate list & test results](poc-regional-sources.md)

---

## PoC 8 — 37-Source Full Survey

**Question:** What's the actual distribution and extraction rate with all 37 sources?

**Result:** 1,821 articles/poll, 1,004 working bodies, 939 rich (2k+ chars). All 7 regions covered. Panel is production-ready.

→ [Survey results](poc-37-survey.md)

**Data:** `data/survey-37-2026-06-26.json`, `data/extraction-37-2026-06-26.json`

---

## PoC 9 — Backfill Pipeline

**Question:** Does the full pipeline work end-to-end with real data?

**Result:** Yes. 1,814 articles scraped, 25 extracted, 1 cluster + 3 claims processed through consensus + snapshots. Pipeline chain proven.

→ [Backfill results](poc-backfill.md) | DB: `data/backfill-2026-06-27.db`

---

## Key numbers

| Metric | Value |
|--------|-------|
| Total sources | **37** |
| Articles/poll | **1,821** |
| Working bodies/poll | **1,004** |
| Rich bodies (2,000+ chars) | **939** |
| Richness ratio | **55.1%** |
| Tier breakdown | T1:5 T2:8 T3:17 T4:4 T5:3 |
| Regions covered | All 7 |
| Firecrawl upside | +45 bodies (Politico 30 + ToI 15) |

---

## Still not done

- **PoC 6 — Content overlap:** How much do sources cover the same stories? Needed to calibrate consensus weights.
- **PoC 7 — Temporal drift:** Does the panel change over hours/days?
- **Firecrawl integration:** Wire Politico/WaPo Firecrawl extraction into pipeline.

---

## File index

| File | Purpose |
|------|---------|
| [README.md](README.md) | This summary |
| [poc-source-distribution.md](poc-source-distribution.md) | PoC 1 spec |
| [poc-source-distribution-results.md](poc-source-distribution-results.md) | PoC 1 results |
| [poc-extraction-yield.md](poc-extraction-yield.md) | PoC 2 spec |
| [poc-extraction-yield-results.md](poc-extraction-yield-results.md) | PoC 2 results |
| [panel-expansion-2026-06.md](panel-expansion-2026-06.md) | PoC 3 — US gap |
| [poc-firecrawl-results.md](poc-firecrawl-results.md) | PoC 4 — Firecrawl |
| [poc-regional-sources.md](poc-regional-sources.md) | PoC 5 — 45 candidates, 14 added |
| [poc-37-survey.md](poc-37-survey.md) | PoC 8 — 37-source survey |
| [poc-backfill.md](poc-backfill.md) | PoC 9 — end-to-end pipeline |

**Scripts:** `scripts/survey-sources.py`, `scripts/survey-extraction.py`
