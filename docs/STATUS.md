# Narrative Nexus — STATUS

**Last updated:** 2026-07-04
**Phase:** Gate reconnaissance. Live-DB run NOT yet authorized.
**Demo DB:** `data/demo/demo.db` (absolute: `/project/narrative-nexus/data/demo/demo.db`)
**Fingerprint:** 327 claims / 8 absorbed / 352 articles / 15 clusters / 10,545 snapshots, span 2026-04-01 → 2026-07-04 (corrected — prior 79-day claim was internally inconsistent; 10,545 = 111 × 95)
**Backups:** `data/demo/backups/` (git-ignored)

## Locked Parameters

| Parameter | Value | Rationale | Set in |
|-----------|-------|-----------|--------|
| eps (DBSCAN) | 0.35 | 4/6 groups merged, 1 over-merge | P1 sweep |
| min_samples | 2 | Higher values reduce multi-source clusters with no gain | P1 sweep |
| sim_threshold (claim matching) | 0.85 | 0.80 introduces factually wrong merges | P2 A/B |
| MAX_CLUSTER_SIZE (blob guard) | 60 | Prevents cross-story blobs | P4 |
| EPS_FLOOR | 0.25 | Recursive split floor | P4 |
| MIN_CORROBORATION | 2 | Single-source claims must NOT self-validate | Phase 2 T1 |
| D1 (absorption rule) | >=2 distinct T1/T2 pool sources AND pct >= vertical threshold | resolution.py:27-33, agent3_consensus.py:70-73 | Phase 2 T3 |
| D2 (R_val window) | Exclude claims within 7 days of as_of | snapshots.py:63-66 | Phase 2 T4 |
| time_window (DBSCAN) | 14 days | Time-bounded clustering window | agent1_intake.py |
| vertical thresholds | geo 65%, econ 75%, tech 75% | DEFAULT_THRESHOLDS in consensus.py | Phase 2 T5 |
| freeze file | nn-frozen-2026-07-05.db | ALL harvest reads from this frozen copy | R1.5 |

## Source Tier Reference

Per `SELECT id, name, tier FROM sources ORDER BY id`:

| Tier | Sources |
|------|---------|
| T1 | reuters(1), apnews(2), bbc(3), npr(4), theguardian(5) |
| T2 | foxnews(6), politico(7), economist(8), nytimes(9), washingtonpost(10), cnn(21), cbsnews(22), abcnews(23) |
| T3 | aljazeera(11), dw(12), NHK World(13), globaltimes(14), france24(15), batimes(24), straitstimes(25), thehindu(26), premiumtimesng(27), timesofisrael(28), vanguardngr(29), thereporterethiopia(30), namibian(31), punchng(32), jamaicaobserver(33), MercoPress(34), tehrantimes(35) |
| T4 | theintercept(16), propublica(17), bellingcat(18), africanarguments(36) |
| T5 | zerohedge(19), thegrayzone(20), sputnikglobe(37) |

## Completed Work

- Phase 0+1: Fireworks-first pipeline, claim matching, consensus fixes (commit a52ae2d)
- Track A: Sources Two-Lens (consensus + coverage lenses)
- Track B Phases 1-3B: SSE Investigate pipeline, threshold slider, persistence
- Recovery gates P0-P7: test fixes, param sweeps, blob-split guard, snapshot backfill, seed corpus prep
- P8-PRE: 3 absorbed claims autopsied on Copy B — see docs/evidence/p10/autopsy.md

## Blob-Split Tradeoff (FACTUAL)

Configurations actually run:

| Metric | Copy B (non-live, sim=0.80, NO split) | P4 (non-live, sim=0.85, WITH split) |
|--------|----------------------------------------|--------------------------------------|
| Clusters | 709 | 1,249 |
| Max cluster size | 1,093 | 94 |
| Multi-source clusters (>=2) | 26 | 101 |
| Absorbed claims | 3 | 0 |

