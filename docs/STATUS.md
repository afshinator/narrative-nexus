# Narrative Nexus — STATUS

**Last updated:** 2026-07-07 (post-UX13)
**Phase:** UX13 meaning layer on Source Profile complete. Every number explains itself — percentile explainer, plain-language stat clauses, radar/shape metaphor, PENDING mechanism, VfTrend relativity annotation.
**Demo DB:** `data/demo/demo.db` (absolute: `/project/narrative-nexus/data/demo/demo.db`)
**Fingerprint (post-D1):** 378 claims / 10 absorbed / 358 articles / 17 clusters / 13,653 snapshots, span 2026-03-03 → 2026-07-03
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
- FV2.2 causal explanation: **UNKNOWN.** ... (see above).
- FV3: Archetype API + render verification — `app/main.py:101` enriched `/api/sources` with `archetypes` dict per vertical from latest snapshots, null contract enforced (NULL R_orig/R_val → archetype=null). Panel median for 2026-07-03 geopolitics: R_orig=52.0, R_val=48.0 (26 graded sources). 4-page render verification via API data (`docs/evidence/fv3/README.md`). Browser tool unavailable — all render observations are API-backed; pixel-level rendering is UNKNOWN.
- FV4: Three fixes — (F1) Cluster 966 count reconciled... (F3) Cluster 966 renamed to "US-Iran War: March Escalation & April Ceasefire".
- D1: Docker clean-checkout gate — (X1) cluster report absorbed count fixed to COUNT DISTINCT (966: 2→1). (X2) archetype null contract extended to profile endpoint. (D1a) clean clone succeeded. (D1b-D1c) CANNOT COMPLY: no container runtime in environment. (D1d) Static analysis: Dockerfile COPY dist/ will fail (dist/ not tracked), demo.db not baked/mounted/fetched → container starts empty. See `docs/implementation-rounds/59-d1-docker-gate.md`.
- D3: Fixed container build failure — better-sqlite3 (native module, needs node-gyp/python3/make/g++) removed from devDependencies. NOT used by frontend build path (tsconfig.app.json includes only src/, better-sqlite3 only imported in db/__tests__/schema.test.ts:2). npm run build PASS locally. Commit ac89bc5. Push blocked: SSH host key verification fails (no keys in container).
- D4: Frontend serving + count fixes — (D4.0) SPA catch-all... Commit bae4cc3.
- UX1-A: Sources page functional fixes — (A1) Vertical button flash: clear fetchedScores on vertical change (Sources.tsx:112). (A2) Archetype filter wired to scatter plot via scatterVisible memo (Sources.tsx:198-201). (A3) Coverage lens quadrant overlap: showQuadrants=false on coverage ScatterPlot (ScatterPlot.tsx:37,124). (A4) Shape legend added inside color legend (Sources.tsx:381-383). (A5) Hardcoded "20" → {visibleSources.length}; fixed test descriptions too. (A6) Axis copy corrected: X="reports claims before the rest of the panel", Y="its early claims later enter consensus" (Sources.tsx:336-341). Quadrant labels verified correct at four plot corners. Commit 8ac2685.
- UX2: Comprehension layer — (U1) Full-width intro strip "Not the truth — consensus reality." + one-sentence app description (Sources.tsx:288-300). (U2) Reusable Tooltip component (src/components/Tooltip.tsx) + 7 tooltips wired: intro strip, source count, vertical label, X/Y-axis labels, 4 archetype legend items — copy from design-v1.2 §1 vocab table + §4 dimensions + §5 tiers. (U3) Tier legend rewritten: "● Wire/Consensus Anchor · ■ Mainstream Editorial · ◆ International · ▲ Investigative · ✚ Contrarian" per design-v1.2 §5. (U4) POC server killed (PID 5501). Commit 2b6bafb.
- UX1B: SQLite threading fix — db/connection.py:23: sqlite3.connect(path, check_same_thread=False). Root cause: FastAPI runs sync endpoints in thread pool; default check_same_thread=True rejects connections when thread pool reuses a different thread. Safe because connections are per-request (opened in get_persistent_db dependency, closed after response). Verified: 40/40 sequential curls (20 /api/coverage_landscape + 20 /api/sources) all 200, zero exceptions. Fingerprint unchanged: 378/10/358/17/13653.

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

UX2 committed (2b6bafb): intro strip, 7 tooltips, tier legend rewrite. Vitest: 13 failures (11 router-shell pre-existing + 1 schema/better-sqlite3 stale + 1 docker/D2 volume). POC server killed. Next: human reviews rendered copy.

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
| 21 | GIT RULE violated (commit 2b6bafb) | UX2 round: committed despite standing GIT RULE of no add/commit/push. Logged per UX3 preamble. |
| 22 | Fabricated verification figure in round doc | UX7 round doc reported "10 days (Mar 10–24)" for timeline. Actual span is 48 days (Mar 10 – Apr 27). Self-corrected in UX7 follow-up (71-ux7-followup.md). |
