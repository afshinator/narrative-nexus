# Narrative Nexus — STATUS

**Last updated:** 2026-07-08 (post-DOCKER-READONLY)
**Phase:** DOCKER-READONLY — RUN touch /app/.readonly baked into Dockerfile.app (line 61). Path verified: _is_readonly() resolves to /app/.readonly. No ENV counterpart in compose — sentinel is sole guard. Submitted image now ships read-only-guarded by default.
**Phase:** PORT-CONFIRM — Submission container audit: app publishes :8000, judge URL http://localhost:8000. FLAGGED: .readonly sentinel does NOT ship in Dockerfile.app — deployed instance has unguarded scraper. Fix: add COPY .readonly or RUN touch to Dockerfile.app.
**Phase:** UX28-FIX — Scraper button visibly disabled in readonly mode (gray, not-allowed, "Scraper (paused)" label). Normal path unchanged. FP: 378/10/358/17/13653.
**Phase:** UX28 — P1: claim_matching nomic pill removed from legend (filtered out). P2: scraper captions removed (guard intact). P3: deferred — scraper controls → Settings page later. FP: 378/10/358/17/13653.
**Phase:** FC-99 — Video script fact-check: all stages ran Fireworks (DeepSeek never executed), Panel functional client-side, OnboardingDialog 6-term glossary active, stage labels verified, 37 sources T1=5/T2=8/T3=17/T4=4/T5=3. FP: 378/10/358/17/13653.
**Phase:** UX27 — 924 timeline link SUPPRESSED (emptyDateCount=145, 62% incomplete). Gate: require distinctDays>1 AND zero empty dates. 966 link shows.
**Phase:** UX26 — 924 timeline suppressed (link hidden, single-day guard), 966 timeline verified 48-day span, 924 counts reconciled (138/20/233/88/6d). Violation #27 logged.
**Phase:** UX25 — Nav restructure (cluster names removed, demo stories block on Sources), cluster 924 title, timeline View-link, nomic limitation recorded in Accepted Limitations. FP: 378/10/358/17/13653.
**Phase:** UX24-K5 — Cluster 924 defects: absorption strip was hardcoded from 966 (fixed dynamic), pending sum double-counted (fixed DISTINCT), source count reconciled (20, not 18). FP: 378/10/358/17/13653.
**Phase:** UX24 — K1: nomic label confirmed correct (claim matching, not article clustering). K2: cluster 924 named + nav links added. K3: narrative description lines on cluster/timeline pages. K4: scraper caption operator clause. FP: 378/10/358/17/13653.
**Phase:** R-DB2 — Clean server restart + guard verified. .readonly sentinel file bypasses uvicorn env-var-loss bug. Server on :3019: scraper start returns 403, status shows readonly:true. Golden fingerprint 378/10/358/17/13653 confirmed.
**Demo DB:** `data/demo/demo.db` (absolute: `/project/narrative-nexus/data/demo/demo.db`)
**Dev server:** `NN_DB_PATH=data/demo/demo.db uvicorn app.main:app --host 0.0.0.0 --port 3015 --reload` (port range 3000–3019 forwarded to host; bind 0.0.0.0 required)
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
- UX3: Regression fixes — nav restore (Sources/Cluster/Timeline/Settings), ClusterReport absorbed-count fix (COUNT DISTINCT), hardcoded archetype-switch routes updated, Coverage lens panel grid restored. See `docs/implementation-rounds/66-ux3-regression-fixes.md`.
- UX5: Sources page subtract — removed Coverage-Only Panel from Sources, adjusted vertical-pill check for scopes, 3 tests updated for static content. See `docs/implementation-rounds/69-ux5-sources-subtract.md`.
- UX6-8: Nav integrity, cluster/timeline presentation, first_seen_at backfill + pipeline guard. Commit 5f18c3e.
- UX9: Tooltip kill-switch — removed 7 tooltips from Sources page per design-direction change. See `docs/implementation-rounds/73-ux9-kill-tooltips.md`.
- UX10-DIAG: Source Profile time-machine diagnostic (read-only). See `docs/implementation-rounds/74-ux10-diag-time-machine.md`.
- UX11: Profile recenter pass. See `docs/implementation-rounds/75-ux11-profile-recenter.md`.
- UX12: Legibility captions, chart color fixes (Chart.js CSS var → hex resolution). See `docs/implementation-rounds/76-ux12-legibility-captions.md`, `78-ux12-fix2.md`, `79-ux12-fix3.md`.
- UX13: Meaning layer on Source Profile — percentile explainer, plain-language stat labels, radar/shape metaphor, PENDING mechanism, VfTrend relativity annotation. Commit cd87056.
- DV1: Design doc refresh v1.2→v1.3 — 5 corrections (default provider Fireworks, locked pipeline params, R-score status, nav/onboarding, source panel 20→37). See `docs/design-v1.3.md`. Same session that produced faq-demo-goal.md.
- DOC-SYNC: FAQ truth-sync — both FAQ files rewritten against demo.db numbers (378/10/358/17/13,653), honest pipeline capacity description for curated verification corpus. Dev server command documented in header.
- DOC-SYNC-FU: Attribution fix — absorbed-per-source table corrected from articles.source_id to claim_sources.source_id (6 sources → 24 sources reporting absorbed claims). Cluster name audit confirmed only 966 rendered on judge pages. Orphaned files (design-v1.3.md, faq-demo-goal.md) bookkept. See `docs/design-v1.3.md`, `docs/faq-demo-goal.md`.
- UX14: Profile trims + Sources click affordance. VfTrendChart unmounted (Validation over time card — percentile-rank noise). SparklineGrid cut (30-day sparklines chart panel data-density, not source behavior). Scatter tooltip gets "Click to view profile →" hint + "Click any source dot" subtitle. Leaderboard source names styled as links (navy + hover underline). See `docs/implementation-rounds/82-ux14-cut-invite.md`.
- UX15: Title blocks on Source Profile, Cluster Report, Timeline. Kicker + h1 + description on all three. Tier names from design-v1.2 §5 (Wire/Consensus Anchor, etc.) not bare numbers. Two-tier stat panel (hero row Origination/Validation, secondary Speed/Framing, dead dims collapsed). No DB changes. See `docs/implementation-rounds/83-ux15-cosmetics.md`.
- UX16: Archetype boundary diagnosis — read-only. Code is correct (pipeline/archetype.py:4-19). User's reported median 27/26 used all 37 sources; correct median is 52/48 from 26 graded sources (pipeline/snapshots.py:297-298 filters to active_ids). All 26 graded sources match §4 rule. Zero mismatches. No fixes applied.
- UX17: Sources page inventory — read-only. 26 elements across 9 sections (intro strip, header, landing copy, vertical label, lens toggle, consensus lens content, coverage lens content, full ledger table, layout container). Tooltips absent (removed UX9). Coverage Panel absent (removed UX5). Click affordances present (UX14). See `docs/implementation-rounds/85-ux17-recon.md`.
- UX18: Font floor + contrast floor + Sources subtract/hierarchy. Design laws recorded in STATUS.md. Token fixes: text-dim #717a68→#606b5f (light 3.91→4.86), #738567→#858f7b (dark 4.43→5.22), slate #5c6b5a→#556453 (4.33→4.80). App-wide font floor: all text-[.66/.68/.65/.62/.6]→0.75rem (9 files, ~30 sites). Sources: deleted landing copy, duplicate shape legend, X/Y axis block. Propaganda/Fringe→Contrarian. Chart subtitle + click CTA added. Page subtitle shortened. No DB writes. See `docs/implementation-rounds/86-ux18-font-contrast.md`.
- UX19: CTA regression fix — B5 CTA was never written (patch failure, undetected YES-on-failed-bound). Two affordances added: "Hover any dot for details — click to open that outlet's profile →" under chart subtitle, and "Click a source row to open its profile" in Full Ledger intro. design-tokens.md synced. Violation #24 logged. See `docs/implementation-rounds/87-ux19-cta-fix.md`.

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

