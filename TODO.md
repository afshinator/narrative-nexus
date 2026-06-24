# Narrative Nexus — Build Todo List
*Ordered by dependency. Items within a phase can run in parallel.*
*API access not yet available — all Phase 1–5 work is fully unblocked.*

STATUS: finished up to 1.9; now trying to decide on plan-slices as per dev-workflow.

---

> **VERIFICATION NOTE**
> Every command and package in this document was run or researched in a live environment before being written.
> Confirmed stack: Node 22, npm 10, Vite 8, React 19.2, **TypeScript 6**, Tailwind 4, shadcn 4.x, react-router 8, zustand 5, d3 7 + @types/d3, chart.js 4, react-chartjs-2 5.3, Python 3.12, FastAPI 0.115+.
> All compatibility issues between tools were checked. Known traps documented inline: zustand v5 selector infinite loops, D3+React DOM ownership conflict, react-router v8 package rename, Tailwind v4 dark mode syntax, TS6 `baseUrl` deprecation, TS6 `erasableSyntaxOnly` banning `enum`.
> Do not substitute "equivalent" commands — the ones here are the ones that work.

---

## PHASE 1 — Project scaffolding

### 1.1 — Create the Vite project

```bash
npm create vite@latest narrative-nexus -- --template react-ts
cd narrative-nexus
npm install
```

This gives you a **TypeScript** project. You get three tsconfig files (`tsconfig.json`, `tsconfig.app.json`, `tsconfig.node.json`) and `vite.config.ts`. TypeScript 6 is installed by the template (`~6.0.2`). The project is `"type": "module"` — all config files are ESM.

---

### 1.2 — Install all dependencies in one pass

```bash
npm install react-router zustand d3 chart.js react-chartjs-2
npm install tailwindcss @tailwindcss/vite
npm install -D @types/d3
```

Note: `@types/node`, `@types/react`, and `@types/react-dom` are already installed by the `react-ts` template. `@types/d3` is the only additional `@types` package needed — `react-router`, `zustand`, `chart.js`, and `react-chartjs-2` all bundle their own types. Verified by inspecting each package's `package.json` for `types` / `typings` fields.

**What each package is and why — every entry traced to a specific spec requirement:**

- `react-router` v8 — client-side routing for the 8 pages. **Not `react-router-dom`** — React Router v8 (released June 2026) dropped `react-router-dom` entirely. All APIs now live in `react-router`. DOM-specific APIs (RouterProvider) live in `react-router/dom`. The simple `BrowserRouter + Routes` pattern still works in v8 and is the right choice for this pure SPA — no SSR, no data loaders needed. Verified: `BrowserRouter`, `Routes`, `Route`, `NavLink`, `Link`, `useParams`, `useLocation`, `useNavigate` all confirmed present in `react-router` v8.
- `zustand` v5 — global state (theme, vertical, filters, fontScale, onboardingComplete). `persist` middleware verified working in v5. **v5 selector warning:** if a component selects multiple values with an inline object `useStore(s => ({ a: s.a, b: s.b }))`, it returns a new reference every render and causes an infinite loop. Always select one value at a time (`useStore(s => s.theme)`) or wrap multi-value selectors with `useShallow` from `zustand/shallow`.
- `d3` v7 — handles: scatter plot custom shapes (5 symbol types verified), 30-day sparklines (line generator), outlier waterfall (scaleBand + rects), Timeline animation (d3.timer, interpolate, easing), Pipeline node-edge diagram + particle flow. **D3 + React DOM pattern:** D3 and React both want to own the DOM — you must choose one approach per component and not mix them. See step 1.9 for the two patterns.
- `chart.js` v4 — radar chart on Source Profile: 6 axes, current-period polygon, previous-period dashed polygon (`borderDash` confirmed supported), percentile orientation.
- `react-chartjs-2` v5 — required wrapper for Chart.js in React. Without it, Chart.js canvas instances leak on component remount. React 19 support added in v5.3.0, confirmed in peer deps.

