# Root File Inventory — READ-ONLY

**Date:** 2026-07-09
**Fingerprint:** 378 / 10 / 358 / 17 / 13653 (unchanged both ends)

---

## 1. Root File Listings

### `ls -la` (all root files)

```
total 18300
-rw-rw-r--   1 afshin afshin        0 Jul  8 12:12 --db
-rw-rw-r--   1 afshin afshin      399 Jul  8 12:12 .dockerignore
-rw-r--r--   1 afshin afshin      150 Jul  2 22:22 .env
-rw-r--r--   1 afshin afshin      979 Jul  9 09:35 .env.example
-rw-rw-r--   1 afshin afshin      716 Jul  8 12:12 .gitignore
-rw-rw-r--   1 afshin afshin      245 Jun 23 13:19 .oxlintrc.json
-rw-r--r--   1 afshin afshin        0 Jul  8 17:02 .readonly
-rw-------   1 afshin afshin      166 Jun 24 17:42 .stylelintrc.json
-rw-rw-r--   1 afshin afshin     3915 Jul  1 15:34 =0.9.5
-rw-rw-r--   1 afshin afshin      557 Jul  1 15:34 =5.0.0
-rw-rw-r--   1 afshin afshin     3427 Jul  8 12:12 CLAUDE.md
-rw-rw-r--   1 afshin afshin     1790 Jul  9 09:37 Dockerfile.app
-rw-rw-r--   1 afshin afshin     1072 Jul  2 14:20 LICENSE
-rw-rw-r--   1 afshin afshin     8855 Jul  9 12:24 README.md
-rw-r--r--   1 afshin afshin  1835709 Jul  9 12:11 app-img-01.png
-rw-r--r--   1 afshin afshin     8664 Jul  1 18:51 backfill.log
-rw-rw-r--   1 afshin afshin      200 Jul  1 15:34 biome.json
-rw-rw-r--   1 afshin afshin      516 Jun 23 13:56 components.json
-rw-r--r--   1 afshin afshin      374 Jun 26 15:53 conftest.py
-rw-rw-r--   1 afshin afshin     2689 Jul  8 12:12 count_chars.py
-rw-r--r--   1 afshin afshin 15971539 Jul  9 11:57 demo-video-01.mp4
-rw-r--r--   1 afshin afshin      745 Jul  9 09:37 docker-compose.yml
-rw-r--r--   1 afshin afshin    14624 Jul  1 18:17 fireworks_backfill.log
-rw-rw-r--   1 afshin afshin      367 Jun 23 13:19 index.html
-rw-r--r--   1 afshin afshin   300394 Jul  9 10:34 narrative-nexus-deck.pdf
-rw-rw-r--   1 afshin afshin     3246 Jul  8 12:12 output_results.py
-rw-rw-r--   1 afshin afshin   336639 Jul  8 12:12 package-lock.json
-rw-rw-r--   1 afshin afshin     1411 Jul  8 12:12 package.json
-rw-------   1 afshin afshin      169 Jun 26 14:12 pytest.ini
-rw-rw-r--   1 afshin afshin      349 Jul  8 12:12 requirements.txt
-rw-rw-r--   1 afshin afshin      224 Jul  8 12:12 run_output.py
-rwxrwxr-x   1 afshin afshin      184 Jul  8 12:12 start-guarded.sh
-rw-rw-r--   1 afshin afshin     5490 Jul  8 12:12 test_count.py
-rw-rw-r--   1 afshin afshin     5080 Jul  8 12:12 tmp_content_1.txt
-rw-rw-r--   1 afshin afshin     4936 Jul  8 12:12 tmp_content_2.txt
-rw-rw-r--   1 afshin afshin      695 Jun 24 15:47 tsconfig.app.json
-rw-rw-r--   1 afshin afshin      119 Jun 23 13:19 tsconfig.json
-rw-rw-r--   1 afshin afshin      558 Jun 23 13:19 tsconfig.node.json
-rw-rw-r--   1 afshin afshin      899 Jul  8 22:56 vite.config.ts
```

Subdirectories (not analyzed): `.commandcode`, `.fallow`, `.git`, `.libretto`, `.pytest_cache`, `__pycache__`, `app`, `config`, `data`, `db`, `dist`, `docs`, `node_modules`, `pipeline`, `public`, `scripts`, `spec`, `src`, `worker`.

### `git ls-files --directory | grep -v /` (tracked root files only)

