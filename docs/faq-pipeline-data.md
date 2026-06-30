# FAQ: What does the pipeline produce, and what does the UI actually show?

*Audience: hackathon judges, demo viewers*
*Last updated: 2026-06-29*

**TL;DR:** The pipeline ingests RSS feeds from 37 news outlets across 6 continents, clusters stories by semantic similarity, extracts factual claims, classifies consensus, detects silent edits, and computes reputation scores. For the hackathon demo, 11 of 37 sources have full reputation data (the rest need more articles to produce claims). The Source Profile page shows real data flowing end-to-end: scored sources, claim absorption events, and detected article edits.

---

## The pipeline at a glance

| Stage | Agent | What it does | Current output |
|---|---|---|---|
| 1 — Intake | Agent 1 | Embeds articles, clusters by similarity | 656 clusters from 2,511 articles |
| 2 — Extraction | Agent 2 | Extracts factual claims via LLM | 2,347 claims |
| 3 — Consensus | Agent 3 | Classifies claims against panel threshold | 1,098 absorbed, 1,249 pending |
| 4 — Silent Audit | Agent 4 | Re-fetches articles, detects unannounced edits | 41 edits detected |

## What data exists now

| Data point | Count | Notes |
|---|---|---|
| Sources with claims | 11 of 37 | BBC, DW, Guardian, CNN, Fox, CBS, NPR, Al Jazeera, ABC, NYT, WaPo |
| Sources without claims | 26 | Articles exist, but not enough article bodies for claim extraction |
| CONSENSUS_ABSORBED claims | 1,098 | 47% of 2,347 claims |
| absorbed_at timestamps | 907 | Claims with recorded absorption time |
| UNRESOLVED claims | 0 | All claims are <90 days old; aging happens naturally over time |
| Silent edits | 41 | Detected by re-fetching and diffing article bodies |
| Daily snapshots | 44,326 | One row per source per day, most r_val values pending recomputation |

## What each page shows

### Sources (home)
Reputation leaderboard + scatter plot. Shows 11 of 37 sources with live scores (r_orig, r_val). Remaining 26 will populate as more article bodies are extracted and claims are produced.

### Source Profile
The richest page — radar chart (6 reputation axes), Vf trend line chart, 30-day sparklines, tier average radar overlay, archetype badge. Fully wired to live data. For sources with claims (11), everything renders with real pipeline output. Silent edit log shows 41 detected edits. Timeline markers show 907 claim absorption events.

### Timeline
Day 0–90 animated claim scrubber. Shows CONSENSUS_ABSORBED markers at absorption time, PENDING claims in progress. Currently a stub — scheduled for build.

### Pipeline Flow
Live animated diagram showing each pipeline stage and its provider configuration. Operational end-to-end.

### Investigate
Ad-hoc forensic analysis. Paste an article URL or text, runs through pipeline stages 1-3 inline. Results persist in localStorage.

## Why only 11 sources have data?

The pipeline needs *article body text* to extract claims. Of the 37 sources:

- **4 use Google News RSS feeds** (Reuters, AP, NHK World, Global Times) — these are now extractable via CloakBrowser (stealth Chromium) which resolves the opaque Google News redirect URLs to canonical article URLs and extracts body text. Firecrawl serves as a paywall-bypass backup for Reuters (partial paywall). Extraction in progress.
- **3 are fully paywalled** (NYT, The Economist, Politico) — newspaper4k gets 0% body extraction. Firecrawl can bypass these paywalls (proven in PoC).
- **19 others** — have articles but not enough bodies extracted yet for Agent 1 to cluster them into claim-producing groups.

The 11 sources with claims are the ones that had working, extractable bodies when the pipeline ran. This ratio improves as the scraper accumulates more articles daily and CloakBrowser extracts Google News sources.

## Why are there zero UNRESOLVED claims?

UNRESOLVED requires claims that are >90 days old AND lack cross-source consensus. The scraper only started accumulating articles ~11 days ago (RSS feeds are shallow — most carry 1-7 days of history). The 188 claims that ARE old enough (from seed data with 2023-2024 dates) all had sufficient cross-source consensus to absorb. New claims will age into UNRESOLVED territory over the next ~80 days.

For the hackathon demo, this is documented as a data-aging limitation, not a broken feature.

## How is this verified?

Every pipeline stage has automated tests. All agents (1-4) produce real output against live data. The end-to-end flow: RSS poll → body extraction → semantic clustering → LLM claim extraction → consensus math → silent edit detection → daily snapshots. 217 Python tests + 139 frontend tests, all passing.
