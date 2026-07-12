# Narrative Nexus — STATUS

**Last updated:** 2026-07-11
**Phase:** AMD-AV1 — Assumption Validation for "AMD evidence artifact" plan. Verified 12 items against codebase + demo.db. Key findings: (1) adding local-GPU BGE via providers.json entry + _LOCAL_PROVIDERS works for EmbeddingClient, but vertical_classifier.py hardcodes all-MiniLM-L6-v2 separately; (2) R_frame backfill is NOT complete (855/13,653 snapshots, 6.3%); (3) LLM client is chat-only — Gemma 4 E4B needs /completions endpoint (no fallback exists); (4) existing Gemma evidence ran on NVIDIA H200, not AMD; (5) embeddings PK is article_id only — pipeline re-run would overwrite cached vectors. All findings at docs/implementation-rounds/025-amd-av1.md. FP: 378/10/358/17/13653.
**Phase:** PIPE-1 — Config-driven provider resolution. Two hardcoded dicts (PROVIDER_BASE_URLS, _EMBEDDING_BASE_URLS) in llm_client.py/embedding_client.py blocked new provider IDs. Fix: each provider entry in config/providers.json now carries base_url + api_key_env. LLMClient/EmbeddingClient/runner.py read from provider dict, fall back to hardcoded maps. 6 new tests (TDD red→green), 0 regressions. 10 LLM entries in Pipeline dropdown (7 Fireworks + opencode + deepseek + openai). Default agent2_llm stays fireworks (deepseek-v4-pro). Gemma removed from functional dropdown; evidence folder intact. FP: 378/10/358/17/13653.
**Phase:** PIPE-1-FIX — Golden DB isolation in test suite. app/test_routes.py client fixture copied demo.db to tmp_path, sets NN_DB_PATH. Full pytest suite no longer touches golden DB. Verified: fingerprint unchanged before/after suite run; no git checkout needed. FP: 378/10/358/17/13653.
**Phase:** SE-COUNT — Venezuela silent edits count fixed. Cluster report endpoint (app/main.py:562) used COUNT(*) on silent_edits INNER JOIN claims — double-counted when an article had multiple claims. Fixed to COUNT(DISTINCT se.id). Cluster 924: was 10, now 5. Same fix applied to corrections COUNT. Script docs (video/pdf) still have hardcoded "10" — reported, not fixed. FP: 378/10/358/17/13653.
**Phase:** FE-CACHE — Fresh-clone confirmation. HTML routes serve no-store. Hashed assets confirmed. Clean build from scratch serves current code. No build artifacts tracked in git. FP: 378/10/358/17/13653.
**Phase:** UXnn — Cluster Report pending-claim grouping. Pending claims grouped by source set, group headers with counter. Multi-source groups sorted first. bbc.com: 17 claims → single header row. Absorbed claims untouched. Build + test suite unchanged. FP: 378/10/358/17/13653.

**Demo DB:** `data/demo/demo.db` (absolute: `/project/narrative-nexus/data/demo/demo.db`)
**Dev server:** `NN_DB_PATH=data/demo/demo.db uvicorn app.main:app --host 0.0.0.0 --port 3015` (port range 3000–3019 forwarded to host; bind 0.0.0.0 required)
**Fingerprint:** 378 claims / 10 absorbed / 358 articles / 17 clusters / 13,653 snapshots, span 2026-03-03 → 2026-07-03
**AI-summary bodies:** articles 940-945 bodies are Firecrawl AI summaries, not raw text — accepted limitation per human decision.
**Backups:** `data/demo/backups/` (git-ignored)

## Pending Changes (uncommitted)

All work from PIPE-1 through UXnn is uncommitted:

| Round | Files changed |
|-------|--------------|
| PIPE-1 | `pipeline/llm_client.py`, `pipeline/embedding_client.py`, `pipeline/runner.py`, `config/providers.json`, `pipeline/test_llm_client.py`, `pipeline/test_embedding_client.py` |
| PIPE-1-FIX | `app/test_routes.py` |
| FE-CACHE | (no code changes — confirmatory only) |
| SE-COUNT | `app/main.py` (lines 562, 568) |
| Label cleanup | `config/providers.json`, `src/pages/PipelineFlow.tsx` |
| Gemma removal | `config/providers.json`, `README.md` |
| UXnn | `src/pages/ClusterReport.tsx` |

## Provider State (post PIPE-1)

- 9 LLM entries in config: fireworks (deepseek-v4-pro, default), fireworks-glm-5p1, fireworks-glm-5p2, fireworks-gpt-oss, fireworks-kimi-k2p5, fireworks-kimi-k2p6, opencode, deepseek, openai
- Gemma removed from functional list; evidence at docs/evidence/gemma/ intact
- Dropdown labels: Fireworks AI — Model Name (account slug hidden)
- AMD badge: red FIREWORKS API pill still renders independently
- README Gemma section: past-tense, evidence-framed, no config/dropdown claim

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

## Accepted Limitations

- **Nomic claim matching + BGE-calibrated threshold:** Demo corpus claim matching ran nomic-embed-text-v1.5 while sim=0.85 remained calibrated in BGE space. Output human-verified; no rebuild.
- **Stories page hardcodes 2 cluster IDs:** `CLUSTER_IDS = [966, 924]`. Post-v1: dynamic API endpoint.
- **Investigate extraction fails in uvicorn, works in direct Python:** Fireworks returns 500 on extraction calls from uvicorn-served endpoints. Search/Fetch/Embed stages all work.

## Design Law

1. **Don't make the user think. Explicit beats elegant.**
2. **FONT FLOOR:** No rendered text below 12px (0.75rem) app-wide.
3. **CONTRAST FLOOR:** All text meets WCAG AA — 4.5:1 in both themes.

## Process Rules

- **Design work is propose-first.** No visual implementation without approved mockup.
- **NEVER start the scraper against data/demo/demo.db.** Golden DB is READ-ONLY.
- **NEVER set NN_ENABLE_PIPELINE.** Pipeline scheduler is off by default.
- **NO git add/commit/push** — human handles all commits.
- **Results doc after every round.** Evidence or void.

## Test Suite Baseline

pytest: 292 passed, 20 failed (pre-existing)
vitest: 112 passed, 21 failed, 4 skipped (pre-existing)
npm run build: passes
demo.db fingerprint: 378|10|358|17|13653
