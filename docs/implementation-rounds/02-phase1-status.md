# NARRATIVE NEXUS — PHASE 1 STATUS REPORT

**Date:** 2026-07-02
**Status:** COMPLETE

---

## T0 — PREFLIGHT

### T0a — Gemma model test
**BLOCKED.** All three Gemma model IDs return 404 on this Fireworks account:
- `accounts/fireworks/models/gemma-4-31b-it` → 404 "Model not found, inaccessible, and/or not deployed"
- `accounts/fireworks/models/gemma-4-26b-a4b-it` → 404
- `accounts/fireworks/models/gemma2-9b-it` → 404

Only `accounts/fireworks/models/deepseek-v4-pro` is available for chat. Embeddings use `nomic-ai/nomic-embed-text-v1.5` (works via API despite not appearing in /models catalog). Phase 3 "Gemma-on-Fireworks" plan is blocked on this account.

Evidence: `scripts/test_gemma.py` output, 2026-07-02.

### T0b — Remaining pytest failures
All 3 are pre-existing, not fallout from Phase 0 T2b lazy-import changes:

| Test | Reason |
|------|--------|
| `TestEmbeddingClientInit::test_api_provider_requires_key` | FIREWORKS_API_KEY in environment, so empty api_key test can't trigger ValueError |
| `TestInsertSnapshot::test_enforces_unique_source_vertical_date` | INSERT OR REPLACE doesn't raise on UNIQUE conflict |
| `TestSourcesRoute::test_source_by_id_returns_null_when_empty` | TestClient DB has seed data from fixture setup |

---

## T1 — SCHEMA ADDITIONS

### T1a/b — embeddings + claim_variants tables
Added to `db/schema.sql:116-137`:
```sql
CREATE TABLE IF NOT EXISTS embeddings (
    article_id  INTEGER PRIMARY KEY REFERENCES articles(id),
    model       TEXT NOT NULL,
    dim         INTEGER NOT NULL,
    vector      BLOB NOT NULL,
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS claim_variants (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    canonical_claim_id  INTEGER NOT NULL REFERENCES claims(id),
    source_id           INTEGER NOT NULL REFERENCES sources(id),
    article_id          INTEGER NOT NULL REFERENCES articles(id),
    text                TEXT NOT NULL,
    first_seen_at       TEXT NOT NULL
);
```

### T1c — Applied to live DB
Both tables created in `data/nn.db`.

---

## T2 — CLAIM MATCHING MODULE

**File:** `pipeline/claim_matching.py` (260 lines)

### Algorithm
Greedy, deterministic cosine-similarity matching within a cluster:
1. Fetch all claims ordered by `articles.published_at ASC`
2. Embed all claim texts in batched calls (max 256 per batch per Fireworks limit)
3. Iterate claims in order: cosine similarity vs current canonicals
4. If best sim >= threshold (0.85) → merge into canonical; else → new canonical
5. Merge: insert/update `claim_sources` for canonical (earliest `first_seen_at` kept); insert `claim_variants` for duplicate; delete duplicate from `claims`
6. Same-source duplicates merge identically — one `claim_sources` per (claim, source)
7. Idempotent: detects prior processing via `claim_variants` presence

### Functions
- `match_claims_in_cluster(conn, cluster_id, embed_client, sim_threshold=0.85)` → dict
- `match_all_clusters(conn, embed_client, sim_threshold=0.85)` → dict (resumable, progress-logged)

### Idempotency
Detects prior processing by checking if any claim in the cluster already has a `claim_variants` row. If found, returns immediately with zero merges.

---

## T3 — CONSENSUS RULE

### T3a — MIN_CORROBORATION
`pipeline/consensus.py:6-9`:
```python
# D1: Minimum corroboration rule — a claim may only become CONSENSUS_ABSORBED
# if reported by >= 2 distinct consensus-pool (T1/T2) sources AND pct >=
# vertical threshold.  Single-source claims resolve to UNRESOLVED at 90 days.
MIN_CORROBORATION = 2
```

### T3b — Enforcement in Agent 3
`pipeline/agent3_consensus.py:72-73`:
```python
if new_state == "CONSENSUS_ABSORBED" and reporting < MIN_CORROBORATION:
    new_state = "PENDING"
```

### T3c — convergence_type
Set to `CROSS_SOURCE_CONVERGENT` at absorption (`agent3_consensus.py:79-82`). SELF_CONSISTENT is never written.

---

## T4 — R_VAL DENOMINATOR

**File:** `pipeline/snapshots.py:63-66,86-101`

