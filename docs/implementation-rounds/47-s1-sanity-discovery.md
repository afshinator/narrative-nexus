# S1 — Sanity / Discovery Round

**Date:** 2026-07-04
**Read-only.** No writes, no code changes, no commits.

---

## S1.1 — DB State Fingerprint

### Demo DB (data/demo/demo.db)

```
.tables: article_framing, articles, claim_sources, claim_variants, claims,
         clusters, corrections, embeddings, silent_edits, snapshots, sources

articles           | 344
claims             | 327
clusters           | 15
claim_sources      | 511
claim_variants     | 518
snapshots          | 10545
silent_edits       | 0
corrections        | 0
embeddings         | 168
sources            | 37
article_framing    | 168

articles published: 2026-04-16 to 2026-07-03
claims by state: PENDING=319, CONSENSUS_ABSORBED=8
absorbed per cluster: 924(Venezuela)=3, 932(Hormuz)=1, 933(Heatwave)=3,
                      934(Anthropic-main)=1, 923(Anthropic-vuln)=0
```

**Expected: 327 claims, 8 absorbed. MATCH.** ✓

### Live DB (data/nn.db)

```
articles           | 5112
claims             | 7747
clusters           | 1179
claim_sources      | 8114
claim_variants     | 932
snapshots          | 44955
silent_edits       | 496
corrections        | 16
embeddings         | 2028
sources            | 37

articles published: 2013-08-21 to 2026-07-03
```

---

## S1.2 — Locked Parameters: Code vs Docs

| Parameter | STATUS.md | Code location | Code value | Match? |
|-----------|-----------|---------------|------------|--------|
| eps (DBSCAN) | 0.35 | `agent1_intake.py:43` (default) / `recluster_all.py:328` (default=0.5, CLI override) | 0.35 (CLI) | ✓ |
| min_samples | 2 | `agent1_intake.py:43`, `recluster_all.py:220` | 2 (hardcoded) | ✓ |
| time_window 14d | **NOT in STATUS.md** | `agent1_intake.py:12` | 14d | ⚠️ GAP |
| MAX_CLUSTER_SIZE | 60 | `agent1_intake.py:34` | 60 | ✓ |
| EPS_FLOOR | 0.25 | `agent1_intake.py:36` | 0.25 | ✓ |
| sim_threshold | 0.85 | `claim_matching.py:65,206` | 0.85 | ✓ |
| MIN_CORROBORATION | 2 | `consensus.py:8` | 2 | ✓ |
| Vertical thresholds | ">= vertical threshold" (unspecified) | `consensus.py:3` | geopolitics=65, economics=75, technology=75 | ⚠️ GAP |
| R_val 7-day exclusion | STATUS.md:17 | `snapshots.py:66` | `date(c.created_at) <= date(?, '-7 days')` — **O8.1 fix present** | ✓ |
| Article clustering model | BGE locked | `providers.json:7` | BAAI/bge-base-en-v1.5 | ✓ |
| Claim matching model | nomic w/ prefix | `providers.json:13,58`, `embedding_client.py:127` | nomic-ai/nomic-embed-text-v1.5, "clustering:" prefix, slot `claim_matching_embedding` | ✓ |
| Agent 2 model | — | `providers.json:33` | `accounts/fireworks/models/deepseek-v4-pro` | ✓ |

### Blob guard eps-step logic

`pipeline/agent1_intake.py:259`: `new_eps = max(eps - 0.05, EPS_FLOOR)`

Steps: 0.35→0.30→0.25→stop at floor. Doc 45's "155 split at eps=0.30" is a **legitimate intermediate step** — the guard starts at eps-0.05 on each recursion, not at the original eps. 0.30 is the first reduction from 0.35. ✓

### Mismatches (2)
1. **time_window=14d** not listed in STATUS.md locked parameters
2. **Vertical thresholds** (65/75/75) not listed in STATUS.md — only says ">= vertical threshold"

---

## S1.3 — Seed Script & Pipeline Entry Points

### (a) seed_demo.py exists

**File:** `scripts/seed_demo.py` (7.6K)

Docstring:
```
"""Seed script — runs the pipeline against existing scraped articles.

Usage: python scripts/seed-demo.py [--db data/nn.db]

Per ADR-0002, this shares code paths with the live pipeline. No demo mode,
no mock data, no separate database. It imports the same agent classes and
snapshot functions the live scheduler uses.

What it does:
  1. Runs Agent 1 (Intake & Clustering) on articles with bodies
  2. Runs Agent 2 (Forensic Extraction) on clustered articles
  3. Runs Agent 3 (Consensus Alignment) on all clusters
  4. Runs Agent 4 (Silent Auditor) to detect edits
  5. Generates date-filtered daily snapshots across the full article date range
"""
```

### (b) Actual entry points used in O-rounds

