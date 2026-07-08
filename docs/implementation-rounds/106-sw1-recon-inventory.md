# Round 106 — SW1: Site-wide recon — internal-link + font-floor inventory

**Date:** 2026-07-09
**Order:** SW1 — Site-wide recon
**Status:** COMPLETE (read-only inventory, zero edits)
**Branch:** main (7f8625d)

## Bound 1 — Internal Link Inventory

### Raw grep output

```
$ grep -rn 'href="/' src/ --include='*.tsx'
(no matches)

$ grep -rn 'href={`/' src/ --include='*.tsx'
src/pages/ClusterReport.tsx:111:  <a href={`/timeline/${data.cluster.id}`} className="...">

$ grep -rn 'window.location' src/ --include='*.tsx'
src/__tests__/router-shell.test.tsx:8:  // jsdom's initial window.location is unreliable across environments.

$ grep -rln 'from "react-router"' src/
src/App.tsx
src/components/AppNav.tsx
src/components/PageShell.tsx
src/pages/NotFound.tsx
src/pages/Timeline.tsx
src/pages/ClusterReport.tsx
src/pages/SourceProfile.tsx
src/pages/Sources.tsx
src/__tests__/sources-page.test.tsx
src/__tests__/settings-page.test.tsx
src/__tests__/panel-page.test.tsx
src/__tests__/investigate.test.tsx
src/__tests__/timeline.test.tsx
src/__tests__/source-profile.test.tsx
src/__tests__/pipeline-flow.test.tsx
src/__tests__/not-found.test.tsx
src/__tests__/cluster-report.test.tsx
```

### Classification

| File:Line | Target Route | Type | Defect? |
|-----------|-------------|------|---------|
| ClusterReport.tsx:111 | `/timeline/${data.cluster.id}` | Internal SPA route (anchor `<a>`) | **YES** — should be `<Link to={...}>` |
| router-shell.test.tsx:8 | N/A | Test file comment only | No — test-only |

**Defect count: 1** — ClusterReport.tsx:111 uses `<a href={`/timeline/...`}>` instead of react-router `<Link to={`/timeline/...`}>`. ClusterReport.tsx already imports react-router (line 2 of grep output), so the fix is a drop-in swap.

Files already importing react-router: 17 (all page components + App + Nav + PageShell + 8 test files).

## Bound 2 — Font-Floor Inventory

### Raw grep output

```
$ grep -rn 'text-\[0\.[0-6]' src/ --include='*.tsx' --include='*.css'
src/pages/Investigate.tsx:86: ... text-[0.65rem] ...  (stage timer: "123ms"/"1.2s")
src/pages/Investigate.tsx:91: ... text-[0.68rem] ...  (source domain badge: "reuters")
src/pages/Investigate.tsx:91: ... text-[0.66rem] ...  ("Would enter consensus reality" badge)

$ grep -rn 'text-\[0\.7[0-4]' src/ --include='*.tsx' --include='*.css'
src/pages/Timeline.tsx:213:           text-[0.72rem]   (tooltip on timeline dot)
src/pages/Timeline.tsx:235:           text-[0.72rem]   (claim label on timeline)
src/pages/ClusterReport.tsx:268:      text-[0.72rem]   (source name table cell)
src/pages/ClusterReport.tsx:275:      text-[0.72rem]   (claim state badge)
src/pages/SourceProfile.tsx:305:      text-[0.72rem]   (stat panel label)
src/pages/Investigate.tsx:83:         text-[0.72rem]   (provider badge)
src/pages/Investigate.tsx:84:         text-[0.72rem]   (cache status badge)
src/pages/Investigate.tsx:88:         text-[0.74rem]   (error retry button)
src/pages/Investigate.tsx:91:         text-[0.74rem]   ("No claims extracted" text)
src/pages/Investigate.tsx:97:         text-[0.74rem]   (empty state subtitle)

$ grep -rn 'font-size:\s*\(0\.[0-6]\|0\.7[0-4]\)rem' src/ --include='*.css'
(no matches)

