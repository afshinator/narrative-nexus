# Source Distribution Survey — Results & Interpretation

**Date:** 2026-06-26
**Data:** `data/survey-2026-06-26.json` — 3 polls, 3,588 total articles

## Headlines

1. **The panel is stable but skewed.** 3 consecutive polls returned identical per-source counts (1,196 each). RSS feeds don't change within a few minutes — expected. The distribution IS the distribution.

2. **The Economist owns 25% of the panel.** 300 articles per poll. The next highest is Deutsche Welle at 148. One source is a quarter of all content — this is not a balanced panel.

3. **Google News sources are capped at 100.** Reuters, AP, NHK World, Global Times all return exactly 100 every poll. Google News RSS truncates at 100 articles. These sources likely produce more — we can't know without native feeds. And they're metadata-only (no body extraction possible).

4. **Washington Post is effectively dead.** 7 articles in 8.2 seconds. The feed exists but returns almost nothing. Investigated 3 alternate URLs — national feed has 1 item, politics feed returns 0. WaPo deprecated public RSS.

5. **NPR is sparse.** 10 articles per poll. Feed exists but volume is low.

6. **Tier 1 is underweight relative to Tier 2.** Tier 1 (5 sources) = 891 articles. Tier 2 (5 sources) = 1,248. The "consensus anchor" tier has less volume than the "mainstream editorial" tier — but this is entirely due to The Economist (300 of 1,248).

## Per-source breakdown

| Source | Tier | Type | Per poll | % of panel | Verdict |
|--------|------|------|----------|------------|---------|
| The Economist | 2 | native | 300 | 25.1% | **Dominant** — skews the panel |
| Deutsche Welle | 3 | native | 148 | 12.4% | Healthy international |
| Reuters | 1 | google_news | 100 | 8.4% | Capped at 100, metadata-only |
| AP | 1 | google_news | 100 | 8.4% | Capped at 100, metadata-only |
| NHK World | 3 | google_news | 100 | 8.4% | Capped at 100, metadata-only |
| Global Times | 3 | google_news | 100 | 8.4% | Capped at 100, metadata-only |
| NYT | 2 | native | 54 | 4.5% | Healthy |
| Guardian | 1 | native | 45 | 3.8% | Healthy |
| BBC | 1 | native | 42 | 3.5% | Healthy |
| Politico | 2 | native | 30 | 2.5% | Moderate |
| Fox News | 2 | native | 25 | 2.1% | Moderate |
| Al Jazeera | 3 | native | 25 | 2.1% | Moderate |
| ZeroHedge | 5 | feedburner | 25 | 2.1% | Moderate |
| France24 | 3 | native | 23 | 1.9% | Moderate |
| The Intercept | 4 | native | 20 | 1.7% | Expected — investigative |
| ProPublica | 4 | native | 20 | 1.7% | Expected — investigative |
| The Gray Zone | 5 | native | 12 | 1.0% | Low |
| NPR | 1 | native | 10 | 0.8% | **Sparse** |
| Bellingcat | 4 | native | 10 | 0.8% | Expected — investigative |
| Washington Post | 2 | native | 7 | 0.6% | **Dead feed** |

## Feed quality by type

| Type | Sources | Total articles | % of panel | Has bodies? |
|------|---------|---------------|------------|-------------|
| native | 15 | 771/poll (64%) | 64% | Yes |
| google_news | 4 | 400/poll (33%) | 33% | **No** — BODY_UNAVAILABLE |
| feedburner | 1 | 25/poll (2%) | 2% | Yes |

**33% of the panel is metadata-only.** These 4 sources contribute article titles, URLs (opaque Google redirects), and timestamps — but no body text. They cannot participate in claim extraction or forensic analysis. Their consensus pool votes are based on RSS summaries alone.

## Timing

| Source | Avg ms | Notes |
|--------|--------|-------|
| Washington Post | 8,200 | **Slowest** — 1.2s per article |
| NHK World | 728 | Google News feed |
| Global Times | 519 | Google News feed |
| Guardian | 414 | Native but slow |
| The Intercept | 408 | Native, moderate |
| ZeroHedge | 405 | FeedBurner |
| Most others | 100-250 | Normal |

## Compromises Accepted

Rather than chase feeds that no longer exist, the following tradeoffs are accepted as working state. Each is documented so future readers understand the constraints.

### Google News proxy for 4 sources (Reuters, AP, NHK World, Global Times)

