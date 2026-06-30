# FAQ: How and why did you choose the news sources?

*Audience: hackathon users, judges, and observers*
*Last updated: 2026-06-30 (verified against live DB)*

**TL;DR:** We started with an idealized panel of 20 major outlets, then tested every source empirically. Paywalls initially blocked 3 Tier 2 sources (NYT, Economist, Politico — 0% body extraction at first), WaPo's feed was dead, and the panel was 90% Global North. We ran 45 candidate feeds through RSS + extraction tests, added 14 regional sources across Africa/LatAm/ME/Asia, plus 3 US replacements (CNN/CBS/ABC), and rescued paywalled sources with Firecrawl + CloakBrowser. Final panel: 37 sources, 5 tiers, 7 regions, 6 continents. All 37 now produce claims (8,097 total); 12 have absorbed claims with reputation scores. Every source earned its seat through verified RSS and extraction tests.

---

## The five tiers

Each source is assigned to one of five tiers that determines its role in the system:

| Tier | Sources | Role |
|------|---------|------|
| **1 — Wire / Consensus Anchor** | Reuters, AP, BBC, NPR, The Guardian | Wire services and public broadcasters that form the consensus baseline — if a majority report a claim, it enters consensus reality |
| **2 — Mainstream Editorial** | Fox News, CNN, CBS News, ABC News, Politico, The Economist, NYT, Washington Post | Major editorial outlets — the volume backbone. Previously paywalled sources (NYT, Economist, Politico) now produce claims via Firecrawl/CloakBrowser extraction |
| **3 — International** | Al Jazeera, Deutsche Welle, NHK World, Global Times, France24, Buenos Aires Times, Straits Times, The Hindu, Premium Times, Times of Israel, Vanguard, The Reporter, Namibian, Punch, Jamaica Observer, MercoPress, Tehran Times | Regional outlets covering all 7 geographic regions — tracked for reputation scoring but not part of the consensus pool |
| **4 — Independent / Investigative** | The Intercept, ProPublica, Bellingcat, African Arguments | Investigative and long-form outlets — lower volume but deeper analysis |
| **5 — Contrarian** | ZeroHedge, The Gray Zone, Sputnik | Sources outside the mainstream — included to detect whether consensus excludes valid alternative narratives |

37 sources across 5 tiers and 7 geographic regions — all 6 inhabited continents represented.

## How were they chosen? What was the selection process?

**Empirically, not ideologically.** Every source in the final panel was tested for two things before it earned its seat:

1. Does it have a working, stable RSS feed?
2. Can we actually extract article body text from it?

We started with a conceptually-designed panel of 20 sources (Tier 1 wire services, Tier 2 mainstream editorial, Tier 3 international, Tier 4 investigative, Tier 5 contrarian). Then we ran systematic PoCs to check whether *these particular sources actually produce usable data*. The final panel is what *survived verification*, not what we originally planned.

## What did the verification find?

Three things that forced us to change the panel:

### 1. Paywalls are pervasive

Sources like the NYT, The Economist, and Politico were fully paywalled — newspaper4k (our open-source extraction library) got 0% body text from them. Fox News was mostly paywalled (20% extraction). These are major outlets with editorial weight, but initially contributed **zero usable article text** to the pipeline. Their RSS metadata (headlines, timestamps) still informed consensus voting, but they couldn't produce claims. *(Resolved: Firecrawl and CloakBrowser now extract from all four. See below.)*

PoC 2 — Body Extraction Yield: `poc-extraction-yield-results.md`

### 2. Some feeds are effectively dead

Washington Post's RSS feed returns 7 articles per poll (vs. 25-300 for comparable outlets). NPR is sparse at 10. Four sources (Reuters, AP, NHK World, Global Times) use Google News RSS, which truncates at 100 items and provides metadata only — no article bodies at all.

PoC 1 — Source Distribution: `poc-source-distribution-results.md`

### 3. The original panel had no regional diversity

The initial 20 sources covered North America and Europe almost exclusively — one source in the Middle East, two in Asia, zero in Africa, Latin America, the Caribbean, or South Asia. A reputation system that only watches the Global North isn't credible.

## So how did you fix it?

Three rounds of expansion, each grounded in real RSS and extraction tests:

### Round 1 — Fill the US editorial gap (June 26)

Tier 2 was broken (32% extraction). We added **CNN, CBS News, and ABC News** — all US-based, all with working native RSS, all producing full article bodies (9k, 7k, 2k chars respectively). These 3 sources added 124 extractable articles per poll.

PoC 3 — Panel Expansion: `panel-expansion-2026-06.md`

### Round 2 — Regional expansion (June 26-27)

We tested **45 candidate feeds** across Africa, Latin America, the Caribbean, the Middle East, and Asia. 14 passed: working RSS + extractable bodies. The panel went from 23 to 37 sources.

What we added, by region:

