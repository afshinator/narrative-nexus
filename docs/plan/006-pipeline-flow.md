# Plan: Slice 6 — Pipeline Flow Page

## Requirements addressed

| Req | Description | How |
|-----|-------------|-----|
| REQ-089 | Animated pipeline diagram with AMD GPU vs Fireworks API execution labeling | `PipelineFlowPage.tsx` — CSS-animated flow diagram with 4 agent stage nodes + compute badges |
| REQ-069 | Nav links to Pipeline Flow page | Already routed in App.tsx (`/pipeline`), stub replaced |
| REQ-004 | Footer tagline on every page | Already on PageShell (inherited) |

Implicit from design-v1.2.md §6 (Pipeline Flow page description):
- "Animated pipeline diagram showing live status"
- "Each stage node shows AMD GPU vs Fireworks API execution"
- The design doc labels this page "The Machine"

From design-v1.2.md §7 (Demo strategy):
- "The pipeline replay — the animated diagram showing which stage ran on the AMD GPU pod vs which called the Fireworks API. This is the 'AMD integration is real, not decorative' moment."

## Verified compute targets

Source: `docs/design-v1.2.md` §3 Compute Allocation Table (lines 95–101), confirmed against spec REQ-013–019.

| Stage | Agent | Compute | REQ |
|-------|-------|---------|-----|
| 1 | Intake & Clustering | AMD GPU (embeddings via ROCm) + Fireworks API (LLM for classification) | REQ-013, REQ-017 |
| 2 | Forensic Extraction | Fireworks API (LLM for framing neutralization + claim extraction) | REQ-014, REQ-018 |
| 3 | Consensus Alignment | CPU (consensus math, agreement scoring, claim classification) | REQ-015, REQ-019 |
| 4 | Silent Auditor | CPU (snapshot diff comparison, edit detection) | REQ-016 |

Pre-pipeline ingress: RSS scraping runs on CPU (design §3). Shown as an entry node in the diagram.

## Dependencies

| Dep | Version | Where | Verified? |
|-----|---------|-------|-----------|
| react | ^19.2.7 | `package.json` | Yes — already used by all other pages |
| react-router | ^7.18.0 | `package.json` | Yes — page already routed at `/pipeline` |
| lucide-react | ^1.21.0 | `package.json` | Yes — used for stage icons |
| No new deps | — | — | CSS animations only, no animation library needed |

## Key assumptions (verified against codebase)

1. **Route exists** — confirmed: `App.tsx:22` has `<Route path="pipeline" element={<PipelineFlowPage />} />`. Nav links to `/pipeline` (AppNav.tsx:12). No route params needed.

2. **CSS tokens exist** — all `--nn-navy`, `--nn-teal`, `--nn-slate`, `--nn-red`, `--nn-amber`, `--nn-text`, `--nn-text-dim`, `--nn-border`, `--nn-surface`, `--nn-surface2` defined in `src/index.css`. No new tokens needed.

3. **Card layout pattern** — confirmed from Panel.tsx and Sources.tsx: `rounded-[14px] border border-[var(--nn-border)] bg-[var(--nn-surface)] p-6`.

4. **No mock file** — confirmed: `docs/mocks/` contains no pipeline-related mock. The page design is original, guided by the design doc and existing page patterns.

5. **No store dependency** — the pipeline diagram is a static architectural description. No zustand store reads needed. Page is self-contained.

6. **No deferred blockers** — `docs/deferred.md` lists no items related to the PipelineFlow page. Replay mode (future slice) needs cluster data from the backend, but the base diagram does not.

## Architecture decisions

### Decision 1: CSS animations over JavaScript animation libraries

Pure CSS chosen because:

- **Zero dependencies** — `@keyframes` pulse/fade animations on connector lines and status indicators. No Framer Motion, no React Spring, no D3.
- **Performance** — CSS animations run on the compositor thread, no JavaScript main-thread cost.
- **Simplicity** — the diagram has 4 nodes + connectors + 1 entry node. No complex motion paths, no physics, no sequencing that requires a library.
- **`animation-delay` for sequencing** — each connector's pulse animation starts with a staggered delay to create a visual "flow" from left to right.

