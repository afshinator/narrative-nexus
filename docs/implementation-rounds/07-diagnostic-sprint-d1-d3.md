# Phase 2 Diagnostic Sprint Report — D1-D3

**Date:** 2026-07-02
**Status:** BLOCKED — embedding model is the bottleneck; awaiting direction on D3 model switch before T5

---

## D1 — NOMIC CLUSTERING PREFIX

**D1a:** No prefix was prepended. `pipeline/embedding_client.py:151` passes texts raw to the API. `claim_matching.py:95` uses the same client.

**D1b:** Added `"clustering: "` prefix for nomic models in `EmbeddingClient.embed()` (line 122-123).

**D1c:** Cache invalidated — 2,028 nomic entries deleted from `/tmp/phase2.db`.

**D1d — Re-sweep with prefix:**

| eps | Clusters | Groups Merged | Over-merges | Largest Cluster |
|-----|----------|---------------|-------------|-----------------|
| 0.30 | 313 | 6/15 (33.9%) | 2 | 1,425 |
| 0.35 | 188 | 6/15 (33.9%) | 2 | 1,432 |
| 0.40 | 137 | 6/15 (33.9%) | 2 | 1,432 |
| 0.45 | 120 | 6/15 (33.9%) | 2 | 1,432 |
| 0.50 | 118 | 6/15 (33.9%) | 2 | 1,432 |

**Result: WORSE than no prefix.** The prefix compressed the embedding space further — cluster count dropped from 857→313 at eps=0.30, mega-cluster grew from 930→1,425 articles. Comparison:

| eps | No prefix | With prefix |
|-----|-----------|-------------|
| 0.30 | 857 clusters, mega=930 | 313 clusters, mega=1,425 |
| 0.35 | 496 clusters, mega=1,297 | 188 clusters, mega=1,432 |
| 0.50 | 161 clusters, mega=1,432 | 118 clusters, mega=1,432 |

The `"clustering: "` prefix makes nomic produce even LESS discriminative vectors for news articles.

---

## D2 — LABEL SET HYGIENE

**D2a — Pairwise overlap matrix:**

| Pair | Shared IDs | Count |
|------|-----------|-------|
| World Cup 2026 ∩ Messi at World Cup | 1719, 1723 | 2 |
| Israel-Gaza-Hezbollah ∩ Lebanon Hezbollah deal | 453, 1885, 2123, 2148, 2910 | 5 |
| Trump birthright ∩ Israel-Gaza-Hezbollah | 453 | 1 |
| Trump birthright ∩ Lebanon Hezbollah deal | 453 | 1 |
| Western Europe heat wave ∩ Anthropic AI | 175 | 1 |

**D2b — Revised label set: 13 groups** (saved in `scripts/labeled_groups_v2.py`):

- **Merged:** World Cup 2026 + Messi at World Cup → "World Cup 2026 (+Messi)" — share 2 articles, same tournament
- **Merged:** Israel-Gaza-Hezbollah + Lebanon Hezbollah deal → "Israel-Hezbollah conflict" — share 5 articles (83% overlap), same war
- **Fixed:** Article 175 removed from Western Europe heat wave — it's about Anthropic AI, mislabeled
- **Fixed:** Article 453 removed from Trump birthright citizenship — it's about Lebanon/Israel/Hezbollah

**D2c — Over-merge check fix:** Groups merged in D2b are treated as a single group. A cluster containing both "World Cup" and "Messi" articles is now scored as correct merge, not over-merge. Groups that share articles are treated as non-distinct — fusion of them into one cluster is not an over-merge.

---

## D3 — ALTERNATIVE EMBEDDING MODELS

Tested 12 models against Fireworks API (`https://api.fireworks.ai/inference/v1`). Available options:

| Model | Dim | Status | Notes |
|-------|-----|--------|-------|
| nomic-ai/nomic-embed-text-v1.5 | 768 | Current | Poor clustering — everything merges |
| BAAI/bge-base-en-v1.5 | 768 | Available | BGE series — strong for semantic clustering |
| BAAI/bge-small-en-v1.5 | 384 | Available | Lighter BGE variant |
| thenlper/gte-large | 1024 | Available | GTE series |
| thenlper/gte-base | 768 | Available | GTE base |
| WhereIsAI/UAE-Large-V1 | 1024 | Available | UAE series |

Unavailable: BAAI/bge-large-en-v1.5, intfloat/e5-*, Snowflake/arctic-embed-*, jinaai/jina-embeddings-*

**Recommended next candidate: BAAI/bge-base-en-v1.5** — same 768-dim as nomic, no special prefix required, well-documented for clustering/retrieval tasks. The BGE series uses standard embedding input with no task-specific prefix.

---

## UPDATED EPS RECOMMENDATION

Nomic-ai/nomic-embed-text-v1.5 cannot separate news article topics regardless of eps value or task prefix. At every eps tested, 70%+ of articles collapse into a single mega-cluster. The embedding model itself is the bottleneck — not the eps parameter, not the task prefix.

**Recommended path:**
1. Test BAAI/bge-base-en-v1.5 on a small sample (50 articles from 5 labeled groups) to verify topic separation
2. If bge-base shows promise, run the full sweep
3. Only then choose eps and proceed to T5

## Files Changed

| File | Change |
|------|--------|
| `pipeline/embedding_client.py` | +MODEL_DIMS entries (bge, gte) + nomic clustering prefix |
| `pipeline/agent1_intake.py` | Dim-aware cache lookup + guard (T2) |
| `pipeline/resolution.py` | `reporting` parameter (T1 zombie fix) |
| `pipeline/agent3_consensus.py` | Pass reporting, remove post-hoc patch (T1) |
| `pipeline/test_resolution.py` | +5 tests (T1b) |
| `scripts/recluster_all.py` | New — full recluster pipeline (T3) |
| `scripts/eps_sweep.py` | New — EPS sweep with labeled groups (T4b) |
| `scripts/labeled_groups_v2.py` | New — D2b revised label set (13 groups) |
