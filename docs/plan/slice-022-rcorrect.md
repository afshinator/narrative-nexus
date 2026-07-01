# Slice 022 — R_correct Formal Correction Detection

**Status:** Plan  
**Date:** 2026-06-30  
**Depends on:** Article bodies in DB, scraper (for future RSS path)

---

## Scope

Detect formal corrections in article bodies via inline marker patterns. Store corrections, compute R_correct per source, wire into snapshot pipeline. Note future RSS and Wayback options in README.

---

## Files to create

1. `pipeline/corrections.py` — detection logic (inline marker patterns)
2. `pipeline/test_corrections.py` — unit tests
3. `db/corrections.py` — DB helpers (create table, insert, read)

## Files to modify

4. `db/schema.sql` — add `corrections` table
5. `pipeline/snapshots.py` — add `compute_r_correct_raw()` (corrections/articles per source)
6. `pipeline/runner.py` — wire `r_correct` into snapshot computation
7. `README.md` — note future C+D options (scrape corrections pages, Wayback diffing)

---

## Architecture

### New table: `corrections`

```sql
CREATE TABLE IF NOT EXISTS corrections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    article_id INTEGER NOT NULL REFERENCES articles(id),
    detected_pattern TEXT NOT NULL,  -- which regex matched
    matched_text TEXT,               -- the matched snippet
    detected_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_corrections_article ON corrections(article_id);
```

### Detection patterns

Five regex patterns, applied to article body text:

```python
CORRECTION_PATTERNS = [
    # AP style: "CORRECTION: Corrects month to June"
    (r'\bCORRECTION:\s*(.+?)(?:\n|$)', 'ap_correction'),
    # CNN style: "This story has been updated with additional information"
    (r'\bThis (?:article|story|post) has been (?:updated|corrected)\b', 'cnn_update'),
    # NYT style: "An earlier version of this article misstated..."
    (r'\bAn earlier version of this article\b', 'nyt_earlier_version'),
    # NYT style: "Corrected on June 29, 2026"
    (r'\bCorrected on \w+ \d{1,2}, \d{4}\b', 'nyt_corrected_on'),
    # Generic: "A previous version..."
    (r'\bA previous version\b', 'previous_version'),
]
```

**False positive guard:** Skip matches where the line also matches `Editor's Note:` at paragraph start (editorial intros, not corrections).

### R_correct computation

`compute_r_correct_raw(conn, as_of)` — joins corrections → articles → source_id, counts corrections per source, divides by article count. Returns `dict[source_id, float]` (0-100).

Wired into `runner.py` alongside existing r_orig/r_val/r_speed/r_edit computation. Snapshot percentile rank applied as usual.

### When does detection run?

Two paths:
1. **Scraper path (future):** During article fetch, scan body for correction patterns. RSS tags checked first (stub for now).
2. **Backfill path (now):** Standalone script `scripts/backfill_corrections.py` reads all article bodies, runs patterns, inserts matches.

Current implementation: backfill only. Scraper integration deferred to README.

---

## Testing strategy

### Unit tests (`test_corrections.py`)

- AP correction: "CORRECTION: Corrects month to June." → detected
- CNN update: "This story has been updated with additional information." → detected
- NYT correction: "An earlier version of this article misstated the day." → detected
- False positive: "Editor's Note: Having enjoyed a long history..." → NOT detected
- Empty text → no matches
- No corrections in body → empty list

### Integration

- Backfill on test DB with 5 articles (3 with corrections) → verify rows inserted
- `compute_r_correct_raw()` test with known corrections → verify ratio

---

## Dependencies

- Zero new dependencies. Pure Python regex, SQLite.

---

## Verification checklist

1. `npm run build` — no regressions
2. `pytest -m "not network"` — all tests pass
3. `vitest run` — no regressions
4. Backfill dry-run on live DB → verify ~15 corrections found
5. `ponytail-review` against diff
6. Verify R_correct wire in runner produces 0-100 scores for 37 sources

---

## Future work (README)

- **Option C — Scrape corrections pages:** Some outlets publish corrections on dedicated URLs (nytimes.com/corrections, apnews.com/corrections). Requires per-site scraping rules.
- **Option D — Wayback/archive diffing:** Periodically re-fetch old articles, diff against stored body. Detects both silent edits AND formal corrections. Heavy on bandwidth/computation.
- **RSS correction tags:** RSS spec defines `<corrections>` and `<updated>` elements, but no major news feed uses them. Stub exists, revisit if adoption changes.
