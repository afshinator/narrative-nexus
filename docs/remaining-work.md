# Narrative Nexus — Remaining Work

Verified against actual code, database, and pipeline paths as of 2026-06-30.
Each item includes the evidence trail: what exists, what's missing, and why.

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

### 2. R_frame — Framing Consistency (no data source)

**Status:** `compute_r_frame()` exists in `pipeline/reputation.py:31` and is tested. But no agent produces framing scores per article. Design doc §3 defines 4 agents — none compute cross-article framing consistency. This needs a new computation or agent definition before any code can be written.

**What's needed:** A way to measure how consistently a source frames stories. Could be:
- Sentiment variance across articles from same source
- Lexical diversity / framing similarity metric
- LLM-based framing classification per article then compute stddev

**Blocked on:** Architecture decision. No REQ for how framing is measured — only REQ-035 says "must track R_frame" as `[desired]`.

### 3. R_correct — Formal Correction Rate (no mechanism)

**Status:** `compute_r_correct()` exists in `pipeline/reputation.py:46` and is tested. But nothing detects formal corrections. No table, no scraper logic, no agent.

**What's needed:** A way to detect when a source publishes a formal correction. Options:
- Parse RSS `<corrections>` or `<update>` tags
- Scrape source-specific corrections pages
- Detect "CORRECTION:" or "UPDATE:" inline markers in article body

**Blocked on:** Architecture decision. No REQ defines the detection mechanism — only REQ-037 says "must track R_correct" as `[desired]`.

### 4. Multi-vertical classification (Economics, Technology)

**Status:** Agent 1 hardcodes `vertical="geopolitics"` at `pipeline/agent1_intake.py:116,126`. Agent 2 also only processes geopolitics. All 4,499 clusters and all 44,363 snapshots are geopolitics-only.

**What exists:**
- REQ-055 (ECONOMICS) and REQ-056 (TECHNOLOGY) — tagged `[desired]`
- Design doc §5 defines three verticals
- Frontend `VerticalPills` component exists and renders multi-vertical pills
- `cluster.vertical` column supports any string
- Snapshots are written per-vertical (loop at `runner.py:193-194` only iterates `["geopolitics"]`)

**What's missing:** No vertical classification logic exists. Agent 1 would need to:
1. Classify article content into vertical(s) — keyword, embedding, or LLM-based
2. Assign clusters to appropriate verticals instead of always "geopolitics"
3. Snapshot loop needs the full vertical list

**Blocked on:** Classification approach decision + Agent 1/2 enhancement.

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

Deleted `pipeline/reputation.py` and `pipeline/test_reputation.py` (114 lines total). The actual snapshot computation uses `*_raw()` variants in `pipeline/snapshots.py`. No production callers lost. No test coverage gap — snapshots.py functions are tested via `test_snapshots.py`.

---

## Summary

| # | Task | Blocked? | Impact | Est. Effort |
|---|---|---|---|---|
| 1 | Wire R_edit into snapshot computation | ✅ Done | High — 4th radar dimension live | ~30 lines |
| 2 | R_frame — build framing consistency agent | Yes — needs design | Medium | Unknown |
| 3 | R_correct — build correction detection | Yes — needs design | Medium | Unknown |
| 4 | Multi-vertical classification | Yes — needs design | High — 2 of 3 verticals dead | Unknown |
| 5 | Fix CLAUDE.md page count | ✅ Done | Trivial | 1 line |
| 6 | Add ClusterReport + Timeline tests | ✅ Done | Low | +20 tests |
| 7 | Radar hexagon completeness | Depends on 2+3 | Visual only | Inherited |
| 8 | Lazy-load openai import | ❌ Stale — openai already installed | N/A | N/A |
| 9 | reputation.py dead code | ✅ Done | Low | Delete 114 lines |