### Decision 2: Static diagram (no live status)

The design doc says "showing live status" and "Replay mode for past clusters." But:

- **No backend exists** — there is no pipeline running, no cluster data to replay.
- **One code path** — per ADR-0002, we don't fabricate data or create demo modes. The page shows the pipeline architecture accurately. Status indicators show "Offline" (the honest state).
- **Replay deferred** — replay mode is listed in `docs/deferred.md` under "Backend pipeline" dependency. When the pipeline runs, the diagram can show live status via a store/API query. The visual infrastructure doesn't change — only the status values.

### Decision 3: Single-file component, no sub-components

Unlike SourceProfile (5 sub-components due to perf requirements from scrubber animation), PipelineFlow is a static diagram with CSS-only animation. No re-render concern — everything renders once. Extractable into sub-components later if replay mode requires per-node reactivity.

## Page layout

```
┌──────────────────────────────────────────────────────────┐
│ PageShell (AppNav + footer — inherited)                  │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  Pipeline Flow                                           │
│  The 4-agent swarm architecture                          │
│                                                          │
│  ┌────────────────────────────────────────────────────┐  │
│  │                                                    │  │
│  │  [RSS] ──→ [Stage 1] ──→ [Stage 2] ──→ [Stage 3] ──→ [Stage 4] ──→ [DB]  │
│  │  Ingest   Intake &    Forensic    Consensus    Silent       │  │
│  │  CPU      Clustering  Extraction  Alignment    Auditor      │  │
│  │           AMD GPU +   Fireworks   CPU          CPU          │  │
│  │           Fireworks   API                                   │  │
│  │           API                                                │  │
│  │  ┌──────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────┐ │  │
│  │  │RSS   │ │Embedding │ │Neutralize│ │Agreement │ │Snapshot│ │  │
│  │  │fetch │ │+ Cluster │ │+ Extract │ │+ Classify│ │diff    │ │  │
│  │  └──────┘ └──────────┘ └──────────┘ └──────────┘ └────────┘ │  │
│  │                                                    │  │
│  └────────────────────────────────────────────────────┘  │
│                                                          │
│  ┌──── Status ────────────────────────────────────────┐  │
│  │  Pipeline offline — no backend connected            │  │
│  │  All stages will activate when the agent swarm runs │  │
│  └────────────────────────────────────────────────────┘  │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

## Stage node design

Each stage node card:
- Agent name (heading, Space Grotesk, semibold)
- One-line description of what it does
- Compute badge (pill/tag showing AMD GPU, Fireworks API, or CPU)
- Status dot: offline (slate), online (teal), active (navy with pulse)

Compute badge colors (matching design tokens):
- AMD GPU → `var(--nn-red)` (AMD brand association)
- Fireworks API → `var(--nn-navy)` (API service)
- CPU → `var(--nn-slate)` (local compute)

Connectors between nodes:
- Arrow lines (CSS `::after` pseudo-elements or border-based)
- Pulse animation on the connector via `@keyframes` opacity pulse with staggered `animation-delay`

Entry/exit nodes (RSS Ingest, Database) are smaller, dimmer — not full agent nodes, just context.

## CSS animation details

### Connector pulse

```css
@keyframes pipeline-pulse {
  0%, 100% { opacity: 0.3; }
  50%      { opacity: 1.0; }
}
```

Each connector gets `animation: pipeline-pulse 2s ease-in-out infinite` with staggered `animation-delay`:
- Connector 1 (RSS → Stage 1): `0s`
- Connector 2 (Stage 1 → Stage 2): `0.5s`
- Connector 3 (Stage 2 → Stage 3): `1.0s`
- Connector 4 (Stage 3 → Stage 4): `1.5s`
- Connector 5 (Stage 4 → DB): `2.0s`

This creates a left-to-right "flow" effect.

### Active status dot

```css
@keyframes status-pulse {
  0%, 100% { box-shadow: 0 0 0 0 var(--nn-navy); }
  50%      { box-shadow: 0 0 0 4px transparent; }
}
```

Only shown when a stage is "active" — currently all stages are "offline" so no dots pulse.

## Empty state

One code path. The page always renders:
- Stage nodes with agent names, descriptions, compute badges
- Connectors with pulse animation
- Status dots showing "offline" (slate)
- Footer message: "Pipeline offline — no backend connected"

When the backend exists, a store/API call populates status. The visual infrastructure doesn't change.

## Data model

No new types needed. The page is self-contained with static content. If replay mode is added later, it would consume cluster run data from the backend, but that's a future slice.

## Store changes

None. No zustand read or write needed.

## New files

| File | Purpose |
|------|---------|
| `src/pages/PipelineFlow.tsx` | Full page component (replaces stub) |
| `src/__tests__/pipeline-flow.test.tsx` | Test suite |

## Existing files modified

| File | Change |
|------|--------|
| `src/App.tsx` | No change — route already exists |
| `src/components/AppNav.tsx` | No change — nav link already exists |

No other files touched. This is the smallest slice since the router shell.

## Implementation order

**Animation approach:** Follow the `animate` skill from `/vault/AgentConfig/skills-library/frontend-specific/animate/`. Target mock: `docs/mocks/pipeline-flow-animate.html`. Key rules: only `transform` + `opacity`, exponential easing (`ease-out-expo`/`ease-out-quart`), staggered entrance via CSS `--i` custom properties, `prefers-reduced-motion` mandatory.

1. **Page shell + heading** — Replace stub with full page shell, header section, entrance choreography (header → legend → pipeline → status, 80ms stagger groups)
2. **Stage nodes** — 4 agent stage cards with name, description, compute badge, status dot
3. **Entry/exit nodes + connectors** — RSS ingest node, DB output node, CSS arrow connectors with pulse animation
4. **Status footer** — Offline message, consistent with design tone
5. **Tests** — Render tests for heading, stage nodes, compute badges, offline status

## Test strategy

All renders are static — no interaction, no store, no async data. Tests use the same pattern as Settings page tests: `MemoryRouter` wrapper + render + assertions.

| Test | What it verifies |
|------|-----------------|
| Renders page heading | "Pipeline Flow" or "The Machine" heading present |
| Renders 4 stage nodes | Each agent name present: Intake & Clustering, Forensic Extraction, Consensus Alignment, Silent Auditor |
| Each node shows compute target | AMD GPU, Fireworks API, CPU badges visible on correct stages |
| Renders RSS ingress node | RSS/Ingest entry point visible |
| Renders Database exit node | Database/storage exit point visible |
| Shows offline status | "Pipeline offline" or similar status message present |
| Connector arrows present | Visual connectors between stages (CSS elements) |
| Integrates with nav | Existing router-shell test already verifies nav to `/pipeline` shows stub text — updated to show actual content |

No mocks needed — no Canvas, no Chart.js, no D3.

## Verification checklist

- [ ] `npm run build` exits 0
- [ ] `npx vitest run` — all tests pass (existing 105 + new pipeline-flow tests)
- [ ] `npx biome check src/` — no new errors introduced
- [ ] Dev server: page renders at `/pipeline`
- [ ] CSS pulse animation visible on connectors (manual visual check)
- [ ] Stage nodes show agent names, descriptions, compute badges
- [ ] Status shows "offline" — honest empty state, no fabricated data
- [ ] Responsive: nodes reflow on narrow viewports (flex-wrap or grid)

## Deferred items

- **Replay mode** — depends on backend cluster run data (deferred.md: "Backend pipeline")
- **Live status indicators** — depends on running pipeline (deferred.md: "Backend pipeline")
- **Per-stage detail expansion** — not in spec, add when needed