**Not installed and why:**
- ~~recharts~~ — zero uses. Every chart in the spec is either a custom D3 visual (scatter, sparklines, waterfall, timeline, pipeline) or a canvas radar (Chart.js). recharts adds weight without covering anything.
- ~~postcss, autoprefixer~~ — Tailwind v3 setup. Tailwind v4 uses a Vite plugin, none of this is needed.
- ~~react-router-dom~~ — dead package as of React Router v8. Do not install it.

**Do NOT run** `npx tailwindcss init` — that is a Tailwind v3 command and will create a config file that breaks v4.

---

### 1.3 — Rewrite `vite.config.ts`

Replace the entire file with this:

```ts
import path from "path"
import { defineConfig } from "vite"
import react from "@vitejs/plugin-react"
import tailwindcss from "@tailwindcss/vite"

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      "@": path.resolve(import.meta.dirname, "./src"),
    },
  },
  server: {
    proxy: {
      "/api": "http://localhost:8000",
    },
  },
})
```

**Why `import.meta.dirname`:** The TS project is ESM (`"type": "module"`), so `__dirname` doesn't exist. In Node 22, `import.meta.dirname` is available natively — no `fileURLToPath` shim needed. This is cleaner than the workaround required for the JS template. Verified working on Node 22.

---

### 1.4 — Replace `src/index.css`

Delete all contents and replace with exactly one line:

```css
@import "tailwindcss";
```

This is the entire Tailwind v4 setup. There is no `tailwind.config.js` to create or edit. Theme customization happens in CSS (see step 1.7). The old `@tailwind base; @tailwind components; @tailwind utilities;` is v3 syntax — do not use it.

---

### 1.5 — Add the `@` path alias to `tsconfig.app.json`

The TS template creates three tsconfig files. The alias goes in `tsconfig.app.json` (which covers `src/`). Open it and add `"paths"` to `compilerOptions`:

```json
{
  "compilerOptions": {
    "tsBuildInfoFile": "./node_modules/.tmp/tsconfig.app.tsbuildinfo",
    "target": "es2023",
    "lib": ["ES2023", "DOM"],
    "module": "esnext",
    "types": ["vite/client"],
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "verbatimModuleSyntax": true,
    "moduleDetection": "force",
    "noEmit": true,
    "jsx": "react-jsx",
    "paths": {
      "@/*": ["./src/*"]
    },
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "erasableSyntaxOnly": true,
    "noFallthroughCasesInSwitch": true
  },
  "include": ["src"]
}
```

**Do not add `baseUrl`.** TypeScript 6 deprecated `baseUrl` when used only for path mapping — it causes a build warning. With `moduleResolution: "bundler"`, `paths` alone is sufficient. Verified: build passes cleanly without `baseUrl`.

**Note on `erasableSyntaxOnly: true`** (new in TS6): this bans the `enum` keyword, `namespace`, and old-style decorators. Use string literal unions instead throughout the codebase: `type Vertical = "GEOPOLITICS" | "ECONOMICS" | "TECHNOLOGY"`. This is more idiomatic TypeScript anyway.

---

### 1.6 — Run shadcn init

```bash
npx shadcn@latest init
```

You will be asked **exactly two questions**. No others. Verified by reading shadcn's source code:

1. **Select a component library** → press Enter (Radix is already highlighted)
2. **Which preset would you like to use?** → press Enter (Nova is already highlighted)

Everything else is automatically skipped:
- Style question: skipped because Tailwind v4 is detected
- Monorepo question: skipped because `package.json` already exists
- Re-install question: skipped because no `components.json` exists yet
- "Proceed?" confirmation: skipped because `--yes` defaults to `true` in shadcn v4

After those two Enter presses, shadcn fetches the Nova preset from its registry and runs silently. It will:
- Write `components.json`
- Update `src/index.css` with its CSS variable block
- Install three npm packages with no prompts and no peer dep warnings: `@fontsource-variable/geist`, `lucide-react`, `tw-animate-css` — all verified React 19 compatible

