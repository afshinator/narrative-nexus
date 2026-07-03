# Phase 2 Post-T5 Reality Check — Code + DB Audit

**Date:** 2026-07-02
**DB:** data/nn.db — 13 absorbed, 1,138 clusters, 1,488 UNRESOLVED, 7,653 claims, 68 multi-source clusters, 8,475 snapshots with R_val

---

## R1 — RUNNING APP

| Check | Detail |
|-------|--------|
| R1a: Backend | FastAPI on `0.0.0.0:8000`, started via `python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000` |
| R1b: Frontend | Vite dev server on `0.0.0.0:5173`, proxies `/api` → `:8000` (`vite.config.ts:16`) |
| R1c: DB path | `data/nn.db` — `app/main.py:43`: `os.environ.get("NN_DB_PATH", "data/nn.db")`. Confirmed post-T5 state (13 absorbed) |
| R1d: Health | `{"status":"ok","version":"0.1.0"}` |

---

## PAGE-BY-PAGE RATINGS

| Page | Rating |
|------|--------|
| Sources home (/) | DEGRADED |
| Source Profile — HEALTHY (theguardian) | DEGRADED |
| Source Profile — ZERO-ABSORBED (aljazeera) | DEGRADED |
| Source Profile — TIER 5 (zerohedge) | HEALTHY |
| Cluster Report RICH (/cluster/5835) | DEGRADED |
| Timeline RICH (/timeline/5835) | HEALTHY |
| Timeline SPARSE (1-source cluster) | DEGRADED |
| Pipeline Flow (/pipeline) | HEALTHY |
| Investigate (/investigate) | EMBARRASSING |
| Panel Management (/panel) | HEALTHY |
| Settings (/settings) | HEALTHY |

---

### R2 — Sources Home (/, /sources)

**API:** `GET /api/scores?vertical=geopolitics`  
**Component:** `src/pages/Sources.tsx`

**Data shape expected:** Array of `{source_id, vertical, R_orig, R_val, ...}` per source.  
**Handling of nulls:** `Sources.tsx:132-133` — `R_orig: score?.R_orig ?? 0, R_val: score?.R_val ?? 0`. Null scores are coerced to (0,0) on both axes, indistinguishable from "genuinely zero."

**What it will show:** Only 3 of 37 sources have R_val > 0 (politico=100, abcnews=96, apnews=93). The remaining 34 sources cluster along y=0. The scatter plot will look like a flat line with 3 dots above it. The "Why are shapes at the bottom?" info panel (`Sources.tsx:332-339`) explains this is by design for Tiers 3-5, but Tier 1-2 sources with R_val=0 (BBC, theguardian, foxnews, cnn, reuters, npr, nytimes) contradict the copy's framing — these ARE mainstream outlets that "should" have non-zero validation but don't because their few absorbed claims are drowned in a sea of originated claims.

**Rating: DEGRADED** — the scatter plot renders correctly for the data but the visual is misleading: Tier 1-2 anchors with 0 R_val sit at y=0 alongside Tier 3-5 outlets, making them look identical. The info text says "sources in Tiers 3-5 will show Validation=0" but Tier 1 sources also show 0.

---

### R2 — Source Profile HEALTHY (theguardian)

**API:** `GET /api/sources/theguardian/profile`  
**Component:** `src/pages/SourceProfile.tsx`

**What it will show:**  
- Stat panel: claim summary bar shows "0 absorbed (0%)" — a thin empty bar.  
- Radar chart: `SourceProfile.tsx:530-538` — `toRadarValues` returns `undefined` when any dimension is null. The radar polygon collapses to nothing. No fallback text, just empty space where the polygon should be.  
- VfTrend chart: `VfTrendChart.tsx:33-42` — shows "No trend data" if snapshots.length === 0. If snapshots exist but R_val is null/0, the chart renders a flat line at y=0.  
- Silent edits section: works fine (theguardian has edits).  
- Absorbed claims list: shows 6 absorbed claims with excerpts — this section works correctly.

**Rating: DEGRADED** — the claim summary shows "0 absorbed" which is technically true for theguardian's most recent snapshot (R_val=0 despite 6 absorbed claims in the DB). The radar collapses — no polygon, no empty-state message.

