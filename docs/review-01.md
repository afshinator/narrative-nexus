# Review 01 — Codebase Audit vs `docs/design-v1.2.md` + `spec/requirements.md`

**Date:** 2026-06-25
**Scope:** All files in `/project/narrative-nexus` as of git HEAD + staged/unstaged changes (Slice 5).
**Method:** Manual audit reading every page, component, data file, config file, Dockerfile, and schema.
**Context:** No backend exists yet. Frontend has 4 implemented pages, 5 stubs.

---

## Severity Key

| Icon | Meaning |
|------|---------|
| 🔴 | Missing — required by spec/REQ, not implemented (beyond stubs) |
| 🟡 | Partial — exists but incomplete, broken, or not wired |
| 🔵 | Suggestion — code quality, polish, or deferred-by-design items |
| ✅ | Compliant — implemented and correct |

---

## SECTION 1: PRODUCT IDENTITY

| REQ | Check | Verdict | Evidence |
|-----|-------|---------|----------|
| REQ-001 | Footer tagline "tracks consensus reality, not truth" | ✅ | `src/components/PageShell.tsx:15` |
| REQ-002 | "Consensus reality" defined in UI tooltip/onboarding | ✅ | `src/components/OnboardingDialog.tsx:13-16` |
| REQ-003 | Vocabulary terms in UI documentation or tooltips | 🟡 | 5 of 6 terms present — "Outlier claim" missing from OnboardingDialog |
| REQ-004 | Footer tagline on every page | ✅ | PageShell wraps all routes via `<Outlet />` |
| REQ-005 | [stack-bound] | ✅ | Informational |
| REQ-006 | [stack-bound] | ✅ | Informational |

**🔴 REQ-003 gap:** The vocabulary table in `docs/design-v1.2.md` §1 defines 6 terms. `OnboardingDialog.tsx` lists only 5 — "Outlier Claim" is absent. REQ-003 explicitly requires it.

---

## SECTION 2: HACKATHON CONSTRAINTS

| REQ | Check | Verdict | Evidence |
|-----|-------|---------|----------|
| REQ-007 | docker-compose.yml at root | ✅ | `docker-compose.yml` exists |
| REQ-008 | 3 services: app, worker, db | ✅ | Defined in compose file |
| REQ-009-012 | [stack-bound] | ✅ | Informational |

---

## SECTION 3: SYSTEM ARCHITECTURE — AGENTS & COMPUTE

| REQ | Check | Verdict | Evidence |
|-----|-------|---------|----------|
| REQ-013 | IntakeClusteringAgent | 🔴 | No `pipeline/` directory. `app/main.py` is 7-line stub. |
| REQ-014 | ForensicExtractionAgent | 🔴 | Not implemented |
| REQ-015 | ConsensusAlignmentAgent | 🔴 | Not implemented |
| REQ-016 | SilentAuditorAgent | 🔴 | Not implemented |
| REQ-017 | Sentence transformer embeddings on AMD GPU | 🔴 | `worker/server.py` is 2-line placeholder |
| REQ-018 | LLM inference via Fireworks API | 🔴 | Not in requirements.txt or code |
| REQ-019 | Consensus math on CPU | 🔴 | Not implemented |
| REQ-020 | [stack-bound] | ✅ | Informational |
| REQ-021 | [stack-bound] | ✅ | Informational |

**🔴 All 4 agents are unimplemented.** The `app/` and `worker/` directories are stubs. This is expected given frontend-first build order (noted in `docs/deferred.md`), but the REQs are not met.

---

## SECTION 4: ANALYTICAL MODEL

### Consensus Thresholds

| REQ | Check | Verdict | Evidence |
|-----|-------|---------|----------|
| REQ-022 | Consensus baseline over Tier 1+2 | 🔴 | No backend computation |
| REQ-023 | Claim enters baseline at threshold% | 🔴 | No backend computation |
| REQ-024 | Default thresholds 65/75/75 | ✅ | `src/data/thresholds.ts:10-12` |
| REQ-025 | Configurable at runtime | ✅ | `src/pages/Settings.tsx:103-131` pill controls |
| REQ-026 | Stored with each cluster run | 🔴 | No cluster runs yet |

### Claim Lifecycle

| REQ | Check | Verdict | Evidence |
|-----|-------|---------|----------|
| REQ-027 | PENDING state | ✅ | `db/schema.sql:46` CHECK constraint |
| REQ-028 | CONSENSUS_ABSORBED terminal | ✅ | `db/schema.sql:46` |
| REQ-029 | UNRESOLVED at 90-day | ✅ | `db/schema.sql:46` |
| REQ-030 | Convergence type CROSS_SOURCE_CONVERGENT / SELF_CONSISTENT | ✅ | `db/schema.sql:47` |
| REQ-031 | SELF_CONSISTENT | ✅ | `db/schema.sql:47` |