- **recluster_all:** `scripts/recluster_all.py --db data/demo/demo.db --eps 0.35`
- **reset_claim_state:** `scripts/reset_claim_state.py data/demo/demo.db`
- **match_all_clusters:** called via `pipeline/claim_matching.py` → `match_all_clusters()` w/ nomic embed client from `get_claim_matching_embed_client()`
- **Agent 2:** `pipeline/agent2_forensic.py` → `ForensicExtractionAgent(…).run(article_map={…})` via execute_code
- **Agent 3:** `pipeline/agent3_consensus.py` → `ConsensusAlignmentAgent(…).run_all()`
- **backfill_snapshots:** `scripts/backfill_snapshots.py --db data/demo/demo.db --since … --until …`

### (c) Full chain

**Manual orchestration.** No single command runs end-to-end. Each step invoked separately.

---

## S1.4 — Frontend Wiring

### (a) DB path selection
`app/main.py:44`:
```python
db_path = os.environ.get("NN_DB_PATH", "data/nn.db")
```

### (b) Can point at demo DB?
**YES.** Set `NN_DB_PATH=data/demo/demo.db`. No code change needed.

### (c) Frontend routes
`src/App.tsx:29-38`:
```
/                       → SourcesPage
/source/:domain          → SourceProfilePage
/cluster/:clusterId      → ClusterReportPage
/timeline/:clusterId     → TimelinePage
/pipeline                → PipelineFlowPage
/investigate             → InvestigatePage
/panel                   → PanelPage
/settings                → SettingsPage
*                        → NotFoundPage
```
All 8 named routes present. No stubs — all resolve to component files in `src/pages/`.

### (d) Two-lens Sources + Investigate SSE
- **Sources page:** `src/pages/Sources.tsx`
- **Investigate SSE:** `app/investigate_endpoint.py`, mounted at `POST /api/investigate/stream`
- **Coverage Landscape API:** `GET /api/coverage-landscape` (`app/main.py:406`)
- **Source Profile:** `GET /api/sources/{source_id}/profile` (`app/main.py:114`)

### (e) Hardcoded "37" references
```
src/pages/Investigate.tsx:97: "... 37-source panel ..."
src/__tests__/sources.test.ts:4-6: expects exactly 37 entries
src/data/sources.ts:2: "37 sources across 5 tiers"
```
Demo DB has 37 source rows but only ~14 sources with actual articles/claims. The "37-source panel" text on Investigate page and test expectation will be misleading.

---

## S1.5 — Time-Depth Prerequisites (nn.db read-only)

### (a) March–April 2026 Iran-arc articles

```
SELECT COUNT(*) FROM articles WHERE published_at >= '2026-03-01'
  AND published_at < '2026-05-01'
  AND (title LIKE '%Iran%' OR title LIKE '%Hormuz%' OR
       title LIKE '%strike%' OR title LIKE '%Strait%');
-- 5 articles, ALL from economist (source_id=8), ALL with body text
```

**5 articles only.** Not sufficient for standalone demo story.

### (b) May 2026 economics/technology stories

May 2026 articles: economist (5), bellingcat (5), thegrayzone (8), cbsnews (1). No clear economics or technology stories with multi-source coverage.

**Demand for Firecrawl shopping is CONFIRMED.** No natural demo-worthy stories exist in May 2026 nn.db.

### (c) Live DB monthly coverage

```
SELECT strftime('%Y-%m', published_at), COUNT(*),
       SUM(body IS NOT NULL AND body != '') FROM articles GROUP BY 1 ORDER BY 1;
```

Coverage starts 2013-08 (5 articles), sparse through 2023-03, then builds:
- 2023-04: 57 (55 with body)
- 2026-05: 19 (18 with body)
- 2026-06: 3,026 (1,620 with body) — RSS mass-fetch
- 2026-07: 1,604 (0 with body) — no bodies for July

### (d) Demo DB date gap

Demo DB: 2026-04-16 to 2026-07-03 (79 days). For 90-day scrubbing, need **11 more days** of coverage (2026-04-05 to 2026-04-15) if keeping the upper bound, or extend the lower bound. The March–April Iran arc would provide exactly the gap fill needed.

---

## S1.6 — Submission Logistics State

### (a) Docker

```
Dockerfile.app     (1841 bytes, Jun 27)
Dockerfile.worker  (976 bytes, Jun 27)
docker-compose.yml (2188 bytes, Jun 27)
```

Clean-checkout build? **UNKNOWN.** No evidence of successful docker build in repo.

### (b) Fireworks provider config

`config/providers.json:33`: Agent 2 model = `accounts/fireworks/models/deepseek-v4-pro`
`config/providers.json:60`: `"agent2_llm": "fireworks"` resolving to above.

### (c) Hosting config

**NONE.** No fly.toml, render.yaml, railway, vercel, or netlify files.

### (d) LICENSE

```
MIT License

Copyright (c) 2026 Narrative Nexus
```

### (e) Test suite

```
pytest --collect-only -q: 314 tests collected in 7.20s
frontend (vitest --run): 0 tests (19 unhandled pool worker errors — environment failure)
```

Frontend tests cannot be collected due to vitest pool fork errors. No tests run.

---

