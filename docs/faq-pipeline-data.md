# FAQ: What does the pipeline produce, and what does the UI actually show?

*Audience: hackathon judges, demo viewers*
*Last updated: 2026-07-02 (post-T5 re-run against live DB)*

**TL;DR:** The pipeline ingests RSS feeds from 37 news outlets across 6 continents, clusters stories by semantic similarity, extracts factual claims, classifies consensus, detects silent edits, scores framing consistency, detects corrections, and computes reputation scores across 6 dimensions and 3 verticals (geopolitics, economics, technology). All 37 sources produce claims (7,635 after cross-source matching, from 8,567 originally). 4 of 37 have absorbed claims with cross-source corroboration. Reputation snapshot time series spans 405 dates. All 6 radar dimensions are live.

---

## Methodology update (2026-07-02)

Earlier absorption counts in this document reflected a self-validation artifact in the consensus computation — single-source clusters could satisfy the pool-percentage threshold with a single reporter. We fixed this by (a) adding cross-source claim matching (BGE embeddings + greedy semantic merge at cosine 0.85), (b) requiring >=2 independent consensus-pool sources for any claim to reach CONSENSUS_ABSORBED, and (c) correcting the state machine so single-source claims properly resolve to UNRESOLVED at day 90. Post-fix absorption counts are lower but honest: they represent claims that genuinely cleared cross-source corroboration on our 37-source panel. Because 25 of those 37 sources are regional or contrarian outlets that frequently cover stories no other panel source touches, the majority of clusters remain single-source by panel design — a phenomenon the Sources home page renders explicitly under the Sole Voices lens rather than as a scatter-plot artifact.

---

## The pipeline at a glance

| Stage | Agent | What it does | Current output |
|---|---|---|---|
| 1 — Intake | Agent 1 | Embeds articles, clusters by similarity (BGE, eps=0.30, 14-day windows) | 1,112 clusters from 2,028 articles |
| 2 — Extraction | Agent 2 | Extracts factual claims + framing scores via LLM | 7,635 claims (after matching), 2,028 LLM framing scores |
| 3 — Consensus | Agent 3 | Classifies claims against panel threshold (MIN_CORROBORATION=2) | 13 absorbed, 6,134 pending, 1,488 unresolved |
| 4 — Silent Audit | Agent 4 | Re-fetches articles, detects unannounced edits | 89 edits detected |
| — Claim Matching | — | Greedy semantic dedup across clusters at sim=0.85 | 932 merges, 407 cross-source links |
| — Snapshots | Runner | Computes 6-dimension reputation per source per vertical per day | 44,955 snapshots (37 sources × 3 verticals × 405 dates) |

## What data exists now

| Data point | Count | Notes |
|---|---|---|
| Sources with claims | 37 of 37 | All sources produce claims. 4 have *absorbed* claims with cross-source corroboration. |
| Sources with absorbed claims | 4 of 37 | The Guardian (6), AP News (4), Fox News (2), BBC (1) |
| Total claims | 7,635 | After cross-source matching (8,567 original). 13 CONSENSUS_ABSORBED, 6,134 PENDING, 1,488 UNRESOLVED |
| Cross-source claim merges | 932 | 407 new source links created via claim_matching at sim=0.85 |
| Vertical classification | 3 verticals | Geopolitics, Economics, Technology — embedding-proximity classifier |
| LLM framing scores | 2,028 | Per-article framing consistency scores from Agent 2 |
| Formal corrections | 16 | Inline marker detection (AP, CNN, NYT patterns) |
| Silent edits | 89 | Detected by re-fetching and diffing article bodies |
| Reputation snapshots | 44,955 | 37 sources × 3 verticals × 405 distinct dates (2013-08 to 2026-07) |
| Multi-source clusters | 68 | Clusters containing articles from >=2 distinct sources |
| Demo-worthy clusters | 26 | Clusters with >=3 distinct sources |

*Query for claims by state:*
```sql
SELECT state, COUNT(*) FROM claims GROUP BY state;
-- PENDING: 6134, UNRESOLVED: 1488, CONSENSUS_ABSORBED: 13
```

*Query for claim counts:*
```sql
SELECT COUNT(*) FROM claims;  -- 7635
SELECT COUNT(*) FROM claim_sources;  -- 8002 (includes cross-source links)
```

*Query for cluster counts:*
```sql
SELECT COUNT(*) FROM clusters;  -- 1112
SELECT COUNT(*) FROM (
  SELECT c.id, COUNT(DISTINCT a.source_id) as n 
  FROM clusters c JOIN claims cl ON cl.cluster_id=c.id 
  JOIN articles a ON a.id=cl.article_id 
  GROUP BY c.id HAVING n>=2
);  -- 68 multi-source clusters
```

*Query for snapshot counts:*
```sql
SELECT COUNT(*) FROM snapshots;  -- 44955
SELECT COUNT(DISTINCT date) FROM snapshots;  -- 405
```

## Why are absorbed claims so low?

The old pipeline (Phase 1) reported 2,625 ABSORBED claims. 96.8% of those were in single-source clusters — a claim from a single source in a cluster with no other sources would compute 1/1 = 100% ≥ threshold → ABSORBED. This was self-validation.

Phase 2 fixes require >=2 distinct consensus-pool sources reporting a claim for it to reach ABSORBED. The remaining 13 absorbed claims are genuinely cross-source corroborated. 25 of 37 panel sources are regional or contrarian outlets whose stories have no cross-source pair — their claims correctly remain PENDING or UNRESOLVED.
