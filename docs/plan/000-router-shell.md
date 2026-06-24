# Plan: Slice 0 — Router Shell (AppNav + PageShell + Stub Pages)

## Requirements addressed

| Req | Description | How |
|-----|-------------|-----|
| REQ-064 | Sticky nav bar on every page: Logo, Sources, Source Profile, Cluster Report, Timeline, Pipeline, Investigate, Panel, Settings | `AppNav.tsx` |
| REQ-065 | Nav links to Sources page at `/` | Route + NavLink |
| REQ-066 | Nav links to Source Profile at `/source/:domain` | Route + NavLink |
| REQ-067 | Nav links to Cluster Report at `/cluster/:clusterId` | Route + NavLink |
| REQ-068 | Nav links to Timeline at `/timeline/:clusterId` | Route + NavLink |
| REQ-069 | Nav links to Pipeline Flow at `/pipeline` | Route + NavLink |
| REQ-070 | Nav links to Investigate at `/investigate` | Route + NavLink |
| REQ-071 | Nav links to Panel at `/panel` | Route + NavLink |
| REQ-072 | Nav links to Settings at `/settings` | Route + NavLink |
| REQ-001, REQ-004 | Footer "Narrative Nexus tracks consensus reality, not truth" on every page | `PageShell.tsx` |

## Dependencies

| Dep | Version | Where | Verified? |
|-----|---------|-------|-----------|
| react-router | ^7.18.0 | `package.json` | Yes — `BrowserRouter`, `Routes`, `Route`, `NavLink`, `Link`, `useLocation`, `useNavigate` all export from `"react-router"` |
| shadcn Button | — | `@/components/ui/button` | ✅ Validated — `npm run build` exits 0 after file move |

## Key assumptions (verified)

1. **BrowserRouter is in `react-router`, not `react-router-dom`.** Confirmed. `react-router/dom` only exports `HydratedRouter` and `RouterProvider` (not needed for this SPA).
2. **react-router is v7.18.0, not v8.** The version string in `package.json` is `^7.18.0`. The TODO.md comment about "React Router v8 dropped react-router-dom" was speculative/incorrect — v7.18 is the installed version, and it works the same way (BrowserRouter stays in `react-router`).

## Assumption requiring validation (Phase 3.5) — ✅ VALIDATED

**shadcn files are misplaced.** `vite.config.ts` maps `@` → `./src`. `tsconfig.app.json` maps `@/*` → `./src/*`. But shadcn CLI placed files at `./@/components/ui/button.tsx` and `./@/lib/utils.ts`. Resolving `@/components/ui/button` will look for `src/components/ui/button.tsx`, which doesn't exist.

**Fix applied:** Files moved to correct locations — `npm run build` exits 0, all imports resolve.

## Files to create

| File | Content |
|------|---------|
| `src/pages/Sources.tsx` | Stub: `export default function SourcesPage() { return <div>Sources</div> }` |
| `src/pages/SourceProfile.tsx` | Stub |
| `src/pages/ClusterReport.tsx` | Stub |
| `src/pages/Timeline.tsx` | Stub |
| `src/pages/PipelineFlow.tsx` | Stub |
| `src/pages/Investigate.tsx` | Stub |
| `src/pages/Panel.tsx` | Stub |
| `src/pages/Settings.tsx` | Stub |
| `src/pages/NotFound.tsx` | Stub: `export default function NotFoundPage() { return <div>Page not found</div> }` |
| `src/components/AppNav.tsx` | Sticky nav bar, 8 `<NavLink>` components (active highlighting free via `className` callback receiving `{ isActive }` — no `useLocation()` needed), `?` icon for onboarding (icon only, no dialog) |
| `src/components/PageShell.tsx` | `<AppNav>` + `<main><Outlet /></main>` + footer with tagline |
| `src/components/ui/button.tsx` | ✅ Already moved from `@/components/ui/` — importable via `@/components/ui/button` |

## Files to modify

| File | Change |
|------|--------|
| `src/App.tsx` | Replace entirely: `<BrowserRouter>` wrapping `<Routes>` with `<Route element={<PageShell />}>` containing all 8 nested routes + a 404 catch-all. This is the sole routing entry point. |
| `src/main.tsx` | **No changes needed** — `<App />` still renders the root, but `App` now returns the router tree. Theme subscription + theme class toggle on `<html>` stays as-is. |
| `src/App.css` | **Delete** — Vite template cruft, not used |
| `src/assets/hero.png` | **Delete** — Vite template asset, dead after App.tsx replacement |
| `src/assets/react.svg` | **Delete** — Vite template asset, dead after App.tsx replacement |
| `src/assets/vite.svg` | **Delete** — Vite template asset, dead after App.tsx replacement |
| `src/index.css` | No changes needed (already has Tailwind v4, shadcn vars, nn tokens, dark mode) |

## Architecture decision

**Routing layout:** `<BrowserRouter>` wraps the app. `PageShell` uses `<Outlet />` for nested routes. Routes structure:

```
<BrowserRouter>
  <Routes>
    <Route element={<PageShell />}>
      <Route index element={<SourcesPage />} />
      <Route path="source/:domain" element={<SourceProfilePage />} />
      <Route path="cluster/:clusterId" element={<ClusterReportPage />} />
      <Route path="timeline/:clusterId" element={<TimelinePage />} />
      <Route path="pipeline" element={<PipelineFlowPage />} />
      <Route path="investigate" element={<InvestigatePage />} />
      <Route path="panel" element={<PanelPage />} />
      <Route path="settings" element={<SettingsPage />} />
      <Route path="*" element={<NotFoundPage />} />
    </Route>
  </Routes>
</BrowserRouter>
```

This keeps the nav and footer rendered once (no remount) while swapping page content via `<Outlet />`.

## Verification

1. `npm run build` exits 0
2. `npm run dev` shows nav bar with 8 links
3. Clicking each nav link navigates to the correct URL
4. Active nav link has `aria-current="page"` attribute (NavLink provides this automatically)
5. Footer tagline "Narrative Nexus tracks consensus reality, not truth" visible on every page
6. No Vite template remnants (no React/Vite logos, no counter button)
