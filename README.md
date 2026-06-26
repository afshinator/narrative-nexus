# Narrative Nexus

A B2B Media Risk and OSINT workflow platform for hedge funds, PR firms, and geopolitical analysts. Monitors ~20 news outlets and algorithmically measures their reporting behavior over time — not to judge who is "right," but to answer which sources reliably break stories ahead of consensus, which generate noise, and which quietly rewrite history after publication.

> *"Narrative Nexus tracks consensus reality, not truth."*

---

## Stack

| Layer | Tools |
|-------|-------|
| Frontend | React 19.2, TypeScript 6, Vite 8, Tailwind 4, shadcn (Nova) |
| Routing / State | react-router v8, zustand 5 |
| Visualizations | D3 v7 (scatter, sparklines, waterfall, timeline, pipeline), Chart.js 4 (radar) |
| Backend | FastAPI, SQLite (WAL), APScheduler |
| ML | sentence-transformers on AMD GPU (ROCm), Fireworks AI API |

## Quick start

```bash
npm install
npm run dev       # Vite dev server on port 5173, proxies /api to localhost:8000
```

For the backend, see Phase 2 slices in `docs/plan/`.

---

## Documentation map

The project follows the [dev-workflow](https://github.com/afshinator/dev-workflow) process. Here's which doc to reach for when:

| When you need… | Open this |
|----------------|-----------|
| The product narrative, architecture, analytical model, demo strategy | `docs/design-v1.2.md` |
| Tagged requirements that `verify-spec-coverage.ts` checks | `spec/requirements.md` |
| Resolved design decisions (filtering behavior, badge colors, etc.) | `CONTEXT.md` |
| Architecture decision records (why we built it this way) | `docs/adr/0001` through `0004` |
| Deferred items tracking (what's waiting on what) | `docs/deferred.md` |
| Implementation reference (commands, gotchas, dependency notes) | `docs/older/TODO-pre-workflow.md` |

### How they relate

- **`docs/design-v1.2.md`** — the design document. Product narrative, system architecture, analytical model, page descriptions, demo strategy. Reference it for context behind the requirements.
- **`spec/requirements.md`** — the dev-workflow spec. Every requirement is tagged (`[desired]`, `[compromise]`, `[stack-bound]`, `[aspirational]`). This is what `verify-spec-coverage.ts` checks, what plan slices reference, and what adversarial reviews verify against.
- **`CONTEXT.md`** — domain glossary of design decisions made during the grilling phase. Captures the nuance between a requirement and its implementation (e.g., "scatter plot uses dim-mode filtering, not hide-mode; radar chart inverts three axes so outward = favorable").
- **`docs/adr/`** — Architecture Decision Records. Each documents a significant decision, alternatives considered, and consequences.
- **`docs/deferred.md`** — Items explicitly deferred during planning. Check this before creating new plan slices — items listed here are blocked by dependencies.

## Phases

The project is currently at **Phase 3 (Plan)** of the dev-workflow. Vertical slices live in `docs/plan/`.

---

*"Narrative Nexus tracks consensus reality, not truth."*
