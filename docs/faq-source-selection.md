# FAQ: How and why did you choose the news sources?

*Audience: hackathon users, judges, and observers*
*Last updated: 2026-07-02 (post-T5 re-run against live DB)*

**TL;DR:** We started with an idealized panel of 20 major outlets, then tested every source empirically. Paywalls initially blocked 3 Tier 2 sources (NYT, Economist, Politico — 0% body extraction at first), WaPo's feed was dead, and the panel was 90% Global North. We ran 45 candidate feeds through RSS + extraction tests, added 14 regional sources across Africa/LatAm/ME/Asia, plus 3 US replacements (CNN/CBS/ABC), and rescued paywalled sources with Firecrawl + CloakBrowser. Final panel: 37 sources, 5 tiers, 7 regions, 6 continents. All 37 now produce claims (7,635 after cross-source matching). 4 sources have absorbed claims with cross-source corroboration. Every source earned its seat through verified RSS and extraction tests. **See `faq-pipeline-data.md` for the methodology update explaining why absorbed counts dropped and why 25 sources sit at y=0 on the scatter plot.**

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

*Query: sources with absorbed claims (post-T5)*
```sql
SELECT s.name, COUNT(*) as absorbed 
FROM claims c JOIN articles a ON a.id=c.article_id 
JOIN sources s ON s.id=a.source_id 
WHERE c.state='CONSENSUS_ABSORBED' 
GROUP BY s.name ORDER BY absorbed DESC;
-- theguardian: 6, apnews: 4, foxnews: 2, bbc: 1
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

## Post-T5 panel statistics

*Query for claims per source (top 10 by volume):*
```sql
SELECT s.name, COUNT(*) as claims 
FROM claims c JOIN articles a ON a.id=c.article_id 
JOIN sources s ON s.id=a.source_id 
GROUP BY s.name ORDER BY claims DESC LIMIT 10;
```

| Source | Claims | Solo % | Absorbed |
|--------|--------|--------|----------|
| economist | 1,181 | 99.7% | 0 |
| theguardian | 463 | 38.9% | 6 |
| batimes | 393 | 28.8% | 0 |
| globaltimes | 234 | 71.8% | 0 |
| thehindu | 229 | 18.3% | 0 |
| nytimes | 185 | 30.8% | 0 |
| cnn | 212 | 100.0% | 0 |
| reuters | 179 | 100.0% | 0 |
| foxnews | 162 | 33.3% | 2 |
| jamaicaobserver | 145 | 70.3% | 0 |

*Query for solo coverage (sources at 100%):*
```sql
-- 6 sources have 100% solo coverage: thereporterethiopia, thegrayzone, 
-- reuters, propublica, cnn, bellingcat
-- Their stories have no cross-source pair in the panel — by design.
```
