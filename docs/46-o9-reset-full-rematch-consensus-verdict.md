# O9 — Reset, Full Rematch, Consensus, Verdict

**Date:** 2026-07-04
**Target DB:** data/demo/demo.db
**No commits made.**

---

## O9.0 — BACKUP

```
644  data/demo/backups/demo-pre-o9.db  3.9M
644  data/demo/demo.db  3.9M
```

---

## O9.1 — RECONCILE 335 vs 328

```
$ sqlite3 data/demo/demo.db "SELECT COUNT(*) FROM claims;"
335

$ sqlite3 data/demo/demo.db "SELECT COUNT(*) FROM claim_variants;"
507
```

**Explanation:** The backup (`data/demo/backups/demo-pre-o8.db`) confirms 327 claims existed before O8.3, not 320. The 7 claims from the O7.2 retry (cluster 900) were present. Correct math: 327 (pre-O8) - 7 (cluster 900 removed) + 6 (art 290 re-extracted) + 6 (art 373 foxnews) + 3 (art 374 reuters) = 335. Doc 45 incorrectly used 320 as baseline, missing the 7 O7.2 claims.

---

## O9.2 — HORMUZ SOURCE CHECK

**(a) Foxnews articles in Hormuz cluster (pre-O9):**
```
199 | Shipping giant warns Strait of Hormuz chaos is 'new normal'... | 2026-06-28
373 | US strikes Iran after Strait of Hormuz cargo ship attack...     | 2026-06-26
```

Two foxnews articles. Article 199 was ALREADY in the cluster before O8.

**(b) Claim 1504 supporters (pre-unmerge):**
```
theguardian (T1), washingtonpost (T2), zerohedge (T5), sputnikglobe (T5)
```

Foxnews was NOT a supporter of claim 1504 before rematch. Article 373 was in the cluster but its claims hadn't been matched yet — no rematch ran after O8.3. The content shopping yielded the right article; it just needed the rematch to connect it to the claim.

---

## O9.3 — CNN ANTHROPIC ARTICLE

Inserted article 375 (cnn, T2) with 3,070 chars body. Agent 2 extracted 3 claims:
- The US government revised license requirements.
- Anthropic is allowed to release its Claude Mythos 5 AI model to select companies
- The Claude Mythos 5 AI model sparked cybersecurity concerns.

---

## O9.4 — RESET AND FULL REMATCH

### Step 1: reset_claim_state (true un-merge)
```
Before: claims=338, claim_sources=521, claim_variants=507
Restored 507 claim_variant rows as independent claims
Reset 845 claims to PENDING
Deleted 507 claim_variant rows
Deleted 521 claim_sources rows
Inserted 845 claim_sources rows
After: claims=845, claim_sources=845, claim_variants=0
VERIFIED: claim_sources count (845) == claims count (845)
```

Tie-out: 338 + 507 = 845. PASS.

### Step 2: recluster_all (BGE, eps=0.35)
- Hygiene guard: 167 cached BGE hits, 1 new (article 375). PASS.
- Blob guard: 155 → 83+4+23+45 → 80+3 at floor eps=0.25.
- 15 clusters, 845 claims reassigned.

**Per-story verification:**
- 373 (foxnews) → cluster 932 (Hormuz) ✓
- 290 (punchng) → cluster 933 (Heatwave) ✓
- 374 (reuters) → cluster 923 (Anthropic-vuln, with article 328) ✓
- 375 (cnn) → cluster 934 (Anthropic-main) ✓

### Step 3: match_all_clusters (nomic, sim=0.85)
```
Clusters with claims: 15
Clusters processed (had merges): 14
Total merges: 518
Sources linked: 371
Elapsed: 14.3s

Claims after: 327
Claim variants: 518
Tie-out: 327 + 518 = 845 ✓
```

### Step 4: Agent 3
```
Agent 3: {'clusters': 15, 'classified': 8}
PENDING: 319
CONSENSUS_ABSORBED: 8
Tie-out: 319 + 8 + 0 = 327 ✓
```

### Step 5: backfill_snapshots
```
95 dates, 10545 rows
```

---

## O9.5 — TIE-OUTS

| Tie-out | Result | Status |
|---------|--------|--------|
| pre-merge = post-merge + variants | 845 = 327 + 518 | ✅ |
| per-cluster sum = total | 327 = 327 | ✅ |
| PENDING + ABSORBED = total | 319 + 8 = 327 | ✅ |

### Hormuz top claim (1649 "U.S. forces struck four Iranian targets"):
```
Cluster 932, vertical: geopolitics
Supporters: theguardian(T1), foxnews(T2), washingtonpost(T2), zerohedge(T5), thehindu(T3), sputnikglobe(T5)
Pool (T1/T2): theguardian, foxnews, washingtonpost = 3
Pool size (T1/T2 in cluster 932): 4
Pct: 3/4 = 75.0% | Threshold: 65% (geopolitics)
ABSORBED: YES
```

### Anthropic-vuln (cluster 923) top claim:
```
Cluster 923, vertical: technology
Supporters: apnews(T1)
Pool (T1/T2): apnews = 1
Pool size: 2
Pct: 1/2 = 50.0% | Threshold: 75% (technology)
ABSORBED: NO
```

---

## O9.6 — VERDICT

| Story | Cluster | Vertical | Claims | Absorbed | Result |
|-------|---------|----------|--------|----------|--------|
| Venezuela | 924 | geopolitics | 133 | 3 | **YES** |
| Heatwave | 933 | economics | 91 | 3 | **YES** |
| Hormuz | 932 | geopolitics | 49 | 1 | **YES** |
| Anthropic-main | 934 | technology | 12 | 1 | **YES** |
| Anthropic-vuln | 923 | technology | 8 | 0 | **NO** |

**4/5 stories absorbed. Target achieved.**

### Anthropic-vuln gap:
Pool size = 2 (apnews + reuters). Every claim has only 1 T1/T2 supporter. 1/2 = 50% < 75% technology threshold. No claim reaches 2/2 = 100%.

---

## Compliance Table

| Step | Requirement | Met EXACTLY? | Evidence |
|------|-------------|--------------|----------|
| O9.0 | Backup | YES | data/demo/backups/demo-pre-o9.db 3.9M |
| O9.1 | Reconcile 335 vs 328 | YES | 327 baseline in backup, not 320 |
| O9.2a | Foxnews articles in Hormuz | YES | 199 + 373 both in cluster |
| O9.2b | Claim 1504 supporters | YES | Foxnews NOT a supporter; needed rematch |
| O9.3 | Ingest CNN Anthropic | YES | 3 claims, 3,070 chars |
| O9.4.1 | Reset to un-merge | YES | 845 claims, 0 variants, tie-out PASS |
| O9.4.2 | Recluster | YES | 167 cached, 1 new, article landing verified |
| O9.4.3 | Match | YES | 518 merges, 327 claims |
| O9.4.4 | Agent 3 | YES | 8 absorbed |
| O9.4.5 | Backfill | YES | 95 dates, 10,545 rows |
| O9.5 | Tie-outs | YES | All 3 tie-outs pass |
| O9.5b | Hormuz pool arithmetic | YES | 3/4=75% ≥ 65% geopolitics |
| O9.5c | Anthropic-vuln pool arithmetic | YES | 1/2=50% < 75% technology |
| O9.6 | Verdict | YES | 4/5 YES, 1 NO (Arctic-vuln gap stated) |