**Why:** These outlets killed public RSS between 2020–2024. Investigation findings:
- Reuters: DataDome captcha on `/tools/rss`. No public RSS endpoint found.
- AP: Moved to paid syndication. `feeds.ap.org` returns 0 entries.
- NHK World: `www3.nhk.or.jp` returns HTTP2 protocol errors on feed pages. No documented RSS.
- Global Times: No RSS endpoint found. `globaltimes.cn/rss/` returns 0 entries.

**What we get:** Google News RSS returns 100 articles/poll per source — titles, timestamps, source attribution, and opaque redirect URLs.

**What we lose:** Article bodies (body_status = BODY_UNAVAILABLE). These 4 sources cannot participate in claim extraction or forensic analysis. The 100-article ceiling means we may miss articles from high-volume days.

**Consensus impact:** These are all Tier 1 (Reuters, AP) or Tier 3 (NHK World, Global Times) consensus pool members. Their consensus votes are based on RSS summary text, not full article extraction. Acceptable per design doc: "RSS summary text [is] used for consensus voting only."

### Washington Post 7-article feed

**Why:** WaPo deprecated public RSS. Three alternate URLs tested — world (7 items, current), national (1 item), politics (0 items). The world feed is the best available.

**What we get:** 7 articles/poll (0.6% of panel).

**What we lose:** Negligible. WaPo's panel contribution is too small to meaningfully affect consensus or reputation scores.

### NPR 10-article feed

**Why:** NPR's `feeds.npr.org/1001/rss.xml` returns 10 articles/poll. Feed is stable but low-volume.

**What we get:** 10 articles/poll from a Tier 1 consensus anchor.

**What we lose:** NPR's brand authority outweighs its volume. Worth keeping for panel credibility even at 0.8% share.

### The Economist dominance

**Why:** 300 articles/poll (25% of panel). No known RSS cap. This is genuine output volume.

**Decision:** Accept the skew. The panel is weighted by output, not one-source-one-vote. If The Economist's volume becomes problematic (e.g. their editorial choices dominate consensus), cap or split later.

## Recommendations (updated 2026-06-26)

1. **Google News sources — ACCEPTED as-is.** No code changes. These 4 sources use Google News RSS proxy, capped at 100 articles, metadata-only. Documented compromise above.

2. **Washington Post — ACCEPTED as-is.** No code changes. 7 articles/poll from world feed. Negligible panel impact. Documented compromise above.

3. **The Economist — ACCEPTED as-is.** 300 articles/poll is genuine output. Monitor for consensus dominance, cap later if needed.

4. **NPR — ACCEPTED as-is.** 10 articles/poll is low but feeds are stable. Keep for Tier 1 brand authority.

## Next PoC runs

With this baseline, future surveys can answer:
- **Body extraction yield** (PoC 2): What % of those 771 native articles actually extract usable body text?
- **Content overlap** (PoC 3): How many articles cover the same story across sources? This needs agent 1 (clustering).
- **Temporal drift** (PoC 4): Run the same survey 24h later — does the distribution shift? This tells us how often to poll.

---

## Executive Summary

**3,588 articles across 3 polls. 1,196 per poll. Distribution is stable (identical across polls).**

### The Shape

| Category | Sources | Articles/poll | % | Bodies? |
|----------|---------|---------------|-----|---------|
| Working native RSS | 15 | 771 | 64% | Yes |
| Google News proxy | 4 | 400 | 33% | **No** |
| FeedBurner | 1 | 25 | 2% | Yes |

### Top 5 by volume

The Economist (300), Deutsche Welle (148), Reuters/AP/NHK/Global Times (100 each — capped), NYT (54), Guardian (45).

### Bottom 3

Washington Post (7), NPR (10), Bellingcat (10).

### Implications

- **33% of articles have no body text.** Claim extraction and forensic analysis impossible for Reuters, AP, NHK World, Global Times. These 4 contribute only titles and timestamps to consensus.
- **The Economist is 25% of all content.** One outlet disproportionately shapes what stories exist and what consensus looks like.
- **Consensus baseline driven by The Economist + NYT + BBC + Guardian** — the 4 native-RSS Tier 1/2 sources with real volume.
- **Thin radar charts** for NPR, Washington Post, and investigative outlets — few articles → few claims.
- **Not a crisis.** Design doc anticipated unequal volume. The app surfaces deviation from consensus, not equal representation.