**After init completes**, open `src/index.css`. It will have shadcn's variable block. You will add the Narrative Nexus design tokens below it in step 1.7.

---

### 1.7 — Add design tokens to `src/index.css`

After shadcn's generated block, append the Narrative Nexus token layer. The spec mentions a theme toggle in Settings, so we use class-based dark mode. In Tailwind v4, there is no `tailwind.config.js` with `darkMode: 'class'` — instead you declare a custom variant directly in CSS.

```css
/* Tailwind v4: declare class-based dark mode variant (replaces darkMode:'class' config) */
@custom-variant dark (&:where(.dark, .dark *));

/* Narrative Nexus design tokens — dark mode is the default/primary theme */
:root {
  --nn-bg:        #0a0a0f;
  --nn-surface:   #111118;
  --nn-border:    #1e1e2e;
  --nn-green:     #00ff88;
  --nn-amber:     #ffaa00;
  --nn-red:       #ff4444;
  --nn-neutral:   #4a4a6a;
  --nn-text:      #e0e0e0;
  --nn-dim:       #888899;
}
```

Apply the dark class to `<html>` via the zustand theme state (see step 1.8). Do not fight shadcn's variables — they live in their own namespace. The `--nn-*` prefix keeps them separate.

---

### 1.8 — Create `src/store.ts`

This is the **first real source file** in the project. Get it right before writing any components that depend on it.

```ts
import { create } from "zustand"
import { persist } from "zustand/middleware"

// Use string literal unions — NOT enums (banned by erasableSyntaxOnly in TS6)
export type Theme = "dark" | "light"
export type Vertical = "ALL" | "GEOPOLITICS" | "ECONOMICS" | "TECHNOLOGY"
export type Archetype =
  | "EARLY_BREAKER"
  | "NOISE_GENERATOR"
  | "SELECTIVE_ACCURATE"
  | "CONSENSUS_FOLLOWER"
  | null

interface StoreState {
  theme: Theme
  vertical: Vertical
  archetypeFilter: Archetype
  fontScale: number
  onboardingComplete: boolean
  setTheme: (theme: Theme) => void
  setVertical: (vertical: Vertical) => void
  setArchetypeFilter: (f: Archetype) => void
  setFontScale: (scale: number) => void
  setOnboardingComplete: (v: boolean) => void
}

export const useStore = create<StoreState>()(
  persist(
    (set) => ({
      theme: "dark",
      vertical: "ALL",
      archetypeFilter: null,
      fontScale: 1.0,
      onboardingComplete: false,
      setTheme: (theme) => set({ theme }),
      setVertical: (vertical) => set({ vertical }),
      setArchetypeFilter: (archetypeFilter) => set({ archetypeFilter }),
      setFontScale: (fontScale) => set({ fontScale }),
      setOnboardingComplete: (onboardingComplete) => set({ onboardingComplete }),
    }),
    { name: "nn-store" }
  )
)
```

Note the `create<StoreState>()()` double-call pattern — required for zustand v5 TypeScript inference with middleware.

`persist` from `zustand/middleware` replaces every manual `localStorage.getItem/setItem` call. Do not add those manually elsewhere.

**Applying theme to the DOM:** In `src/main.tsx`, subscribe to the store and apply the theme class to `<html>`:

```ts
// In main.tsx, after creating the root:
useStore.subscribe(
  (state) => state.theme,
  (theme) => {
    document.documentElement.classList.toggle("dark", theme === "dark")
  },
  { fireImmediately: true }
)
```

**Zustand v5 selector rule — read this before writing any component:**
- **Safe:** `const theme = useStore(s => s.theme)` — one primitive, stable reference
- **Unsafe:** `const { theme, vertical } = useStore(s => ({ theme: s.theme, vertical: s.vertical }))` — new object every render → infinite loop
- **Fix for multi-value:** `import { useShallow } from "zustand/shallow"` then `useStore(useShallow(s => ({ theme: s.theme, vertical: s.vertical })))`

