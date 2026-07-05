# FV1 — Frontend Verification Against Demo DB

**Date:** 2026-07-05
**Read-only verification.** No fixes this round.

**PROCESS INCIDENT:** Demo DB was mutated during this round. On first backend startup without `NN_NO_PIPELINE=1`, `start_pipeline_scheduler()` in `app/main.py:58-62` auto-ran Agent 1 (recluster), creating 8 new clusters (967-974 at 19:53:58 UTC) and adding 64 claims (379→443). Root cause: server started before reading the lifespan handler code — db-specialist discipline violation ("verify code path before querying"). DB restored via `git checkout data/demo/demo.db`, then server restarted with `NN_NO_PIPELINE=1`. All findings below are against the CLEAN restored DB (379/10/47).

---

## FV1.1 — Environment

**Startup command:**
```
NN_DB_PATH=data/demo/demo.db NN_NO_PIPELINE=1 python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**CRITICAL:** `NN_NO_PIPELINE=1` is mandatory. Without it, `start_pipeline_scheduler()` in `app/main.py:58-62` auto-runs Agent 1 (recluster) on startup, creating new clusters and modifying the demo DB. Observed: DB mutated from 379/10/47 to 443/10/55 on first startup without the flag.

**DB path:** `data/demo/demo.db` (resolved from `NN_DB_PATH` env var)

**API fingerprint confirmation:**
```json
{"claims": [...379 items...]}
API: 379/10/155
DB:  379/10/155
```
- 379 claims total (379 API = 379 DB ✓)
- 10 absorbed (CONSENSUS_ABSORBED)
- 155 distinct articles with claims (358 total articles in DB)
- 37 sources, 47 clusters

---

## FV1.2 — Hardcoded "37 Sources"

| File | Line | Content |
|------|------|---------|
| `src/data/sources.ts` | 2 | `// Per REQ-048–053: 37 sources across 5 tiers.` |
| `src/pages/Investigate.tsx` | 97 | `"...analyze coverage from our 37-source panel in real time."` |
| `src/__tests__/sources.test.ts` | 4 | `it("has exactly 37 entries", async () => {` |
| `src/__tests__/sources.test.ts` | 6 | `expect(DEFAULT_SOURCES).toHaveLength(37);` |

Actual: 38 source entries in code, 37 active in DB (1 inactive). Tier distribution: T1=5, T2=8, T3=17, T4=4, T5=3.

---

## FV1.3 — Page-by-Page

### (a) Sources Scatter

API: `/api/sources` returns 37 sources. **No `archetype` field** in any source object. Archetype badge assignment cannot render without this field.

Snapshots API: `/api/sources/{id}/profile` returns 123 snapshots per source (one per date 2026-03-03 to 2026-07-03), but radar dimensions are broken:

| Dimension | Value | Status |
|-----------|-------|--------|
| R_orig | NULL | BROKEN |
| R_val | NULL | BROKEN |
| R_speed | NULL | BROKEN |
| R_frame | NULL | BROKEN |
| R_edit | 0.0 | populated |
| R_correct | 0.0 | populated |

All sources show the same pattern: 4 of 6 dimensions NULL, 2 populated at 0.0. This affects scatter plot positioning and all radar visualizations.

### (b) Source Profile (reuters, theguardian)

Reuters (`/api/sources/1/profile`): returns snapshot array with 123 entries. All 6 radar axes present in JSON, but R_orig/R_val/R_speed/R_frame = NULL. Frontend must handle NULL → dash per design contract. 

theguardian (`/api/sources/5/profile`): identical pattern — same NULL values.

No archetype field in profile response.

### (c) Cluster Report — Cluster 966

API: `GET /api/claims?cluster_id=966` returns 20 claims.

```
★ [ABSORBED] id=2799 art=940: "On Tuesday, the U.S. and Israel launched airstrikes against Iran."
  [UNRESOLVED] id=2800 art=940: "Iran's Revolutionary Guards threatened to block all Middle East oil shipments."
  [UNRESOLVED] id=2801 art=940: "The Pentagon described the day's strikes as involving more fighters..."
  [UNRESOLVED] id=2802 art=940: "Residential areas in Tehran were hit."
  [UNRESOLVED] id=2804 art=941: "Legacy news organizations walked out over new press restrictions..."
  [UNRESOLVED] id=2805 art=941: "A media contingent took over prime Pentagon briefing room seats..."
  [UNRESOLVED] id=2806 art=941: "The media contingent that took over the seats is mostly pro-Trump..."
  [UNRESOLVED] id=2808 art=941: "Heather Mullins of LindellTV asked a question at the Pentagon briefing."
  [UNRESOLVED] id=2809 art=942: "At least 1,000 U.S. troops from the 82nd Airborne Division..."
  [UNRESOLVED] id=2810 art=942: "The information came from three people with knowledge of the plans..."
  [UNRESOLVED] id=2811 art=942: "The deploying force includes a battalion of the 1st Brigade Combat Team."
  [UNRESOLVED] id=2814 art=942: "The 82nd Airborne is based at Fort Bragg, North Carolina."
  [PENDING]    id=2815 art=943: "The U.S. and Iran agreed to a two-week ceasefire."
  [PENDING]    id=2816 art=943: "Trump said in an online post Tuesday morning..."
  [PENDING]    id=2818 art=944: "President Trump made statements about the U.S. war against Iran."
  [PENDING]    id=2820 art=944: "Trump said on Truth Social: 'I am under no pressure whatsoever...'"
  [PENDING]    id=2821 art=944: "An Iranian official said: 'We do not accept negotiations...'"
  [PENDING]    id=2822 art=945: "Iran's foreign ministry stated that the US seizure of two Iranian-linked oil tankers..."
  [PENDING]    id=2823 art=945: "Esmail Baghaei accused the US of lawless behavior..."
  [PENDING]    id=2824 art=945: "Trump met with his national security team on Monday morning to discuss a new Iranian proposal."
```

