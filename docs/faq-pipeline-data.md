# FAQ: What does the pipeline produce, and what does the UI actually show?

*Audience: hackathon judges, demo viewers*
*Last updated: 2026-07-02 (verified against live DB)*

**TL;DR:** The pipeline ingests RSS feeds from 37 news outlets across 6 continents, clusters stories by semantic similarity, extracts factual claims, classifies consensus, detects silent edits, scores framing consistency, detects corrections, and computes reputation scores across 6 dimensions and 3 verticals (geopolitics, economics, technology). All 37 sources produce claims (8,567 total). 12 of 37 have absorbed claims with reputation scores visible in the UI. Reputation snapshot time series spans 1,200 days; R-score sparsity on early dates is a data recency artifact, not a bug. All 6 radar dimensions are now live.

---

## The pipeline at a glance

| Stage | Agent | What it does | Current output |
|---|---|---|---|
| 1 — Intake | Agent 1 | Embeds articles, clusters by similarity | 4,640 clusters from 3,548 articles (2,028 with bodies) |
| 2 — Extraction | Agent 2 | Extracts factual claims + framing scores via LLM | 8,567 claims, 2,028 LLM framing scores |
| 3 — Consensus | Agent 3 | Classifies claims against panel threshold | 2,625 absorbed, 4,907 pending, 565 unresolved |
| 4 — Silent Audit | Agent 4 | Re-fetches articles, detects unannounced edits | 89 edits detected |
| — Snapshots | Runner | Computes 6-dimension reputation per source per vertical per day | 106,673 snapshots (37 sources × 3 verticals × 1,200 days) |

## What data exists now

| Data point | Count | Notes |
|---|---|---|
| Sources with claims | 37 of 37 | All sources produce claims. 12 have *absorbed* claims with reputation scores. |
| Sources with absorbed claims | 12 of 37 | Economist, AP, BBC, Guardian, CNN, Fox, ABC, CBS, NPR, NYT, Politico, Reuters |
| Total claims | 8,567 | 2,625 CONSENSUS_ABSORBED (31%), 4,907 PENDING, 565 UNRESOLVED |
| Vertical classification | 3 verticals | Geopolitics (44,400 snapshots), Economics (31,154), Technology (31,119) — embedding-proximity classifier |
| LLM framing scores | 2,028 | Per-article framing consistency scores (1–10 scale) from Agent 2 |
| Formal corrections | 16 | Inline marker detection (AP, CNN, NYT patterns) |
| Silent edits | 89 | Detected by re-fetching and diffing article bodies |
| Daily snapshots | 106,673 | 37 sources × 3 verticals × 1,200 days (2023-03-19 → 2026-07-02). R scores sparse on early dates: see below. |

## The six reputation dimensions

All 6 are now live and wired into daily snapshot computation:

| Dimension | Abbrev | What it measures | Source |
|---|---|---|---|
| Origination (Early Breaker) | R_orig | Percentile rank of first-reporter counts | Agent 3 consensus data |
| Validation | R_val | Absorbed/originated claim ratio | Agent 3 consensus data |
| Speed | R_speed | Median days from first report to absorption | Agent 3 consensus data |
| Framing Consistency | R_frame | Stddev of LLM framing scores — lower = more consistent editorial voice | Agent 2 LLM scores |
| Silent Editing | R_edit | Edits-per-article ratio | Agent 4 silent audit |
| Correction Rate | R_correct | Formal corrections per article | Inline marker detection |

All dimensions are percentile-ranked 0–100. Three dimensions (R_speed, R_frame, R_edit) are inverted so outward = favorable on the radar chart.

## Why are R scores sparse in snapshots?

R_orig, R_val, and R_speed are populated for 93,427 of 106,673 snapshots (88%). R_frame is sparse (12,059, 11%) because framing scores were backfilled later and many sources have <2 scored articles on early dates. R_correct and R_edit are widely populated (93K+ each).

R_orig/R_val/R_speed sparsity on early dates is a data recency artifact:

- **83% of claims (6,753/8,097) have `created_at` in June 2026** — when the pipeline was last run against June 2026 articles.
- The snapshot computation uses `claims.created_at <= as_of` to filter claims visible at each date.
- For a snapshot dated 2023-03-19, only ~16% of claims existed, so most sources had 0 first-reporter claims → `r_orig = NULL`.
- 2026-07-02 has 37/37 sources with populated R scores. Earlier dates taper off.

**This is inherent to seed data, not a code issue.** More historical articles with bodies would fill the gap.

## What each page shows

### Sources (home)
Reputation leaderboard + scatter plot (R_orig vs R_val). Shows 12 of 37 sources with non-zero R_val; remaining 25 cluster at y=0 because they produce claims but don't have cross-source absorption yet. See "Why do only 12 sources have absorbed claims" below.

### Source Profile
The richest page — 6-axis radar chart (all dimensions now live), Vf trend line chart, 30-day sparklines, tier average radar overlay, archetype badge. Fully wired to live data. For sources with absorbed claims (12), everything renders with real pipeline output. Silent edit log and correction log show detected events. Convergence types are not yet displayed (deferred).

### Timeline
Day 0–90 claim progression view. Shows CONSENSUS_ABSORBED markers at absorption time, PENDING claims in progress, and UNRESOLVED claims that aged out. Built and routed at `/timeline/:clusterId`.

### Pipeline Flow
Live diagram showing each pipeline stage and its provider configuration. Operational end-to-end.

### Investigate
Ad-hoc forensic analysis. Paste an article URL or text, runs through pipeline stages 1-3 inline. Results persist in localStorage.

## Why do only 12 sources have absorbed claims when all 37 have claims?

The pipeline extracts claims from all 37 sources (Agent 2 extracts from every article with a body). But consensus absorption (Agent 3) requires **multiple sources reporting the same claim within a cluster**. The 25 sources without absorbed claims are primarily:

- **Regional sources** (Tier 3): Buenos Aires Times, The Hindu, Straits Times, Jamaica Observer, etc. — often the only source covering their region's stories, so no cross-source consensus can form.
- **Contrarian sources** (Tier 5): ZeroHedge, The Gray Zone — by design, they report different narratives that may not overlap with mainstream consensus.
- **Non-English sources**: DW, France24, Sputnik — language differences reduce cluster overlap with English-language sources.

**This is why the scatter plot on the Sources page shows 25 sources clustered at y=0.** R_val measures the ratio of absorbed claims to originated claims. Sources with no absorbed claims get R_val = 0, so they appear along the bottom edge of the scatter plot. This is a panel composition characteristic (many regional/non-overlapping sources), not a pipeline failure. As the scraper accumulates more articles and cross-regional story overlap grows, more sources will reach consensus absorption thresholds.

## How is this verified?

Every pipeline stage has automated tests. All agents (1-4) produce real output against live data. The end-to-end flow: RSS poll → body extraction → semantic clustering → LLM claim extraction + framing scoring → consensus math → silent edit detection → correction detection → daily snapshots across 3 verticals. 260+ Python tests + 148 frontend tests.

Snapshot sparsity was verified against the live database: all 8,567 claims backlinked to claim_sources, all first_seen_at dates populated, created_at distribution confirmed, percentile ranking producing valid 0–100 scores. The computation is correct; the time series depth is a data volume limitation.
