# Narrative Nexus — Remaining Work

Verified against actual code, database, and pipeline paths as of 2026-06-30.
Each item includes the evidence trail: what exists, what's missing, and why.

**Note (2026-07-03):** Phase 2, Track A, and Track B recon complete. See docs/06- through docs/22- for full history. Track B Recon-5 identified Kimi-K2P5 as the best extraction model (1.8s per call vs 36s for DeepSeek-V4-Pro). If live Investigate is built, `providers.json` agent2_llm model may need switching from `accounts/fireworks/models/deepseek-v4-pro` to `accounts/fireworks/models/kimi-k2p5` — but hold pending build decision. Do NOT change without testing extraction quality on the actual pipeline path first.

---

## TIER 1 — Unblocked, High Impact

### 1. Wire R_edit into snapshot computation ✅ DONE (2026-06-30)

**Impact:** The Silent Editor dimension (R_edit) on the Source Profile radar chart now shows live values for all 37 sources. Agent 4 runs and produces real data — this was the last missing link in the chain.

**What was done:**
- Added `compute_r_edit_raw()` to `pipeline/snapshots.py` (edits/articles ratio per source, as_of filter)
- Wired into `_compute_and_write_snapshots` in `pipeline/runner.py` (compute → percentile rank → write)
- Fixed zero-article edge case: iterate `list_sources()` not `article_counts`
- +3 tests: zero-article, as_of filter, end-to-end (30 pytest total for snapshots/reputation/archetype)
- Live DB: 37/37 non-NULL r_edit, 0–100 range, values match edit counts
- Radar: 3→4 live dimensions (triangle → quadrilateral)

**Evidence trail:**
| Layer | Status | File |
|---|---|---|
| Agent 4 Silent Auditor | Runs, writes 89 rows | `pipeline/agent4_silent.py` |
| `compute_r_edit_raw()` | Computes edit rate | `pipeline/snapshots.py:159` |
| Snapshot computation | Wires r_edit → percentile → write | `pipeline/runner.py:173,181,206` |
| `silent_edits` table | 89 rows, live data | `data/nn.db` |
| API endpoint serves per-source edits | `/api/source/{id}` returns edits array | `app/main.py:182-192` |
| Frontend renders silent edit log | Table in SourceProfile | `src/pages/SourceProfile.tsx:344-366` |
| Snapshot r_edit | 37/37 non-NULL (was all NULL) | `data/nn.db` snapshots |

---

## TIER 2 — Blocked, Needs Design Decision

### 2. R_frame — Framing Consistency (data collected, wiring pending)

**Status:** Three framing scorers built (LLM, lexical, sentiment). Lexical + sentiment scored for all 2,028 articles. LLM backfill partial — 433/2028 (21%) scored before OpenCode Zen free-tier rate limits. Remaining 1,595 need retry with paid provider or rate-limit reset.

**What exists:**
- `pipeline/framing.py` — 3 scorers: `score_llm_prompt()`, `score_lexical()`, `score_sentiment()`
- `article_framing` table with llm_score, lexical_score, sentiment_score columns
- Agent 2 integrated: framing scores computed alongside claim extraction (zero extra API calls)
- Backfill: `scripts/backfill_framing.py --llm-only` for remaining articles
- Snapshot wiring NOT YET DONE — needs `compute_r_frame_raw()` to compute variance per source

**Evidence trail:**
| Layer | Status | File |
|---|---|---|
| Lexical scorer | 2,028/2,028 scored | `pipeline/framing.py:score_lexical()` |
| Sentiment scorer | 2,028/2,028 scored | `pipeline/framing.py:score_sentiment()` |
| LLM scorer | 433/2,028 scored | `pipeline/framing.py:score_llm_prompt()` |
| Agent 2 integration | Combined prompt | `pipeline/agent2_forensic.py:27-56` |
| DB storage | article_framing table | `db/framing.py` |
| Backfill script | With retry logic | `scripts/backfill_framing.py` |

### 3. R_correct — Formal Correction Rate ✅ DONE (2026-06-30)

Implemented inline marker detection for formal corrections. 16 corrections detected across 2,028 articles (AP, CNN, NYT patterns). Wired into daily snapshot computation alongside existing dimensions.

**What was done:**
- `pipeline/corrections.py` — 5 regex patterns + false positive guard
- `corrections` table with detected_pattern and matched_text
- `compute_r_correct_raw()` in `pipeline/snapshots.py`
- Wired into `runner.py` snapshot computation
- Backfill: `scripts/backfill_corrections.py`
- +15 tests
- Future C+D options in README

**Evidence trail:**
| Layer | Status | File |
|---|---|---|
| Detection patterns | 5 patterns (AP, CNN, NYT) | `pipeline/corrections.py` |
| DB storage | corrections table | `db/corrections.py` |
| Snapshot computation | corr/articles ratio | `pipeline/snapshots.py:compute_r_correct_raw()` |
| Runner wiring | percentile rank + write | `pipeline/runner.py:174,183,209` |
| Backfill script | 16 detected | `scripts/backfill_corrections.py` |