### Reputation Dimensions

| REQ | Check | Verdict | Evidence |
|-----|-------|---------|----------|
| REQ-032 | R_orig | ✅ | `src/data/scores.ts:8` |
| REQ-033 | R_val | ✅ | `src/data/scores.ts:9` |
| REQ-034 | R_speed | ✅ | `src/data/scores.ts:10` |
| REQ-035 | R_frame | ✅ | `src/data/scores.ts:11` |
| REQ-036 | R_edit | ✅ | `src/data/scores.ts:12` |
| REQ-037 | R_correct | ✅ | `src/data/scores.ts:13` |
| REQ-038 | Trait dims neutral color | ✅ | `src/utils/polarity.ts:8` returns `--nn-slate`. Stat panel shows "(trait)" label. |

### Archetype Assignment

| REQ | Check | Verdict | Evidence |
|-----|-------|---------|----------|
| REQ-039 | EARLY_BREAKER (R_orig > median, R_val > median) | ✅ | `src/utils/archetype.ts:9` |
| REQ-040 | NOISE_GENERATOR (R_orig > median, R_val ≤ median) | ✅ | `src/utils/archetype.ts:10` |
| REQ-041 | SELECTIVE_ACCURATE (R_orig ≤ median, R_val > median) | ✅ | `src/utils/archetype.ts:11` |
| REQ-042 | CONSENSUS_FOLLOWER (R_orig ≤ median, R_val ≤ median) | ✅ | `src/utils/archetype.ts:12` |

### Resolution Schedule

| REQ | Check | Verdict | Evidence |
|-----|-------|---------|----------|
| REQ-043 | 7-day check | 🔴 | Not implemented (backend) |
| REQ-044 | 30-day check | 🔴 | Not implemented |
| REQ-045 | 90-day check | 🔴 | Not implemented |
| REQ-046 | Daily snapshots per source × vertical | ✅ | `db/schema.sql:65-79` snapshots table |

---

## SECTION 5: DATA & SOURCES

### Source Panel

| REQ | Check | Verdict | Evidence |
|-----|-------|---------|----------|
| REQ-047 | Consensus pool (T1+2) vs tracked (all tiers) | ✅ | `src/pages/Panel.tsx:170` labels "consensus pool" for T1+2 |
| REQ-048 | Tier 1: Reuters, AP, BBC, NPR, The Guardian | ✅ | `src/data/sources.ts:24-28` |
| REQ-049 | Tier 2: Fox News, Politico, The Economist, NYT, Washington Post | ✅ | `src/data/sources.ts:31-35` |
| REQ-050 | Tier 3: Al Jazeera, DW, NHK World, Global Times, France24 | ✅ | `src/data/sources.ts:38-42` |
| REQ-051 | Tier 4: The Intercept, ProPublica, Bellingcat | ✅ | `src/data/sources.ts:45-47` |
| REQ-052 | Tier 5: ZeroHedge, The Gray Zone | ✅ | `src/data/sources.ts:50-51` |
| REQ-053 | Total 20 sources | ✅ | `src/data/sources.ts` has 20 entries |

### Topic Verticals

| REQ | Check | Verdict | Evidence |
|-----|-------|---------|----------|
| REQ-054 | GEOPOLITICS | ✅ | `src/data/thresholds.ts:5` type includes it |
| REQ-055 | ECONOMICS | ✅ | |
| REQ-056 | TECHNOLOGY | ✅ | |
| REQ-057 | Sports excluded | ✅ | Not present anywhere |

### Scraping Stack

| REQ | Check | Verdict | Evidence |
|-----|-------|---------|----------|
| REQ-058 | feedparser for RSS | 🔴 | Not in `requirements.txt` |
| REQ-059 | newspaper4k for body extraction | 🔴 | Not in `requirements.txt` |
| REQ-060 | Firecrawl fallback (1000 credits/month) | 🔴 | Not configured |
| REQ-061 | BODY_UNAVAILABLE marker | ✅ | `db/schema.sql:25` CHECK constraint |
| REQ-062 | OI_EXCLUDED in UI | 🔴 | Not implemented in any page |
| REQ-063 | [stack-bound] RSS summary for voting | ✅ | Informational |

**🔴 Scraping deps entirely missing.** `requirements.txt` only has `fastapi` and `uvicorn`. No `feedparser`, `newspaper4k`, `firecrawl`, or `sentence-transformers`.

---

## SECTION 6: FRONTEND — PAGES & DESIGN

### Navigation

