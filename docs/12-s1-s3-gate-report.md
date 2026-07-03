# Phase 2 S1-S3 Gate Report

**Date:** 2026-07-02
**Status:** S3h FAILED — 93.9% single-source clusters, target was <70%. Cannot proceed to S4 (live DB).

---

## S1 — CONFIG LOCKS ✅

| Check | File | Line | Status |
|-------|------|------|--------|
| S1a: BGE model in providers | `config/providers.json:7` | `"model": "BAAI/bge-base-en-v1.5"` | ✅ |
| S1b: Cleaned input | `pipeline/agent1_intake.py:63` | `get_embedding_input(..., max_body_chars=1000)` | ✅ |
| S1b: 14-day windows | `pipeline/agent1_intake.py:130` | `window_days = 14` | ✅ |
| S1b: DBSCAN eps=0.30 | `pipeline/agent1_intake.py:165` | `eps=0.30` | ✅ |
| S1c: sim_threshold=0.85 | `pipeline/claim_matching.py:47` | `sim_threshold: float = 0.85` | ✅ |
| S1d: MIN_CORROBORATION=2 | `pipeline/consensus.py:8` | `MIN_CORROBORATION = 2` | ✅ |
| S1d: reporting parameter | `pipeline/resolution.py:13` | `reporting: int \| None = None` | ✅ |

---

## S2 — FULL RE-RUN ON /tmp/phase2.db

| Step | Description | Wall-clock | Key output |
|------|-------------|-----------|------------|
| S2.1 | Fresh copy: cp data/nn.db → /tmp/phase2.db | — | 29MB |
| S2.2 | Cache invalidated | — | 0 entries (already empty) |
| S2.3 | Reset claim state | — | claims=8,567, claim_sources=8,567 ✅ |
| S2.4 | cleanup_empty_clusters | skipped | Clusters replaced by recluster |
| S2.5 | recluster_all.py (BGE, eps=0.30) | ~40s | 1,112 clusters, largest=561 |
| S2.6 | claim_matching (0.85) | 381s | 932 merges, 407 sources linked |
| S2.7 | Agent 3 consensus | 2.5s | 1,112 clusters, 1,501 reclassified |
| S2.8 | Snapshot recompute | 74s | 44,844 snapshots, 404 dates |

**Cluster histogram (S2.5):**
```
Sources per cluster:
  0 src:     6   1 src: 1,037   2 src: 43   3 src: 13   4 src: 2
  5 src:     2   6 src:     2   7 src:  2   8 src:  1   9 src: 1
 10 src:     2  29 src:     1

Articles per cluster:
  1 art:   986   2 art: 73   3 art: 22   4 art: 11   6 art: 3
  561 art:   1 (largest)
```

---

## S3 — ACCEPTANCE CHECKS

| Check | Result | Threshold | Pass/Fail |
|-------|--------|-----------|-----------|
| (a) Absorbed in multi-source | 13/13 = 100% | MUST be 100% | **PASS** |
| (b) convergence_type non-null | 13/13 = 100% | MUST be 100% | **PASS** |
| (c) claim_sources > claims | 8,002 > 7,635 = 1.05x | MUST be true | **PASS** |
| (d) Claims by state | PENDING=6,134, UNRESOLVED=1,488, ABSORBED=13 | Record only | — |
| (e) Sources with absorbed | theguardian(6), apnews(4), foxnews(2), bbc(1) | Record only | — |
| (f) Solo coverage top 10 | 6 sources at 100%, bottom: politico/wp at 0% | Record only | — |
| (g) UNRESOLVED past 90 days | 1,488 | MUST be >0 | **PASS** |
| (h) Single-source share | 93.9% (1,044/1,112) | MUST be <70% | **FAIL** |
| (i) R_val spot-check | skipped (blocked by S3h) | — | — |
| (j) Test regressions | pytest 289/8, vitest 149/11/4 | No regression | **PASS** |

---

## FAILURE ANALYSIS

**S3h FAILED: 93.9% single-source clusters.** Target was <70%.

Root cause: BGE embeddings at eps=0.30 produce only 69 multi-source clusters (>=2 distinct sources) out of 1,112 total. The W1 sweep predicted this — W1 eps=0.30 gave 48 multi-source clusters, which was already below the 50-cluster target. The actual run with claim_matching added some cross-source links but not enough to push single-source share below 70%.

Comparison to pre-Phase-2 baseline: 959/1,020 populated clusters were single-source (94.0%). We improved from 94.0% → 93.9% — a 0.1% improvement, not the dramatic drop the work order requires.

**The embedding model (BGE or nomic) cannot produce enough cross-source topic separation to get single-source share below 70%.** The Z1/Z2 gap analysis showed a real intra/across gap (0.17 for BGE) but with overlapping distributions — some same-story cross-source pairs are as low as 0.35, preventing clean threshold-based separation.

---

## CONTRADICTION CHECK

No contradictions with design docs. The design doc §4 schedule describes the state machine (now fixed with T1) and the MIN_CORROBORATION rule (now enforced). The sparse absorption (13 claims) is consistent with the design: only claims with >=2 independent sources reporting them can be absorbed.

---

## STOP

Per S3h failure, cannot proceed to S4 (live DB). The single-source cluster share (93.9%) exceeds the 70% threshold.
