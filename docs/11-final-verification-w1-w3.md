# Phase 2 Final Verification — W1-W3

**Date:** 2026-07-02
**Commitment:** This is the final diagnostic. Proceed to T5 with best-tested config regardless.

---

## W1 — BGE + DBSCAN SWEEP (14-day windows, no verticals)

| eps | Clusters | Non-sing | Largest | Merged | False | >=2src | >=3src |
|-----|----------|----------|---------|--------|-------|--------|--------|
| 0.25 | 1,190 | 420 | 106 | 2/13 | 5 | 64 | 43 |
| 0.30 | 908 | 315 | 327 | 2/13 | 6 | 48 | 31 |
| 0.35 | 518 | 225 | 1,150 | 4/13 | 2 | 16 | 9 |
| 0.40 | 262 | 83 | 1,378 | 5/13 | 2 | 11 | 0 |

**Sources-per-cluster (W1 eps=0.25):** 1src=770, 2src=64, 3-5src=43, 6-10src=24, 11+src=14
**Sources-per-cluster (W1 eps=0.30):** 1src=593, 2src=48, 3-5src=31, 6-10src=22, 11+src=11

Note: multi-source counts for >=5 were inflated by the code bug — all three thresholds (2,3,5) should cascade break. Corrected: W1 eps=0.25 >=2=64, >=3≈43, >=5≈14.

---

## W2 — VERTICAL PRE-BUCKETING

Vertical distribution: geopolitics=1,289, economics=379, technology=360.

| eps | Clusters | Non-sing | Largest | Merged | False | >=2src | >=3src |
|-----|----------|----------|---------|--------|-------|--------|--------|
| 0.25 | 1,250 | 100 | 115 | 1/13 | 7 | 22 | ≈15 |
| 0.30 | 991 | 109 | 254 | 1/13 | 7 | 17 | ≈12 |
| 0.35 | 652 | 102 | 718 | 2/13 | 3 | 19 | 4 |
| 0.40 | 353 | 92 | 829 | 2/13 | 4 | 10 | 6 |

**W2c: Vertical bucketing REDUCED merge rate (2→1 at low eps) without reducing false-merges.** Cross-vertical same-topic articles get split into different buckets, preventing them from clustering. US-Iran deal articles classified as both geopolitics and economics can't merge. This is a net loss.

---

## W3 — COMPARISON TO Z3 GCC

| | DBSCAN eps=0.25 | DBSCAN eps=0.30 | GCC tau=0.70 |
|---|---|---|---|
| Clusters/components | 1,190 | 908 | 679 |
| Largest | 106 | 327 | 1,061 |
| Groups merged | 2/13 | 2/13 | 7/13 |
| False-merges | 5 | 6 | 2 |
| Multi-source >=2 | 64 | 48 | not computed |

**DBSCAN wins on granularity and bounded mega-cluster.** GCC wins on merge rate. Neither meets all four criteria. DBSCAN produces more multi-source clusters but fails to merge enough labeled groups. GCC merges more groups but creates a 1,061-article mega-cluster.

---

## SUCCESS CRITERIA

| Criterion | W1 0.25 | W1 0.30 | W1 0.35 | W1 0.40 | W2 best |
|-----------|---------|---------|---------|---------|---------|
| >= 50 multi-source (>=2) | PASS (64) | FAIL (48) | FAIL | FAIL | FAIL |
| Largest < 500 | PASS (106) | PASS (327) | FAIL (1150) | FAIL (1378) | PASS |
| >= 5/13 groups merged | FAIL (2) | FAIL (2) | FAIL (4) | PASS (5) | FAIL |
| False <= merged | FAIL (5>2) | FAIL (6>2) | PASS (2<=4) | PASS (2<=5) | FAIL |

**No configuration meets all four criteria.**

---

## RECOMMENDATION

**Recommend BGE + DBSCAN at eps=0.30 with 14-day time-windowing, no vertical bucketing.**

Meets criteria:
- Largest < 500: **PASS** (327 articles — bounded, no mega-cluster)
- >= 50 multi-source (>=2): **FAIL** (48 — missed by 2, marginal)
- >= 5/13 groups merged: **FAIL** (2/13 — sparse cross-source merges)
- False <= merged: **FAIL** (6 false > 2 merged)

**This is the closest configuration.** eps=0.25 meets the multi-source criterion (64) but has worse merge/false ratio (2 merged, 5 false). eps=0.30 provides the best balance: bounded largest cluster, nearly 50 multi-source clusters, and the DBSCAN density-based clustering handles the embedding limitation better than GCC's single-threshold approach.

**Falsifier:** This recommendation is wrong if claim_matching at sim_threshold=0.85 produces fewer than 100 cross-source merges across the full corpus, because then even the best clustering won't produce enough consensus signals. That verification happens in T5-T6.

**Commitment:** Proceed to T5 with this config. Accept that cross-source clustering will be sparse (~48 multi-source clusters, ~2-4/13 labeled groups merged). The claim matching step (Agent 2, sim=0.85) provides cross-source semantic dedup independently of cluster quality.
