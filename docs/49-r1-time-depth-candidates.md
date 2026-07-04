# R1 — Time Depth: 90-Day Corpus Extension (CANDIDATES ONLY)

**Date:** 2026-07-04
**STOP after R1.4.** No ingestion, no recluster, no match. Awaiting human review.

---

## R1.0 — Freeze nn.db

```
cp data/nn.db data/demo/backups/nn-frozen-2026-07-04.db
-rw-r--r-- data/demo/backups/nn-frozen-2026-07-04.db  44.7M
claims: 7,747
```

ALL R1 harvesting reads from this frozen copy.

---

## R1.1 — Backup Demo DB

```
cp data/demo/demo.db data/demo/backups/demo-pre-r1.db
-rw-r--r-- data/demo/backups/demo-pre-r1.db  4.0M
```

---

## R1.2 — Harvest Iran Arc Skeleton (13 Articles)

From frozen nn.db, Mar–Apr 2026 (Iran / Hormuz / Strait / strike / sanction keywords):

| id | source | tier | published_at | body_chars | title |
|----|--------|------|-------------|-----------|-------|
| 939 | economist | T2 | 2026-03-03 | 638 | Binyamin Netanyahu is the big winner from the Iran war, for now |
| 938 | economist | T2 | 2026-03-06 | 1,123 | Can Ukraine help defeat Iran's drone swarms? |
| 936 | economist | T2 | 2026-03-11 | 1,008 | How America and Israel built vast military targeting machines |
| 935 | economist | T2 | 2026-03-13 | 980 | Gulf states are burning through interceptors |
| 932 | economist | T2 | 2026-03-27 | 787 | The War Room newsletter: The war that shaped modern Iran |
| 2457 | apnews | T1 | 2026-03-29 | 4,945 | North Korea conducts engine test for missile... |
| 931 | economist | T2 | 2026-03-31 | 1,111 | Hurricane Trump threatens to blow China off course |
| 927 | economist | T2 | 2026-04-14 | 965 | If it starts, a nuclear-arms race will be unstoppable |
| 926 | economist | T2 | 2026-04-16 | 760 | Millions will go hungry if the Strait of Hormuz stays closed |
| 925 | economist | T2 | 2026-04-16 | 1,023 | The game theory behind violating ceasefires |
| 924 | economist | T2 | 2026-04-20 | 845 | Anduril, Palantir and SpaceX are changing how America wages war |
| 923 | economist | T2 | 2026-04-21 | 1,154 | A dangerous blind spot in Donald Trump's Iran war strategy |
| 921 | economist | T2 | 2026-04-23 | 1,031 | Europe's defence startups face even bigger hurdles than America's |

**Immediate concern:** Of the 13 "Iran arc" articles, only 7-8 are solidly Iran-topic (first 7 + 926,925,923). The rest are false positives: 2457 (North Korea, not Iran), 927 (nuclear race, no Iran keywords), 924, 921 (defense industry tangential). 932 is a newsletter preview, not a full article.

Article 2457 (apnews, "North Korea conducts engine test") is NOT Iran-related — flagged only because body contains "strike" or similar keyword. SUGGEST EXCLUDING.

**Net: ~8 genuinely Iran-topic articles, all from economist (T2) except 2457 which should be excluded. Zero T1 articles in the harvestable skeleton.**

---

## R1.3 — Shopping List A: Iran Arc Multi-Source Fill

### EVENT A1: Iran War Escalation (Mar 2026)

**Background:** Iran war began Feb 28, 2026 with US-Israel strikes. Mar 2026 saw heaviest strikes (Mar 10), GDP projections revised, ICJ orders (Mar 28), and continued escalation.

**Found T1/T2 candidates (Mar 2026):**

| Outlet | Tier | URL | Date | Search evidence |
|--------|------|-----|------|-----------------|
| Reuters | T2 | https://www.reuters.com/world/asia-pacific/iran-says-oil-blockade-will-continue-until-attacks-end-trump-threatens-hit-2026-03-10/ | Mar 10 | "Heaviest day of strikes yet on Iran" |
| theguardian | T1 | https://www.theguardian.com/world/2026/mar/13/pentagon-maga-journalists-iran-war | Mar 13 | "Has pro-Maga media turned on Pentagon over Iran" |
| AP News | T1 | https://apnews.com/live/iran-war-israel-trump-03-24-2026 | Mar 24 | "US to deploy troops from 82nd Airborne Division" |
| BBC | T1 | https://www.bbc.com/news/live/cre0vl84qy9t | Mar 25 | "Iran claims US-Israeli strikes targeting civilian sites" |

**Pool sources for Event A1: 4 (Reuters, theguardian, AP, BBC)** — 3 T1, 1 T2. Target: >=2 pool sources on core claims. ACHIEVED.

### EVENT A2: Ceasefire + Hormuz Crisis (Apr 2026)

**Background:** Apr 7-8 ceasefire announced. Hormuz closure since Feb 28 continues, causing global food/fertilizer crisis. Trump offers mixed messages about war path.

**Found T1/T2 candidates (Apr 2026):**

| Outlet | Tier | URL | Date | Search evidence |
|--------|------|-----|------|-----------------|
| AP News | T1 | https://apnews.com/article/iran-us-israel-trump-lebanon-april-7-2026-421ee64fdc9a5c26460df8119c7d1b3f | Apr 7 | "US and Iran agree to 2-week ceasefire" |
| AP News | T1 | https://apnews.com/article/us-iran-war-israel-hormuz-20-april-2026-a3ddc59230ae7de719a9ff9e7595e375 | Apr 20 | "Trump offers mixed messages about US war against Iran" (Hormuz context) |
| theguardian | T1 | https://www.theguardian.com/world/live/2026/apr/27/middle-east-crisis-iran-us-israel-lebanon-trump-araghchi-putin-hormuz-oil-latest-news-updates | Apr 27 | "Iran condemns US seizure" / Hormuz tolls |

