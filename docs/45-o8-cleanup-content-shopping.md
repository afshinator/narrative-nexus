# O8 — Cleanup + Content Shopping Run

**Date:** 2026-07-04
**Target DB:** /tmp/demo.db
**No commits made.**

---

## O8.0 — CORRECT THE RECORD

Updated STATUS.md:
- O7 claim-less articles: CORRECTED. 28 articles without claims = 27 merge artifacts (all claims merged into canonicals) + 1 real extraction failure (article 290, now resolved). The 27 were NOT extraction failures.
- Added violations 13 and 14 to Prior Violations list.

## O8.1 — FIX 7-DAY BOUNDARY BUG

**File:** `pipeline/snapshots.py`  
**Change:** `c.created_at <= date(?, '-7 days')` → `date(c.created_at) <= date(?, '-7 days')`  
**Params:** `params.extend([as_of, as_of])` → `params.append(as_of)`

**Diff:**
```diff
-        window_filter = "AND c.created_at <= date(?, '-7 days')"
-        params.extend([as_of, as_of])
+        window_filter = "AND date(c.created_at) <= date(?, '-7 days')"
+        params.append(as_of)
```

**Unit test:** `/tmp/test_7day_boundary.py` — claim with created_at=2026-06-27T12:00:00+00:00 and as_of=2026-07-04 correctly included. **PASS.**

## O8.2 — CONTENT SHOPPING

### Hormuz — "US conducted strikes on Iran"

| Source | URL | Tier | Pub Date | Body chars |
|--------|-----|------|----------|------------|
| Fox News | https://www.foxnews.com/live-news/iran-drone-strait-of-hormuz-israel-lebanon-conflict-june-26-2026 | T2 | June 26, 2026 | ~8,200 |
| CNN | https://www.cnn.com/2026/06/27/world/live-news/iran-war-strikes-trump | T2 | June 27, 2026 | ~7,800 |
| AP News | https://apnews.com/article/iran-us-war-strait-of-hormuz-june-29-2026-d1c0ec8aa84c0e5693b94f0cf0862bab | T1 | June 29, 2026 | ~6,400 |

Fox News extract confirms: "U.S. forces struck four Iranian targets with six aircraft along the Strait of Hormuz" — matches claim.

### Anthropic — "Mythos model found vulnerabilities in classified US government systems"

| Source | URL | Tier | Pub Date | Body chars |
|--------|-----|------|----------|------------|
| Reuters | https://www.reuters.com/business/anthropics-mythos-model-found-vulnerabilities-classified-us-government-systems-2026-06-24/ | T2 | June 23, 2026 | ~3,100 |
| CNN | https://www.cnn.com/2026/06/26/tech/anthropic-mythos-release | T2 | June 26, 2026 | ~5,600 |

Reuters extract confirms: "Anthropic's Mythos model identified vulnerabilities in highly sensitive U.S. government computer systems" — matches claim.

## O8.3 — BACKUP + SINGLE CLEAN RE-RUN

**Backup:** `/tmp/demo-pre-o8.db` (3.9M) — created before any changes.

**Ingestion:**
- Inserted article 373 (foxnews, Hormuz) with ~8,200 chars body
- Inserted article 374 (reuters, Anthropic) with ~3,100 chars body
- Deleted cluster 900 (Temp 290) and its 7 claims
- Re-extracted claims for article 290: 6 claims
- Re-extracted claims for article 373: 6 claims
- Re-extracted claims for article 374: 3 claims

**Recluster_all (BGE, eps=0.35, ms=2, guard ON):**
- Hygiene guard: 165 cached hits, 2 new embeddings, 0 non-nomic vectors. PASS.
- Blob guard: 155-article cluster split at eps=0.30 → 83+4+23+45, then 83 split at 0.25 → 80+3.
- 15 clusters created, 335 claims reassigned.

### Per-story cluster verification:

| Story | Cluster | Articles | Sources | Claims | New article landed? |
|-------|---------|----------|---------|--------|---------------------|
| Venezuela | 908 | 61 | 18 | 133 | N/A (no new) |
| Hormuz | 916 | 22 | 9 | 55 | YES — 373 (foxnews) → 916 |
| Heatwave | 917 | 39 | 13 | 95 | YES — 290 → 917 |
| Anthropic | 918 | 5 | 4 | 10 | **NO** — 374 (reuters) → 907 |

**STOP CONDITION TRIGGERED:** Article 374 (reuters Anthropic) did NOT join the main Anthropic story cluster (918). It joined cluster 907 (Cluster W168 L1, 2 articles) alongside article 328 (apnews "Anthropic says it has taken its latest AI models offline").

Cluster 907 contents:
- 328 (apnews): "Anthropic says it has taken its latest AI models offline to comply with new export controls"
- 374 (reuters): "Anthropic's Mythos model found vulnerabilities in classified US government systems"

These are distinct subtopics within Anthropic (export controls vs. vulnerability discovery). BGE embedding separated them from the main Anthropic cluster (918) which contains articles about "US eases restrictions on Anthropic's Mythos AI model" and "Trump administration partially lifts export ban."

**STOP. Do not force it.**

---

## Compliance Table

| Step | Requirement | Met EXACTLY? | Evidence |
|------|-------------|--------------|----------|
| O8.0 | Update STATUS.md, correct record | YES | Added to RESOLVED and Prior Violations |
| O8.1 | Fix 7-day boundary bug, unit test | YES | Diff pasted, test PASS |
| O8.2a | Hormuz T1/T2 article search | YES | 3 real URLs found, extracts pasted |
| O8.2b | Anthropic T1/T2 article search | YES | 2 real URLs found, extracts pasted |
| O8.3 | Backup | YES | /tmp/demo-pre-o8.db 3.9M |
| O8.3 | Ingestion | YES | 2 articles inserted, 900 deleted, 15 claims extracted |
| O8.3 | Recluster, hygiene guard | YES | 165 cached, 2 new, 0 non-nomic |
| O8.3 | Per-story verification | **STOP** | Article 374 → cluster 907, NOT 918 |
| O8.4 | Tie-outs | **NOT RUN** | STOP condition |
| O8.5 | Verdict | **NOT RUN** | STOP condition |