D2: R_val denominator excludes claims with `created_at` within 7 days of `as_of`. Both numerator (absorbed count) and denominator (originated count) use the windowed filter. `compute_r_orig_raw()` is NOT changed — R_orig stays raw.

SQL filter: `AND c.created_at <= ? AND c.created_at <= date(?, '-7 days')`

---

## T5 — CLUSTERING FIXES

### T5a — Persisted embeddings
`pipeline/agent1_intake.py:71-82,97-104`: Agent 1 checks `embeddings` table before generating new vectors. Uncached articles get new embeddings which are written to DB. Cached embeddings are deserialized from BLOB.

### T5b — Time-windowing
`pipeline/agent1_intake.py:109-122`: Articles bucketed into 14-day windows by `published_at` (fallback to `created_at`). DBSCAN runs per window. Single-article windows get singleton clusters. Cross-year mega-clusters eliminated by construction.

### T5c — Empty cluster cleanup
`scripts/cleanup_empty_clusters.py`: Deletes clusters with zero linked claims. Ready to run against live DB.

### T5d — Eps tuning harness
`scripts/tune_clustering.py`: 15 labeled story groups with hand-picked article IDs. Sweeps eps in {0.30, 0.35, 0.40, 0.45, 0.50}, reports cluster counts, max cluster size, noise count, and cross-source merge status. **Note:** Article IDs are synthetic range estimates — need real DB IDs substituted before running.

---

## T6 — TESTS + DRY RUN

### T6a — Unit tests
`pipeline/test_phase1.py`: 10 tests, all passing (`test_phase1.py`):
- Claim matching: same-source dupes merge, cross-source merges, below-threshold no merge, idempotency, threshold boundary
- Consensus rule: MIN_CORROBORATION=2, 1-source rejected, 2-source accepted
- R_val: 7-day window excludes recent claims (with windowed denominator), no as_of returns all

### T6b — Dry run results

**COPY:** `/tmp/dryrun.db` (30MB copy of `data/nn.db`)

| Cluster | Sources | Claims Before | Canonicals After | Merges | Time |
|---------|---------|---------------|------------------|--------|------|
| 4648 | 30 | 2,196 | 1,742 | 454 | 27.4s |
| 2400 | 6 | 297 | 260 | 37 | 3.5s |
| 880 | 9 | 203 | 185 | 18 | 2.5s |
| 885 | 8 | 110 | 83 | 27 | 1.5s |
| 703 | 4 | 77 | 59 | 18 | 1.1s |

**Total:** 554 merges across 5 clusters, 35.9s total.

**Merge quality:** Semantically correct. Identical texts merge ("Donald Trump is President" = "Donald Trump is President"), near-duplicates merge ("earthquake struck" ≈ "earthquakes hit"), same-source repeats dedup, unrelated claims stay separate.

**Threshold observation:** 0.85 produces sensible merges. Near-misses exist (scores just below threshold logged at DEBUG) — tuning the threshold up/down would adjust precision/recall.

### T6c — Full test suite

| Suite | Passed | Failed | Skipped | Change |
|-------|--------|--------|---------|--------|
| Pytest | 257 | 3 | 15 | +10 from Phase 1 |
| Vitest | 149 | 11 | 4 | unchanged |

No regressions. The 3 pytest failures and 11 vitest failures are pre-existing.

---

## FILES CHANGED

| File | Change | Lines |
|------|--------|-------|
| `db/schema.sql` | +embeddings +claim_variants tables | +21 |
| `pipeline/claim_matching.py` | NEW — claim matching module | +260 |
| `pipeline/consensus.py` | +MIN_CORROBORATION | +5 |
| `pipeline/agent3_consensus.py` | import MIN_CORROBORATION, enforce >=2 rule, convergence_type | ~15 |
| `pipeline/snapshots.py` | 7-day window for R_val denominator | ~35 |
| `pipeline/agent1_intake.py` | Persisted embeddings + time-windowing | rewrite |
| `pipeline/test_phase1.py` | NEW — 10 unit tests | +240 |
| `scripts/cleanup_empty_clusters.py` | NEW | +40 |
| `scripts/tune_clustering.py` | NEW | +180 |
| `scripts/dryrun_claim_matching.py` | NEW | +90 |
| `scripts/test_gemma.py` | NEW | +45 |

## UNRESOLVED

- **T5d article IDs:** Tuning harness uses synthetic article ID ranges — need real IDs substituted before running. The script is structurally complete.
- **Gemma:** Not available on this Fireworks account. Phase 3 Gemma integration is blocked until account is upgraded or alternative found.
- **T5c cleanup:** Script exists but not yet executed against production DB. Safe to run (idempotent DELETE WHERE id NOT IN).
