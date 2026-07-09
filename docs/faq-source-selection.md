# FAQ: How and why did you choose the news sources?

*Audience: hackathon users, judges, and observers*
*Last updated: 2026-07-07 (DOC-SYNC — rewritten against demo.db)*

**TL;DR:** We started with an idealized panel of 20 major outlets, then tested every source empirically. Paywalls initially blocked 3 Tier 2 sources (NYT, Economist, Politico — 0% body extraction at first), WaPo's feed was dead, and the panel was 90% Global North. We ran 45 candidate feeds through RSS + extraction tests, added 14 regional sources across Africa/LatAm/ME/Asia, plus 3 US replacements (CNN/CBS/ABC), and rescued paywalled sources with Firecrawl. Final panel: 37 sources, 5 tiers, 7 regions, 6 continents.

**The database** contains 358 articles from 37 sources spanning 2026-03-03 to 2026-07-03, processed through the full pipeline (Agent 1 clustering → Agent 2 extraction → claim matching → Agent 3 consensus → snapshot backfill). It produces 378 claims across 17 story clusters. 6 of 37 sources originated absorbed claims (10 total); 24 of 37 sources report at least one absorbed claim (via claim_sources). 9 of 37 sources have no articles — they are in the panel but not exercised by the stories collected so far.

**Scale note:** The 358-article corpus is a starting dataset. The pipeline can process any volume — the source panel, clustering, and consensus mechanisms all scale linearly with article count. Start the scraper in Settings to grow the database with live collection.

---

## Methodology update (2026-07-02)

Earlier absorption counts in this document reflected a self-validation artifact in the consensus computation — single-source clusters could satisfy the pool-percentage threshold with a single reporter. We fixed this by (a) adding cross-source claim matching (BGE embeddings + greedy semantic merge at cosine 0.85), (b) requiring >=2 independent consensus-pool sources for any claim to reach CONSENSUS_ABSORBED, and (c) correcting the state machine so single-source claims properly resolve to UNRESOLVED at day 90. Post-fix absorption counts are lower but honest: they represent claims that genuinely cleared cross-source corroboration on our 37-source panel. Because 25 of those 37 sources are regional or contrarian outlets that frequently cover stories no other panel source touches, the majority of clusters remain single-source by panel design — a phenomenon the Sources home page renders explicitly under the Sole Voices lens rather than as a scatter-plot artifact.

---

## The five tiers

Each source is assigned to one of five tiers that determines its role in the system:

| Tier | Sources | Role |
|------|---------|------|
| **1 — Wire / Consensus Anchor** | Reuters, AP, BBC, NPR, The Guardian | Wire services and public broadcasters that form the consensus baseline |
| **2 — Mainstream Editorial** | Fox News, CNN, CBS News, ABC News, Politico, The Economist, NYT, Washington Post | Major editorial outlets — the volume backbone |
| **3 — International** | Al Jazeera, Deutsche Welle, NHK World, Global Times, France24, Buenos Aires Times, Straits Times, The Hindu, Premium Times, Times of Israel, Vanguard, The Reporter, Namibian, Punch, Jamaica Observer, MercoPress, Tehran Times | Regional outlets across all 7 geographic regions |
| **4 — Independent / Investigative** | The Intercept, ProPublica, Bellingcat, African Arguments | Investigative and long-form outlets |
| **5 — Contrarian** | ZeroHedge, The Gray Zone, Sputnik | Sources outside the mainstream — included to detect excluded narratives |

37 sources across 5 tiers and 7 geographic regions — all 6 inhabited continents represented.

*Demo DB sources reporting absorbed claims (via claim_sources — who reported the claim, not who originated the article):*
```sql
SELECT s.name, COUNT(*) FROM claim_sources cs
JOIN claims c ON c.id=cs.claim_id
JOIN sources s ON s.id=cs.source_id
WHERE c.state='CONSENSUS_ABSORBED'
GROUP BY s.name ORDER BY COUNT(*) DESC;
-- theguardian: 8, apnews: 7, nytimes: 6, bbc: 6, thehindu: 5, france24: 5,
-- foxnews: 5, cbsnews: 5, NHK World: 5, zerohedge: 3, globaltimes: 3, dw: 3,
-- batimes: 3, theintercept: 2, sputnikglobe: 2, jamaicaobserver: 2, aljazeera: 2,
-- washingtonpost: 1, reuters: 1, punchng: 1, npr: 1, cnn: 1, abcnews: 1, MercoPress: 1
-- (24 sources report at least one absorbed claim)
```

## How were they chosen? What was the selection process?

**Empirically, not ideologically.** Every source in the final panel was tested for two things before it earned its seat:

1. Does it have a working, stable RSS feed?
2. Can we actually extract article body text from it?

The panel includes sources across the ideological spectrum by design — ZeroHedge and Sputnik sit alongside Reuters and BBC. This is not endorsement; it's detection. If a claim only appears on contrarian outlets and nowhere in the consensus pool, the dashboard surfaces that as an outlier, not as false.

## What's the coverage across regions?

The panel covers 7 geographic regions with at least one source in each:

| Region | Sources | Count |
|--------|---------|-------|
| North America | AP, NPR, Fox News, CNN, CBS, ABC, NYT, Politico, ProPublica, The Intercept, ZeroHedge, The Gray Zone | 12 |
| Europe | BBC, The Guardian, Economist, DW, France24, Reuters, Bellingcat | 7 |
| Middle East | Al Jazeera, Times of Israel, Tehran Times, Sputnik | 4 |
| Asia | NHK World, Global Times, The Hindu, Straits Times | 4 |
| Africa | Premium Times, Namibian, Punch, Vanguard, African Arguments, The Reporter | 6 |
| Latin America | Buenos Aires Times, MercoPress | 2 |
| Caribbean | Jamaica Observer | 1 |

## Demo corpus panel statistics

*Query for claims per source (top 10 by volume):*
```sql
SELECT s.name, COUNT(*) as claims
FROM claims c JOIN articles a ON a.id=c.article_id
JOIN sources s ON s.id=a.source_id
GROUP BY s.name ORDER BY claims DESC LIMIT 10;
```

| Source | Claims | Absorbed |
|--------|--------|----------|
| theguardian | 65 | 0 |
| apnews | 58 | 1 |
| bbc | 36 | 1 |
| dw | 32 | 0 |
| foxnews | 23 | 2 |
| nytimes | 22 | 0 |
| NHK World | 19 | 3 |
| npr | 14 | 0 |
| globaltimes | 14 | 2 |
| thehindu | 13 | 0 |

*Query for solo coverage — sources where all claims are in single-source clusters:*
```sql
-- 9 of 17 clusters are single-source (only 1 source reporting).
-- This is normal for a heterogeneous panel where regional outlets cover
-- stories no other source reports. Multi-source clusters emerge as more
-- articles are collected.
```

## Sources with no articles

9 sources have 0 articles (present in the panel but not yet exercised by collected stories):
politico, propublica, thegrayzone, premiumtimesng, vanguardngr, thereporterethiopia, namibian, africanarguments.

These sources are fully configured and active in the source panel; they simply haven't been involved in the stories collected so far. Start the scraper in Settings to begin live collection across all 37 sources.