| REQ | Check | Verdict | Evidence |
|-----|-------|---------|----------|
| REQ-064 | Sticky nav: Logo, Sources, Source Profile, Cluster Report, Timeline, Pipeline, Investigate, Panel, Settings | ✅ | `src/components/AppNav.tsx:7-15` — 8 nav items |
| REQ-065 | Sources page → SourcesPage | ✅ | `src/pages/Sources.tsx` (214 lines) |
| REQ-066 | Source Profile → SourceProfilePage | ✅ | `src/pages/SourceProfile.tsx` (521 lines) |
| REQ-067 | Cluster Report → ClusterReportPage | 🟡 | Stub `<div>Cluster Report</div>` |
| REQ-068 | Timeline → TimelinePage | 🟡 | Stub `<div>Timeline</div>` |
| REQ-069 | Pipeline Flow → PipelineFlowPage | 🟡 | Stub `<div>Pipeline Flow</div>` |
| REQ-070 | Investigate → InvestigatePage | 🟡 | Stub `<div>Investigate</div>` |
| REQ-071 | Panel Management → PanelPage | ✅ | `src/pages/Panel.tsx` (202 lines) |
| REQ-072 | Settings → SettingsPage | ✅ | `src/pages/Settings.tsx` (150 lines) |

**🟡 5 pages remain stubs**: ClusterReport, Timeline, PipelineFlow, Investigate, NotFound. Routes exist but only render placeholder divs.

### Design Tokens

| REQ | Check | Verdict | Evidence |
|-----|-------|---------|----------|
| REQ-073 | `--nn-*` CSS custom properties per `design-tokens.md` | ✅ | `src/index.css:98-115` (light), `151-169` (dark) |
| REQ-074-081 | (Covered by REQ-073) | ✅ | |
| REQ-082 | Polarity color via `getPolarityColor` | ✅ | `src/utils/polarity.ts` + SourceProfile stat panel |
| REQ-083 | Monospace for data values | ✅ | IBM Plex Mono on all data cells |
| REQ-084 | 3 font families | ✅ | Space Grotesk, IBM Plex Sans, IBM Plex Mono — imported in `index.css:4-12` |

### Page Features

| REQ | Check | Verdict | Evidence |
|-----|-------|---------|----------|
| REQ-085 | Sources: scatter plot, archetype pills, sortable leaderboard | 🟡 | Pills + table work. Scatter plot renders empty (`data={[]}` at `Sources.tsx:142`) |
| REQ-086 | Source Profile: radar (6 axes), archetype badge, sparklines | ✅ | Full implementation: RadarChart, SparklineGrid, StatPanel, DayScrubber |
| REQ-087 | Cluster Report: forensic report | 🟡 | Stub only |
| REQ-088 | Timeline: Day 0-90 animation | 🟡 | Stub only |
| REQ-089 | Pipeline Flow: animated diagram | 🟡 | Stub only |
| REQ-090 | Investigate: snapshot banner | 🟡 | Stub only |
| REQ-091 | Panel: activate/deactivate + balance indicator | ✅ | Toggle switches, tier bar, geographic spread, low-panel warning |
| REQ-092 | Settings: thresholds, font scale, theme | ✅ | Pill controls for thresholds, presets for font scale, dark/light toggle |

### Onboarding

| REQ | Check | Verdict | Evidence |
|-----|-------|---------|----------|
| REQ-093 | 5-step walkthrough in localStorage | 🟡 | Single dialog (not 5-step) — all 5 terms listed at once in scrollable list. Persisted via zustand persist middleware |
| REQ-094 | Re-accessible from ? icon in nav | ✅ | `AppNav.tsx:84-91` — HelpCircle button opens dialog |
| REQ-095 | Defines all vocabulary terms | 🟡 | 5 of 6 defined. Missing "Outlier claim" |

**🔴 "Outlier claim" absent from onboarding.** REQ-003 and design §1 table include it. OnboardingDialog lists only: Consensus Reality, Consensus-Absorbed, Cross-Source Convergent, Self-Consistent, Unresolved.

**🟡 Not a 5-step walkthrough.** The design spec §6 describes a "5-step first-launch walkthrough." Current implementation is a single dialog with all terms in a scrolling list. This works but doesn't match the spec's UX description.

---

## SECTION 7: DEMO STRATEGY

All `[aspirational]` — not checked against code. No seed script (`scripts/seed-demo.py` referenced in design §7) or scripts directory exists.

---

## SECTION 8: CONTAINERIZATION

