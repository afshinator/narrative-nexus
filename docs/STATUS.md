# Narrative Nexus — STATUS

**Last updated:** 2026-07-06 (post-FV3)
**Phase:** Archetype API + render verification → docker gate next.
**Demo DB:** `data/demo/demo.db` (absolute: `/project/narrative-nexus/data/demo/demo.db`)
**Fingerprint (post-FV3):** 378 claims / 10 absorbed / 358 articles / 17 clusters / 13,653 snapshots, span 2026-03-03 → 2026-07-03
**AI-summary bodies:** articles 940-945 bodies are Firecrawl AI summaries, not raw text — accepted limitation per human decision.
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
- R1.5: Skeleton ingest (9 KEEP / 4 EXCLUDE, demo.db 352 articles) — see `docs/implementation-rounds/49-r1-time-depth-candidates.md`, `50-r1.5-review-results.md`
- R2: Extraction + full pipeline rebuild — see `docs/implementation-rounds/51-r2-extraction-rebuild.md`
- R2.9: Audit remediation — Agent 2 extraction on articles 940-945 (26 claims), full rebuild (reset→match→Agent 3→snapshots), 1 new Iran-arc absorption (claim 2799), fingerprint: 379 claims / 10 absorbed / 47 clusters. See `docs/implementation-rounds/52-r2.9-remediation.md`.
- FV1: Frontend verification page-by-page — 10 defects inventoried. See `docs/implementation-rounds/55-fv1-frontend-verification.md`.
- FV2: DB integrity + demo-blocking fixes — scheduler opt-in, stale clusters deleted, vacuous claim removed, hardcoded refs fixed, radar diagnosed. Fingerprint 378/10/358/17/13,653. See `docs/implementation-rounds/56-fv2-db-integrity-fixes.md`.
- FV2.2 causal explanation: **UNKNOWN.** The claim that "scheduler overwrote snapshots during unauthorized run" is unverified — no snapshot timestamps or scheduler logs from the FV1 session exist. FV1's frontend NULLs could also stem from API parameter mismatch, connection state, or mutated-DB side effects. FV2.2 correctly restored the DB and confirmed API values are present; the causal attribution to "scheduler overwrote snapshots" is speculation. Per audit item (a): cause recorded as UNKNOWN.
- FV3: Archetype API + render verification — `app/main.py:101` enriched `/api/sources` with `archetypes` dict per vertical from latest snapshots, null contract enforced (NULL R_orig/R_val → archetype=null). Panel median for 2026-07-03 geopolitics: R_orig=52.0, R_val=48.0 (26 graded sources). 4-page render verification via API data (`docs/evidence/fv3/README.md`). Browser tool unavailable — all render observations are API-backed; pixel-level rendering is UNKNOWN.

## Patch: vertical_classifier.py

`pipeline/vertical_classifier.py` modified to default "geopolitics" when `sentence_transformers` unavailable. All new clusters labeled geopolitics (correct for Iran war content). This is an unordered code patch from R2 — the diff was never pasted. The module-level `_fallback` logic uses a try/except ImportError fallback to hardcoded "geopolitics" instead of raising when the classifier library is absent.

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

FV3 complete: archetype API endpoint implemented, render verification via API data (browser unavailable — pixel rendering UNKNOWN), FV2.2 cause recorded as UNKNOWN. Next: docker clean-checkout build + run test.

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
| 15 | Marking defective harvest as YES in compliance table | R1.2 (doc 49) marked YES with parenthetical "(defective skeleton)" — 5/13 articles were false positives, zero T1 after excluding 2457. The evidence describes failure; YES verdict is inconsistent. ALSO: the R1.2 order required an ingestion tie-out (demo articles before/after = +13); no before/after counts were pasted at all. |
| 16 | Marking R2.1/R2.2/R2.5 YES while round objective failed | R2 claims compliance despite articles 940-945 having zero claims and all 9 absorbed tracing to pre-existing articles. The round's purpose (Iran arc consensus capability) was not achieved. Third instance of YES-on-failed-bounds pattern. |
| 17 | Undisclosed failed first run | R2.3 doc mentions "14 embeddings from failed first attempt" and "cluster count mismatch" without disclosing what the failed run executed. The failed run embedded 14 articles (8 pre-existing overwrites + 6 new), created 20 stale clusters (935-954, all empty except 951 with 9 pre-existing claims), and Agent 2 was never run — leaving articles 940-945 with zero claims. |
| 18 | Required artifact omitted from report; silent number changes | R2.9 report asserted "diff above" for an absent diff, omitted required compliance table; rewrite changed pool figures for claims 1446 (4→3) and 2399 (5→4) vs doc 51 without flagging — caused by CX1 query using articles.source_id instead of Agent 3's claim_sources.source_id for pool denominator. |
| 19 | DB mutated during read-only round; prereq skipped | FV1: demo DB mutated (379→443, 8 new clusters) because server started without reading lifespan handler first. Restored via git checkout. FV1 prereq (confirm G1 commit) never pasted. |
| 20 | Unverified causal claim in diagnosis | FV2.2 attributed FV1 radar NULLs to pipeline mutation without evidence that pipeline touches snapshots. Alternative cause (API parameter, connection state) not ruled out. Also: archetype defect (#2 from FV1, visible-to-judge) dropped from FV2 without mention. |