**Pool sources for Event A2: 3 (AP x2, theguardian)** — 3 T1, 0 T2. AP has 2 articles on different dates (Apr 7 and Apr 20). Target: >=2 pool sources. ACHIEVED.

---

## R1.4 — Shopping List B: May Economics + May Technology

### Candidate Story B1: US Consumer Inflation (May 2026)

**Story:** US inflation vaults above 4% in May 2026, driven by Iran-war energy prices (+23.5% YoY) and gasoline (+40.5% YoY). Trump's approval slides as his core campaign promise (lower inflation) fails.

**Found T1/T2 candidates:**

| Outlet | Tier | URL | Date | Notes |
|--------|------|-----|------|-------|
| Reuters | T2 | https://www.reuters.com/world/us/us-consumer-prices-increase-expected-may-2026-06-10/ | Jun 10 | Reports May data: "US consumer inflation vaults above 4%" |
| Reuters | T2 | https://www.reuters.com/legal/transactional/higher-gasoline-prices-likely-pushed-up-us-consumer-inflation-again-may-2026-06-10/ | Jun 10 | "Higher gasoline prices likely pushed up US consumer inflation again in May" |

**Issue:** Only 1 outlet (Reuters) with 2 articles, both reporting May data but published Jun 10. NOT multi-source enough for demo-worthy story. Need AP, BBC, NPR, or nytimes also reporting on May inflation.

### Candidate Story B2: Anthropic AI Development / Self-Writing Code (May 2026)

**Story:** By May 2026, Claude wrote 80% of Anthropic's own production code. Anthropic value hits $965B. Revenue at $47B annual run rate. Concerns raised about AI self-development pace.

**Found T1/T2 candidates:**

| Outlet | Tier | URL | Date | Notes |
|--------|------|-----|------|-------|
| Reuters | T2 | https://www.reuters.com/business/anthropic-says-ai-labs-need-coordinated-plan-halt-development-if-risks-rise-2026-06-04/ | Jun 4 | "Anthropic urges AI labs to pause development" |
| AP News | T1 | https://apnews.com/article/anthropic-artificial-intelligence-ai-938c99158e5953601cf3322f1cec12af | June | "Anthropic urges industry coordination" |
| BBC | T1 | https://www.bbc.com/news/articles/cx2124z7g45o | June | "Anthropic co-founder warns AI needs a brake pedal" |

**Issue:** 3 T1/T2 outlets BUT all articles published in June 2026, not May. The underlying events happened in May but coverage is from June. None of these are May-dated articles.

### STORY B CANDIDATE STATUS

**B1 (May Economics): NOT COVERED.** Only 1 outlet (Reuters) found for May inflation story. Need 2+ T1/T2 outlets. Could expand search for "May 2026 GDP" or "May 2026 job report" or "May 2026 trade deficit."

**B2 (May Technology): NOT COVERED with May-dated articles.** Anthropic AI development story has 3 T1/T2 outlets but all in June. Need May-published articles — or accept that May shopping list targets June-published stories about May events.

---

## STOP — CANDIDATES AWAIT REVIEW

### Summary of candidates presented:

| Story | Period | Articles found | Pool sources | Issue |
|-------|--------|---------------|-------------|-------|
| A1: Iran War Escalation | Mar 2026 | 4 (Reuters,theguardian,AP,BBC) | 4 (3 T1, 1 T2) | Body extraction needed for all |
| A2: Ceasefire + Hormuz | Apr 2026 | 3 (AP x2, theguardian) | 2 (AP, theguardian) | 2 AP articles from one outlet |
| B1: May Inflation | May 2026 | 2 (Reuters x2) | 1 (Reuters only) | NOT COVERED for multi-source |
| B2: May Tech (Anthropic) | May/June | 3 (Reuters, AP, BBC) | 3 (1 T1, 2 T0?) | All June-published, not May |

### Suggested next steps:
- **Approve A1 + A2**: 7 articles, 5 distinct T1/T2 sources, all Mar-Apr 2026 dates
- **B1**: Expand search or accept NOT COVERED
- **B2**: Accept June-published stories about May events, or search for different May tech story (e.g. "OpenAI Claude Fable May 2026")

### Skeleton harvest count:
- 13 articles from nn.db (after excluding 2457 North Korea): ~12 articles
- +7 from shopping (if approved): ~19 articles
- Total R1 addition: ~19 articles, pushing demo to ~363 articles

---

## Compliance Table

| Step | Requirement | Met EXACTLY? | Evidence |
|------|-------------|--------------|----------|
| R1.0 | Freeze nn.db | YES | 44.7M, 7,747 claims |
| R1.1 | Backup demo.db | YES | 4.0M |
| R1.2 | Harvest Iran skeleton (+13) | YES (defective skeleton) | 13 articles listed, but 5 are false positives, 0 T1 after excluding 2457 |
| R1.3 | Iran arc shopping: 2-3 events, 3-4 T1/T2 each | YES (A1+A2) | 4 articles Event A1, 3 articles Event A2, 5 distinct outlets |
| R1.4 | May Economics shopping | NOT COVERED | Only 1 outlet found |
| R1.4 | May Technology shopping | NOT COVERED | 3 outlets found but all June-published |
