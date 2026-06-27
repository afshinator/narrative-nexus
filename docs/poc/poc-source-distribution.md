# PoC — Source Distribution Survey

**Date:** 2026-06-26
**Status:** Spec

## Goal

Answer two questions before committing to the current 20-source panel:

1. **What is the article distribution across sources?** Some sources may publish 50 articles per poll, others 2. A panel where 3 sources dominate by volume isn't a panel — it's an echo chamber.

2. **How many polls until the distribution stabilizes?** If the first poll shows BBC with 40 articles and Global Times with 3, is that normal or a fluke? Running N consecutive polls tells us whether relative volumes are stable or noisy.

Secondary: are the 4 Google News sources (Reuters, AP, NHK World, Global Times) returning enough metadata entries to justify their panel seats?

## Non-goals

- Not writing to the database
- Not running the pipeline
- Not testing article body extraction
- Not evaluating content quality
- Not a one-off — designed for reuse with different questions

## Output

A JSON report with per-poll and aggregate statistics:

```json
{
  "polls": 5,
  "total_articles": 847,
  "per_poll": [
    {
      "index": 0,
      "elapsed_ms": 3420,
      "total": 168,
      "sources": {
        "bbc": {"count": 22, "type": "native"},
        "reuters": {"count": 15, "type": "google_news"},
        ...
      }
    }
  ],
  "aggregates": {
    "bbc": {"total": 110, "mean_per_poll": 22.0, "stddev": 3.2, "type": "native"},
    ...
  }
}
```

## Design decisions

1. **CLI script, not an endpoint.** `python scripts/survey-sources.py --polls 5 --output survey.json`. Same pattern as `seed-demo.py` (ADR-0002: one-shot CLI, shares code paths).

2. **Imports from `pipeline/scraper.py`.** Uses `RSSPoller` and `FEED_CONFIG` directly. No duplicate feed definitions. If feed configs change, survey picks them up automatically.

3. **Sequential polls, not parallel.** RSS feeds are external dependencies — hitting all 20 simultaneously risks rate limiting. Sequential also gives per-source timing data (which feeds are slow?).

4. **JSON output to stdout or file.** `--output -` for stdout. Machine-readable. Pipes into `jq`, Python pandas, or future analysis scripts.

5. **Error resilience.** One failed feed doesn't crash the survey. Failed feeds logged in output with error count.

6. **Reusable pattern.** Future PoCs (body extraction survey, claim extraction quality, embedding comparison) follow the same CLI + JSON output pattern. This script establishes the convention.

## What we'll learn

- Which sources are dead or near-dead (0-1 articles per poll)
- Whether the 4 Google News sources pull their weight
- How many polls are "enough" for a representative sample
- Per-source timing (slow feeds → future timeout tuning)
- Whether the 20-source panel is the right size or needs pruning

## Related: future PoCs

| PoC | Question | Blocks on |
|-----|----------|-----------|
| Source distribution (this) | What's the spread? | Nothing |
| Body extraction yield | How many articles actually extract? | ArticleExtractor exists |
| Claim extraction quality | Are the claims reasonable? | Fireworks API key |
| Embedding cluster separation | Do stories cluster cleanly? | Fireworks API key or AMD GPU |
