# Narrative Nexus — Remaining Work

Verified against actual code, database, and pipeline paths as of 2026-06-30.
Each item includes the evidence trail: what exists, what's missing, and why.

---

## TIER 1 — Unblocked, High Impact

### 1. Wire R_edit into snapshot computation

**Impact:** The Silent Editor dimension (R_edit) on the Source Profile radar chart shows "—" for every source even though Agent 4 runs and produces real data. This is a live demo feature that's wired end-to-end except for one missing function call.

**Evidence trail:**
| Layer | Status | File |
|---|---|---|
| Agent 4 Silent Auditor | Runs, writes 89 rows | `pipeline/agent4_silent.py` |
| `compute_r_edit()` function | Exists, tested | `pipeline/reputation.py:39` |
| `silent_edits` table | 89 rows, live data | `data/nn.db` |
| API endpoint serves per-source edits | `/api/source/{id}` returns edits array | `app/main.py:182-192` |
| Frontend renders silent edit log | Table in SourceProfile | `src/pages/SourceProfile.tsx:344-366` |
| **Snapshot computation** | **Never passes r_edit — all NULL** | `pipeline/runner.py:194-203` |

**Root cause:** `_compute_and_write_snapshots` at `pipeline/runner.py:194-203` calls `write_daily_snapshots()` without passing `r_edit` (or `r_frame`, `r_correct`). The params default to `None`, which become `{}`, so `.get(sid)` returns `None` → stored as NULL.

**Fix:** Add an `r_edit` computation in `_compute_and_write_snapshots` that JOINs `silent_edits` → `articles` → `source_id`, counts edits per source, divides by article count, percentile-ranks it, and passes to `write_daily_snapshots`. Same pattern as `r_orig`/`r_val`/`r_speed`.

**Estimated effort:** ~20 lines of SQL + plumbing. One function, no new files.

**DB query needed:**
```sql
SELECT a.source_id, COUNT(se.id) as edit_count
FROM silent_edits se
JOIN articles a ON a.id = se.article_id
GROUP BY a.source_id
```

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

### 5. CLAUDE.md says "7 design-doc pages" — should be 8

`CLAUDE.md:19`: "All 7 design-doc pages implemented." Actually 8 pages: Sources, SourceProfile, ClusterReport, Timeline, PipelineFlow, Investigate, Panel, Settings. All are routed in `src/App.tsx`.

### 6. Missing test files for ClusterReport and Timeline pages

All other pages have test files under `src/__tests__/`:
- `sources-page.test.tsx`
- `source-profile.test.tsx`
- `pipeline-flow.test.tsx`
- `investigate.test.tsx`
- `settings-page.test.tsx`
- `panel-page.test.tsx`
- `router-shell.test.tsx`
- `onboarding.test.tsx`
- `not-found.test.tsx`

No `cluster-report.test.tsx` or `timeline.test.tsx` exist. Both pages were Slice 016 and 017 — last two slices, possibly rushed for hackathon demo readiness.

### 7. Frontend handles NULL dimensions correctly but radar looks incomplete

`src/pages/SourceProfile.tsx` renders "—" for null dimensions and skips them in the radar chart. This is correct per design doc ("Nullable fields handled gracefully"). However, with only 3 of 6 dimensions live, the radar chart shows a triangle instead of a hexagon. R_edit wiring (item 1) would make it a quadrilateral. Full hexagon needs R_frame + R_correct (items 2+3).

---

## Summary

| # | Task | Blocked? | Impact | Est. Effort |
|---|---|---|---|---|
| 1 | Wire R_edit into snapshot computation | No | High — 4th radar dimension goes live | ~20 lines |
| 2 | R_frame — build framing consistency agent | Yes — needs design | Medium | Unknown |
| 3 | R_correct — build correction detection | Yes — needs design | Medium | Unknown |
| 4 | Multi-vertical classification | Yes — needs design | High — 2 of 3 verticals dead | Unknown |
| 5 | Fix CLAUDE.md page count | No | Trivial | 1 line |
| 6 | Add ClusterReport + Timeline tests | No | Low | ~100 lines each |
| 7 | Radar hexagon completeness | Depends on 1-3 | Visual only | Inherited |