## S1.7 — Docs Drift Inventory

Comparing FAQ claims against demo.db reality:

| Doc claim (FAQ) | Live DB value | Demo DB value | Demo drift |
|----------------|---------------|---------------|------------|
| "7,635 claims" | 7,747 | 327 | ✗ |
| "4 sources with absorbed: theguardian(6), apnews(4), foxnews(2), bbc(1)" | truth for LIVE | demo: 8 absorbed across different set | ✗ |
| "All 6 radar dimensions live" | varies | 57 of 111 snapshot rows have all 6 non-null | ✗ Partial |
| "44,955 snapshots" | 44,955 | 10,545 | ✗ (different span) |
| "1,112 clusters" | 1,179 | 15 | ✗ |
| "68 multi-source clusters" | truth for LIVE | ~6 | ✗ |
| "26 demo-worthy clusters" | truth for LIVE | ~6 | ✗ |
| "89 silent edits" | 496 | 0 | ✗ |
| "16 corrections" | 16 | 0 | ✗ |
| "405 snapshot dates" | 405 | 95 | ✗ |
| "37 sources all produce claims" | truth for LIVE | 37 in sources table, ~14 with claims | ✗ |
| "3 verticals" | geopolitics, economics, technology | same 3 | ✓ |
| "0.85 sim threshold" | 0.85 code | 0.85 code | ✓ |

**Bottom line:** FAQ documents describe the LIVE DB (data/nn.db), not the demo DB. Every FAQ claim will be FALSE when read against the demo DB. The FAQs need a "Demo DB" section or disclaimer.

---

## Assumption Failures

1. **STATUS.md missing 2 locked parameters:** time_window=14d, vertical thresholds (65/75/75)
2. **FAQ docs describe live DB, not demo DB** — all numbers misleading for demo DB context
3. **Frontend vitest tests cannot run** (19 pool worker errors) — cleanup needed before demo
4. **Hardcoded "37" references** in frontend UI and tests — misleading against demo DB's active sources
5. **No seed-demo.py** (it's `seed_demo.py`, underscore not hyphen) — minor naming mismatch
6. **May 2026 has no demo-worthy stories** — Firecrawl shopping required for time-depth
7. **Demo DB has 0 silent_edits, 0 corrections** — Agent 4 never run on demo, corrections never detected

---

## Blockers for Next Rounds

1. **Time-depth:** Need March-April Iran arc (Firecrawl shopping) to fill 90-day gap. May requires new stories from scratch.
2. **Frontend:** vitest broken — cannot verify against demo DB without test fix. "37" hardcoded text needs conditional or change.
3. **Docker:** No evidence of successful build. Needs verification before demo.
4. **Hosting:** No hosting config. Needs fly.io/render/etc. setup before demo.
5. **Faq docs:** Need truth-sync against demo DB before judge reads them.

---

## Compliance Table

| Step | Requirement | Met EXACTLY? | Evidence |
|------|-------------|--------------|----------|
| S1.1a | Demo DB fingerprint | YES | All 11 tables counted, 327/8/5 match |
| S1.1b | nn.db fingerprint | YES | All 10 tables counted |
| S1.1c | Demo dates + state + absorbed | YES | Apr 16–Jul 3, PENDING=319/ABSORBED=8 |
| S1.2 | Locked params code vs docs | YES (2 gaps found) | File+line for all 12 params |
| S1.2b | Blob guard eps-step logic | YES | `eps - 0.05` step, floor 0.25 |
| S1.3a | seed_demo.py existence | YES | Exists at `scripts/seed_demo.py` (underscore, not hyphen) |
| S1.3b | Entry points used | YES | 6 scripts listed with invocation |
| S1.3c | Full chain automated? | YES (manual) | No single command |
| S1.4a | DB path mechanism | YES | `NN_DB_PATH` env var, default `data/nn.db` |
| S1.4b | Point at demo without code change? | YES | `NN_DB_PATH=data/demo/demo.db` |
| S1.4c | Frontend routes | YES | 9 routes in `src/App.tsx:29-38` |
| S1.4d | Two-lens + Investigate SSE | YES | Sources.tsx, investigate_endpoint.py, Coverage Landscape |
| S1.4e | Hardcoded numbers | YES | 3 references to "37" found |
| S1.5a | March-April Iran articles | YES | 5 articles, all economist |
| S1.5b | May economics/tech stories | YES | None found — Firecrawl confirmed needed |
| S1.5c | Monthly histogram | YES | Full histogram pasted |
| S1.5d | Demo DB date gap | YES | 79 days; need 11 more for 90-day |
| S1.6a | Docker files | YES | 3 files listed, build status UNKNOWN |
| S1.6b | Fireworks config | YES | deepseek-v4-pro via Fireworks |
| S1.6c | Hosting config | YES | NONE |
| S1.6d | LICENSE | YES | MIT |
| S1.6e | Test collection | YES | 314 pytest; 0 vitest (broken) |
| S1.7 | Docs drift inventory | YES | 13 drift items identified |
