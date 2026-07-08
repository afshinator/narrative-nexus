# Round 111 — UX32: Cluster Report coverage stat block + tempo descriptor

**Date:** 2026-07-09
**Order:** UX32
**Status:** COMPLETE
**Branch:** main

## Changes

### API (app/main.py)

Added to `/api/clusters/{cluster_id}/report` response summary:
```python
"articleCount": COUNT(DISTINCT article_id) FROM claims,
"coverageStart": MIN(a.published_at),
"coverageEnd":   MAX(a.published_at),
```

### Frontend (ClusterReport.tsx)

Added "Coverage" card beside Consensus Summary in a 2-column grid:
- Tempo descriptor: `"48-day arc"` (≥30d) or `"5-day surge"` (<30d) — computed per cluster
- Coverage window: `Jun 24 – Jun 29, 2026 (5 days)`
- Article count, claim count, source count

Layout: `grid grid-cols-[1fr_280px]` on lg screens.

### Test update (cluster-report.test.tsx)

Updated consensus summary stats assertion — numbers now appear in both Consensus Summary and Coverage blocks.

## Verified against UX31 audit

```
966: 6 articles, 19 claims, 3 sources, 2026-03-10 → 2026-04-27  ✓
924: 61 articles, 138 claims, 20 sources, 2026-06-24 → 2026-06-29  ✓
```

## Verification

| Check | Result |
|-------|--------|
| Build | `✓ built in 495ms` |
| Vitest | 12 failed (baseline), 119 passed, 4 skipped |
| FP | 378/10/358/17/13653 |
| Font floor | All ≥ 0.75rem (`font-mono text-[0.75rem]`) |
| Contrast | Uses existing `--nn-text` / `--nn-text-dim` tokens |
| Absorption strip | Unchanged |
| Title block | Unchanged |

## Files Changed

```
app/main.py                          | +12 lines
src/pages/ClusterReport.tsx          | +55 lines
src/__tests__/cluster-report.test.tsx | 3 lines adjusted
```

## Compliance Table

| # | Requirement | Met? | Evidence |
|---|-------------|------|----------|
| 1 | Coverage stat block beside absorption strip | YES | Grid layout, Coverage card beside Consensus Summary |
| 2a | Tempo descriptor: "48-day arc" (≥30) / "5-day surge" (<30) | YES | `THRESHOLD = 30` constant, computed per cluster |
| 2b | Descriptor factual/neutral — no adjectives | YES | "arc" / "surge" only |
| 3 | DB-driven, not hardcoded | YES | All counts from API queries, date window from DB |
| 4a | 966 matches UX31 audit | YES | 6/19/3/48d via API |
| 4b | 924 matches UX31 audit | YES | 61/138/20/5.1d via API |
| 5a | Font floor ≥ 0.75rem | YES | Coverage card uses `text-[0.75rem]` and `text-[0.78rem]` |
| 5b | Contrast WCAG AA | YES | Uses existing design tokens |
| 5c | Absorption strip unchanged | YES | Consensus Summary card content preserved |
| 5d | Title block unchanged | YES | Kicker/h1/description unchanged |
| 5e | Build passes | YES | `✓ built in 495ms` |
| 5f | Vitest baseline | YES | 12 failed (baseline), 0 new |
| — | FP 378/10/358/17/13653 | YES | Confirmed start + end |
| — | STATUS.md updated | YES | UX32 phase line added |
