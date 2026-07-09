# Deployment TODO — deferred until after deck/video

**Status:** All pre-deployment gates verified on host, 2026-07-09.
Nothing blocks deployment — the container is judge-runnable.
Deployment itself is deferred so the team focuses on the presentation deck and video first.

---

## Verified state (ground truth — no re-derivation needed)

These facts were confirmed with real tool output on the human's host:

- **`scripts/smoke.sh` ALL PASS.** Container rebuilds from `Dockerfile.app` +
  `docker-compose.yml`, boots, serves `/api/stats` (358 articles / 37 sources),
  SPA served, in-container DB fingerprint matches golden (378/10/358/17/13653),
  host DB untouched at 358 articles after teardown.

- **Egress OK.** `docker compose exec app curl -s http://example.com` returns 200.

- **Keyless scraper confirmed functional.** `POST /api/scraper/start` succeeded
  with zero API keys in a disposable container copy — articles went 358 → 1,855
  via RSS polling + newspaper4k. Harmless locally (disposable copy); this is
  exactly why `NN_DISABLE_SCRAPER=1` is mandatory on any hosted deployment.

- **`NN_DISABLE_SCRAPER=1` verified:**
  - `GET /api/scraper/status` → `"disabled": true`
  - `POST /api/scraper/start` → 403 `"Scraper is disabled on this deployment."`
  - Settings page button disabled with amber text

- **Empty-DB guard verified.** Booting with `NN_DB_PATH=/tmp/nowhere.db` raises
  `RuntimeError` naming the path and both likely causes (wrong path / missing COPY).

- **Image content size: 2.99 GB.** torch + sentence-transformers present as
  local-CPU embedding fallback (all provider defaults are Fireworks).

- **Fingerprint: 378/10/358/17/13653** — the golden copy.

- **Single-service compose:** `docker compose up` starts one `app` container
  on port 8000. No db/worker services, no volumes, no networks block.

---

## HF Spaces deployment steps

1. Create a **Docker SDK Space** on Hugging Face Spaces.
2. Set the README metadata header:

   ```yaml
   ---
   title: Narrative Nexus
   app_port: 8000
   ---
   ```

3. Set Space variable: `NN_DISABLE_SCRAPER=1` (mandatory — prevents any visitor
   from mutating the shared DB by clicking Start).
4. Push the repo to the Space. HF Spaces builds from `Dockerfile.app` and
   `docker-compose.yml` automatically.
5. Get the URL from the Space settings. (There is no live URL yet — this doc
   will be updated when one exists.)

---

## Image-size lever (DECISION for deployment round)

The runtime image is **2.99 GB**. This is because `requirements.txt` includes
torch and sentence-transformers as a local-CPU embedding fallback. However:

- All provider defaults in `config/providers.json` use Fireworks AI (remote)
  for embeddings and LLM — the local fallback is never invoked in normal
  operation.
- Dropping torch + sentence-transformers from `requirements.txt` is the
  single largest image-size reduction available.

**Decision to make:** keep the local fallback (self-contained, works offline)
vs. strip it (smaller image, faster HF Spaces build). If HF build limits or
disk quotas bite, remove torch/sentence-transformers from requirements.txt —
the empty-DB guard will still fire correctly, and the app will run with
Fireworks defaults.

**Not decided here.** The deployment round picks.

---

## Repo hygiene (optional cleanup)

The human raised these as candidates for trimming — none required for a
working image, all safe to drop:

- `docs/` tree — large collection of design docs, implementation round
  logs, evidence directories. High-value for maintainers but not needed
  at runtime. Dockerfile.app already excludes `docs/` from the COPY
  stage.
- `vault/` references — workflow files, external config. Not in the
  container build path.
- Unused npm packages — `chart.js`, `d3`, `react-chartjs-2` listed in
  CLAUDE.md as "known intentional dead code" (installed for Sources
  page). If Sources page is cut, these can go.

None of these affect the container. Purely optional — the 2.99 GB image
works as-is.