| Region | Sources added | Why these |
|--------|--------------|-----------|
| Africa | Premium Times (Nigeria), Vanguard (Nigeria), Punch (Nigeria), The Reporter (Ethiopia), Namibian (Namibia), African Arguments (pan-African) | Working RSS, verified body extraction, geographic spread across West, East, Southern, and pan-African coverage |
| Latin America | Buenos Aires Times (Argentina), MercoPress (Falklands/Patagonia) | BAT produces 100 articles/poll with 9k+ char bodies — one of the best sources in the entire panel |
| Caribbean | Jamaica Observer | Only Caribbean outlet with working RSS at decent volume (37/poll) |
| Middle East | Times of Israel, Tehran Times | Opposite sides of a conflict — deliberate balance |
| South Asia | The Hindu (India) | Major Indian daily, 60/poll, 4.7k char bodies |
| SE Asia | Straits Times (Singapore) | 50/poll, 7.9k char bodies — excellent extraction |
| Europe | Sputnik (Russia) | Tier 5 contrarian, 100/poll, added for ideological diversity |

PoC 5 — Regional Source Expansion: `poc-regional-sources.md`

### Round 3 — Firecrawl rescue (June 26)

Firecrawl (cloud scraping) rescues two Tier 2 paywalled sources:

| Source | Before | After Firecrawl |
|--------|--------|----------------|
| Politico | 0% (paywall) | 39,564 chars — full articles |
| Washington Post | 438-char RSS summaries | 5,856 chars — real body text |

Firecrawl is registered and operational in keyless mode. The Economist gets 1 paragraph (better than 0, but not rich). NYT and Fox are now extractable via CloakBrowser (stealth Chromium).

PoC 4 — Firecrawl Results: `poc-firecrawl-results.md`

### Round 4 — Full pipeline proof (June 27)

We ran all 37 sources through the full pipeline (scrape → extract → cluster → claims → consensus → snapshots). As of June 30: 2,568 articles (2,028 with bodies), 4,499 clusters, 8,097 claims (2,625 absorbed), 44,363 daily snapshots, 89 silent edits detected. Pipeline end-to-end verified.

PoC 9 — Backfill: `poc-backfill.md`

## Why did paywalled sources stay in the panel?

Paywalled sources were initially a problem (0% body extraction). Now, Firecrawl and CloakBrowser (stealth Chromium) resolve paywalls for most of them:

| Source | Claims extracted | Method |
|--------|-----------------|--------|
| The Economist | 1,196 | Firecrawl (partial — gets lede paragraphs) |
| NYT | 206 | CloakBrowser (resolves paywall redirect) |
| Politico | 100 | Firecrawl (full article bodies) |
| Fox News | 187 | CloakBrowser (partial, ~20% extraction) |

Even for sources that produce fewer claims, RSS metadata (headlines, publication timing) still contributes to consensus math: speed calculation, consensus baseline, and outlier detection. No source is purely decorative — every one contributes either claims or timing signal.

## What about bias? Are you only picking sources you agree with?

**The opposite.** We deliberately include sources across the political spectrum — from The Gray Zone (left-wing independent) to Fox News (right-wing corporate) to Sputnik (Russian state media). The system tracks *consensus reality*, not truth. You can't measure consensus if your panel is an echo chamber.

The selection criteria are purely operational:
1. Working RSS feed (reliable, stable)
2. Extractable body text (or documented reason for exception)
3. Geographic or editorial diversity relative to existing panel

## What's the final panel composition?

```
Tier 1 — Wire / Consensus Anchor (5):    Reuters, AP, BBC, NPR, The Guardian
Tier 2 — Mainstream Editorial (8):       Fox News, CNN, CBS News, ABC News, 
                                          Politico, The Economist, NYT, Washington Post
Tier 3 — International (17):             Al Jazeera, Deutsche Welle, NHK World,
                                          Global Times, France24, Buenos Aires Times,
                                          Straits Times, The Hindu, Premium Times,
                                          Times of Israel, Vanguard, The Reporter,
                                          Namibian, Punch, Jamaica Observer,
                                          MercoPress, Tehran Times
Tier 4 — Investigative (4):             The Intercept, ProPublica, Bellingcat,
                                          African Arguments
Tier 5 — Contrarian (3):                ZeroHedge, The Gray Zone, Sputnik

Regions: NA(10), EU(8), ME(4), Asia(4), Africa(6), LatAm(4), SA(1)
```

## Is the panel final?

No. The source panel is designed to evolve. Adding paywalled-source access (NYT API, Bloomberg Terminal, NewsAPI) would let us re-include sources we had to drop. New geographic regions (Central Asia, Pacific Islands) would fill remaining gaps. Every addition goes through the same PoC pipeline: RSS verification → extraction test → tier assignment → production.

---

## Where to find the evidence

All source selection decisions are documented in `docs/poc/`:
- [PoC 1 — Source Distribution](poc-source-distribution-results.md) — per-source article counts, feed health
- [PoC 2 — Body Extraction](poc-extraction-yield-results.md) — per-source extraction rates, paywall analysis
- [Panel Expansion (US gap)](panel-expansion-2026-06.md) — why we added CNN, CBS, ABC
- [PoC 4 — Firecrawl](poc-firecrawl-results.md) — which paywalls can and can't be bypassed
- [PoC 5 — Regional Expansion](poc-regional-sources.md) — 45 feeds tested, 14 added, complete dead-end log
- [PoC 8 — 37-Source Survey](poc-37-survey.md) — final panel distribution and extraction stats
- [PoC 9 — Backfill](poc-backfill.md) — end-to-end pipeline verification
- [Source code — src/data/sources.ts](/src/data/sources.ts) — the canonical source list