```
--db
.dockerignore
.env.example
.gitignore
.oxlintrc.json
.stylelintrc.json
=0.9.5
=5.0.0
CLAUDE.md
Dockerfile.app
LICENSE
README.md
app-img-01.png
biome.json
components.json
conftest.py
count_chars.py
demo-video-01.mp4
docker-compose.yml
index.html
narrative-nexus-deck.pdf
output_results.py
package-lock.json
package.json
pytest.ini
requirements.txt
run_output.py
start-guarded.sh
test_count.py
tmp_content_1.txt
tmp_content_2.txt
tsconfig.app.json
tsconfig.json
tsconfig.node.json
vite.config.ts
```

### UNTRACKED root files (in `ls` but not in `git ls-files`)

| File | Why untracked |
|------|---------------|
| `.env` | Gitignored (`.gitignore:41`) |
| `.readonly` | Gitignored (`.gitignore:52`) |
| `backfill.log` | Gitignored (`.gitignore:42`) |
| `fireworks_backfill.log` | Gitignored (`.gitignore:43`) |

---

## 2. Per-File Analysis

### --db
- **Tracked?** YES
- **Type:** `./--db: empty` (0 bytes)
- **Size:** 0 lines
- **Git:** `6c41dbf 2026-07-03 refactor db`
- **Referenced?** No — `grep -rn '\-\-db'` returned only script arg parsers using `--db` as a CLI flag, not the root file.
- **VERDICT:** **STALE** — 0-byte empty file. Looks like a shell redirect typo artifact (`somecmd --db > --db` or similar). Not referenced by anything.