---

### R2 — Source Profile ZERO-ABSORBED (aljazeera)

**API:** `GET /api/sources/aljazeera/profile`  

**What it will show:** Identical to theguardian but with 0 absorbed claims and 0 silent edits. Empty claim summary bar, collapsed radar, flat VfTrend. No silent edit log. The page is mostly empty cards.

**Rating: DEGRADED** — honest but sparse. The page communicates "this source has no consensus signals" correctly, but the collapsed radar and flat chart feel like rendering bugs to a judge who doesn't know the data is sparse.

---

### R2 — Source Profile TIER 5 (zerohedge)

**API:** `GET /api/sources/zerohedge/profile`  

**What it will show:** Same as aljazeera — 0 absorbed, collapsed radar, flat chart. But this is EXPECTED for a Tier 5 source — its isolation IS the story. The info text "Tier 5 contrarian" is prominent.

**Rating: HEALTHY** — a Tier 5 source with zero absorption communicates exactly what the system is designed to show: this outlet produces claims no other panel source corroborates. The sparse UI tells the right story here.

---

### R2 — Cluster Report RICH (/cluster/5835)

**API:** `GET /api/clusters/5835/report`  
**Component:** `src/pages/ClusterReport.tsx`

**Data shape expected:** `{cluster_id, vertical, summary: {absorbed, pending, ...}, source_stats: [...], claims: [...]}`  

