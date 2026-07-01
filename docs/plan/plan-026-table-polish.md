# Slice 026 — Full Ledger Table Polish

## Verified problems

| # | Finding | Evidence |
|---|---------|----------|
| 1 | `.0` suffix — `97.0`, `0.0`, `64.0` | API returns REAL → JSON float → table renders raw. Scatter tooltip already rounds, table doesn't |
| 2 | R_frame + R_correct are ALL NULL (37/37 rows) | Two of six columns are entirely dashes. Looks broken |
| 3 | 25/37 R_val=0 — wall of zeros | User sees a column full of zeros with no indication of what that means |
| 4 | Explanation text is one dense paragraph | Six dimension definitions crammed into a single `<p>`. Doesn't match scatter plot's clean layout |

## Implementation

### 1. Round score values in table (`src/pages/Sources.tsx` circa line 340)

Current:
```tsx
{score != null ? score[col.key as keyof ReputationScore] : "—"}
```

Fix: apply `Math.round()` for percentile dimensions (R_orig, R_val, R_speed, R_edit, R_correct are all 0–100 after percentile_rank. R_frame will be too when wired):
```tsx
const val = score?.[col.key as keyof ReputationScore];
{val != null ? Math.round(val) : "—"}
```

### 2. Pending-indicator for all-NULL columns

Two columns (R_frame, R_correct) are entirely NULL. Instead of showing 37 rows of "—", add a single banner below the column headers:

"Framing and Corrections pending — data collection in progress."

Render below the `<thead>` as a `<tr>` with `colSpan` or as a text annotation. This tells the user the columns are intentionally empty, not broken.

### 3. Redesign explanation section

Replace the single dense `<p>` with a layout matching the scatter plot card above it. One short line per dimension, grouped by meaning:

```
Each source scored 0–100. Click column headers to sort.

Origination   — first to report stories that become consensus-absorbed
Validation    — claims absorbed by the panel consensus
Speed         — how quickly claims spread (days → percentile)
Framing*      — editorial consistency (pending)
Silent Edits  — rate of unreported article changes
Corrections*  — formal correction rate (pending)

↑ higher is better · ↓ lower is better
* Not yet computed — shows "—" for all sources
```

Font: IBM Plex Sans, 0.72rem. Use `--nn-text` for dimension names, `--nn-text-dim` for descriptions. Two-column or stacked layout.

### 4. Zero-meaning context

For R_val specifically — 25 of 37 sources show 0. Add a brief note: "Sources with 0 Validation have no consensus-absorbed claims yet." This is more honest than letting the user wonder if the data is broken.

## Files touched

| File | Changes |
|------|---------|
| `src/pages/Sources.tsx` | Format scores with Math.round(), redesign explanation, add pending banner, zero note |

Single file. No backend changes — percentile_rank already fixed in slice 025.

## Verification

- [ ] Numbers display as clean integers (97 not 97.0)
- [ ] Explanation section uses grouped layout, not one sentence
- [ ] R_frame/R_correct have pending indicator
- [ ] R_val zero note present
- [ ] `npm run build` passes
- [ ] `vitest run` passes (column header test may need updating)