- recluster_all vs P4 cluster-count discrepancy: RESOLVED... (see above).
- O7 claim-less articles: CORRECTED... 

## Accepted Limitations (human — standing, UX25)

- **Nomic claim matching + BGE-calibrated threshold:** Demo corpus claim matching ran nomic-embed-text-v1.5 (F5-REDO commit 2b3b1df changed provider BGE→nomic) while sim=0.85 remained calibrated in BGE space. Threshold uncalibrated for the model that used it. Output human-verified (P8-PRE autopsies; clusters 966/924 eyeballed); no rebuild. Recalibration is post-hackathon work.

## Next Action

UX2 committed (2b6bafb): intro strip, 7 tooltips, tier legend rewrite. Vitest: 13 failures (11 router-shell pre-existing + 1 schema/better-sqlite3 stale + 1 docker/D2 volume). POC server killed. Next: human reviews rendered copy.

## Design Law (human — standing, UX18)

1. **Don't make the user think. Explicit beats elegant.** Cold visitor understands the chart and knows to click in 10 sec.
2. **FONT FLOOR:** No rendered text below 12px (0.75rem) app-wide. Sole exception: chart-internal SVG/canvas labels where geometry forces it.
3. **CONTRAST FLOOR:** All text meets WCAG AA — 4.5:1 against its actual background (3:1 permitted only for text >= 18.66px bold or >= 24px regular). Applies in BOTH themes. Non-text UI (borders on interactive elements, chart marks) >= 3:1.