**What it will show:** Cluster 5835 has 29 sources, 561 claims. The summary section shows "0 absorbed" (because the cluster's claims are mostly PENDING, not ABSORBED — absorption happens per-claim via Agent 3 consensus math, not per-cluster). The source-stats table works correctly. The "convergence-type data is not yet computed" message (`ClusterReport.tsx:232-233`) appears.

**Rating: DEGRADED** — the largest multi-source cluster in the system shows "0 absorbed" which contradicts the narrative. The claim table renders fine. The convergence-type disclaimer is honest but reads like a bug to a judge.

---

### R2 — Timeline RICH (/timeline/5835)

**API:** `GET /api/timeline/5835`  
**Component:** `src/pages/Timeline.tsx`

**What it will show:** 561 claims across 29 sources propagated over time. The timeline waterfall renders correctly. `Timeline.tsx:88-89` has an empty state for zero-claim clusters (not triggered here).

**Rating: HEALTHY** — the timeline is the strongest visual in the app. Shows claim propagation across sources and time. Works regardless of absorption count.

---

### R2 — Timeline SPARSE (1-source cluster)

**API:** `GET /api/timeline/<1-source-id>`  

**What it will show:** A timeline with claims from a single source. No cross-source propagation lines. The waterfall reduces to a single-column timeline. `Timeline.tsx:88-89` empty state for zero claims works.

**Rating: DEGRADED** — renders correctly but a single-source timeline is visually identical to any timeline with no cross-source data. Judge sees "one column, that's it?"

---

### R2 — Pipeline Flow (/pipeline)

**API:** `GET /api/scraper/status`, `GET /api/config/providers/available`, `GET /api/config/providers`  
**Component:** `src/pages/PipelineFlow.tsx`

**What it will show:** Scraper status (running/paused), provider configuration (shows BGE as embedding model), agent descriptions. No data dependency on claims/clusters.

**Rating: HEALTHY** — configuration display page, unaffected by sparse absorption.

---

### R2 — Investigate (/investigate)

**API:** None (local-only store)  
**Component:** `src/pages/Investigate.tsx`

**What it will show:** A text input that submits ad-hoc queries to an in-memory store. No backend endpoint. Results appear in a local list. It's a stub with search UI — no actual investigation logic wired.

**Rating: EMBARRASSING** — the search UI submits queries to nothing. Results are ephemeral local state. A judge typing "Trump Iran deal" gets a blank results list that disappears on refresh. The page exists but has no backend.

---

### R2 — Panel Management (/panel)

**API:** `GET /api/sources`  
**Component:** `src/pages/Panel.tsx`

**What it will show:** Toggle switches for all 37 sources grouped by tier and region. Reads from `DEFAULT_SOURCES` and zustand store. No dependency on claims/absorption data.

**Rating: HEALTHY** — pure config UI, unaffected by sparse data.

---

### R2 — Settings (/settings)

**API:** None (local-only store)  
**Component:** `src/pages/Settings.tsx`

**What it will show:** Theme toggle, font scale presets, consensus threshold sliders. The threshold explanation (`Settings.tsx:124`) says "These thresholds determine how many sources must report a claim before [consensus]" — still reads correctly post-T5 since MIN_CORROBORATION=2 is enforced.

**Rating: HEALTHY** — pure config UI, unaffected by sparse data.

---

## R3 — SPECIFIC CONCERN AREAS

### R3a — Sources.tsx `?? 0` coercion

**`Sources.tsx:132-133`:**
```typescript
R_orig: score?.R_orig ?? 0,
R_val: score?.R_val ?? 0,
```
**Still in place.** Sources with null R_orig/R_val get plotted at (0,0). 28 of 37 sources have non-null R_val (DB query confirmed). The coercion hides the source-has-data vs source-has-zero distinction, but in practice most sources DO have data — the issue is that R_val=0 even for sources with data (BBC at 0.0 despite 1 absorbed claim).

### R3b — Radar chart empty state

**`SourceProfile.tsx:530-538`:** When any dimension is null, `toRadarValues` returns `undefined`. The chart simply doesn't render a polygon. There is NO empty-state fallback text — the radar area is blank. `hasData` being false results in void, not a message.

### R3c — VfTrend chart with null R_val

**`VfTrendChart.tsx:33-42`:** When `snapshots.length === 0`, shows "No trend data." When snapshots exist but R_val is null/zero, the chart renders a flat line at y=0 with the full x-axis. This is technically correct but visually deceptive — a flat line at 0 looks like "consistently zero validation" rather than "no validation events."

### R3d — Cluster Report with absorbed_count=0

**`ClusterReport.tsx`:** The summary bar shows `data.summary.absorbed` with label "absorbed." When 0, it shows "0 absorbed" in the stat panel. No empty-state or fallback — just displays 0. The source-stats table shows `(0A)` for each source. This is technically correct but makes every cluster look like a failure.

### R3e — Hardcoded thresholds in UI copy

| Location | Text | Problem |
|----------|------|---------|
| `OnboardingDialog.tsx:23` | "The version of events agreed upon by the **majority** of the panel" | With 13 absorbed claims across 4 sources, no claim has "majority" agreement. "Majority" implies >50% of panel; actual max is 4/13 Tier 1+2. |
| `Sources.tsx:338-339` | "Sources in Tiers 3–5...will show Validation = 0" | Tier 1-2 sources (BBC, theguardian, foxnews) also show 0. The text is factually wrong. |
| `Settings.tsx:124` | "how many sources must report a claim before [consensus]" | Reads fine — threshold sliders still function, just produce sparse results. |

---

## R4 — DOCS DRIFT CHECK

**R4a:** Both `faq-pipeline-data.md` and `faq-source-selection.md` were updated post-T5 with methodology update sections. All numbers reflect current DB state.

**R4b — Stale number survivors:**
- `faq-pipeline-data.md` — "89 edits detected" → correct (89 is current count)
- `faq-source-selection.md` — "37 sources" → correct  
- No stale counts of 2,625/2,792/3,548/4,493/106,673 found. Docs were properly updated.

---

## SUMMARY

Three pages are EMBARRASSING or DEGRADED in ways that a judge would notice:

1. **Sources scatter plot** — 34 of 37 sources at y=0 makes the plot look broken, and the info text says only Tiers 3-5 should show 0 when Tier 1-2 also do.  
2. **Source Profile radar** — collapses to nothing for most sources with no fallback message.  
3. **Investigate page** — a search box wired to ephemeral local state with no backend.  
4. **Cluster Report** — shows "0 absorbed" for even the richest cluster, making every cluster look like a failure.  
5. **Onboarding copy** — says "majority of the panel" which is false with 13 absorbed claims.
