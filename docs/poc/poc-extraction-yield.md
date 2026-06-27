# PoC 2 — Body Extraction Yield Survey

**Date:** 2026-06-26
**Status:** Plan
**Depends on:** PoC 1 (source distribution survey)

## Goal

Answer: of the 771 native articles per poll, what % produce usable body text?

Article extraction is the gating factor for the entire pipeline. If 80% of articles are paywalled or fail to extract, the pipeline produces 80% fewer claims. This survey tells us whether extraction is viable or whether we need a different approach (RSS summary-only, headless browser, API access).

## Questions this PoC answers

1. **Per-source extraction yield:** What % of articles return body text? Which sources are paywalled?
2. **Body length distribution:** For articles that DO extract, how long is the text? (Short bodies = unusable for claim extraction)
3. **Extraction timing:** How long does newspaper4k take per article? Per source? Total runtime?
4. **Failure modes:** Paywall vs timeout vs empty body vs download error — what are the dominant failure reasons?

## Design decisions

1. **Sample, don't extract all.** Extracting 771 articles per poll would take hours. Extract first 5 articles per native source per poll. 15 sources × 5 = 75 extractions per poll. 3 polls = 225 extractions. Manageable runtime (~5-10 minutes).
2. **Skip Google News sources.** They're already BODY_UNAVAILABLE — no point re-extracting.
3. **Skip FeedBurner.** ZeroHedge extracts fine (FeedBurner is just a redirect wrapper).
4. **Per-article timing.** Measure download + parse time per article, not just per source.
5. **Same CLI pattern as survey-sources.py.** `--polls`, `--output`, `--sample N`. Reuses RSSPoller + FEED_CONFIG.
6. **Track failure reasons.** Not just "did it work?" but "why didn't it work?" — paywall indicator, empty body, download error.

## Implementation

Script: `scripts/survey-extraction.py`

```bash
python scripts/survey-extraction.py --polls 1 --sample 5
python scripts/survey-extraction.py --polls 3 --sample 10 --output extraction.json
```

Output schema:
```json
{
  "polls": 3,
  "sample_per_source": 5,
  "total_attempted": 225,
  "total_extracted": 120,
  "extraction_rate_pct": 53.3,
  "per_source": {
    "bbc": {
      "attempted": 15,
      "extracted": 12,
      "rate_pct": 80.0,
      "avg_body_chars": 3200,
      "avg_extract_ms": 1200,
      "failures": {
        "paywall": 2,
        "empty_body": 1,
        "download_error": 0,
        "timeout": 0
      }
    }
  }
}
```