Laws 2 and 3 SUPERSEDE design-tokens.md where they conflict.

## Process Rule (human — standing, UX20)

**Design work is propose-first.** No visual implementation without an approved mockup. All styling changes must follow: mockup → human review → approval → implement. Violating this = unordered work.

**NN_READONLY=1 is standing default** for all dev and hosted servers. The scraper Start button mutates the golden demo DB — it is a destructive action, not a UI toy. Rounds needing scraper writes must state that explicitly and run against a scratch DB, never `data/demo/demo.db`.

**Deferred (UX28):** Scraper start/stop control to be relocated to Settings page in a future session. Currently: endpoints exist, guarded read-only via `.readonly` sentinel, no special caption on Pipeline page — scraper controls are Start/Stop button (always visible, guarded by 403 if sentinel present).

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
| 23 | Evidence computed by method the code doesn't use; presented as system state | UX16-precursor query computed panel medians (27/26) over all 37 snapshot rows including 11 ungraded zero-rows, contradicting the code's active_ids-filtered medians (52/48, per snapshots.py:297-298). Triggered an unnecessary diagnosis round — the code was never wrong. Pattern: deriving evidence with a non-matching computation and presenting it as the system's actual output. |
| 24 | YES-on-failed-bound: B5 CTA marked YES, never rendered | UX18 B5 compliance table row marked YES — "Click any dot to open that outlet's profile →" CTA. Patch tool failed with "Found 3 matches" error, never retried. Code was never added to Sources.tsx. Human browser confirms zero click affordance on Sources page. The B5 evidence was a summary claim, not a pasted working diff. |
| 25 | Partial-fix reported complete: y-axis padding under-sized | UX20-A1 claimed both x and y D3 scale ranges padded for edge clipping. Only x-axis fixes were visible in browser (guardian at orig=100 OK). Dots at y-extremes (washingtonpost r_val=100, reuters/economist/tehrantimes r_val=0) still clipped. Root cause: PAD=8 insufficient for D3 symbol.size(120) marks — diamond symbol half-diagonal is ~11px. PAD raised to 14px in UX21. |
| 26 | YES-on-failed-bound + demo DB contamination — unguarded destructive action (design flaw) | UX23 round doc marked "DB untouched: YES" while fingerprinting 2,143 articles (was 358). +1,785 articles scraped. Root cause: human pressed Start on Pipeline page expecting UI animation — the Start/Stop button is a destructive action (mutates golden demo DB) presented as a benign play control. Design flaw: no guard, no confirmation, no readonly default. Fix: NN_READONLY=1 guard (UX23) now standing default for all dev/hosted servers. Rounds needing scraper writes must state explicitly and run against scratch DB, never data/demo/demo.db. See R-DB round.
| 27 | YES-on-failed-bound: UX25 L4 claimed "both timelines render: YES" while L4b evidence shows cluster 924 timeline collapses to 1 day (145/233 rows empty first_seen_at). Suppressed in UX26 per cut-not-caption rule — timeline link hidden when ≤1 distinct day of first_seen_at data. See UX26 diary. |
| 28 | Arithmetic error: summary count ≠ raw data count | SW1 summary claimed 14 font-floor violations / 9 Investigate-only. Raw grep output: 13 grep matches, 8 Investigate-only. The misplaced +1 came from double-counting Investigate.tsx:91's multi-hit line. Corrected in SW2 fix round. |

## Completed Work (recent)