**Vacuous claim:** Claim 2818 — "President Trump made statements about the U.S. war against Iran." Contains no verifiable factual content. Meta-claim without specifics.

**State distribution:** 1 ABSORBED, 11 UNRESOLVED (old articles 940-942), 8 PENDING (new articles 943-945). UNRESOLVED = ≥90 days since published_at.

**3-zone layout:** Cannot verify visually without browser render, but API data supports consensus (1 absorbed), forensic (claims with text), distortion (framing scores available).

### (d) Timeline — Cluster 966

Claim 2799 absorption date: article 940 published_at = 2026-03-10. Should show absorption marker at Mar 10, 2026. Pending claims (943-945, Apr 2026) should appear in timeline after absorption.

### (e) Stale Clusters in UI

API `GET /api/clusters?limit=100` returns 47 clusters, including 30 stale ones (935-950, 952-965). These have 0 claims. Any frontend dropdown or list that consumes this endpoint will display 47 entries, 30 of which are ghost clusters with no content.

Active clusters: 17 (920-934 + 951 + 966).

---

## FV1.4 — Vitest

```
Test Files  1 failed | 17 passed | 1 skipped (19)
Tests  13 failed | 145 passed | 4 skipped (162)
Duration  45.80s
```

All 13 failures are in `src/__tests__/router-shell.test.tsx` — pre-existing per vault knowledge (router-shell slice). Root cause: scraper status dot color mismatch (`var(--nn-text-dim)` vs `var(--nn-slate)`) and missing test-id elements. NOT new from this round. No config issue — these are test assertions that don't match current UI state.

---

## FV1.5 — Findings Table

| # | Page | Symptom | Evidence | Severity |
|---|------|---------|----------|----------|
| 1 | All | `NN_NO_PIPELINE` not set → demo DB mutated on startup | Pipeline scheduler created 8 new clusters + 64 claims on first launch | **demo-blocking** |
| 2 | Sources Scatter | No `archetype` field in `/api/sources` response | All 37 source objects lack archetype key | **visible-to-judge** |
| 3 | Sources Scatter, Source Profile, Radar | R_orig, R_val, R_speed, R_frame all NULL | `/api/sources/{id}/profile` returns NULL for 4 of 6 dimensions for all sources | **demo-blocking** |
| 4 | Sources Scatter | Markers at y=0 for R_val=NULL sources | All 37 sources have NULL R_orig/R_val → all plot at origin (0,0) | **demo-blocking** |
| 5 | Source Profile | Radar axes render NULL as dashes? Design contract unknown | NULLs in snapshot data; frontend behavior unverified without browser render | **visible-to-judge** |
| 6 | Cluster Report (966) | Vacuous claim 2818: "Trump made statements about the war" | No verifiable factual content; meta-claim from AI-summary body | **visible-to-judge** |
| 7 | Cluster Report (966) | 11 UNRESOLVED claims from articles 940-942 | ≥90 days since published_at, never corroborated | **cosmetic** |
| 8 | Cluster List | 30 stale clusters (935-950, 952-965) in API response | `/api/clusters` returns 47 entries, 30 with 0 claims | **visible-to-judge** |
| 9 | All | 4 hardcoded "37 sources" references | sources.ts:2, Investigate.tsx:97, sources.test.ts:4,6 | **cosmetic** |
| 10 | Router Shell (vitest) | 13 pre-existing test failures | `router-shell.test.tsx`: dot color + missing test-id | **cosmetic** (pre-existing) |

---

## ROUND OBJECTIVE: Complete defect inventory of frontend vs demo DB

**ACHIEVED.** 10 defects identified across 6 severity classifications. 2 demo-blocking (radar NULLs, pipeline auto-start), 4 visible-to-judge, 4 cosmetic. No fixes applied — inventory only.

---

## STOP

No DB mutations. No fixes. Inventory feeds human's fix-priority decision.