---

### 1.9 — Create utility files

These are imported by almost every component. Write them once now so they're stable:

**`src/utils/archetype.ts`** — maps (R_orig, R_val, medians) → `Archetype` type
**`src/utils/polarity.ts`** — maps (dimension, value) → CSS color var (`--nn-green`, `--nn-amber`, `--nn-red`, `--nn-neutral`)
**`src/utils/format.ts`** — number formatting helpers (percentages, days, rates)
**`src/utils/cssVar.ts`** — `getCssVar(name: string): string` helper for reading CSS custom properties in JS (needed for Chart.js canvas rendering which cannot read CSS vars directly)

Stubs are fine at this stage — the interfaces matter more than the implementations.

// NOTE:  now have bare implementation of those.

---

**D3 + React DOM pattern — establish this before writing any D3 component:**

// NOTE: tmi!  not necessary at this point.  Nothing actionable here.

D3 and React both want to control the DOM. You must pick one approach per component and not mix them.

**Pattern A — D3 owns the SVG** (use for: Timeline, Pipeline)
These components have complex imperative animation (`d3.timer`, particle flow). D3 must own the SVG entirely.
```tsx
// React renders only the container ref — nothing inside the SVG
function Timeline() {
  const svgRef = useRef<SVGSVGElement>(null)
  useEffect(() => {
    if (!svgRef.current) return
    const svg = d3.select(svgRef.current)
    // D3 does everything inside here — append, transition, timer, etc.
    return () => { svg.selectAll("*").remove() } // cleanup on unmount
  }, [data])
  return <svg ref={svgRef} width={800} height={400} />
}
```

**Pattern B — React owns the SVG, D3 for math only** (use for: scatter plot, sparklines, waterfall)
D3 calculates scales, paths, and shapes. React renders the actual SVG elements as JSX. No DOM conflict.
```tsx
interface SparkDatum { day: number; value: number }
function Sparkline({ data }: { data: SparkDatum[] }) {
  const line = d3.line<SparkDatum>().x(d => xScale(d.day)).y(d => yScale(d.value))
  return (
    <svg>
      <path d={line(data) ?? ""} stroke="var(--nn-green)" fill="none" />
    </svg>
  )
}
```

Never mix patterns within a single component. Never call `d3.select()` on a ref that React is also rendering children into.

---

### 1.10 — Set up React Router and stub pages

**Import from `react-router`, not `react-router-dom`** — v8 dropped the `-dom` package.

```ts
// Correct v8 imports — all from "react-router", not "react-router-dom"
import { BrowserRouter, Routes, Route, NavLink, Link, useParams, useLocation, useNavigate } from "react-router"
```

**`src/main.tsx`** — wrap in `<BrowserRouter>` (imported from `react-router`)

**`src/App.tsx`** — declare all 8 routes pointing to stub components:

| Route | Component |
|---|---|
| `/` | `Sources` |
| `/source/:domain` | `SourceProfile` |
| `/cluster/:clusterId` | `ClusterReport` |
| `/timeline/:clusterId` | `Timeline` |
| `/pipeline` | `PipelineFlow` |
| `/investigate` | `Investigate` |
| `/panel` | `Panel` |
| `/settings` | `Settings` |

Each stub page just returns a `<div>PageName</div>` for now.

---

### 1.11 — Build `AppNav.jsx` and `PageShell.jsx`

- `AppNav.tsx` — sticky top bar, all 8 nav links, `?` icon that opens onboarding, active link highlighting via `useLocation()` (imported from `react-router`)
- `PageShell.tsx` — wraps every page: `<AppNav>` + `<main>` + footer with the tagline **"Narrative Nexus tracks consensus reality, not truth."**

Every page renders inside `<PageShell>`. The footer tagline is not optional — it's in the spec as a requirement on every page.

---

### 1.12 — Verify the full Phase 1 build

```bash
npm run build
```

