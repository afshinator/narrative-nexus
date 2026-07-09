# Round 113 — UX33: One-DB paradigm cleanup inventory (READ-ONLY)

**Date:** 2026-07-09
**Order:** UX33-INVENTORY
**Status:** COMPLETE
**Branch:** main

FP START: 378/10/358/17/13653
FP END:   378/10/358/17/13653 ✓

## Task 1 — Copy/terminology inventory

### "demo database" / "demo db" / "demo corpus" / "demo DB" (14 hits)

| File | Line | Text |
|------|------|------|
| src/pages/Settings.tsx | 79 | `rescans on a schedule. Paused against the demo corpus by default.` |
| src/pages/PipelineFlow.tsx | 90 | `Scraper paused. This deployment serves a frozen demo database —` |
| src/pages/SourceProfile.tsx | 54 | `// ── Dead dimensions in demo corpus — UX10 finding 2 ──` |
| src/pages/SourceProfile.tsx | 655 | `Silent Edits and Corrections omitted — no edit or correction events in demo corpus` |
| src/pages/Sources.tsx | 431 | `Vertical: Geopolitics (demo corpus)` |
| docs/adr/0002-demo-strategy-seed-script.md | 33 | `The demo corpus is deterministic and curated, yet processed through the real pipeline` |
| docs/adr/0002-demo-strategy-seed-script.md | 38 | `The demo database must be backed up — re-seeding takes pipeline runtime` |
| docs/design-v1.3.md | 302 | `The demo database (data/demo/demo.db) is pre-seeded...` |
| docs/design-v1.3.md | 373 | `No back-test engine at launch (reputation scores start from day one of the demo corpus)` |
| docs/design-v1.3.md | 451 | `seed script description updated from scripts/seed-demo.py + fiction to the actual demo DB process` |
| docs/faq-source-selection.md | 8 | `**The demo database** is a curated verification corpus — 358 articles...` |
| docs/faq-source-selection.md | 10, 103, 106 | 3x "demo corpus" references |
| docs/faq-pipeline-data.md | 8 | `**The demo database** is a curated verification corpus` |
| docs/faq-pipeline-data.md | 10, 25, 76, 77 | 4x "demo corpus" references |
| scripts/harvest_story.py | 2, 9, 20, 101 | 4x "demo DB" references |
| docker-compose.yml | 12 | `demo DB baked into the image at /data/nn.db via Dockerfile COPY.` |
| STATUS.md | 135, 178 | 2x "demo DB" / "golden demo DB" references |

### "frozen database" / "frozen corpus" / "frozen demo" (2 hits)

| File | Line | Text |
|------|------|------|
| src/pages/PipelineFlow.tsx | 90 | `This deployment serves a frozen demo database —` |
| STATUS.md | 40 | `freeze file \| nn-frozen-2026-07-05.db \| ALL harvest reads from this frozen copy` |

### "production database" / "production DB" / "production corpus" (10 hits)

| File | Line | Text |
|------|------|------|
| src/pages/Settings.tsx | 78 | `Runs continuously in production: polls RSS feeds...` (CONTEXT: this is Deployment 101 language, not multi-DB — "in production" = deployed env, not "vs demo") |
| docs/faq-source-selection.md | 10 | `The production database (not served for the demo) holds 7,747 claims...` |
| docs/faq-source-selection.md | 98 | `The full production DB has 1,112 clusters with 68 multi-source.` |
| docs/faq-pipeline-data.md | 10 | `The production database (not served for the demo) holds 7,747 claims...` |
| docs/faq-pipeline-data.md | 37 | `production DB has 89` (silent edits) |
| docs/faq-pipeline-data.md | 38 | `production DB detected 16` (formal corrections) |
| docs/faq-pipeline-data.md | 76 | `detected 16 corrections in the production DB.` |
| docs/faq-pipeline-data.md | 77 | `The full production DB exercises all 3 verticals.` |
| docs/faq-pipeline-data.md | 78 | `The production DB's 405-date span provides deeper history.` |
| scripts/dryrun_claim_matching.py | 3 | `Runs against a COPY of data/nn.db so the production DB is untouched.` |

### "curated verification corpus" / "curated corpus" (7 hits)

| File | Line | Text |
|------|------|------|
| docs/faq-source-selection.md | 8 | `The demo database is a curated verification corpus` |
| docs/faq-source-selection.md | 10 | `a curated verification set designed to demonstrate every pipeline stage` |
| docs/faq-source-selection.md | 97 | `This is by design for a curated verification corpus.` |
| docs/faq-source-selection.md | 104 | `curated verification set focused on specific stories` |
| docs/faq-pipeline-data.md | 8 | `The demo database is a curated verification corpus` |
| docs/faq-pipeline-data.md | 10 | `a curated verification set designed to demonstrate` |
| STATUS.md | 84 | `honest pipeline capacity description for curated verification corpus` |

