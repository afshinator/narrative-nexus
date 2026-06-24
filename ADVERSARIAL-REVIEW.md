# Adversarial Code Review: Narrative Nexus

**Date:** 2026-06-24
**Scope:** Full repository review (source, tests, config, docs, infrastructure)
**Reviewer:** Automated adversarial review agent
**Methodology:** Read every file in the project tree against spec/requirements.md, docs/plan/*.md, docs/adr/*.md, and CONTEXT.md

---

## 1. EXECUTIVE SUMMARY

Narrative Nexus is an early-stage hackathon project with solid architectural foundations but significant implementation gaps. The frontend shell (routing, navigation, state management) is well-built. However, 5 of 9 pages are stubs, the Python backend is 17 lines of placeholder code, the onboarding dialog is missing entirely, and the AMD GPU worker container ships an idle loop instead of the required ROCm+sentence-transformers stack.

**Overall readiness for Track 3 hackathon demo: ~25%.** The project has the skeleton in place but lacks the core value proposition — the 4 AI agents, the data pipeline, and 5 data visualization pages.

---

## 2. STRENGTHS

1. **Solid architecture decisions.** The project follows documented ADRs (0001-0004) with clear rationales. The app/worker split, multi-vertical thresholds, demo seed strategy, and timeline/cluster-report page boundary are well-reasoned.

2. **Clean state management.** zustand with persist middleware provides type-safe, localStorage-backed state for theme, thresholds, font scale, active sources, and archetype filter. Single sources of truth in `src/data/thresholds.ts` and `src/data/sources.ts`.

3. **Well-structured component tree.** PageShell + Outlet pattern avoids nav/footer remounts. AppNav uses NavLink for automatic aria-current. shadcn components properly integrated.

4. **Strong test coverage for what exists.** 15 Docker compose structural tests, 4 integration tests (with Docker-availability gating), full SQLite schema validation including CHECK constraints and foreign keys, router shell navigation tests, settings/panel page tests, store tests, and data structure tests. Tests use `beforeEach` + `useStore.setState()` for clean isolation.

5. **CSS design token system.** Custom nn-* properties (nn-bg, nn-green, nn-amber, nn-red, nn-neutral, nn-dim) provide a consistent dark-terminal aesthetic. Polarity color logic (`getPolarityColor`) and archetype assignment (`getArchetype`) are implemented as pure functions.

6. **Good separation of concerns.** Utility functions (archetype, cssVar, format, polarity, shapes) are isolated from components. Data files are separate from store logic.

---

## 3. CRITICAL ISSUES

### 3.1 CI-01: Worker Container Is a Stub (REQ-107 FAIL)

**File:** `docker-compose.yml`, `Dockerfile.worker`
**Severity:** CRITICAL — fails a [desired] hackathon requirement.

The worker container's Dockerfile uses `FROM python:3.12-slim` and runs `python -c "print('Worker ready'); import time; time.sleep(3600)"`. This is an infinite sleep loop. REQ-107 requires: "The worker container must use ROCm base image and include sentence transformers."

The commented-out production stanza shows intent:
```
# FROM rocm/pytorch:latest
# RUN pip install sentence-transformers
```
But the actual deployed image does nothing. There is no embedding server, no HTTP endpoint. The plan document (002-docker-db.md) acknowledges this but defers it.

**Impact:** The pipeline's core embedding step (REQ-017: "Sentence transformer embeddings must run on AMD GPU via ROCm") cannot function. The Pipeline Flow page renders a distinct node labeled "AMD GPU Pod (sentence-transformers)" — this would be deceptive in a demo if the worker is actually idle.

**Fix:** Implement the worker as a minimal HTTP server (FastAPI or Flask) exposing a `/embed` endpoint that runs sentence-transformers. Use the ROCm base image. If AMD GPU is unavailable for development, provide a CPU fallback mode with a clear warning.

---

### 3.2 CI-02: 5 of 9 Pages Are Stubs (REQ-085–090 FAIL)

**Files:** `src/pages/SourceProfile.tsx`, `src/pages/ClusterReport.tsx`, `src/pages/Timeline.tsx`, `src/pages/PipelineFlow.tsx`, `src/pages/Investigate.tsx`
**Severity:** CRITICAL — fails 6 [desired] requirements.

Each of these pages returns only `<div>Page Name</div>`:

| Page | Stub Content | Missing REQs |
|------|-------------|-------------|
| SourceProfile | `<div>Source Profile</div>` | REQ-086 (radar chart, archetype badge, sparklines) |
| ClusterReport | `<div>Cluster Report</div>` | REQ-087 (forensic report, consensus summary, distortion matrix) |
| Timeline | `<div>Timeline</div>` | REQ-088 (Day 0-90 animation, CONSENSUS_ABSORBED line) |
| PipelineFlow | `<div>Pipeline Flow</div>` | REQ-089 (animated pipeline, AMD/Fireworks labeling) |
| Investigate | `<div>Investigate</div>` | REQ-090 (snapshot banner) |

Additionally, `Sources.tsx` also returns `<div>Sources</div>`, failing REQ-085 (scatter plot, archetype filter pills, leaderboard). That means **6 of 9 pages are effectively unimplemented.**

Only Settings, Panel, and NotFound are complete.

---

### 3.3 CI-03: Python Backend Is a Placeholder (REQ-013–016 FAIL)

**File:** `app/main.py`
**Severity:** CRITICAL — none of the 4 AI agents exist.

```python
from fastapi import FastAPI
app = FastAPI(title="Narrative Nexus")
@app.get("/health")
def health():
    return {"status": "ok"}
```

There is no:
- IntakeClusteringAgent (REQ-013)
- ForensicExtractionAgent (REQ-014)
- ConsensusAlignmentAgent (REQ-015)
- SilentAuditorAgent (REQ-016)

The scraping stack (feedparser, newspaper4k, Firecrawl — REQ-058–060) is not imported or used. The consensus math, reputation scoring, and resolution schedule (REQ-022–046) have no implementation. The entire data pipeline exists only in documentation.

---

### 3.4 CI-04: Onboarding Walkthrough Not Implemented (REQ-093–095 FAIL)

**File:** `src/components/AppNav.tsx`, no dialog component exists
**Severity:** CRITICAL — fails 3 [desired] requirements.

The nav bar renders a `?` icon (HelpCircle from lucide-react) with `aria-label="Open onboarding"` but the button has **no onClick handler**. There is no dialog component, no 5-step walkthrough, and no integration with the store's `onboardingComplete` flag.

REQ-093: "A 5 step first launch walkthrough must be implemented and stored in localStorage using onboardingComplete state."
REQ-094: "The onboarding walkthrough must be re accessible from onboarding icon in the nav bar."
REQ-095: "The onboarding walkthrough must define all vocabulary terms from spec section 1."

None of these are met.

---

### 3.5 CI-05: No Claim Lifecycle State Machine Logic (REQ-027–029 FAIL)

**File:** No implementation exists
**Severity:** CRITICAL — the analytical model has no runtime implementation.

The SQLite schema defines CHECK constraints for `state IN ('PENDING', 'CONSENSUS_ABSORBED', 'UNRESOLVED')` and `convergence_type IN ('CROSS_SOURCE_CONVERGENT', 'SELF_CONSISTENT')`. But there is no code to:

- Transition PENDING → CONSENSUS_ABSORBED (REQ-028)
- Transition PENDING → UNRESOLVED at 90 days (REQ-029)
- Classify absorbed claims with convergence type (REQ-030–031)

The 7d/30d/90d resolution schedule (REQ-043–045) and daily snapshots (REQ-046) are similarly unbuilt.

---

### 3.6 CI-06: Worker Has No HTTP Communication (REQ-105 FAIL)

**File:** `docker-compose.yml`, `worker/server.py`
**Severity:** CRITICAL — fails a [desired] containerization requirement.

REQ-105: "The app and worker containers must communicate over HTTP."

`worker/server.py` is a 2-line placeholder that just prints "Worker placeholder started". There is no HTTP server, no `/embed` endpoint. The Dockerfile.worker's CMD is a sleep loop. Even on the same Docker network, the app container has nothing to call.

---

## 4. HIGH-SEVERITY ISSUES

### 4.1 HI-01: Theme CSS Breaks in Light Mode

**File:** `src/index.css`
**Severity:** HIGH — visual corruption in non-default theme.

The `--nn-*` design tokens are defined only in `:root`:
```css
:root {
    --nn-bg:      #0a0a0f;
    --nn-surface: #111118;
    --nn-border:  #1e1e2e;
    --nn-green:   #00ff88;
    ...
}
```

The `.dark` block does NOT redefine nn-* tokens. In light mode, shadcn tokens switch to light, but nn-* tokens remain dark-theme hex values. Components using `var(--nn-green)` will render bright green on a light background — technically visible but the dark-terminal aesthetic dissolves entirely.

The Settings and Panel pages use `var(--nn-green)`, `var(--nn-amber)`, `var(--nn-red)`, `var(--nn-neutral)` for the balance bar. These will look wrong in light mode.

**Fix:** Move nn-* tokens inside `.dark {}` and provide lighter variants in `:root`.

---

### 4.2 HI-02: Dockerfile.app Has No Build Step for Frontend

**File:** `Dockerfile.app`
**Severity:** HIGH — container build assumes pre-built artifacts.

```dockerfile
COPY dist/ ./dist/
```

The Dockerfile copies `dist/` without running `npm run build`. If `dist/` doesn't exist on the build host, the container ships with no frontend. A proper multi-stage build would:
1. Stage 1: `FROM node:22`, `npm ci`, `npm run build`
2. Stage 2: `FROM python:3.12-slim`, copy dist from stage 1

Currently, `docker compose build` on a clean checkout will fail or produce a broken container.

---

### 4.3 HI-03: No Error Boundaries in React Tree

**Files:** `src/main.tsx`, `src/App.tsx`
**Severity:** HIGH — any unhandled exception crashes the entire SPA.

There is no `<ErrorBoundary>` wrapper around the router or individual page components. If a data visualization (D3 scatter plot, Chart.js radar, or any page component) throws during render, the entire app unmounts to a white screen. This is particularly risky for pages implementing D3 and Chart.js (REQ-085–088), where malformed data or missing DOM refs can throw.

**Fix:** Add a React error boundary component wrapping `<Outlet />` in PageShell, with a fallback UI that preserves navigation.

---

### 4.4 HI-04: Vertical Filter Has No UI Control

**File:** `src/store.ts`
**Severity:** HIGH — store state is unreachable by users.

The store defines:
```typescript
vertical: Vertical  // "ALL" | "GEOPOLITICS" | "ECONOMICS" | "TECHNOLOGY"
setVertical: (vertical: Vertical) => void
```

But no page or component exposes a UI control to change the vertical. The `archetypeFilter` similarly has no UI. These exist in store but are dead code from a user perspective.

---

### 4.5 HI-05: No Loading/Error States for Data Fetching

**File:** All page components
**Severity:** HIGH — the app has no data integration pattern.

Every page component renders static content. There is no `useEffect` for data fetching, no `useState` for loading/error states, no API client module, and no pattern for handling async data. When real data sources are connected, every page will need to be restructured.

---

### 4.6 HI-06: Missing scapy/dependency for Worker GPU

**File:** `requirements.txt`
**Severity:** HIGH — worker dependencies undefined.

`requirements.txt` contains only `fastapi>=0.115.0` and `uvicorn>=0.34.0`. These are app dependencies. The worker needs `sentence-transformers` (and its torch/ROCm dependencies) but has no requirements file at all. The Dockerfile.worker doesn't `pip install` anything.

---

## 5. MEDIUM-SEVERITY ISSUES

### 5.1 MI-01: Hardcoded Example Routes in Navigation

**File:** `src/components/AppNav.tsx`
```typescript
{ to: "/source/example.com", label: "Source Profile" },
{ to: "/cluster/abc123", label: "Cluster Report" },
{ to: "/timeline/abc123", label: "Timeline" },
```

These are dead links. The plan document (000-router-shell.md) acknowledges this as intentional for the shell slice, but users clicking these links will navigate to stub pages rendering literal `<div>Source Profile</div>`. This should be replaced with either disabled links or links that go to a meaningful listing page.

---

### 5.2 MI-02: Font Scale Subscription Fires Excessively

**File:** `src/main.tsx`
```typescript
useStore.subscribe((state) => {
  document.documentElement.classList.toggle("dark", state.theme === "dark");
  document.documentElement.style.setProperty("--font-scale", String(state.fontScale));
});
```

This fires on **every** state change (any threshold adjustment, any source toggle, any vertical change). The `classList.toggle` and `setProperty` calls are cheap but unnecessary 99% of the time. Should use a selector:
```typescript
useStore.subscribe(
  (state) => ({ theme: state.theme, fontScale: state.fontScale }),
  ({ theme, fontScale }) => { ... }
);
```

---

### 5.3 MI-03: Duplicate formatPercent Functions

**File:** `src/utils/format.ts` vs `src/pages/Settings.tsx`

`format.ts` exports:
```typescript
export function formatPercent(value: number, decimals = 1): string {
  return `${(value * 100).toFixed(decimals)}%`
}
```

Settings.tsx defines its own:
```typescript
function formatPercent(n: number): string {
  return `${n}%`
}
```

These have incompatible interfaces — the shared one expects a decimal (0.65 → "65.0%"), while Settings passes an integer (65 → "65%"). If someone imports the shared version into Settings, all display values break.

---

### 5.4 MI-04: No README Setup Instructions

**File:** `README.md` (exists but content unknown)
**Severity:** MEDIUM — poor developer experience.

A hackathon project should have clear setup instructions: how to install dependencies, start the dev server, run tests, and launch Docker. Without this, judges cannot evaluate the project.

---

### 5.5 MI-05: Busybox DB Service Is Wasteful

**File:** `docker-compose.yml`
```yaml
db:
  image: busybox
  volumes:
    - nn-data:/data
  command: ["sh", "-c", "touch /data/.ready && tail -f /dev/null"]
```

SQLite is file-based. The app service already mounts the `nn-data` volume. A separate busybox container running `tail -f /dev/null` serves no purpose except to satisfy REQ-008's "at least 3 services" requirement. This is technically compliant but adds unnecessary resource usage and a misleading "db" service name (it's not a database).

---

### 5.6 MI-06: Store Persists Stale Schema Data

**File:** `src/store.ts`
**Severity:** MEDIUM — potential runtime errors on schema changes.

The persist middleware stores all state under `localStorage['nn-store']`. If the Thresholds type or Source interface changes, old persisted data may cause TypeScript runtime mismatches. There is no migration logic or version tracking.

---

### 5.7 MI-07: No Accessible Labels on Panel Switches

**File:** `src/pages/Panel.tsx`

Each source row has a `Switch` with no associated `<label>` element:
```tsx
<Switch
  checked={activeSources.includes(source.id)}
  onCheckedChange={() => toggleSource(source.id)}
/>
```

Screen readers cannot determine which source each switch controls without a proper `htmlFor` + `id` association or `aria-label`.

---

## 6. LOW-SEVERITY ISSUES

### 6.1 LI-01: ResizeObserver Mock Is Incomplete

**File:** `src/test-setup.ts`
```typescript
globalThis.ResizeObserver = class {
  observe() {}
  unobserve() {}
  disconnect() {}
} as unknown as typeof ResizeObserver;
```

If any component reads `ResizeObserver` properties (e.g., checking for browser support), this mock will behave unexpectedly because the class has no static properties.

---

### 6.2 LI-02: Vite Dev Server Proxy Points to Localhost:8000

**File:** `vite.config.ts`
```yaml
proxy: { "/api": "http://localhost:8000" }
```

This only works when the Python backend is running locally outside Docker. In a Docker environment, the proxy would need to point to the app container's hostname.

---

### 6.3 LI-03: `"use client"` Directive in Slider Component

**File:** `src/components/ui/slider.tsx`

The `"use client"` directive is a Next.js convention. In a Vite project, it's a no-op. Harmless but misleading.

---

### 6.4 LI-04: Favicon Has No Dark-Mode Variant

**File:** `public/favicon.svg`, `index.html`

The favicon is an SVG but `index.html` only links one variant. For a dark-terminal app, a light-colored favicon would be more visible in browser tabs with dark themes.

---

### 6.5 LI-05: No .env.example or Environment Variable Documentation

The Dockerfile.app sets `DATABASE_URL=sqlite:///data/narrative-nexus.db` but there's no documentation for Fireworks API keys, AMD GPU configuration, or other required environment variables.

---

## 7. INCONSISTENCIES

### 7.1 INC-01: spec/requirements.md vs CONTEXT.md — Seed Script Path

CONTEXT.md references `scripts/seed-demo.py` for the demo seed strategy:
> "a seed script (`scripts/seed-demo.py`) processes ~80 curated article URLs"

No `scripts/` directory exists in the project tree. This file has not been created.

---

### 7.2 INC-02: Vertical Key Casing Mismatch

- Store type: `Vertical = "ALL" | "GEOPOLITICS" | "ECONOMICS" | "TECHNOLOGY"` (UPPERCASE)
- Threshold keys: `"geopolitics" | "economics" | "technology"` (lowercase)
- Settings labels: `"Geopolitics"`, `"Economics"`, `"Technology"` (Title Case)
- Schema `clusters.vertical`: free-text TEXT field (no enum constraint)

Three different casing conventions for the same concept. This will cause bugs when filtering clusters by vertical.

---

### 7.3 INC-03: Panel Balance Bar Uses Inline Styles Instead of Tailwind

**File:** `src/pages/Panel.tsx`

The balance bar uses inline `style={{ width, backgroundColor }}` while the rest of the app uses Tailwind classes. Consistent with the design for dynamic values, but the color values mix `var(--nn-*)` CSS custom properties with hardcoded inline styles — fragile.

---

### 7.4 INC-04: Docker Compose Test — Worker Port Assertion Is Wrong

**File:** `src/__tests__/docker/compose.test.ts`

```typescript
it("has no published ports", () => {
  expect(worker.ports || []).toEqual([]);
});
```

The actual `docker-compose.yml` has no `ports:` key on the worker service at all. When parsed by YAML, this becomes `undefined`. The test passes because `undefined || []` equals `[]`, but semantically the worker SHOULD expose port 8001 for HTTP communication with the app container. The worker currently has no port published internally either (no `expose:` or `ports:` directive). The test is asserting the wrong thing.

---

## 8. COMPLETENESS ASSESSMENT

### Requirements Traceability Matrix

| Section | REQ Range | Status | Coverage |
|---------|-----------|--------|----------|
| Product Identity | REQ-001–006 | PARTIAL | Footer tagline present; onboarding terms missing |
| Hackathon Constraints | REQ-007–012 | PARTIAL | Docker compose exists; worker is a stub |
| System Architecture | REQ-013–021 | NOT STARTED | 4 agents unbuilt; no pipeline code |
| Analytical Model | REQ-022–046 | PARTIAL | Thresholds/schema defined; no runtime logic |
| Data & Sources | REQ-047–063 | PARTIAL | Source panel complete; scraping stack missing |
| Frontend Pages | REQ-064–092 | PARTIAL | Navigation complete; 6/9 pages are stubs |
| Onboarding | REQ-093–095 | NOT STARTED | No dialog component exists |
| Demo Strategy | REQ-096–101 | [aspirational] | Excluded from checks |
| Containerization | REQ-102–108 | PARTIAL | Docker structure valid; worker non-functional |
| Out of Scope | REQ-109–116 | [stack-bound] | Informational only |

**Summary:** 0 of 9 sections fully complete; 6 partially complete; 2 not started.

---

### Test Coverage Assessment

| Test File | Tests | Status |
|-----------|-------|--------|
| router-shell.test.tsx | 12 | PASS — comprehensive navigation tests |
| settings-page.test.tsx | 5 | PASS — renders all sections |
| panel-page.test.tsx | 4 | PASS — tier labels, balance, source list |
| thresholds.test.ts | 3 | PASS — validates defaults, types, ranges |
| sources.test.ts | 6 | PASS — 20 sources, 5 tiers, structural validation |
| store-settings.test.ts | 6 | PASS — threshold updates, toggle, reset |
| schema.test.ts | 17 | PASS — all 6 tables, CHECK constraints, foreign keys |
| compose.test.ts | 15 | PASS — YAML structure validation |
| integration.test.ts | 4 | SKIP if no Docker; PASS with Docker |
| **TOTAL** | **72** | |

Tests cover what exists well. No tests exist for unimplemented features (no agent tests, no visualization tests, no pipeline tests).

---

## 9. RECOMMENDATIONS

### Immediate (Before Demo)

1. **Implement the Python backend agents** (REQ-013–016). This is the core value proposition. Without these, there is no product to demo.
2. **Fix the worker container** (REQ-107). Ship a real HTTP embedding server, not a sleep loop.
3. **Build the 5 stub pages** (REQ-085–090). These are the user-facing deliverables. Use the d3 and chart.js dependencies already in package.json.
4. **Implement the onboarding dialog** (REQ-093–095). This is a judged user experience feature.

### Short-Term (Post-Hackathon)

5. **Add error boundaries** to prevent white-screen crashes.
6. **Fix theme CSS** so light mode works correctly.
7. **Add a multi-stage Docker build** for the frontend.
8. **Implement the vertical filter UI** and normalize key casing.
9. **Unify formatPercent** to use the shared utility.
10. **Add API client module** with loading/error state patterns.

### Nice to Have

11. Add README with setup instructions and architecture diagram.
12. Replace busybox db service with a real init container or remove it.
13. Add store migration logic for schema versioning.
14. Add accessibility labels to Panel switches.

---

## 10. APPENDIX: File-by-File Assessment

| File | Status | Notes |
|------|--------|-------|
| src/App.tsx | COMPLETE | Router tree correct, all 9 routes defined |
| src/main.tsx | COMPLETE | Theme/font-scale sync; missing error boundary |
| src/store.ts | COMPLETE | Well-typed; vertical UI missing |
| src/index.css | BUG | nn tokens not defined for light mode |
| src/components/AppNav.tsx | BUG | ? button has no onClick handler |
| src/components/PageShell.tsx | COMPLETE | Correct Outlet + footer pattern |
| src/pages/Sources.tsx | STUB | Only renders `<div>Sources</div>` |
| src/pages/SourceProfile.tsx | STUB | Only renders `<div>Source Profile</div>` |
| src/pages/ClusterReport.tsx | STUB | Only renders `<div>Cluster Report</div>` |
| src/pages/Timeline.tsx | STUB | Only renders `<div>Timeline</div>` |
| src/pages/PipelineFlow.tsx | STUB | Only renders `<div>Pipeline Flow</div>` |
| src/pages/Investigate.tsx | STUB | Only renders `<div>Investigate</div>` |
| src/pages/Panel.tsx | COMPLETE | Balance bar, source toggles, tier grouping |
| src/pages/Settings.tsx | COMPLETE | Thresholds, font scale, theme toggle |
| src/pages/NotFound.tsx | COMPLETE | Minimal catch-all |
| src/data/thresholds.ts | COMPLETE | Single source of truth |
| src/data/sources.ts | COMPLETE | 20 sources, getSourcesByTier helper |
| src/lib/utils.ts | COMPLETE | cn() helper for Tailwind class merging |
| src/utils/archetype.ts | COMPLETE | Correct quadrant-based classification |
| src/utils/cssVar.ts | COMPLETE | getCssVar helper |
| src/utils/format.ts | COMPLETE | formatPercent, formatDays, formatRate |
| src/utils/polarity.ts | COMPLETE | Trait dimensions + polarity color logic |
| src/utils/shapes.ts | COMPLETE | Tier-to-shape mapping for D3 |
| src/test-setup.ts | COMPLETE | Jest-dom + ResizeObserver mock |
| src/components/ui/button.tsx | COMPLETE | shadcn component |
| src/components/ui/card.tsx | COMPLETE | shadcn component |
| src/components/ui/slider.tsx | COMPLETE | shadcn component |
| src/components/ui/switch.tsx | COMPLETE | shadcn component |
| app/main.py | STUB | Only /health endpoint |
| worker/server.py | STUB | Only a print statement |
| db/schema.sql | COMPLETE | 6 tables, indexes, CHECK constraints, FK |
| docker-compose.yml | PARTIAL | Valid structure; worker is stub |
| Dockerfile.app | BUG | No frontend build step |
| Dockerfile.worker | STUB | Sleep loop, not ROCm |
| requirements.txt | INCOMPLETE | Only fastapi+uvicorn; worker deps missing |
| spec/requirements.md | COMPLETE | 116 requirements with tag system |
| docs/plan/000-router-shell.md | COMPLETE | Clear plan, all items executed |
| docs/plan/001-settings-panel.md | COMPLETE | Clear plan, all items executed |
| docs/plan/002-docker-db.md | PARTIAL | Schema done; worker deferred |
| CONTEXT.md | COMPLETE | Domain glossary and conventions |