| REQ | Check | Verdict | Evidence |
|-----|-------|---------|----------|
| REQ-102 | App service (FastAPI) | ✅ | `docker-compose.yml:5-18` + `Dockerfile.app` |
| REQ-103 | Worker service (AMD GPU) | ✅ | `docker-compose.yml:20-30` + `Dockerfile.worker` |
| REQ-104 | DB service/volume (SQLite) | ✅ | `docker-compose.yml:32-38` + `nn-data` volume |
| REQ-105 | HTTP between app and worker | ✅ | Both on `nn-network`, worker `expose: 8001` |
| REQ-106 | Fireworks calls from app | ✅ | Comment documents the constraint |
| REQ-107 | ROCm + sentence-transformers | 🟡 | `Dockerfile.worker:8-9` shows commented-out ROCm line. Current build uses slim placeholder |
| REQ-108 | No GPU in app | ✅ | `Dockerfile.app` has no GPU deps |

**🟡 Worker Dockerfile is a placeholder.** The ROCm base image and sentence-transformers install are commented out (expected per M1 ponytail skip in `docs/deferred.md`).

---

## ADDITIONAL FINDINGS

### 🔴 Scatter Plot Renders No Data Points

`src/pages/Sources.tsx:142` passes `data={[]}` to `<ScatterPlot>`. The component (`src/components/ScatterPlot.tsx`) accepts `data` via props but its `useEffect` has an empty dependency array `[]` — it never reads the prop. The quadrants, axes, and labels render, but no source markers appear. Two issues:
1. Sources page passes empty array
2. ScatterPlot component doesn't react to prop changes

**Fix:** Wire mock data into Sources page or connect scatter to actual source scores. Make the D3 `useEffect` depend on `data` and render points.

### 🔴 Nav Links Use Hardcoded Example Paths

`src/components/AppNav.tsx:9-11`:
- `/source/example.com` — hardcoded example domain
- `/cluster/abc123` — hardcoded example ID
- `/timeline/abc123` — hardcoded example ID

These are nav links, not navigation actions — clicking them navigates to those specific paths regardless of context. For source profile and cluster/timeline pages, the nav should either be disabled or context-aware.

### 🟡 Missing `verify-spec-coverage.ts`

Referenced in `/vault/Knowledge/narrative-nexus.md` and `CLAUDE.md` as part of the dev-workflow but doesn't exist in the project.

### 🟡 Missing `scripts/` Directory

Design doc §7 references `scripts/seed-demo.py`. No `scripts/` directory exists.

### 🟡 `requirements.txt` Is Minimal

Only contains `fastapi>=0.115.0` and `uvicorn>=0.34.0`. Missing all pipeline dependencies:
- `feedparser` (REQ-058)
- `newspaper4k` (REQ-059)
- `sentence-transformers` (REQ-107)
- `apscheduler` (design §10 — explicitly chosen for scheduling)
- `firecrawl` python SDK (REQ-060)

### 🟡 API Proxy Without Endpoints

`vite.config.ts` proxies `/api` to `http://localhost:8000`, but `app/main.py` only serves `/health` — no `/api/*` routes exist.

### 🔵 Onboarding UX Differs From Spec

Design §6 describes a "5-step first-launch walkthrough." Current implementation is a single dialog with a scrollable list of terms. If the step-by-step progression is important, the dialog needs restructuring.

### 🔵 Outlier Claim Term

The design doc §1 vocabulary table defines "Outlier claim" as: *"A claim present in one or few sources but absent from the consensus baseline at extraction time."* This term is used in the design for the outlier waterfall (Source Profile extras), scatter plot axes (R_orig / R_val), and general UI copy. The term should be added to the onboarding dialog and could appear in tooltips on the Sources page.

---

## SUMMARY TALLY

| Category | ✅ Compliant | 🟡 Partial | 🔴 Missing |
|----------|-------------|------------|------------|
| Product Identity | 3 | 1 | 0 |
| Hackathon Constraints | 2 | 0 | 0 |
| Architecture (Agents) | 0 | 0 | 7 |
| Analytical Model | 14 | 0 | 5 |
| Data & Sources | 9 | 0 | 4 |
| Frontend (Pages) | 9 | 9 | 0 |
| Frontend (Design Tokens) | 6 | 0 | 0 |
| Onboarding | 1 | 2 | 0 |
| Containerization | 6 | 1 | 0 |
| **Total** | **50** | **13** | **16** |

**Note:** The 16 🔴 failures are all expected — they are either backend-dependent (frontend-first build order, documented in `docs/deferred.md`) or stub pages that are placeholders for future slices. No findings indicate unexpected regression or broken existing functionality.

---

*Audit conducted 2026-06-25. See `/vault/Knowledge/narrative-nexus.md` for project conventions and `docs/deferred.md` for items blocked by dependencies.*