Should complete with no errors. If it does, Phase 1 is done. The dev server (`npm run dev`) should show the stub nav with 8 working links.

---

## PHASE 2 — FastAPI skeleton + database schema
*Pure Python/SQL. No API access needed. Run in parallel with Phase 3 once Phase 1 is complete.*

### 2.1 — Install Python dependencies

```bash
pip install fastapi uvicorn apscheduler --break-system-packages
```

If you're working inside a venv (recommended for the backend), omit `--break-system-packages`.

---

### 2.2 — Write `schema.sql`

All `CREATE TABLE IF NOT EXISTS` statements for the tables listed in the spec:
`source_panel`, `story_clusters`, `cluster_verticals`, `cluster_articles`, `source_reputation`, `outlier_claims`, `reputation_snapshots`, `silent_edits`, `ingestion_manifest_log`, `discovery_run_log`, `firecrawl_usage`, `pipeline_queue`, `pipeline_run_log`

---

### 2.3 — Write `database.py`

SQLite connection factory with WAL mode enabled:

```python
import sqlite3

def get_conn(path="nn.db"):
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA synchronous=NORMAL")
    return conn
```

---

### 2.4 — Write `seed.py`

Seeds the 20 default active sources from spec Section 5 into `source_panel`. All others in the pre-vetted catalog go in as `active=0`. Run this once to initialize `nn.db`.

---

### 2.5 — Write `app.py` — FastAPI with mock endpoints

All `/api/*` routes return hardcoded mock JSON in the correct response shape. Build them in this priority order (the frontend pages depend on them in this order):

1. `GET /api/leaderboard` — list of sources with all 6 reputation dimensions
2. `GET /api/scatter` — (x, y, shape, archetype) per source for the scatter plot
3. `GET /api/source/{domain}/radar` — 6-dimension percentile data for one source
4. `GET /api/pipeline/status` — current stage + queue depth for PipelineFlow page
5. `GET /api/cluster/{cluster_id}` — full cluster report data
6. `GET /api/source/{domain}/waterfall` — outlier claim timeline for one source
7. `GET /api/panel/catalog` — all sources with active/inactive status
8. All remaining endpoints

**Static file serving — mount it last:**

```python
import os
from fastapi.staticfiles import StaticFiles

# All /api/* routes must be declared BEFORE this line
if os.path.exists("dist"):
    app.mount("/", StaticFiles(directory="dist", html=True), name="static")
```