CONFOUNDED: Copy B and P4 differ in BOTH blob-split AND sim_threshold. The 3→0 absorption drop cannot be attributed to either variable alone. P4 with sim=0.85 had far fewer merges (65 vs 1,626), reducing cross-source claims and thus absorption candidates.

## RESOLVED

- recluster_all vs P4 cluster-count discrepancy: RESOLVED. P1 sweep and P4 (max 94) ran on cached BGE vectors (F5-REDO baseline: embeddings table = 2,028 BGE). All true-nomic runs produced floor-limited mega-clusters (809 / 1,329 / 154). Locked params (eps=0.35, floor=0.25, sim=0.85) were calibrated in BGE space. Embedding model hereby locked to BAAI/bge-base-en-v1.5 on empirical grounds, superseding the nomic intent. "clustering:" prefix is nomic-specific and moot under BGE.
- O7 claim-less articles: CORRECTED. 28 articles without claims = 27 merge artifacts (all claims merged into canonicals) + 1 real extraction failure (article 290, now resolved). The 27 were NOT extraction failures.

## Next Action

R1.5 review complete — see `docs/implementation-rounds/50-r1.5-review-results.md`. Skeleton triage: 9 KEEP / 4 EXCLUDE, 8 ingested into demo.db (1 already present), demo.db now 352 articles. Liveblog replacement: AP static FOUND (`apnews.com/article/us-military-iran-war-82nd-airborne-4b4c30ebc807b323fbf35c4435a739f1`), BBC NOT COVERED (no static equivalent exists). A1 source pool: Reuters (T2), Guardian (T1), AP static (T1) — 3 pool sources, meets >=2. R2 (Firecrawl extraction of approved URLs + ingestion + recluster) pending human authorization.

## BANNED

| Category | Why |
|----------|-----|
| Sports stories (World Cup, etc.) | LOCKED exclusion — sports is not a tracked vertical |
| Non-panel sources (sites not in the 37-source panel) | Would not contribute to R scores |
| cloakbrowser / stealth browser | Not authorized. Firecrawl API only. |
| Paywall bypass | Not needed — Firecrawl extracts all major news sites |
| Live data/nn.db writes | Recon phase only. Writes to /tmp copies. |

## Prior Violations (for agents to reference)

| # | Violation | Example |
|---|-----------|---------|
| 1 | Substituting an easier proxy for an explicit instruction | Random claim pairs instead of 0.75-0.85 cosine band |
| 2 | Reporting ~estimates as exact | "~3,000 chars" instead of exact count |
| 3 | Testing non-panel sources | WSJ tested though not in 37-source panel |
| 4 | Proposing LOCKED exclusion as seed story | World Cup (sports) |
| 5 | Short-changing counts | Top/bottom 5 instead of 10 |
| 6 | Causal claim without controlled comparison | "Blob split causes fewer multi-source clusters" — disproven by data |
| 7 | Fabricating numbers from memory | "Copy B had 0 absorbed" — it had 3 |
| 8 | Fabricating a table column | STATUS.md had "With split Copy B" column for a configuration never run |
| 9 | Chunk double-counting / phantom completion claims | Doc 43 reported 1,023 claims from overlapping run logs; DB said 827 |
| 10 | Marking failed bounds as YES in compliance tables | Max cluster 80 > 60 marked YES/CANNOT COMPLY inconsistently |
| 11 | Memory-based numbers instead of query output | "1 remaining" article; DB query showed 28 body-bearing articles without claims |
| 12 | Unverified assumptions about which date field code uses | Assumed created_at = extraction date; actual code backdates to article published_at |
| 13 | Misattributing merge artifacts to extraction failure | Doc 44 O7.2: 27 claim-less articles were merge artifacts, not extraction failures |
| 14 | Post-verdict DB mutation left unreconciled | Cluster 900 "Temp 290" created by O7.2 retry, never cleaned up |
| 15 | Marking defective harvest as YES in compliance table | R1.2 (doc 49) marked YES with parenthetical "(defective skeleton)" — 5/13 articles were false positives, zero T1 after excluding 2457. The evidence describes failure; YES verdict is inconsistent. |
