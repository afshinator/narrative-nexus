# F5 Full Copy Rehearsal — Evidence Log

**Date:** 2026-07-03
**Source DB:** data/nn.db (5,112 articles, 7,747 claims, 1,179 clusters)
**Target DB:** /tmp/p8.db

---

## Step -1: PRE-FLIGHT

### (a) Scheduler status
Server not running. No scraper/scheduler active. DB quiescent.

### (b) Article growth explanation
Articles grew from 4,493→5,112 through normal pipeline ingestion (June 27-July 2 batches):
```
created_at       count
2026-06-27       507
2026-06-28        68
2026-06-29      1,877
2026-06-30        958
2026-07-01        138
2026-07-02      1,147
```
Scraper pipeline runs on June 29-30 and July 2 account for the growth.

### (c) CLAUDE.md updated
Commit d84ac68: replaced volatile DB stats with pointer to docs/STATUS.md.

---

## Step 0: PRE-CHECK — Anthropic AI export-ban articles

```
id  | title                                                          | source   | tier | cluster
157 | Anthropic says it has taken its latest AI models offline...    | apnews   | T1   | 5735
175 | Anthropic's Mythos model found vulnerabilities...              | apnews   | T1   | 6366
486 | Trump administration partially lifts export ban on Anthropic...| npr      | T1   | 6366
830 | U.S. eases restrictions on Anthropic's Mythos AI model         | cbsnews  | T2   | 6366
1382| US curbs Anthropic AI access, raising global concerns          | dw       | T3   | 6366
```
Distinct T1/T2 pool sources: AP News (T1), NPR (T1), CBS News (T2) = 3 pool sources.
Can absorb from existing data alone: YES (>= 2 pool sources).

---

## Step 1: Copy DB

```
$ cp data/nn.db /tmp/p8.db && ls -la data/nn.db /tmp/p8.db
-rw-r--r-- /tmp/p8.db    46841856
-rw-rw-r-- data/nn.db    46841856
```

---

## Step 2: Ingestion

```
$ python scripts/ingest_urls.py --db /tmp/p8.db --csv docs/evidence/p10/urls.csv
[via execute_code with web_extract — firecrawl-py 4.17.0 installed]

Articles before: 5,112
Articles after:  5,139
Delta: +27
Added: 27, Errors: 0
Match: YES
```
All 27 non-duplicate URLs from urls.csv fetched and inserted. 4 already existed (skipped).

---