### .dockerignore
- **Tracked?** YES
- **Type:** Unicode text (17 lines)
- **Git:** `3526275 2026-07-06 D2: container self-sufficiency`
- **Referenced?** Standard Docker file — Docker reads it automatically during build.
- **VERDICT:** **KEEP** — Docker build requirement. Excludes node_modules, .git, data/* (except demo.db), docs, tests.

### .env
- **Tracked?** NO (gitignored)
- **Type:** ASCII text, 3 lines
- **Content:** Contains real API keys: `DEEPSEEK_API_KEY=***`, `FIREWORKS_API_KEY=fw_57R...z2FV`, `FIRECRAWL_API_KEY=fc-e09...T---`
- **Git:** untracked
- **Referenced?** Referenced by `.gitignore:41` and `.dockerignore:5` (both ignore it). App reads via `python-dotenv` in `app/main.py:7`.
- **FLAG:** **CONTAINS SECRETS** — real API keys. Already gitignored. Do NOT delete without backing up keys.

### .env.example
- **Tracked?** YES
- **Type:** Unicode text, 17 lines
- **Git:** `6bdb76b 2026-07-09 Docker setup done`
- **Referenced?** No direct references — it's a documentation template.
- **VERDICT:** **KEEP** — UX58 artifact. Documents optional env vars and NN_DISABLE_SCRAPER.

### .gitignore
- **Tracked?** YES
- **Type:** Unicode text, 51 lines
- **Git:** `2f2ea42 2026-07-08 Update .gitignore`
- **Referenced?** Standard Git file.
- **VERDICT:** **KEEP** — Required by Git.

### .oxlintrc.json
- **Tracked?** YES
- **Type:** JSON, 8 lines
- **Content:** Configures oxlint rules (react, typescript, oxc plugins)
- **Git:** `897c03a 2026-06-23 scaffold project`
- **Referenced?** `package.json:9` — `"lint": "oxlint"`. Oxlint auto-discovers `.oxlintrc.json`.
- **VERDICT:** **KEEP** — Linter config, referenced by build.

### .readonly
- **Tracked?** NO (gitignored)
- **Type:** Empty file (0 bytes)
- **Content:** (empty)
- **Git:** untracked
- **Referenced?** `.gitignore:52` ignores it. No code references `_is_readonly()` or `NN_READONLY` remain (removed in UX36, confirmed by grep).
- **VERDICT:** **STALE** — Dead paradigm artifact. The `.readonly` sentinel mechanism was fully removed in UX36. The file is gitignored and has zero effect. Safe to delete.

### .stylelintrc.json
- **Tracked?** YES
- **Type:** JSON, 7 lines
- **Content:** Configures stylelint for Tailwind at-rules
- **Git:** `d97ceee 2026-06-24 chore: add biome, stylelint, fallow`
- **Referenced?** NOT referenced in `package.json` — no `stylelint` dependency or script. Only `"lint": "oxlint"` exists.
- **VERDICT:** **STALE** — Stylelint was never wired into the build. No package.json script, no dependency. Leftover from initial scaffold.

### =0.9.5
- **Tracked?** YES
- **Type:** Unicode text, ~70 lines
- **Content:** Pip install output for `newspaper4k 0.9.5`
- **Git:** `82ee675 2026-07-01 Slices 024b-026`
- **Referenced?** `requirements.txt:5` — `newspaper4k>=0.9.5` (the package, not this file). The file `=0.9.5` is not referenced.
- **VERDICT:** **STALE** — Shell redirect typo artifact. Likely produced by `pip install newspaper4k > =0.9.5` or similar mis-typed command. A paste of pip stdout, not a config file.

### =5.0.0
- **Tracked?** YES
- **Type:** ASCII text, ~10 lines
- **Content:** Pip install output for `sentence-transformers 5.6.0`
- **Git:** `82ee675 2026-07-01 Slices 024b-026`
- **Referenced?** `requirements.txt:9` — `sentence-transformers>=5.0.0` (the package, not this file). The file `=5.0.0` is not referenced.
- **VERDICT:** **STALE** — Same pattern as `=0.9.5`. Shell redirect typo artifact.

### app-img-01.png
- **Tracked?** YES
- **Type:** PNG image, 1376x768, RGBA, 1.8MB
- **Git:** `d577317 2026-07-09 final touches`
- **Referenced?** `README.md:9` — `![Narrative Nexus — Media Risk & OSINT Reputational Workflow](app-img-01.png)`
- **VERDICT:** **KEEP** — Referenced by README. App screenshot for the repo landing page.

### backfill.log
- **Tracked?** NO (gitignored, `.gitignore:42`)
- **Type:** ASCII text, 131 lines
- **Content:** Backfill run log: "Backfilling 300 articles..."
- **Git:** untracked
- **Referenced?** Only `.gitignore:42` which ignores it.
- **VERDICT:** **STALE** — Log file. Already gitignored. Diagnostic output from a one-off backfill run.

### biome.json
- **Tracked?** YES
- **Type:** JSON, 11 lines
- **Content:** Biome linter config (noNonNullAssertion off, noExplicitAny off, noArrayIndexKey off)
- **Git:** `6b00fd1 2026-07-01 Update frontpage`
- **Referenced?** NOT referenced in `package.json` — no `biome` dependency or script. Only `"lint": "oxlint"` exists.
- **VERDICT:** **STALE** — Biome was replaced by oxlint. No package.json reference, no dependency.

### CLAUDE.md
- **Tracked?** YES
- **Type:** Unicode text, 21 lines
- **Git:** `d84ac68 2026-07-03 PRE-FLIGHT`
- **Referenced?** Agent startup protocol — read by Hermes/Claude Code at session start.
- **VERDICT:** **KEEP** — Agent context file. Referenced by the agent runtime.

### components.json
- **Tracked?** YES
- **Type:** JSON, 25 lines
- **Content:** shadcn/ui configuration (style, aliases, icon library)
- **Git:** `897c03a 2026-06-23 scaffold project`
- **Referenced?** `package.json:30` — `"shadcn": "^4.11.0"`. shadcn CLI reads `components.json`.
- **VERDICT:** **KEEP** — shadcn/ui config. Referenced by shadcn CLI during component additions.

### conftest.py
- **Tracked?** YES
- **Type:** Python script, 15 lines
- **Content:** Pytest fixture providing in-memory SQLite DB with schema loaded.
- **Git:** `20950ea 2026-06-26 feat(010): daily snapshot computation`
- **Referenced?** Standard pytest convention — pytest auto-discovers `conftest.py` in the test root. `pytest.ini` sets `testpaths = pipeline db app`.
- **VERDICT:** **KEEP** — Pytest fixtures for backend tests.

### count_chars.py
- **Tracked?** YES
- **Type:** Python script, 57 lines
- **Content:** Extracts content strings from web_extract results for NPR Venezuela stories
- **Git:** `8eff7fa 2026-07-03 F1-F4: Recovery gates`
- **Referenced?** No references found (`grep -rn 'count_char'` returned only the file itself).
- **VERDICT:** **STALE** — One-off diagnostic script. Measures character counts from web_extract output. Not imported, not referenced by any build or test.

### demo-video-01.mp4
- **Tracked?** YES
- **Type:** MP4 video, 16MB
- **Git:** `d577317 2026-07-09 final touches`
- **Referenced?** `README.md:13` — `🎥 Demo video: [demo-video-01.mp4](demo-video-01.mp4)`
- **VERDICT:** **KEEP** — Referenced by README. Hackathon demo video.

### Dockerfile.app
- **Tracked?** YES
- **Type:** Unicode text, 55 lines
- **Git:** `6bdb76b 2026-07-09 Docker setup done`
- **Referenced?** `docker-compose.yml:16` — `dockerfile: Dockerfile.app`
- **VERDICT:** **KEEP** — Docker build file. Referenced by compose.

### docker-compose.yml
- **Tracked?** YES
- **Type:** ASCII text, 26 lines
- **Git:** `6bdb76b 2026-07-09 Docker setup done`
- **Referenced?** Standard — `docker compose` reads it.
- **VERDICT:** **KEEP** — Docker compose config.

### fireworks_backfill.log
- **Tracked?** NO (gitignored, `.gitignore:43`)
- **Type:** ASCII text, 131 lines
- **Content:** Fireworks backfill run log: "model=accounts/fireworks/models/deepseek-v4-flash"
- **Git:** untracked
- **Referenced?** Only `.gitignore:43` which ignores it.
- **VERDICT:** **STALE** — Log file. Already gitignored. Diagnostic output from a one-off backfill run.

### index.html
- **Tracked?** YES
- **Type:** HTML document, 12 lines
- **Content:** Vite entry point — `<div id="root">` + `<script src="/src/main.tsx">`
- **Git:** `897c03a 2026-06-23 scaffold project`
- **Referenced?** Standard — Vite reads `index.html` as the HTML entry point.
- **VERDICT:** **KEEP** — Vite entry point.

### LICENSE
- **Tracked?** YES
- **Type:** ASCII text, 21 lines
- **Git:** `bedf240 2026-07-02 Phase 0+1`
- **Referenced?** Standard — GitHub and package managers read LICENSE.
- **VERDICT:** **KEEP** — Project license.

### narrative-nexus-deck.pdf
- **Tracked?** YES
- **Type:** PDF document, 300KB
- **Git:** `d577317 2026-07-09 final touches`
- **Referenced?** `README.md:12` — `📊 Slide deck: [narrative-nexus-deck.pdf](narrative-nexus-deck.pdf)`
- **VERDICT:** **KEEP** — Referenced by README. Hackathon slide deck.

### output_results.py
- **Tracked?** YES
- **Type:** Python script, 79 lines
- **Content:** Web extract result data — NPR Venezuela story content
- **Git:** `8eff7fa 2026-07-03 F1-F4: Recovery gates`
- **Referenced?** `run_output.py:3-4` — calls `output_results.py` via subprocess.
- **VERDICT:** **STALE** — One-off diagnostic data dump. Only referenced by `run_output.py` (also stale). Not imported by any app module.

### package.json
- **Tracked?** YES
- **Type:** JSON, 52 lines
- **Git:** `ac89bc5 2026-07-06 D3: remove better-sqlite3`
- **Referenced?** Standard — npm/Vite read it.
- **VERDICT:** **KEEP** — Node project manifest.

### package-lock.json
- **Tracked?** YES
- **Type:** JSON, 9379 lines
- **Git:** `ac89bc5 2026-07-06 D3: remove better-sqlite3`
- **Referenced?** Standard — npm reads it for deterministic installs.
- **VERDICT:** **KEEP** — Dependency lock file.

### pytest.ini
- **Tracked?** YES
- **Type:** ASCII text, 6 lines
- **Content:** pytest config: `testpaths = pipeline db app`, asyncio mode, network marker
- **Git:** `f1171ff 2026-06-26 implement 8b 8c`
- **Referenced?** Standard — pytest auto-discovers `pytest.ini`.
- **VERDICT:** **KEEP** — Pytest configuration.

### README.md
- **Tracked?** YES
- **Type:** Unicode text, 148 lines
- **Git:** `d577317 2026-07-09 final touches`
- **Referenced?** Standard — GitHub displays it as the project landing page.
- **VERDICT:** **KEEP** — Project README.

### requirements.txt
- **Tracked?** YES
- **Type:** Unicode text, 15 lines
- **Git:** `b031a4b 2026-07-03 revise plan a`
- **Referenced?** `Dockerfile.app:41` — `RUN pip install --no-cache-dir -r requirements.txt`
- **VERDICT:** **KEEP** — Python dependencies. Referenced by Docker build.

### run_output.py
- **Tracked?** YES
- **Type:** Python script, 7 lines
- **Content:** Runs `output_results.py` via subprocess and prints stdout.
- **Git:** `8eff7fa 2026-07-03 F1-F4: Recovery gates`
- **Referenced?** No references found. It calls `output_results.py` (stale).
- **VERDICT:** **STALE** — Wrapper script that calls another stale script. Self-referencing loop with `output_results.py`. Not imported by any app module.

### start-guarded.sh
- **Tracked?** YES
- **Type:** Bash script, 6 lines
- **Content:** Sets `NN_READONLY=1` and starts uvicorn on port 3015.
- **Git:** `abb95de 2026-07-08 UX14-28 + AMD README`
- **Referenced?** No references found.
- **VERDICT:** **STALE** — Uses the dead `NN_READONLY` paradigm (removed in UX36). Sets a path specific to the dev machine (`/project/narrative-nexus`). Not referenced by Docker, compose, or any script.

### test_count.py
- **Tracked?** YES
- **Type:** Python script, 97 lines
- **Content:** Web extract content for NPR Venezuela stories — similar to `count_chars.py`
- **Git:** `8eff7fa 2026-07-03 F1-F4: Recovery gates`
- **Referenced?** No references found.
- **VERDICT:** **STALE** — One-off diagnostic script. Measures character counts from web_extract. Not imported, not referenced.

### tmp_content_1.txt
- **Tracked?** YES
- **Type:** Unicode text, 78 lines
- **Content:** "European Heatwave" article content from The Guardian
- **Git:** `8eff7fa 2026-07-03 F1-F4: Recovery gates`
- **Referenced?** No references found.
- **VERDICT:** **STALE** — Scratch content dump. Not referenced anywhere.

### tmp_content_2.txt
- **Tracked?** YES
- **Type:** Unicode text, 71 lines
- **Content:** "How climate change is influencing Europe's record-breaking heat wave" from NPR
- **Git:** `8eff7fa 2026-07-03 F1-F4: Recovery gates`
- **Referenced?** No references found.
- **VERDICT:** **STALE** — Scratch content dump. Not referenced anywhere.

### tsconfig.app.json
- **Tracked?** YES
- **Type:** ASCII text, 28 lines
- **Content:** TypeScript config for app source (target ES2023, bundler mode, jsx react-jsx, paths @/*)
- **Git:** `727d14a 2026-06-24 feat(docker)`
- **Referenced?** `tsconfig.json:4` — `{ "path": "./tsconfig.app.json" }`
- **VERDICT:** **KEEP** — TypeScript config. Referenced by tsconfig.json.

### tsconfig.json
- **Tracked?** YES
- **Type:** JSON, 7 lines
- **Content:** Project references to tsconfig.app.json and tsconfig.node.json
- **Git:** `897c03a 2026-06-23 scaffold project`
- **Referenced?** Standard — TypeScript reads it.
- **VERDICT:** **KEEP** — TypeScript project root config.

### tsconfig.node.json
- **Tracked?** YES
- **Type:** ASCII text, 22 lines
- **Content:** TypeScript config for Node files (vite.config.ts)
- **Git:** `897c03a 2026-06-23 scaffold project`
- **Referenced?** `tsconfig.json:5` — `{ "path": "./tsconfig.node.json" }`
- **VERDICT:** **KEEP** — TypeScript config. Referenced by tsconfig.json.

### vite.config.ts
- **Tracked?** YES
- **Type:** TypeScript, 35 lines
- **Content:** Vite config: React + Tailwind plugins, @ alias, API proxy to :3015, manual chunks (chartjs, d3), vitest jsdom
- **Git:** `2eab455 2026-07-08 Update stories and docs`
- **Referenced?** Standard — Vite reads it.
- **VERDICT:** **KEEP** — Vite build config.

---

## 3. Summary Table

| File | Tracked? | Referenced? | VERDICT |
|------|----------|-------------|---------|
| `--db` | YES | No | **STALE** — 0B shell redirect typo |
| `.dockerignore` | YES | Docker reads it | **KEEP** |
| `.env` | NO (gitignored) | app reads via dotenv | **FLAG: SECRETS** |
| `.env.example` | YES | Template doc | **KEEP** |
| `.gitignore` | YES | Git reads it | **KEEP** |
| `.oxlintrc.json` | YES | oxlint via `"lint": "oxlint"` | **KEEP** |
| `.readonly` | NO (gitignored) | Dead paradigm (UX36) | **STALE** |
| `.stylelintrc.json` | YES | No (no stylelint dep) | **STALE** |
| `=0.9.5` | YES | No | **STALE** — pip stdout typo |
| `=5.0.0` | YES | No | **STALE** — pip stdout typo |
| `CLAUDE.md` | YES | Agent runtime | **KEEP** |
| `Dockerfile.app` | YES | compose → `dockerfile:` | **KEEP** |
| `LICENSE` | YES | Standard | **KEEP** |
| `README.md` | YES | GitHub landing page | **KEEP** |
| `app-img-01.png` | YES | README.md | **KEEP** |
| `backfill.log` | NO (gitignored) | `.gitignore` only | **STALE** |
| `biome.json` | YES | No (replaced by oxlint) | **STALE** |
| `components.json` | YES | shadcn CLI | **KEEP** |
| `conftest.py` | YES | pytest auto-discovers | **KEEP** |
| `count_chars.py` | YES | No | **STALE** |
| `demo-video-01.mp4` | YES | README.md | **KEEP** |
| `docker-compose.yml` | YES | `docker compose` | **KEEP** |
| `fireworks_backfill.log` | NO (gitignored) | `.gitignore` only | **STALE** |
| `index.html` | YES | Vite entry point | **KEEP** |
| `narrative-nexus-deck.pdf` | YES | README.md | **KEEP** |
| `output_results.py` | YES | Only by `run_output.py` (stale) | **STALE** |
| `package-lock.json` | YES | npm | **KEEP** |
| `package.json` | YES | npm/Vite | **KEEP** |
| `pytest.ini` | YES | pytest auto-discovers | **KEEP** |
| `requirements.txt` | YES | Dockerfile.app | **KEEP** |
| `run_output.py` | YES | No (self-ref loop w/ stale file) | **STALE** |
| `start-guarded.sh` | YES | No | **STALE** |
| `test_count.py` | YES | No | **STALE** |
| `tmp_content_1.txt` | YES | No | **STALE** |
| `tmp_content_2.txt` | YES | No | **STALE** |
| `tsconfig.app.json` | YES | tsconfig.json | **KEEP** |
| `tsconfig.json` | YES | TypeScript | **KEEP** |
| `tsconfig.node.json` | YES | tsconfig.json | **KEEP** |
| `vite.config.ts` | YES | Vite | **KEEP** |

---

## 4. Compliance Table

| # | Requirement | Met EXACTLY? | Evidence |
|---|-------------|--------------|----------|
| 1 | List root files (ls -la) | YES | Pasted verbatim above |
| 2 | List tracked root files (git ls-files) | YES | Pasted verbatim above |
| 3 | Flag untracked root files | YES | 4 untracked identified: .env, .readonly, backfill.log, fireworks_backfill.log |
| 4 | `file` + `head`/`wc` for every file | YES | All 39 files have type/content evidence |
| 5 | `git log` for every file | YES | All 39 files have last-commit evidence |
| 6 | Reference check for every file | YES | grep searched .py/.ts/.tsx/.json/.sh/.yml/Dockerfile |
| 7 | Flag `=9.95`/`=5.0.0`/`--db`/`biome.json` etc. | YES | All suspect files classified |
| 8 | Flag log files | YES | backfill.log, fireworks_backfill.log → STALE |
| 9 | Flag scratch dumps | YES | tmp_content_1.txt, tmp_content_2.txt → STALE |
| 10 | Flag `.readonly` dead paradigm | YES | STALE — UX36 removed all references |
| 11 | Flag `.env` with real keys | YES | FLAGGED: contains FIREWORKS_API_KEY, FIRECRAWL_API_KEY |
| 12 | Fingerprint unchanged both ends | YES | 378/10/358/17/13653 before and after |
| 13 | No deletions performed | YES | Read-only, zero file changes |

---

## 5. Fingerprint (after)

```
378 / 10 / 358 / 17 / 13653
```

Unchanged from start.

---

## PROPOSED (not done)

**14 files marked STALE** — safe to delete:
`--db`, `.readonly`, `.stylelintrc.json`, `=0.9.5`, `=5.0.0`, `biome.json`, `count_chars.py`, `output_results.py`, `run_output.py`, `start-guarded.sh`, `test_count.py`, `tmp_content_1.txt`, `tmp_content_2.txt`, `backfill.log`, `fireworks_backfill.log`

**1 file FLAGGED with secrets:** `.env` — already gitignored. Do NOT delete without backing up keys.

**Dead config:** `biome.json` and `.stylelintrc.json` — both linter configs with zero references in `package.json`. Only `oxlint` is active.
