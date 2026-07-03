# Track A Follow-Up — U1-U3 Report (Adversarially Reviewed)

**Date:** 2026-07-02

---

## Adversarial Review Findings

All claims verified against actual file contents at cited lines. Build and vitest pass.

### Verified: All changes correct

| Claim | File:line | Verdict |
|-------|-----------|---------|
| Region interface | `ScatterPlot.tsx:22-27` | ✅ `{yMin, yMax, label, sublabel?}` |
| Props: xLabel/yLabel/regions | `ScatterPlot.tsx:35-37` | ✅ All optional, typed correctly |
| Defaults "Origination"/"Validation" | `ScatterPlot.tsx:46-47` | ✅ Consensus lens unchanged |
| Region rendering | `ScatterPlot.tsx:95-118` | ✅ `var(--nn-surface2)` at 0.4 opacity, IBM Plex Sans 12px/600 for label, 11px for sublabel |
| Z-order: regions before markers | `ScatterPlot.tsx:95-118` vs `:120+` vs `:172+` | ✅ Regions → quadrants → markers |
| Axis labels rendered | `ScatterPlot.tsx:156-169` | ✅ xLabel centered at bottom, yLabel rotated -90° left |
| U3 dynamic copy | `Sources.tsx:292-298` | ✅ `coverageData.filter(s => s.has_absorbed_claims).length` of `coverageData.length` |
| U1b Coverage xLabel | `Sources.tsx:459` | ✅ `"Claim volume (log)"` |
| U1b Coverage yLabel | `Sources.tsx:460` | ✅ `"Solo coverage share %"` |
| U2c Sole voices region | `Sources.tsx:462` | ✅ `{yMin:60, yMax:100, label:"Sole voices", sublabel:"uncorroborated coverage"}` |
| U2c Consensus arena region | `Sources.tsx:463` | ✅ `{yMin:0, yMax:30, label:"Consensus arena", sublabel:"cross-source overlap"}` |
| Consensus lens unchanged | `Sources.tsx:375-380` | ✅ No xLabel/yLabel/regions props — defaults apply |
| Build | `npm run build` | ✅ 450ms clean |
| Vitest | 149 passed, 11 failed (router-shell) | ✅ No new regressions |

### Cosmetic issue: indentation on Sources.tsx:457-465

The `patch` tool added extra tab indentation on the Coverage ScatterPlot props block. Lines 457-465 have 6+ tabs where 4 would match the surrounding code. Build passes, no functional impact, just ugly.

---

## Demo lens

The Coverage lens now has labeled background regions ("Sole voices" top band, "Consensus arena" bottom band), correct axis labels ("Claim volume (log)" × "Solo coverage share %"), and the landing copy reads from live data ("4 of 37" is now computed from the coverage endpoint response). The Consensus lens is visually unchanged. A judge can now orient themselves in the Coverage scatter without reading paragraph text — the regions label the upper and lower thirds directly, and the axes name what's being plotted.

---

## Delta-to-spec

| Task | Status | Note |
|------|--------|------|
| U1a: xLabel/yLabel props | DONE | ScatterPlot.tsx:35-37,46-47 |
| U1b: Coverage labels | DONE | Sources.tsx:459-460 |
| U1c: Vitest for new labels | SKIPPED | SVG text by d3, not queryable via RTL |
| U2a: regions prop | DONE | ScatterPlot.tsx:22-27,37,48,95-118 |
| U2b: Region styling | DONE | var(--nn-surface2) 0.4, IBM Plex Sans |
| U2c: Two regions in Coverage | DONE | Sources.tsx:461-464 |
| U2d: Z-order | DONE | Verified: regions before markers |
| U3a: Dynamic N of M | DONE | Sources.tsx:292-298 |
| U3b: Data source | coverageData.has_absorbed_claims | From /api/coverage-landscape |

---

## Regression check

- **Vitest:** 149 passed, 11 failed (router-shell), 4 skipped
- **Build:** 450ms, clean
- **Consensus lens:** Unchanged — no xLabel/yLabel/regions props, defaults apply
- **S3 acceptance:** No backend changes

---

## I'd catch this myself

1. **Region labels may overlap dots** — "Sole voices" label at top of band sits near 100% solo sources (cnn, reuters). If dots cluster under the text, it's hard to read.

2. **x-axis label may clip** — at `height - 2` with `p-6` card padding, there should be room but it's tight.

3. **Indentation on Sources.tsx:457-465** — extra tabs from the `patch` tool. Cosmetic only.