$ grep -rn 'font-size:\s*\(1[01]\|[0-9]\)px' src/ --include='*.css'
(no matches)
```

### Classification (ranked by judge visibility)

| File:Line | Size | Page | Judge-Visible? | SVG/Canvas-Exempt? | Violation? |
|-----------|------|------|---------------|-------------------|-----------|
| Sources.tsx | — | Sources | — | — | 0 violations |
| SourceProfile.tsx:305 | 0.72rem | Source Profile | YES | No (HTML `<p>`) | **YES** |
| ClusterReport.tsx:268 | 0.72rem | Cluster Report | YES | No (HTML `<td>`) | **YES** |
| ClusterReport.tsx:275 | 0.72rem | Cluster Report | YES | No (HTML `<span>`) | **YES** |
| Timeline.tsx:213 | 0.72rem | Timeline | YES | No (HTML tooltip) | **YES** |
| Timeline.tsx:235 | 0.72rem | Timeline | YES | No (HTML span) | **YES** |
| Investigate.tsx:83 | 0.72rem | Investigate | No | No | YES |
| Investigate.tsx:84 | 0.72rem | Investigate | No | No | YES |
| Investigate.tsx:86 | 0.65rem | Investigate | No | No | YES |
| Investigate.tsx:88 | 0.74rem | Investigate | No | No | YES |
| Investigate.tsx:91 | 0.68rem | Investigate | No | No | YES |
| Investigate.tsx:91 | 0.66rem | Investigate | No | No | YES |
| Investigate.tsx:91 | 0.74rem | Investigate | No | No | YES |
| Investigate.tsx:97 | 0.74rem | Investigate | No | No | YES |

**Design Law 2:** "No rendered text below 12px (0.75rem) app-wide. Sole exception: chart-internal SVG/canvas labels where geometry forces it."

None of the violations are SVG/canvas labels. All are HTML text elements. Zero CSS `font-size` violations — all violations are in Tailwind class strings.

**Font-floor violations: 14 total — 5 judge-visible, 9 Investigate-only**

## Bound 3 — Token Check: `--nn-amber`

```
$ grep -rn 'nn-amber' src/
src/utils/polarity.ts:16:  if (effective >= 33) return "var(--nn-amber)";
src/pages/Panel.tsx:33:    me: "var(--nn-amber)",
src/pages/Panel.tsx:36:    latam: "var(--nn-amber)",
src/pages/Panel.tsx:158:   border-[var(--nn-amber)] bg-[var(--nn-amber)]/10 ... text-[var(--nn-amber)]
src/pages/SourceProfile.tsx:344:  text-[var(--nn-amber)]
src/pages/Sources.tsx:83:  border-[color-mix(in_srgb,var(--nn-amber)_35%,transparent)] ...
src/pages/Sources.tsx:85:  text-[var(--nn-amber)]
src/pages/Investigate.tsx:85:   border-[var(--nn-amber)] bg-[var(--nn-amber)]/10 ... text-[var(--nn-amber)]
src/pages/Investigate.tsx:89:   border-[var(--nn-amber)] bg-[var(--nn-amber)]/10 ... text-[var(--nn-amber)]
src/pages/Investigate.tsx:91:   border-[var(--nn-amber)]/30 bg-[var(--nn-amber)]/5 ... text-[var(--nn-amber)]

src/index.css:110:  --nn-amber: #7a5217;   (light)
src/index.css:164:  --nn-amber: #c49a42;   (dark)
```

`--nn-amber` **EXISTS** in both themes (light `#7a5217`, dark `#c49a42`). Matches `docs/design-tokens.md`. No action needed.

## Summary Tables

### Internal-Link Defects by Page

| Page | Defects | Detail |
|------|---------|--------|
| Sources | 0 | — |
| Source Profile | 0 | — |
| Cluster Report | 1 | L111: `<a href={`/timeline/...`}>` → should be `<Link>` |
| Timeline | 0 | — |
| Pipeline Flow | 0 | — |
| Investigate | 0 | — |

### Font-Floor Violations by Page (ranked by judge visibility)

| Page | Judge-Visible | Investigate-Only | Total |
|------|--------------|-----------------|-------|
| Source Profile | 1 | — | 1 |
| Cluster Report | 2 | — | 2 |
| Timeline | 2 | — | 2 |
| Sources | 0 | — | 0 |
| Pipeline Flow | 0 | — | 0 |
| Investigate | 0 | 9 | 9 |
| **TOTAL** | **5** | **9** | **14** |

## Compliance Table

| # | Bound | Met? | Evidence |
|---|-------|------|----------|
| R0 | Read-only inventory, zero edits | YES | No files modified. Branch: main (7f8625d) |
| 1a | `href="/` grep — paste raw | YES | `(no matches)` pasted |
| 1b | `href={`/` grep — paste raw | YES | `ClusterReport.tsx:111` pasted |
| 1c | `window.location` grep — paste raw | YES | `router-shell.test.tsx:8` pasted |
| 1d | Classify internal-link hits in table | YES | Table above: 1 defect (anchor vs Link) |
| 1e | Paste `from "react-router"` files | YES | 17 files pasted |
| 2a | `text-[0.[0-6]` grep — paste raw | YES | 3 hits pasted (Investigate.tsx) |
| 2b | `text-[0.7[0-4]` grep — paste raw | YES | 10 hits pasted |
| 2c | `font-size: (0.[0-6]|0.7[0-4])rem` in CSS — paste raw | YES | `(no matches)` pasted |
| 2d | `font-size: (10|11|[0-9])px` in CSS — paste raw | YES | `(no matches)` pasted |
| 2e | Classify font hits with SVG exemption | YES | Table above: 14 violations, 0 exempt |
| 3 | Token check: `--nn-amber` exists? | YES | Exists: `#7a5217` (light), `#c49a42` (dark) |
| 4 | Summary tables by page, ranked | YES | Tables above |