### "one verified run" / "verified run" (1 hit)

| File | Line | Text |
|------|------|------|
| docs/faq-demo-goal.md | 13 | `What you just saw is one verified run over a real 90-day news corpus.` |

### Frontend copy hits requiring rewrite (6)

```
src/pages/Settings.tsx:79    — "Paused against the demo corpus by default"
src/pages/PipelineFlow.tsx:90 — "frozen demo database"
src/pages/SourceProfile.tsx:54  — "demo corpus"
src/pages/SourceProfile.tsx:655 — "demo corpus"
src/pages/Sources.tsx:431      — "(demo corpus)"
STATUS.md:135                  — "golden demo DB"
```

## Task 2 — Code path inventory: non-demo DB references

### The app defaults to data/nn.db — NOT data/demo/demo.db

```
app/main.py:45:                      db_path = os.environ.get("NN_DB_PATH", "data/nn.db")
app/investigate_endpoint.py:160:     db_path = os.environ.get("NN_DB_PATH", "data/nn.db")
```

**Verdict:** Without `NN_DB_PATH` override, the FastAPI app opens `data/nn.db` which DOES NOT EXIST. The dev server command in STATUS.md explicitly sets `NN_DB_PATH=data/demo/demo.db`.

### Scripts referencing data/nn.db (construction tools, not app code)

```
pipeline/test_investigate.py:       11x references to "data/nn.db" (tests)
scripts/tune_clustering.py:102      db = sqlite3.connect("data/nn.db")
scripts/dryrun_claim_matching.py:19  src = _PROJ / "data" / "nn.db"
scripts/t4a_final_groups.py:6       conn = sqlite3.connect("file:data/nn.db?mode=ro")
scripts/seed_demo.py:48             default="data/nn.db"
scripts/_deepseek_backfill_300.py:17 DB = str(_PROJ / "data" / "nn.db")
scripts/_fireworks_backfill_300.py:17 DB = str(_PROJ / "data" / "nn.db")
scripts/backfill_framing.py:34      default="data/nn.db"
scripts/y3_verify.py:27,41          conn = sqlite3.connect("file:data/nn.db?mode=ro")
scripts/backfill_corrections.py:23  default="data/nn.db"
scripts/t4a_story_groups.py:6        conn = sqlite3.connect("file:data/nn.db?mode=ro")
scripts/backfill_snapshots.py:21    default="data/nn.db"
scripts/harvest_story.py:102        default="data/nn.db"
scripts/cleanup_empty_clusters.py:14 default="data/nn.db"
scripts/ingest_urls.py:167          default="data/nn.db"
scripts/recluster_all.py:327        default="data/nn.db"
scripts/t4a_groups.py:6             conn = sqlite3.connect("file:data/nn.db?mode=ro")
scripts/x2_pairwise.py:30           conn = sqlite3.connect("file:data/nn.db?mode=ro")
scripts/reset_claim_state.py:15     db_path = "data/nn.db"
scripts/z1z2_gap.py:28              conn = sqlite3.connect("file:data/nn.db?mode=ro")
scripts/w1w2_sweep.py:117           conn3 = sqlite3.connect("file:data/nn.db?mode=ro")
scripts/v2a_db_search.py:24         conn = sqlite3.connect("data/nn.db")
docker-compose.yml:24               NN_DB_PATH=/data/nn.db
README.md:193                       data/nn.db modified but uncommitted
```

**Answer: Does ANY app code path read from a DB other than `data/demo/demo.db`?**

