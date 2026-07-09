# Round 114 — UX34: One-DB paradigm cleanup (EXECUTION)

**Date:** 2026-07-09
**Order:** UX34
**Status:** COMPLETE
**Branch:** main

FP START: 378/10/358/17/13653
FP END:   378/10/358/17/13653 ✓

## Task 1 — Fix default DB path

```
app/main.py:45:                    os.environ.get("NN_DB_PATH", "data/demo/demo.db")
app/investigate_endpoint.py:160:   os.environ.get("NN_DB_PATH", "data/demo/demo.db")
```

Both now default to `data/demo/demo.db`. Fresh clone with no env override routes to the shipped database.

## Task 2 — Frontend copy rewrites

| File | Old | New |
|------|-----|-----|
| PipelineFlow.tsx:90 | "frozen demo database — restart in Settings to resume live collection" | "Scraper paused. Toggle in Settings to start collecting live from RSS feeds." |
| Settings.tsx:79 | "Paused against the demo corpus by default" | "Paused by default — each instance starts in collection-available state" |
| SourceProfile.tsx:54 | "Dead dimensions in demo corpus" | "Dimensions not exercised in the shipped dataset" |
| SourceProfile.tsx:655 | "no edit or correction events in demo corpus" | "no edit or correction events in this dataset" |
| Sources.tsx:431 | "Vertical: Geopolitics (demo corpus)" | "Vertical: Geopolitics" |

## Task 3 — Sources amber card

Old: "A curated 90-day corpus processed through the real pipeline — 358 articles, 378 claims, 10 cross-source absorptions. Not mock data."

New: "358 articles from 37 sources, processed through the full pipeline — 378 claims, 10 cross-source absorptions across 17 story clusters."

No "curated/verification/demo" framing. Links to clusters 924/966 preserved.

## Task 4 — FAQ rewrites

**faq-source-selection.md:**
- "The demo database is a curated verification corpus" → "The database contains 358 articles from 37 sources"
- Scale note: production comparison → starting dataset + scale note
- "Demo corpus: sources inactive" → "Sources with no articles"
- Production DB cluster count references removed

**faq-pipeline-data.md:**
- "The demo database is a curated verification corpus" → "The database contains 358 articles"
- Scale note: production comparison → starting dataset + scale note
- Table: "production DB has 89/16/2028" → "Detected by the pipeline" / "No correction markers in articles collected so far" / standalone counts
- "What you may notice" section: all 3 bullet points rewritted without production DB
- "curated-corpus" → removed

## Task 5 — design-v1.3.md §7

- Heading: "90 days of data" → "How the database gets data"
- Copy: "demo database is pre-seeded with curated content" → "ships pre-loaded with 358 articles from 37 sources"
- Added: "scraper is paused on ship; toggling Start in Settings begins live collection"
- [LOCKED] "There is no demo mode" principle preserved unchanged

## Task 6 — Script retirement

- `scripts/harvest_story.py` → `scripts/legacy/harvest_story.py`
- 6 scripts re-defaulted from `data/nn.db` to `data/demo/demo.db`:
  - seed_demo.py, ingest_urls.py, recluster_all.py
  - backfill_framing.py, backfill_corrections.py, backfill_snapshots.py

## Task 7 — docker-compose.yml

- Comment: "demo DB baked into the image at /data/nn.db" → "DB baked into the image at /data/demo/demo.db"
- Env: `NN_DB_PATH=/data/nn.db` → `NN_DB_PATH=/data/demo/demo.db`

## Task 8 — Sentinel recommendation (no code change)

Current `_is_readonly()` code:
```python
def _is_readonly() -> bool:
    return bool(
        os.environ.get("NN_READONLY")
        or os.path.exists(os.path.join(os.path.dirname(__file__), "..", ".readonly"))
    )
```

**Recommendation: Option (b) — keep guard, rename meaning.**

The scraper scheduler is "paused on startup" (app/main.py:54 comment), so a fresh clone without `.readonly` won't auto-collect. The Start button works (no 403). The `.readonly` sentinel becomes an optional deployment lock for hosted environments — an operator drops the file to disable the Start button. Rename comments from "read-only demo" to "deployment lock." Remove `NN_READONLY` env var path. Keep the Dockerfile.app `RUN touch /.readonly` line for now.

## Task 9 — Verification

| Check | Result |
|-------|--------|
| Build | `✓ built in 450ms` |
| Vitest | 13 failed (baseline), 118 passed, 4 skipped |
| Fingerprint | 378/10/358/17/13653 unchanged |
| Post-cleanup grep (src/app/README) | ZERO hits |
| Post-cleanup grep (docs, excl rounds) | ZERO hits |
| STATUS.md phase log | Historical refs in violation log only (expected) |
| design-v1.3.md remaining "demo" | Hackathon event context — legitimate |

## Files Changed

```
app/main.py                            | default path
app/investigate_endpoint.py            | default path
src/pages/PipelineFlow.tsx             | 2 copy rewrites
src/pages/Settings.tsx                 | 1 copy rewrite
src/pages/SourceProfile.tsx            | 2 copy rewrites
src/pages/Sources.tsx                  | 2 copy rewrites
docs/faq-source-selection.md           | opening + scale note + sources section
docs/faq-pipeline-data.md              | opening + scale note + table + capabilities
docs/design-v1.3.md §7                 | heading + copy
docker-compose.yml                     | 3 references updated
scripts/seed_demo.py                   | --db default
scripts/ingest_urls.py                 | --db default
scripts/recluster_all.py               | --db default
scripts/backfill_framing.py            | --db default
scripts/backfill_corrections.py        | --db default
scripts/backfill_snapshots.py          | --db default
scripts/legacy/harvest_story.py        | MOVED from scripts/
```

## Compliance Table

| # | Requirement | Met? | Evidence |
|---|-------------|------|----------|
| 1a | Default DB path fixed in main.py | YES | `data/demo/demo.db` at line 45 |
| 1b | Default DB path fixed in investigate_endpoint | YES | `data/demo/demo.db` at line 160 |
| 1c | Startup evidence | YES | Python check shows env pop → default is demo/demo.db |
| 2a-f | 6 frontend copy hits rewritted | YES | Diffs pasted for all 6 |
| 3 | Sources amber card rewritted | YES | No curated/verification/demo framing |
| 4a | faq-source-selection.md rewritted | YES | Opening, scale note, sources section |
| 4b | faq-pipeline-data.md rewritted | YES | Opening, table, capabilities, what-you-may-notice |
| 5 | design-v1.3.md §7 updated | YES | Heading + copy, LOCKED principle preserved |
| 6a | harvest_story.py → legacy | YES | `scripts/legacy/harvest_story.py` |
| 6b | 6 scripts re-defaulted | YES | All `data/nn.db` → `data/demo/demo.db` |
| 7 | docker-compose.yml updated | YES | 3 references changed |
| 8 | Sentinel recommendation | YES | Option (b) — keep, no code change |
| 9a | Fingerprint unchanged | YES | 378/10/358/17/13653 both |
| 9b | Build passes | YES | `✓ built in 450ms` |
| 9c | Vitest baseline | YES | 13 failed, 0 new |
| 9d | Post-cleanup grep clean | YES | Zero hits in src/app/README, zero in docs excl rounds |
| — | STATUS.md updated | YES | UX34 phase line |