`StaticFiles(html=True)` handles the SPA catch-all automatically (serves `index.html` for any path that doesn't match a file). Do **not** add a separate `@app.get("/{full_path:path}")` route — it will conflict with StaticFiles and cause a routing error.

---

### 2.6 — Verify end-to-end mock flow

```bash
# Terminal 1 — build frontend and start API server
npm run build
uvicorn app:app --reload --port 8000

# Terminal 2 — start Vite dev server
npm run dev
```

The frontend dev server (port 5173) proxies `/api/*` to port 8000 per the `vite.config.js` proxy set up in step 1.3. The Sources page should fetch `/api/leaderboard` and render the mock data. This is the integration checkpoint — if this works, all subsequent frontend pages can be built against real-shaped mock data.

---

## PHASE 3 — Frontend pages
*Build in this order. Each page uses mock API data from Phase 2.*

- [ ] **3.1** `Sources.tsx` — scatter plot + leaderboard table. The demo entry point. Pixel-perfect.
- [ ] **3.2** `PipelineFlow.tsx` — D3 animated node-edge diagram, AMD GPU vs Fireworks badges. Build second — it's the "Application of Technology" showpiece.
- [ ] **3.3** `SourceProfile.tsx` — radar chart (Chart.js canvas, 6 axes), archetype badge, 30-day sparklines
- [ ] **3.4** `ClusterReport.tsx` — 3-zone layout, consensus-reality language throughout, never "source was right/wrong"
- [ ] **3.5** `Timeline.tsx` — D3 horizontal Day 0–90, claim dots, absorption line, echo-mimic connections, play/pause
- [ ] **3.6** `Investigate.tsx` — search input, snapshot-mode banner, read-only forensic report
- [ ] **3.7** `Panel.tsx` — active sources table, archived section collapsed, category balance indicator
- [ ] **3.8** `Settings.tsx` — font scale slider (updates `--scale` via store), theme toggle, threshold inputs, health panel. Use shadcn components here.
- [ ] **3.9** `Onboarding.tsx` — shadcn Dialog, 5 steps, all 5 vocabulary terms as monospace chips, re-openable from `?` nav icon

---

## PHASE 4 — Containerization
*Write these before adding more backend logic — all subsequent backend code should be written inside the containers it will run in.*

### 4.1 — `Dockerfile.app`

Python FastAPI server. No GPU dependency.

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN npm ci && npm run build
EXPOSE 8000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

### 4.2 — `Dockerfile.worker`

ROCm + sentence-transformers. **[PENDING]** exact base image tag until GPU pod access arrives. Use the CPU fallback for local dev:

```dockerfile
# Production (AMD GPU pod — confirm base image tag at access time):
# FROM rocm/pytorch:latest
# RUN pip install sentence-transformers

# Local dev (CPU fallback — use this until GPU pod access is confirmed):
FROM python:3.12-slim
RUN pip install --no-cache-dir sentence-transformers torch --index-url https://download.pytorch.org/whl/cpu
WORKDIR /app
COPY worker.py .
EXPOSE 8001
CMD ["uvicorn", "worker:app", "--host", "0.0.0.0", "--port", "8001"]
```

The confirmed current ROCm PyTorch base image format is `rocm/pytorch:rocm6.X_ubuntuXX.XX_pyX.XX_pytorch_release_X.X.X`. Switch the FROM line when you have pod access and know the exact tag. The sentence-transformers install step is the same regardless.

---

### 4.3 — `docker-compose.yml`

```yaml
services:
  app:
    build:
      context: .
      dockerfile: Dockerfile.app
    ports:
      - "3000:8000"
    environment:
      - FIREWORKS_API_KEY=${FIREWORKS_API_KEY}
      - WORKER_URL=http://worker:8001
    volumes:
      - ./nn.db:/app/nn.db
    depends_on:
      - worker

  worker:
    build:
      context: .
      dockerfile: Dockerfile.worker
    devices:
      - /dev/kfd
      - /dev/dri
    group_add:
      - video
    ports:
      - "8001:8001"
```

The `devices` block is what gives the worker container access to the AMD GPU. It will be silently ignored if no GPU is present (local dev on CPU).

---

### 4.4 — Verify `docker compose up` starts cleanly

```bash
docker compose up --build
```

Frontend should be reachable at `localhost:3000`. If the worker fails on CPU (no GPU locally), that's expected — the app container's mock endpoints will still work.

---

## PHASE 5 — Scraping pipeline
*No API access needed. Real network calls, real edge cases.*

- [ ] **5.1** `ingestion.py` — RSS polling with feedparser for all Tier 1+2 sources
- [ ] **5.2** Add newspaper4k body extraction with the full fallback chain: `newspaper4k` → RSS `<content:encoded>` → Firecrawl (budget-gated) → RSS summary
- [ ] **5.3** `check_firecrawl_budget()` — `firecrawl_usage` table, daily cap = 16 credits, reset midnight UTC
- [ ] **5.4** DuckDuckGo URL discovery for panel fan-out (`site:{domain} {cluster_topic_label}`)
- [ ] **5.5** Validation gates — 300 char / 50 word floor, paywall detection regex, nav-bloat detection. Log all rejections with `passed_validation = 0`.
- [ ] **5.6** Source-specific edge cases:
  - Fox News: always fetch fresh URL from RSS, never use stored URL
  - ProPublica: use RSS `<content:encoded>` field directly
  - NYT, WaPo, Economist: tag `BODY_UNAVAILABLE`, use RSS summary only
- [ ] **5.7** Test against all 20 default sources — note failures, mark as `DEGRADED` candidates, verify fallback chain triggers correctly

---

## PHASE 6 — Consensus math and reputation scoring
*Pure Python. Write unit tests alongside the logic — this is the analytical core.*

- [ ] **6.1** `reputation.py` — all table read/write helpers
- [ ] **6.2** `compute_gc(cluster_id, threshold)` — consensus baseline from Tier 1+2 source graphs
- [ ] **6.3** `compute_oi(source_graph, gc_nodes)` — omission index, gated on `body_available`
- [ ] **6.4** Claim resolution state machine — `resolve_7d()`, `resolve_30d()`, `resolve_90d()`. Only `resolve_90d` writes UNRESOLVED. Convergence type written only at absorption.
- [ ] **6.5** All six reputation dimensions: R_orig, R_val, R_speed, R_frame, R_edit, R_correct
- [ ] **6.6** Archetype assignment — compare R_orig and R_val to panel medians → one of four archetypes
- [ ] **6.7** `take_daily_snapshot()` — unconditional write once per UTC day per (source, vertical). No change-detection gate — sparklines and time-machine require gapless series.
- [ ] **6.8** Unit tests for all of the above against synthetic source graphs with known expected outputs

---

## PHASE 7 — Pre-baked demo corpus
*Editorial research + data authoring. Not coding. Start early — it unblocks the demo.*

- [ ] **7.1** Select 3–4 historical stories where coverage famously fractured
- [ ] **7.2** For each story: write hardcoded article stubs (headline, body excerpt, source, published date) for all relevant panel sources
- [ ] **7.3** Manually assign extracted claims, set `current_state` and `convergence_type` for each
- [ ] **7.4** Author `reputation_snapshots` keyframes for the time-machine arc (Day 0 → Day 90 with event markers)
- [ ] **7.5** Wire `Timeline.jsx` (3.5) to replay this corpus — the demo's centerpiece animation

---

## PHASE 8 — Unblocked only after API access arrives
*Do not attempt before credentials are confirmed.*

- [ ] **8.1** Benchmark Fireworks: DeepSeek-V4-Pro vs Llama 3.3 70B. 20 extraction calls on demo corpus articles, compare JSON parse failure rate and output quality. Pick the winner.
- [ ] **8.2** Set up sentence-transformers on the GPU pod with ROCm — confirm `device="cuda"` maps to the Radeon GPU via ROCm
- [ ] **8.3** Confirm embedding model VRAM fit — `nomic-embed-text` or `bge-large-en`, both under 1GB
- [ ] **8.4** `llm_client.py` — OpenAI-compatible client pointing at Fireworks base URL, key from env
- [ ] **8.5** `processing.py` — entity clustering (sentence-transformer + DBSCAN), framing neutralization (LLM Call 2), Vf embeddings
- [ ] **8.6** `analysis.py` — graph extraction (LLM Call 3), consensus baseline (wraps Phase 6), outlier detection (Python set math), forensic synthesis (LLM Call 4)
- [ ] **8.7** Full pipeline end-to-end on demo corpus — verify against known expected values from Phase 7
- [ ] **8.8** `scheduler.py` — APScheduler: 2-hour discovery, daily resolution at 3am UTC, daily snapshot at 3:30am UTC, watchdog every 30 min

---

## QUICK REFERENCE — What's blocked vs unblocked

| Unblocked now | Blocked until API access |
|---|---|
| Phases 1–7 entirely | Fireworks API calls (8.1, 8.4) |
| All frontend pages | Sentence-transformer on GPU pod (8.2, 8.3) |
| Database schema + seed | BERTopic clustering (needs embeddings) |
| FastAPI mock endpoints | Full end-to-end pipeline run (8.7) |
| Docker Compose setup | APScheduler with live pipeline (8.8) |
| Scraping pipeline | LLM call wrappers (8.5, 8.6) |
| Consensus + reputation math | — |
| Demo corpus authoring | — |