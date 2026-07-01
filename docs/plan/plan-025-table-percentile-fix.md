# Slice 025 — Full Ledger Table + Percentile Rank Rounding

## Verified root causes

### 1. `percentile_rank()` stores raw floats (snapshots.py:151)

**Verified:** `(i / (n-1)) * 100` with n=37 produces `44.44444444444444`, `86.11111111111111`, etc. No rounding anywhere in the pipeline.

**Evidence:**
- `percentile_rank()` returns `dict[int, float]` with raw division results
- `insert_snapshot()` (db/snapshots.py:25) does `INSERT ... VALUES (?, r_orig, ...)` — raw value
- Column is `REAL` — SQLite stores full IEEE 754 double
- API serves as JSON float → frontend renders verbatim

**Affected dimensions:** R_orig, R_val, R_speed — all pass through `percentile_rank()`. R_edit and R_correct also go through it but currently produce clean values (0.0, NULL).

**DB state:** 42 rows have fractional values (out of 44,363 total). Only the latest snapshot dates have populated R_orig/R_val/R_speed — earlier dates have NULLs (see CLAUDE.md: "83% of claims created in June 2026, early dates have 0 first-reporter claims").

### 2. SCORE_COLUMNS labels don't match DIMENSIONS

**Verified:** Sources.tsx:23-30 uses shorter labels:

| Key | SCORE_COLUMNS (table) | DIMENSIONS (profile page) |
|-----|----------------------|---------------------------|
| R_speed | "Speed" | "Speed Premium" |
| R_frame | "Framing" | "Framing Consist." |

DIMENSIONS is the canonical source (defined in `src/data/scores.ts:44-51`).

### 3. Five high-priority issues from table review

| # | Issue | Evidence |
|---|-------|----------|
| 1 | Missing `scope="col"` on `<th>` | Sources.tsx:301,308 — no scope attribute |
| 2 | No keyboard support on sortable headers | Sources.tsx:303,311 — onClick only, no tabIndex/keydown |
| 3 | No `aria-sort` on sorted column | Sources.tsx:301-316 — no aria-sort attribute |
| 4 | Label mismatch vs DIMENSIONS (verified above) | |
| 5 | No directionality indicator on inverted dimensions | users can't tell if 0 is good (low edits) or bad (low origination) |

## Implementation

### Fix 1: Round in `percentile_rank()` — source-level fix

**File:** `pipeline/snapshots.py:151`

```python
# Before
pct = (i / (n - 1)) * 100 if n > 1 else 100.0
# After
pct = round((i / (n - 1)) * 100) if n > 1 else 100.0
```

**Backfill:** One-time SQL to fix existing 42 fractional rows:
```sql
UPDATE snapshots SET
  r_orig = round(r_orig),
  r_val = round(r_val),
  r_speed = round(r_speed)
WHERE r_orig IS NOT NULL AND r_orig != CAST(r_orig AS INTEGER);
```

**Impact:** All consumers fixed — table, tooltip, API, seed script, exports. +1 test in `test_snapshots.py`.

### Fix 2: Align table labels with DIMENSIONS

**File:** `src/pages/Sources.tsx:23-30`

Replace `SCORE_COLUMNS` constant. Two options:

**Option A (ponytail):** Just fix the two mismatched strings:
```tsx
const SCORE_COLUMNS = [
    { key: "R_orig", label: "Origination" },
    { key: "R_val", label: "Validation" },
    { key: "R_speed", label: "Speed Premium" },
    { key: "R_frame", label: "Framing Consist." },
    { key: "R_edit", label: "Silent Edits" },
    { key: "R_correct", label: "Corrections" },
] as const;
```

**Option B:** Derive from `DIMENSIONS` (guarantees future consistency):
```tsx
const SCORE_COLUMNS = DIMENSIONS.map(d => ({ key: d.key, label: d.label })) as const;
```

Option A is simpler (no import of DIMENSIONS). Both are correct.

### Fix 3: Add directionality indicators to column headers

**File:** `src/pages/Sources.tsx`

Add `title` attribute and small indicator to each `<th>`. Match the ReputationScore interface comments (scores.ts:8-13):

```tsx
const SCORE_COLUMNS = [
    { key: "R_orig", label: "Origination", direction: null },
    { key: "R_val", label: "Validation", direction: "↑" },    // high = favorable
    { key: "R_speed", label: "Speed Premium", direction: "↓" }, // low = favorable
    { key: "R_frame", label: "Framing Consist.", direction: "↓" },
    { key: "R_edit", label: "Silent Edits", direction: "↓" },
    { key: "R_correct", label: "Corrections", direction: null },
] as const;
```

Render with `<th title={...}>` and append the direction indicator.

### Fix 4: Add `scope="col"`, `aria-sort`, keyboard to `<th>`

**File:** `src/pages/Sources.tsx:301-316`

Three a11y additions to each `<th>`:
- `scope="col"` — WCAG H63
- `aria-sort` — "ascending" / "descending" / "none"
- `tabIndex={0}`, `onKeyDown` for Enter/Space — keyboard sorting

### Non-scope (deferred)

These from the review are explicitly deferred:
- Score formatting with decimals (R_frame/R_speed are 0-100 now too per `percentile_rank()`, so no decimal issue unless non-percentiled values appear)
- Inline arrow closures in map (pre-existing, not a bug)
- `<caption>` on table (nice-to-have)
- Dim-mode screen reader support (edge case, no user complaint)
- `handleSort` memoization (pre-existing, no user complaint)

## Files touched

| File | Changes |
|------|---------|
| `pipeline/snapshots.py` | `round()` in `percentile_rank()` + backfill script |
| `pipeline/test_snapshots.py` | Test rounded output |
| `src/pages/Sources.tsx` | Fix labels, add directionality, add scope/aria-sort/keyboard |
| `src/__tests__/sources-page.test.tsx` | Update column header test for new labels |

## Verification checklist

- [ ] `percentile_rank()` returns rounded integers
- [ ] Backfill SQL converts existing 42 fractional rows
- [ ] Table column headers say "Speed Premium" not "Speed", "Framing Consist." not "Framing"
- [ ] Column headers show ↑/↓ directionality indicators
- [ ] `<th>` elements have `scope="col"`, `aria-sort`, keyboard support
- [ ] `pytest pipeline/test_snapshots.py` passes
- [ ] `vitest run src/__tests__/sources-page.test.tsx` passes
- [ ] `npm run build` passes
