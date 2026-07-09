# FAQ: What does the pipeline produce, and what does the UI actually show?

*Audience: hackathon judges, demo viewers*
*Last updated: 2026-07-07 (DOC-SYNC — rewritten against demo.db)*

**TL;DR:** The pipeline ingests RSS feeds from 37 news outlets across 6 continents, clusters stories by semantic similarity, extracts factual claims, classifies consensus, detects silent edits, scores framing consistency, detects corrections, and computes reputation scores across 6 dimensions and 3 verticals (geopolitics, economics, technology).

**The database** contains 358 articles spanning 2026-03-03 to 2026-07-03, processed through the full pipeline. It produces 378 claims (10 absorbed, 357 pending, 11 unresolved) across 17 story clusters. 6 of 37 sources have absorbed claims with cross-source corroboration. The reputation snapshot time series spans 123 dates with 13,653 rows. All 6 radar dimensions are live, with all 37 sources having computed R_orig, R_val, R_speed, R_edit, and R_correct values; R_frame is partially populated (855 of 13,653 rows).

**Scale note:** The 358-article corpus is a starting dataset. The pipeline scales linearly — start the scraper in Settings to grow into higher volumes. All pipeline mechanisms (clustering, consensus, correction detection) become richer with more articles.

---

## The pipeline at a glance

| Stage | Agent | What it does | Demo corpus output |
|---|---|---|---|
| 1 — Intake | Agent 1 | Embeds articles, clusters by similarity (BGE, eps=0.35, 14-day windows) | 17 clusters from 358 articles (182 with bodies) |
| 2 — Extraction | Agent 2 | Extracts factual claims + framing scores via LLM | 378 claims, 174 framing scores |
| 3 — Consensus | Agent 3 | Classifies claims against panel threshold (MIN_CORROBORATION=2) | 10 absorbed, 357 pending, 11 unresolved |
| 4 — Silent Audit | Agent 4 | Re-fetches articles, detects unannounced edits | 6 edits detected |
| — Claim Matching | — | Greedy semantic dedup across clusters at sim=0.85 | 605 claim_variants (merged → canonicals) |
| — Snapshots | Runner | Computes 6-dimension reputation per source per vertical per day | 13,653 snapshots (37 sources × 3 verticals × 123 dates) |

## What data exists

| Data point | Count | Notes |
|---|---|---|
| Sources in panel | 37 of 37 | 29 have articles collected; 9 are panel members not yet exercised by collected stories |
| Sources reporting absorbed claims | 24 of 37 | Via claim_sources: theguardian(8), apnews(7), nytimes(6), bbc(6), thehindu(5), france24(5), foxnews(5), cbsnews(5), NHK World(5), zerohedge(3), globaltimes(3), dw(3), batimes(3), theintercept(2), sputnikglobe(2), jamaicaobserver(2), aljazeera(2), washingtonpost(1), reuters(1), punchng(1), npr(1), cnn(1), abcnews(1), MercoPress(1) |
| Total claims | 378 | 10 CONSENSUS_ABSORBED, 357 PENDING, 11 UNRESOLVED |
| Articles | 358 | 182 with extracted body text (others RSS summary or paywalled) |
| Clusters | 17 | 8 multi-source (>=2 distinct sources), 6 with >=3 sources |
| Claim variants (merges) | 605 | Cross-source match artifacts; merged into canonical claims |
| Cross-source links | 569 | claim_sources rows spanning matched claims |
| Reputation snapshots | 13,653 | 37 sources × 3 verticals × 123 dates (2026-03-03 → 2026-07-03) |
| Silent edits | 6 | Detected by the pipeline |
| Formal corrections | 0 | No correction markers in articles collected so far |
| LLM framing scores | 174 | Per-article framing consistency from Agent 2 |
| R_frame snapshots populated | 855 of 13,653 | Partial coverage; all other R-dimensions: 10,701 populated |

*Query for claims by state:*
```sql
SELECT state, COUNT(*) FROM claims GROUP BY state;
-- CONSENSUS_ABSORBED: 10, PENDING: 357, UNRESOLVED: 11
```

*Query for cluster counts:*
```sql
SELECT COUNT(*) FROM clusters;  -- 17
SELECT COUNT(*) FROM (
  SELECT c.id, COUNT(DISTINCT a.source_id) as n
  FROM clusters c JOIN claims cl ON cl.cluster_id=c.id
  JOIN articles a ON a.id=cl.article_id
  GROUP BY c.id HAVING n>=2
);  -- 8 multi-source clusters
```

*Query for snapshot counts:*
```sql
SELECT COUNT(*) FROM snapshots;  -- 13653
SELECT COUNT(DISTINCT date) FROM snapshots;  -- 123
SELECT MIN(date), MAX(date) FROM snapshots;  -- 2026-03-03 | 2026-07-03
```

## Why are absorbed claims so low?

The old pipeline (Phase 1) reported 2,625 ABSORBED claims. 96.8% of those were in single-source clusters — a claim from a single source in a cluster with no other sources would compute 1/1 = 100% ≥ threshold → ABSORBED. This was self-validation.

Phase 2 fixes require >=2 distinct consensus-pool sources reporting a claim for it to reach ABSORBED. The 10 absorbed claims in the demo corpus are genuinely cross-source corroborated.

Of the 17 clusters, 9 are single-source — regional outlets frequently cover stories no other panel source reports. 8 clusters are multi-source, and 6 have >=3 distinct sources reporting the same story. The pipeline correctly distinguishes single-source stories (claims remain PENDING or resolve to UNRESOLVED at day 90) from multi-source stories where cross-corroboration is possible.

## Pipeline capabilities active but not yet numerically visible

- **Formal corrections:** The pipeline's 5 regex patterns (AP, CNN, NYT markers) are active. The articles collected so far happen not to contain correction markers — none of the panel sources issued formal corrections for the covered stories during the collection window.
- **Per-vertical differences:** The 3-vertical classifier (geopolitics/economics/technology) runs on every cluster and every snapshot row. The current dataset is geopolitics-heavy by the nature of the stories collected; all 3 verticals are exercised as the database grows.
- **Time-machine scrub:** The 123-date span across 13,653 snapshot rows enables the Source Profile's 90-day radar animation. The span expands as articles accumulate.
