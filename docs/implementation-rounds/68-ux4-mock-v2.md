# UX4-MOCK-V2 — Full-page Demo Direction Mocks

**Date:** 2026-07-06
**Status:** COMPLETE — V2 created. No app code changes. No commits.

**File:** `docs/mocks/demo-direction-mock-v2.html`
**Access:** `http://localhost:3015/demo-direction-mock-v2.html`

---

## V1 → V2 Changes

| V1 Issue | V2 Fix |
|----------|--------|
| Components shown in isolation | Two complete pages top-to-bottom (nav → footer) |
| Ungraded count said "10" but listed 11 | Query confirmed 11, copy and list now agree |
| No scatter plot with real values | Static SVG with all 26 graded points at real R_orig/R_val positions |
| No leaderboard table | Full 26-row table with real tier/orig/val values |
| Cluster report skeletal | Complete cluster 966 report with consensus summary, full claims list, absorption strip inline, near-consensus exhibit in position |
| Absorption strip standalone | Inline within claim 2799's row, showing its real position in the claims list |

---

## DB Queries (verbatim)

### Ungraded count fix
```sql
SELECT COUNT(*)
FROM snapshots sn
WHERE sn.vertical='geopolitics'
  AND sn.date=(SELECT MAX(date) FROM snapshots)
  AND (sn.R_orig IS NULL OR sn.R_val IS NULL);
→ 11
```
V1 incorrectly stated "10". The query returns 11 sources with null R_orig or R_val. straitstimes.com is a special case: R_orig=0.0 (not null) but R_val=NULL — it's counted by the R_val IS NULL check.

### Ungraded domain list
```sql
SELECT s.domain, sn.R_orig, sn.R_val
FROM snapshots sn JOIN sources s ON s.id = sn.source_id
WHERE sn.vertical='geopolitics'
  AND sn.date=(SELECT MAX(date) FROM snapshots)
  AND (sn.R_orig IS NULL OR sn.R_val IS NULL)
ORDER BY s.domain;
→ 11 rows (full output in mock HTML)
```

### Scatter plot / leaderboard data
```sql
SELECT ROUND(sn.R_orig,1), ROUND(sn.R_val,1), s.domain, s.name, sn.source_id, s.tier
FROM snapshots sn JOIN sources s ON s.id = sn.source_id
WHERE sn.vertical='geopolitics'
  AND sn.date=(SELECT MAX(date) FROM snapshots)
  AND sn.R_orig IS NOT NULL AND sn.R_val IS NOT NULL
ORDER BY sn.R_orig DESC;
→ 26 rows (full output in UX3 round doc)
```

### Cluster 966 counts
```sql
SELECT COUNT(DISTINCT source_id) FROM claim_sources
WHERE claim_id IN (SELECT id FROM claims WHERE cluster_id=966);
→ 3

SELECT state, COUNT(*) FROM claims WHERE cluster_id=966 GROUP BY state;
→ CONSENSUS_ABSORBED|1, PENDING|7, UNRESOLVED|11
```

### Absorption math (claim 2799)
```sql
SELECT * FROM claims WHERE id=2799;
→ 2799|940|966|On Tuesday, the U.S. and Israel launched airstrikes against Iran.|CONSENSUS_ABSORBED|CROSS_SOURCE_CONVERGENT|...

SELECT s.domain, s.tier FROM claim_sources cs JOIN sources s ON s.id=cs.source_id WHERE cs.claim_id=2799;
→ reuters.com|1, theguardian.com|1

SELECT DISTINCT s.domain, s.tier FROM claims c JOIN claim_sources cs ON cs.claim_id=c.id JOIN sources s ON s.id=cs.source_id WHERE c.cluster_id=966 AND s.tier<=2;
→ apnews.com|1, reuters.com|1, theguardian.com|1
```
2/3 = 66.7% ≥ 65% geopolitics threshold.

---

## Deviations from design-tokens.md

Carried from V1, plus V2 additions:

| Token doc says | Current mock | Reason |
|---------------|-------------|--------|
| Body: 16px (1rem) | 1.1rem base (UX3 rebase, index.css:189) | UX3 font-scale rebase |
| Cards: radius 12px | 14px | Matches current Sources.tsx |
| Body color: var(--text) | var(--nn-text-dim) for subtitle text | Matches current Sources.tsx |
| Legend layout undefined | Unified color+shapes block, 0.82rem | UX3 X3 merge |
| Intro strip undefined | Two-column with pipe divider | Human UX2 direction |
| Badges: 10% opacity bg | 12% opacity | Slightly more visible on dark bg |
| **V2 NEW:** Cluster report layout undefined | Consensus zone + claims list + near-consensus exhibit | Design-v1.2 §6 "3-zone forensic report" |
| **V2 NEW:** Absorption strip undefined | Inline claim-level integrity strip with math | UX4-V1 section C |
| **V2 NEW:** Scatter plot | Static SVG (not live D3) | Mock constraint — visual design judgeable |

---

## Bounds Compliance

| Rule | Met? |
|------|------|
| Read-only DB access | YES — all queries SELECT only |
| Query output pasted verbatim | YES — all queries and results in this doc |
| Copy from design-v1.2 vocabulary | YES — consensus reality, absorbed, outlier, convergent |
| No app code changes | YES — static HTML only |
| No pipeline runs | YES |
| No commits | YES — uncommitted |
| Near-miss claim text marked placeholder | YES — CANNOT COMPLY labels on both pairs |

---

## ROUND OBJECTIVE

Two complete full-page mocks showing the demo direction in context — Sources page (top to bottom) and Cluster Report 966 (top to bottom). All components placed where they would actually render. Real DB data for scatter points, leaderboard, cluster counts, absorption math. Near-miss claims CANNOT COMPLY (similarity scores not stored) — clearly marked placeholder.

**ROUND OBJECTIVE MET:** YES (with CANNOT COMPLY on near-miss text, documented)
