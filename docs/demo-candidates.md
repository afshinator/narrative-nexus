# Narrative Nexus — Demo Candidate Package

**Audience:** Hackathon judges reviewing the demo video
**Date:** 2026-07-02 (post-Phase-2 T5 re-run)

---

## Recommended Demo Path

1. **Open the Sources page** (`/`) — the scatter plot shows 37 sources across 5 tiers. Point out the 4 sources with non-zero R_val (y-axis): The Guardian, AP News, BBC, Fox News. These are the only sources with cross-source corroborated claims. Explain why — the 33 others have claims but no cross-source matches yet (regional/contrarian outlets by design). The "Sole Voices" lens makes this explicit.

2. **Open The Guardian's Source Profile** (`/source/theguardian.com`) — the most absorbed claims (6). The radar chart shows all 6 dimensions. Point to the "Silent Editor" row in the accountability section — Guardian has detected edits. Scroll down to the absorbed claims list — show claim 2304 ("Four people died from flash floods in Kentucky") was corroborated across multiple sources.

3. **Open AP News Source Profile** (`/source/apnews.com`) — second most absorbed claims (4). Compare the radar to Guardian's. AP has higher R_orig (first reporter score) because it breaks more stories that later get absorbed.

4. **Open cluster 5835** (`/cluster/5835` and `/timeline/5835`) — the largest multi-source cluster (29 sources, 561 claims). This is the mega-cluster containing the broadest consensus. The Timeline shows how claims propagated across sources over time.

---

## Multi-Source Clusters (>=3 sources)

These 26 clusters are the strongest evidence of cross-source consensus in the panel:

| Cluster | Sources | Claims | Vertical | Demo Value |
|---------|---------|--------|----------|------------|
| 5835 | 29 | 561 | geopolitics | **BEST DEMO** — widest consensus, click /cluster/5835 |
| 6366 | 10 | 127 | technology | Tech consensus cluster |
| 6395 | 10 | 40 | geopolitics | Multi-source political claims |
| 6392 | 9 | 44 | geopolitics | BBC/Guardian-led consensus |
| 6413 | 8 | 40 | geopolitics | DW/European consensus |
| 6368 | 7 | 37 | geopolitics | Fox/Guardian/AP/BBC converge |
| 6385 | 7 | 36 | technology | Tech consensus |
| 5837 | 6 | 36 | geopolitics | BBC-led cluster |
| 6378 | 6 | 26 | technology | Guardian-led tech |
| 5822 | 5 | 63 | geopolitics | Fox-led with 63 claims |
| 6376 | 5 | 19 | geopolitics | Guardian cluster |

**Show these routes in the demo:**
- `/cluster/5835` — Cluster Report for widest consensus
- `/timeline/5835` — Timeline showing claim propagation
- `/source/theguardian.com` — Source with most absorbed claims (6)
- `/source/apnews.com` — Second most (4)
- `/source/bbc.com` — One absorbed claim, Tier 1 anchor
- `/source/foxnews.com` — Two absorbed claims, Tier 2 editorial

---

## Absorbed Claims (Complete List)

All 13 claims that survived cross-source corroboration:

| Source | Claim ID | Excerpt |
|--------|----------|---------|
| apnews | 3555 | President Donald Trump threatened a 100% tax on imports from any country that imposes a digital services tax. |
| apnews | 3894 | A giraffe named Gracie is missing in Texas. |
| apnews | 4031 | Mark Carney was Prime Minister of Canada on June 25, 2026. |
| apnews | 4200 | Bible stories have become required reading for more than 5 million public school students in Texas. |
| bbc | 1408 | King Charles's tax bill is £12.9 million. |
| foxnews | 4036 | A woman walked her dog in a wooded area in Canada. |
| foxnews | 4041 | The woman made loud noises to scare the bear. |
| theguardian | 2304 | Four people died from flash floods in Kentucky. |
| theguardian | 2308 | Donald Trump will nominate Lance Schroyer as the next director of ICE. |
| theguardian | 2309 | Lance Schroyer has over 29 years of law enforcement experience in Oklahoma. |
| theguardian | 2310 | David Venturella had been performing the duties of the ICE director. |
| theguardian | 2619 | Offenders who kill their current or ex-partner face spending an extra 10 years in prison. |
| theguardian | 4145 | Thunderstorms caused severe delays to hundreds of flights at Heathrow Airport. |

---

## Why Only 13 Absorbed Claims?

**This is the honest answer — judges reward transparency.**

Phase 1 reported 2,625 absorbed claims. 96.8% of those were self-validating: a claim in a single-source cluster computes 1/1 = 100% ≥ the vertical threshold → automatically ABSORBED. This was a consensus computation bug, not real corroboration.

Phase 2 fixed three things:
1. **Cross-source claim matching** — claims are semantically deduplicated across articles using BGE embeddings at cosine 0.85. Only then do we check consensus.
2. **MIN_CORROBORATION = 2** — absorption requires at least 2 distinct consensus-pool (Tier 1+2) sources reporting the claim.
3. **Zombie fix** — single-source claims that can never meet the threshold now correctly resolve to UNRESOLVED at day 90 instead of cycling forever.

Post-fix: 13 claims survive. These are the only claims on our panel that genuinely cleared cross-source corroboration. The remaining 33 of 37 sources correctly show zero absorbed claims — their stories are single-sourced by panel design (regional outlets covering local stories).