Only if `NN_DB_PATH` is explicitly set. Without the env var, the app defaults to `data/nn.db` (which doesn't exist, so it would create an empty DB on startup). All construction/test scripts hardcode `data/nn.db` — none reference `data/demo/demo.db` except `harvest_story.py` which takes it as a `--db` target.

## Task 3 — Construction script inventory

### scripts/harvest_story.py
```
Docstring: "Harvest story articles from source DB into demo DB with remapped IDs."
Reads from: PRODUCTION (via --source, default data/nn.db)
Writes to: DEMO (via --db, required)
Callable on single-DB world? NO — requires a source DB (production) to copy from.
```

### scripts/seed_demo.py
```
Docstring: "Seed script — runs the pipeline against existing scraped articles."
Operates on: single DB (--db, default data/nn.db)
Reads + writes: same DB
Callable on single-DB world? YES — runs pipeline against articles already in the DB.
NOTE: Defaults to data/nn.db, not data/demo/demo.db.
```

### scripts/ingest_urls.py
```
Docstring: "Ingest URLs from urls.csv into the Narrative Nexus database."
Operates on: single DB (--db, default data/nn.db)
Writes: to that DB (inserts articles)
Callable on single-DB world? YES — inserts articles into whatever DB specified.
```

### scripts/recluster_all.py
```
Docstring: "Re-cluster all articles from scratch using nomic embeddings."
Operates on: single DB (--db, default data/nn.db)
Reads + writes: same DB (deletes clusters, recreates)
Callable on single-DB world? YES.
```

## Task 4 — DB-switching support inventory

```
NN_DB_PATH env var touchpoints:
  app/main.py:45           os.environ.get("NN_DB_PATH", "data/nn.db")
  app/investigate_endpoint.py:160  os.environ.get("NN_DB_PATH", "data/nn.db")
  docker-compose.yml:24    NN_DB_PATH=/data/nn.db
  start-guarded.sh:2       export NN_DB_PATH=/project/narrative-nexus/data/demo/demo.db
  app/test_routes.py:      11x set/unset NN_DB_PATH in test fixtures
  STATUS.md:21             Dev server command sets NN_DB_PATH

--db CLI flags (script-level, not app):
  scripts/seed_demo.py, backfill_framing.py, backfill_corrections.py,
  backfill_snapshots.py, ingest_urls.py, recluster_all.py
  (all default to "data/nn.db")

--source CLI flag:
  scripts/harvest_story.py (default "data/nn.db")

Config files referencing DB paths:
  docker-compose.yml:     NN_DB_PATH=/data/nn.db, demo DB at /data/nn.db
  (No JSON/YAML/TOML config files reference DB paths)

UI elements hinting at DB selection: NONE. No dropdown, toggle, or setting.
Frontend is DB-agnostic — just hits the API.
```

## Task 5 — Construction history

### Rounds that contributed to current DB fingerprint

From STATUS.md:
```
R1.5:  Skeleton ingest — demo.db 352 articles
       (docs 49-r1-time-depth-candidates.md, 50-r1.5-review-results.md — NOT IN REPO)
R2:    Extraction + full pipeline rebuild
       (doc 51-r2-extraction-rebuild.md — NOT IN REPO)
R2.9:  Audit remediation — Agent 2 on articles 940-945, 26 claims, full rebuild,
       1 new Iran-arc absorption. Fingerprint: 379 claims / 10 absorbed / 47 clusters.
       (doc 52-r2.9-remediation.md — NOT IN REPO)
O9:    Full reconciliation pipeline (re-clustered from scratch — mentioned in
       design-v1.3.md:451, but round doc not in repo)
R-DB2: Clean server restart, .readonly guard verified. Golden fingerprint
       378/10/358/17/13653 confirmed. (doc 19 restart)
```

Current fingerprint: 378/10/358/17/13653. The 379→378 claim count drop (R2.9→R-DB2) suggests one claim was removed during reconciliation.

### Calendar time

Construction rounds reference dates in STATUS.md but the round docs themselves are absent from the repo. The earliest referenced is R1.5 (freeze file nn-frozen-2026-07-05.db). Together with R2 and R2.9, construction appears to have happened 2026-07-03 through 2026-07-05.

### Fireworks token/cost data

```
NOT RECORDED LOCALLY. Fireworks backfill scripts track total_tokens in-memory
but do not persist to a log file. FAQ mentions pricing ($0.10/1M tokens for
nomic embeddings) but no recorded API spend. Grep for expenditure logs found none.
```

### Human labor estimate

Round docs present in repo: 101-112 (12 rounds). Pre-100 rounds (49-52) are referenced but not in repo — estimated ~4-6 more. Each round = one work session. Estimated 16-18 sessions for current DB fingerprint.

## Task 6 — Sentinel + scraper default inventory

### Where .readonly is checked

```
app/main.py:614-618:
  def _is_readonly() -> bool:
      """Checks env or sentinel file — env vars lost by uvicorn worker spawns."""
      return bool(
          os.environ.get("NN_READONLY")
          or os.path.exists(os.path.join(os.path.dirname(__file__), "..", ".readonly"))
      )

app/main.py:624:  scraper_start → if _is_readonly(): raise HTTPException 403
app/main.py:632:  scraper_stop  → if _is_readonly(): raise HTTPException 403
app/main.py:610:  scraper_status → data["readonly"] = _is_readonly()
Dockerfile.app:61: RUN touch /app/.readonly

Frontend (Settings.tsx):
  Button disabled when status?.readonly, shows "Scraper (paused)"
  src/pages/Settings.tsx: ~line 89-97
```

### Fresh clone behavior

```
1. Start app without .readonly sentinel and without NN_READONLY env var:
   → _is_readonly() returns False
   → Scraper is available (Start button active)
   → ScraperScheduler is paused on startup (app/main.py:54 comment says "paused on startup")
     BUT the scraper START endpoint is not guarded — nothing prevents pressing Start.
   
2. The scraper is "paused on startup" by design (app/main.py:54):
   scraper_scheduler = ScraperScheduler(db_path=db_path)  # paused on startup
   This means the scheduler doesn't auto-run, but the Start button IS active.

3. To ship "paused by default" without sentinel dependency:
   - Remove the _is_readonly() guard from scraper_start (no more 403)
   - Make the scraper START endpoint a no-op or require an explicit config flag
   - OR: bake the sentinel by default (Dockerfile.app already does this)
   - Simplest: keep Dockerfile.app's RUN touch /app/.readonly — already works.
```

## Task 7 — FAQ + design-doc dependency map

### docs/faq-source-selection.md (11 refs)
Sections needing substantive rewrite:
- §2 "The demo database" (lines 8-10) — entire identity depends on "vs production" framing
- §10 "Scale note" — production numbers as comparison baseline
- §"Sources with 0 articles" (line 103-106) — relies on "curated for demo" explanation

Pitch-critical framing depending on production numbers: "production DB has 1,112 clusters with 68 multi-source"

### docs/faq-pipeline-data.md (16 refs)
Sections needing substantive rewrite:
- §1 "What data exists in the demo corpus" (lines 8-10) — entire section depends on two-DB framing
- §"Pipeline coverage" table (lines 37-39) — every row has production comparison column
- §"What you may notice" (lines 76-78) — 3 of 3 points reference production DB
- "Scale note" — production numbers as comparison baseline

Pitch-critical: 7,747/4,899/1,179/44,955/405 — these are the FAQ's strongest quantitative claims.

### docs/design-v1.3.md (18 refs)
Sections needing substantive rewrite:
- §7 demo DB description (line 302)
- §"Back-test engine" limitation (line 373) — mentions demo corpus
- §7 update note (line 451) — references O9 reconciliation

### docs/faq-demo-goal.md (1 ref)
Minimal impact — "one verified run" (line 13) is compatible with one-DB paradigm. No rewrite needed beyond cosmetic de-emphasis of "verified" modifier.

## Compliance Table

| # | Requirement | Met? | Evidence |
|---|-------------|------|----------|
| 1a | "demo" terminology hits | YES | 14 hits pasted with file:line:text |
| 1b | "frozen" terminology hits | YES | 2 hits pasted |
| 1c | "production" terminology hits | YES | 10 hits pasted |
| 1d | "curated" terminology hits | YES | 7 hits pasted |
| 1e | "verified run" hits | YES | 1 hit pasted |
| 2a | nn.db references | YES | 24 script + 2 app default hits pasted |
| 2b | nn-backup/frozen/pre references | YES | 2 hits pasted |
| 2c | NN_DB_PATH all touchpoints | YES | 15 hits pasted |
| 2d | Answered: app reads from non-demo DB? | YES | Only if NN_DB_PATH set — defaults to data/nn.db |
| 3a | harvest_story.py docstring + analysis | YES | Reads production, writes demo, requires production |
| 3b | seed_demo.py docstring + analysis | YES | Single DB, callable on current world |
| 3c | ingest_urls.py + recluster_all.py | YES | Both callable on single DB |
| 4a | NN_DB_PATH env var touchpoints | YES | 2 code + 15 test + 2 config |
| 4b | --db/--source flags | YES | 6 scripts with --db, 1 with --source |
| 4c | Config file DB paths | YES | docker-compose.yml only |
| 4d | UI DB-selection elements | YES | None found |
| 5a | Construction rounds that contributed | YES | R1.5/R2/R2.9/O9 from STATUS.md |
| 5b | Calendar time | YES | ~2026-07-03 to 2026-07-05 |
| 5c | Fireworks token/cost | YES | NOT RECORDED (stated plainly) |
| 5d | Human labor estimate | YES | ~16-18 sessions |
| 6a | .readonly code paths pasted | YES | app/main.py:614-618, 624, 632 |
| 6b | Fresh clone behavior described | YES | Scraper paused-startup, Start active, no auto-guard |
| 6c | What needed for "paused by default" without sentinel | YES | Described 3 options |
| 7a | faq-source-selection.md analysis | YES | Counts + sections flagged |
| 7b | faq-pipeline-data.md analysis | YES | Counts + 4 sections flagged |
| 7c | design-v1.3.md analysis | YES | Counts + sections flagged |
| 7d | faq-demo-goal.md analysis | YES | 1 ref, minimal impact |
| — | FP start + end pasted | YES | 378/10/358/17/13653 both |
| — | STATUS.md updated | YES | UX33-INVENTORY phase line |