### 4. Multi-vertical classification (Economics, Technology) ✅ DONE (2026-06-30)

Implemented embedding-proximity vertical classifier in `pipeline/vertical_classifier.py`. Agent 1 now classifies each cluster by majority vote of article embeddings against rich prototype descriptions. Runner snapshot loop uses `get_vertical_list()` instead of hardcoded `["geopolitics"]`. All classification logic in one place — edit `VERTICAL_PROTOTYPES` to tune.

**What was done:**
- `pipeline/vertical_classifier.py` (120 lines) — single module with prototypes + `classify_text()` + `classify_cluster()` + `get_vertical_list()`
- Agent 1: `classify_cluster()` replaces hardcoded `"geopolitics"` for both noise and non-noise clusters
- Runner: `get_vertical_list()` replaces `["geopolitics"]` in snapshot loop
- +13 unit tests, 9/10 accuracy on benchmark articles
- See `docs/plan/slice-020-multi-vertical.md` (plan doc, if created)

**Evidence trail:**
| Layer | Status | File |
|---|---|---|
| Classifier module | Embedding proximity to prototypes | `pipeline/vertical_classifier.py` |
| Agent 1 integration | classify_cluster + classify_text | `pipeline/agent1_intake.py:110-138` |
| Runner integration | get_vertical_list() | `pipeline/runner.py:196` |
| Tests | 13 unit tests | `pipeline/test_vertical_classifier.py` |

---

## TIER 3 — Low Priority / Cleanup

### 5. CLAUDE.md says "7 design-doc pages" — should be 8 ✅ DONE

`CLAUDE.md` updated to "All 8 design-doc pages implemented" in Slice 018 commit.

### 6. Missing test files for ClusterReport and Timeline pages ✅ DONE (2026-06-30)

Added `src/__tests__/cluster-report.test.tsx` (8 tests) and `src/__tests__/timeline.test.tsx` (12 tests). All 11 pages now have frontend tests. See `docs/plan/slice-019-frontend-tests.md`.

### 7. Frontend handles NULL dimensions correctly but radar looks incomplete

`src/pages/SourceProfile.tsx` renders "—" for null dimensions and skips them in the radar chart. This is correct per design doc ("Nullable fields handled gracefully"). With 4 of 6 dimensions live (R_orig, R_val, R_speed, R_edit), the radar shows a quadrilateral. Full hexagon needs R_frame + R_correct (items 2+3).

### 8. `openai` import blocks ~30 pytest — make lazy ❌ STALE (2026-06-30)

`openai` IS installed system-wide at `/usr/local/lib/python3.11/dist-packages/openai/`. All 6 "blocked" test files collect and pass (51 tests). No `.venv/` exists — system python3 is used directly. No action needed. Doc was wrong.

### 9. `pipeline/reputation.py` — 6 pure functions, zero production callers ✅ DONE (2026-06-30)

### 10. Onboarding/startup modal fontsize too small

Source Profile page startup modal text is too small. Needs larger font size for readability. Check `src/pages/SourceProfile.tsx` startup modal styles.

Deleted `pipeline/reputation.py` and `pipeline/test_reputation.py` (114 lines total). The actual snapshot computation uses `*_raw()` variants in `pipeline/snapshots.py`. No production callers lost. No test coverage gap — snapshots.py functions are tested via `test_snapshots.py`.

---

## Summary

| # | Task | Blocked? | Impact | Est. Effort |
|---|---|---|---|---|
| 1 | Wire R_edit into snapshot computation | ✅ Done | High — 4th radar dimension live | ~30 lines |
| 2 | R_frame — build framing consistency agent | Partially done | Medium | Scorers built, LLM backfill rate-limited |
| 3 | R_correct — build correction detection | ✅ Done | Medium | 16 detected, wired into snapshots |
| 4 | Multi-vertical classification | ✅ Done | High — embedding-proximity classifier | 120 lines |
| 5 | Fix CLAUDE.md page count | ✅ Done | Trivial | 1 line |
| 6 | Add ClusterReport + Timeline tests | ✅ Done | Low | +20 tests |
| 7 | Radar hexagon completeness | R_frame wiring pending | Visual only | 1 dimension left |
| 8 | Lazy-load openai import | ❌ Stale — openai already installed | N/A | N/A |
| 9 | reputation.py dead code | ✅ Done | Low | Delete 114 lines |
|| 10 | Startup modal fontsize too small | UI fix — font size in SourceProfile.tsx | Low | CSS tweak |
|| 11 | Biome lint cleanup | ✅ Done | 12 → 0 errors via biome.json + 1 aria fix | 2 files |
|| 12 | Sources page scatter affordances | ✅ Done | Axis explanations, legend, tooltip, a11y, Math.round() | 3 files |
|| 13 | Full Ledger table polish | ✅ Done | Dim definitions, pending indicators, Math.round() | 1 file |
|| 14 | Percentile rank rounding | ✅ Done | round() in snapshots.py + DB backfill | 1 file |
