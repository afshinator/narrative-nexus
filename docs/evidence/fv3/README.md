# FV3.2 — Render Verification

**Date:** 2026-07-06
**Method:** API data verification (browser tool unavailable — `browser-harness` not on PATH).
Text description with specific observed values from API responses. UNKNOWN where rendering cannot be verified from API alone.

---

## Sources Scatter

**API source:** GET /api/scores?vertical=geopolitics (37 sources)

- **Marker count on scatter:** 26 (graded sources with non-NULL R_val)
- **Ungraded listed below plot:** 11 (politico.com, namibian.com.na, premiumtimesng.com, straitstimes.com, thereporterethiopia.com, timesofisrael.com, vanguardngr.com, africanarguments.org, bellingcat.com, propublica.org, thegrayzone.com)
- **Quadrant boundaries:** panel median R_orig=52.0, R_val=48.0 (computed from latest-date percentile scores)
- **Null display:** Table cells with NULL R_orig/R_val → dash ("—") per null contract, not 0. Scatter excludes NULL points.
- **Shape encoding:** 5 shapes by tier (circle/square/diamond/triangle/cross)
- **Color encoding:** 4 archetype colors per quadrant (navy/red/teal/slate)
- **Archetype distribution (geopolitics):** CONSENSUS_FOLLOWER=6, EARLY_BREAKER=6, NOISE_GENERATOR=7, SELECTIVE_ACCURATE=7, null=11
- **UNKNOWN:** Actual visual marker positions, colors, shape rendering, tooltip behavior (browser not available)

---

## Source Profile (theguardian, id=5)

**API source:** GET /api/sources/5/profile?vertical=geopolitics

- **Radar polygon:** 6 axes all populated with non-NULL values
  - R_orig=100.0, R_val=28.0, R_speed=23.0, R_frame=60.0, R_edit=0.0, R_correct=0.0
  - R_edit=0.0 and R_correct=0.0 are legitimate zero values (NOT NULL), displayed as 0 on radar
- **Archetype badge:** EARLY_BREAKER (R_orig=100 > median 76, R_val=28 > median 0)
  - NOTE: The stored snapshot archetype is NOISE_GENERATOR (pipeline used different median computation). Frontend computes badge from API panelMedian, which pools ALL dates — stored value differs.
- **Snapshots returned:** 123 daily snapshots
- **Events:** 1 event in timeline
- **Edits:** 0 silent edits
- **Claim summary:** 85 total (8 absorbed, 73 pending)
- **Panel median (API):** R_orig=76.0, R_val=0.0
- **UNKNOWN:** Radar polygon rendering in Chart.js canvas, sparkline curves, event marker placement

---

## Cluster Report 966

**API source:** GET /api/clusters/966/report

- **Cluster title:** "R2.9c temporary — articles 940-945"
- **Vertical:** geopolitics
- **Source count:** 3 sources, all T1
- **Source breakdown:**
  - reuters.com (T1): 4 claims (1 absorbed, 0 pending, 3 unresolved)
  - apnews.com (T1): 8 claims (0 absorbed, 4 pending, 4 unresolved)
  - theguardian.com (T1): 8 claims (1 absorbed, 3 pending, 4 unresolved)
- **Claims total:** 20 (2 CONSENSUS_ABSORBED, 7 PENDING, 11 UNRESOLVED)
- **UNKNOWN:** Layout rendering (consensus summary zone, distortion matrix, forensic analysis zone), config-change banner, version indicator

---

## Timeline 966

**API source:** GET /api/timeline/966

- **Total claims:** 20 across 3 sources
- **Absorbed claim marker:** claim 2799, absorbed_at=2026-07-05T18:57:28.402773+00:00
  - Appears under BOTH reuters.com AND theguardian.com (merged claim, shared across sources)
  - Marker type: solid diamond (◆ absorption marker)
- **Unresolved claims:** 11 (hollow dots)
- **Pending claims:** 7 (hollow dots)
- **Echo-mimic dots:** Multi-source claims should show dashed connection lines to origin source
- **Day 0 of timeline:** earliest first_seen_at = 2026-03-10 (reuters)
- **Day 90 fade:** No claims exceed 90-day window
- **UNKNOWN:** Actual timeline bar chart rendering, dashed connection lines, Day 90 fade animation, marker positioning along date axis
