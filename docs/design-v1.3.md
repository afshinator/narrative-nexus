# NARRATIVE NEXUS — Project Definition v1.3

Historical design document (v1.3, 2026-07-07). Where this conflicts with README.md or docs/STATUS.md, those are current.

**Hackathon:** AMD Developer Hackathon: ACT II | Ends July 12, 2026 (extended)
**Track:** Track 3 — Unicorn (creativity, originality, product/market potential)
**Status:** Corrected to match current code/DB reality (2026-07-07). Supersedes v1.2.

**Post-v1.3 amendments (2026-07-09):**
- §6 Nav updated: Cluster Report and Timeline removed from top-level nav, Stories page added (UX40). Timeline reached via Stories cards, gated on data completeness.
- Stories page added to §6 pages: flagship story cards with full stats, CTAs to cluster report and timeline.
- Archetype labels updated throughout: Noise Generator → Unmatched Breaker, Selective but Accurate → Late but Reliable, Consensus Follower → Consensus Echo (UX49).
- §3 §4 §7: Legacy nn.db-era snapshot/R_frame counts corrected to demo.db fingerprint (378/10/358/17/13,653).
- One-DB paradigm adopted (UX34): No separate "demo corpus" vs "production" DB. Single shipped database. "Frozen"/"curated verification" language removed from all docs.
- `.readonly` sentinel guard removed (UX36): Replaced by per-endpoint confirmation modals for destructive scraper controls. `NN_READONLY` env var no longer exists.
- Scraper control relocated to Settings page (UX30): Start/stop buttons moved from Pipeline to Settings. Pipeline page shows read-only status.
- Nav scraper indicator upgraded to live (UX52): 30s polling, breathing animation on running state, reduced-motion support.
- Docker optional for Track 3 submission (§2, §8): Submission is repo + video + deck. Docker Compose included as deployment convenience.
- 924 Venezuela earthquake timeline backfilled and unsuppressed (UX43-47): 145 claim_sources rows with first_seen_at, timeline now available via Stories page.
- §9 Open questions marked RESOLVED: Hardware (48GB GPU), models (DeepSeek V4), credits, JSON reliability, fallback, demo config all decided.

**Post-v1.3 amendments (2026-07-12):**
- Header: hackathon deadline extended to July 12, 2026.
- §3 [PENDING] hardware resolved: hackathon pod is AMD Radeon gfx1100 (RDNA3), ROCm 7.2 + PyTorch 2.9. Production embedding model (BAAI/bge-base-en-v1.5) validated running directly on it — capability validation, see `docs/evidence/amd/README.md`.
- §3 [DECISION] extraction model resolved: deepseek-v4-pro shipped as default for all LLM agent slots. Post-PIPE-1, `providers.json` entries carry `base_url` + `api_key_env`; 9 LLM entries shipped (6 Fireworks incl. GLM 5.1/5.2, GPT-OSS 120B, Kimi K2.5/K2.6, plus opencode/deepseek/openai).
- §8 corrected: `docker-compose.yml` defines only the `app` service. The `worker` container was designed but not shipped; `worker/server.py` is a non-wired stub (verified in AMD-AV1, `docs/implementation-rounds/025-amd-av1.md`).
- §8: hosted-deployment guard is `NN_DISABLE_SCRAPER=1` (see README "Hosted deployment").

---

## STATUS KEY

Throughout this document:
- **[LOCKED]** — decided, does not change when access arrives
- **[PENDING]** — waiting on hardware/API access to confirm
- **[DECISION]** — a real open choice we must make, flagged at the right time

---

## SECTION 1: WHAT THIS IS

### The Pitch [LOCKED]

**Narrative Nexus** is a B2B Media Risk and OSINT workflow platform for hedge funds, PR firms, and geopolitical analysts. It monitors a curated panel of 37 news outlets and algorithmically measures their reporting behavior over time — not to judge who is "right," but to answer: *which sources reliably break stories ahead of the mainstream consensus, which ones generate systematic noise, and which quietly rewrite history after publication?*

The system's foundational constraint — **it tracks consensus reality, not truth** — is both an ethical design decision and a feature. It makes the system defensible and non-partisan, which is a genuine competitive moat in the media analytics space.

### What it produces [LOCKED]

A **living reputation ledger** for each monitored source, built from measurable behavior across hundreds of stories. The ledger answers:

- Does this source break outlier claims that later become mainstream consensus? (**Early Breaker**)
- Does this source produce high-volume claims that never get confirmed? (**Unmatched Breaker**)
- Does this source cover stories selectively, but accurately? (**Late but Reliable**)
- Does this source stay close to the mainstream view? (**Consensus Echo**)
- Does this source quietly edit its own articles without issuing corrections?

No composite score. Six independent dimensions. The user sorts by what matters to them.

### The vocabulary [LOCKED]

These terms are used throughout the system and must be defined consistently in UI copy, tooltips, and onboarding:

| Term | Meaning |
|---|---|
| **Consensus reality** | The version of events agreed upon by the majority of the panel at a given threshold. Not "the truth." |
| **Consensus-absorbed** | A claim that has entered the consensus version of events. Terminal state. |
| **Cross-source convergent** | A consensus-absorbed claim that was independently corroborated by another source before absorption. |
| **Self-consistent** | A consensus-absorbed claim where only the origin source published consistent follow-up; no independent corroboration, but the panel eventually agreed. |
| **Unresolved** | A claim that never became consensus-absorbed after 90 days. Terminal state. |
| **Outlier claim** | A claim present in one or few sources but absent from the consensus baseline at extraction time. |

The footer on every page reads: **"Narrative Nexus tracks consensus reality, not truth."**

---

## SECTION 2: HACKATHON REQUIREMENTS

### Confirmed constraints [LOCKED]

- **Track 3 submission format:** GitHub repository + 5-minute demo video + slide deck. Hosted demo URL is optional. No Docker image is required for Track 3 — Docker Compose is included as a deployment convenience, not a submission requirement.
- **Track 3 judging criteria:** Creativity · Originality · Product/Market Potential · Business Value · Application of Technology · Presentation.
- **Model restriction:** The "two AMD-hardware models only" restriction applies to Tracks 1 and 2 only. Track 3 explicitly says "any open-source models and frameworks." We are not model-restricted.
- **No benchmark scoring.** There is no throughput or accuracy score. The demo *is* the submission.

### Credits [LOCKED amounts, PENDING activation]

| Resource | Amount | How used |
|---|---|---|
| AMD Developer Cloud credits | $100 | GPU pod for embedding workloads |
| Fireworks AI API credits | $50 | LLM inference |
| Hackathon launch bonus credits | Unknown | TBD at kickoff |

**Note:** These are hackathon-provided resources. The architecture is provider-agnostic — if credits are unavailable or exhausted, the pipeline falls back to alternate providers. See §3 compute allocation table and `config/providers.json` for the full provider matrix.

---

## SECTION 3: SYSTEM ARCHITECTURE

### Design principle [LOCKED]

The pipeline is framed as a **coordinated swarm of specialized AI Agents**, not a batch processing pipeline. This framing is correct (agents have specific instructions, schemas, and tools) and aligns directly with the hackathon's stated theme of "intelligent workflows, automation, and real AI applications."

### The four agents [LOCKED]

**Agent 1 — Intake & Clustering Agent**
Ingests article text, generates embeddings, clusters articles about the same event into unified story threads using semantic similarity. Provider-configurable via JSON config + API (available: Fireworks, OpenCode Zen, OpenAI, Local CPU, AMD GPU pod via ROCm). Default: Fireworks AI (`providers.json:59` — `"agent1_llm": "fireworks"`, embeddings: `"agent1_embedding": "fireworks"`).

**Agent 2 — Forensic Extraction Agent**
Takes raw article text, strips editorial framing, and extracts atomic factual claims as structured JSON. Provider-configurable via JSON config + API (available: Fireworks, OpenCode Zen, DeepSeek, OpenAI). Enforces strict output schema — no freeform text output, only parseable claim arrays. Default: Fireworks AI (`providers.json:60` — `"agent2_llm": "fireworks"`).

**Agent 3 — Consensus Alignment Agent**
Takes claims from all sources covering the same story, computes cross-source agreement, identifies the consensus baseline, and classifies each claim as consensus-absorbed, developing, or outlier. Pure Python set math — runs on CPU, no GPU or LLM required for the core computation.

**Agent 4 — Silent Auditor Agent**
Compares historical snapshots of article body text to detect significant unreported edits. Provider-configurable via JSON config + API (same providers as Agent 2). Runs as a background job. Flags candidates for human review. Default: Fireworks AI (`providers.json:61` — `"agent4_llm": "fireworks"`).

### Compute allocation [LOCKED architecture, PENDING exact hardware specs]

| Workload | Where it runs (configurable) | Why |
|---|---|---|
| Sentence transformer embeddings (article clustering, vertical classification) | Configurable: Fireworks API / OpenAI API / OpenCode Zen / Local CPU via llama.cpp / AMD GPU pod via ROCm | Defaults to Fireworks AI (BAAI/bge-base-en-v1.5); AMD GPU pod when available (VRAM-light, <2GB) |
| Claim matching embeddings | Configurable: separate embedding slot | Defaults to Fireworks AI nomic-embed-text-v1.5 (`providers.json:58`: `"claim_matching_embedding": "fireworks-nomic"`) |
| LLM inference: framing neutralization, claim extraction, forensic synthesis | Configurable: Fireworks API / OpenCode Zen / DeepSeek API / OpenAI API | All providers support JSON schema output; calling Fireworks IS using AMD Instinct hardware |
| Consensus math, reputation scoring, claim resolution | CPU (app server) | Pure Python, no GPU required |
| Article scraping, RSS polling, scheduling | CPU (app server) | I/O bound, no GPU required |
| SQLite database | App server volume | Sufficient for hackathon scale |

**Note on provider selection:** Provider assignments are configurable at runtime via the Pipeline Flow page dropdowns, backed by `config/providers.json`. All agent defaults are Fireworks AI (see `providers.json:56-62`). An AMD 1-click shortcut sets all agents to Fireworks (AMD Instinct-backed). Fallback providers ensure the pipeline works even without AMD access. See `docs/impact-provider-agnostic-architecture.md` for the full provider matrix.

**[RESOLVED — see 2026-07-12 amendments]:** Hackathon pod confirmed as AMD Radeon gfx1100 (RDNA3) on ROCm 7.2. The production embedding model was validated running directly on it (`docs/evidence/amd/README.md`). Exact VRAM total not measured; all planned GPU workloads (embedding models) fit comfortably regardless.

**[DECIDED: deepseek-v4-pro]:** Shipped as the default for all LLM agent slots; JSON output reliability sufficient via `response_format`. For non-Fireworks providers, model selection follows defaults in `config/providers.json`.

### Data format contracts [LOCKED]

The following formats apply system-wide across all pipeline stages and API boundaries:

- **Dates:** All dates stored in ISO 8601 format with UTC timezone (`YYYY-MM-DDTHH:MM:SS+00:00`). Feed dates from RSS (RFC 2822) must be converted before storage. The frontend displays dates in Pacific Time (America/Los_Angeles) with the appropriate offset applied at render time — the canonical store is always UTC.
- **URLs:** All article URLs stored as canonical source URLs. Redirect chains must be resolved before storage. Google News redirect URLs must not be stored as-is — extract the original source URL from the redirect target.
- **Numeric scales:** All percentage values normalized to 0–100. No 0–1 fractional values in the database. Raw values (days, counts) stored at native scale.
- **Nullable fields:** Dimensions not yet computable for a given cell (e.g., R_frame for sources with no framing scores collected yet) are stored as `NULL` in SQLite, not 0 or empty string. The frontend handles nulls gracefully (dash display, no rendering of missing data as zero). As of 2026-07-09, all 6 dimensions are live: R_edit, R_correct, and R_frame are computed in snapshots and have populated values. R_frame has partial coverage (855 of 13,653 snapshots non-NULL) due to incomplete LLM framing backfill — remaining cells are NULL but the computation pipeline exists.

---

## SECTION 4: THE ANALYTICAL MODEL

*This section is the moat. Do not simplify it for the demo.*

### Locked pipeline parameters [LOCKED]

These parameters are calibrated on empirical data and should not be changed without explicit authorization and a full recluster cycle:

| Parameter | Value | Where set | Evidence |
|---|---|---|---|
| eps (DBSCAN) | 0.35 | `pipeline/agent1_intake.py:43` | P1 sweep; 4/6 groups merged, 1 over-merge |
| min_samples | 2 | `pipeline/agent1_intake.py:43` | Higher values reduce multi-source clusters with no gain |
| sim_threshold (claim matching) | 0.85 | `pipeline/claim_matching.py:65` | P2 A/B; 0.80 introduces factually wrong merges |
| MAX_CLUSTER_SIZE (blob guard) | 60 | `pipeline/agent1_intake.py:34` | Prevents cross-story blobs |
| EPS_FLOOR | 0.25 | `pipeline/agent1_intake.py:36` | Recursive split floor |
| MIN_CORROBORATION | 2 | `pipeline/consensus.py:8` | Single-source claims must NOT self-validate (D1 rule) |
| D1 absorption rule | reporting ≥ MIN_CORROBORATION AND pct ≥ vertical threshold | `pipeline/resolution.py:28` | D1: >=2 distinct T1/T2 pool sources AND pct >= threshold |
| D2 R_val window | Exclude claims created within 7 days of as_of | `pipeline/snapshots.py:66` — `AND date(c.created_at) <= date(?, '-7 days')` | Claims too new to assess validation |
| time_window (DBSCAN) | 14 days | `pipeline/agent1_intake.py:138` — `window_days = 14` | Time-bounded clustering window |
| Embedding model (article clustering) | BAAI/bge-base-en-v1.5 | `config/providers.json:7` | Locked on empirical grounds (STATUS.md §RESOLVED) |
| Claim matching embedding | nomic-ai/nomic-embed-text-v1.5 | `config/providers.json:13`, `providers.json:58` | Task-specific embedding space (N-round) |
| vertical thresholds | geo 65%, econ 75%, tech 75% | `pipeline/consensus.py:3` — `DEFAULT_THRESHOLDS` | Calibrated per-vertical |

### Consensus threshold [LOCKED]

The consensus baseline is computed over Tier 1+2 sources only (the "consensus pool"). A claim enters the consensus baseline when it appears in more than `threshold`% of the pool's source graphs for that story.

Default thresholds:
- GEOPOLITICS: 65%
- ECONOMICS: 75%
- TECHNOLOGY: 75%

Configurable at runtime. Stored with each cluster run so historical comparisons remain valid.

### Claim lifecycle [LOCKED]

Claims follow a formal state machine. Two axes are independent — do not conflate them.

**Axis 1 — Lifecycle state:**
```
PENDING → CONSENSUS_ABSORBED  (terminal, at 7-day, 30-day, or 90-day check)
PENDING → UNRESOLVED          (terminal, forced at 90-day check only)
```

**Axis 2 — Convergence type** (written only at absorption):
- `CROSS_SOURCE_CONVERGENT` — independently corroborated before absorption
- `SELF_CONSISTENT` — absorbed without independent corroboration

### Reputation dimensions [LOCKED]

Six dimensions tracked per source per vertical. All six shown simultaneously; no composite rank. All six are now live (all implemented and wired into snapshot computation).

| Dimension | Symbol | Polarity | What it measures |
|---|---|---|---|
| Outlier Origination Rate | R_orig | Trait (no favorable direction) | How often a source breaks outlier claims |
| Outlier Validation Rate | R_val | Graded — high is favorable | Of claims originated, how many became absorbed |
| Speed Premium | R_speed | Graded — low (days) is favorable | Median days between origination and absorption |
| Framing Consistency | R_frame | Graded — low stddev is favorable | Consistency of editorial framing across stories |
| Silent Edit Rate | R_edit | Graded — low is favorable | Rate of significant unreported article edits |
| Formal Correction Rate | R_correct | Trait (no favorable direction) | Rate of formal published corrections |

**Implementation status:** All 6 computed per `pipeline/snapshots.py` (R_edit: line 184, R_correct: line 227, R_frame: line 258), wired into snapshot computation per `pipeline/runner.py:176-178`. R_frame has partial coverage (855/13,653 snapshots non-NULL — LLM framing backfill is incomplete; remaining cells are NULL and shown as dash).

**Archetype assignment** (from R_orig and R_val relative to panel median):
- R_orig > median AND R_val > median → **Early Breaker**
- R_orig > median AND R_val ≤ median → **Unmatched Breaker**
- R_orig ≤ median AND R_val > median → **Late but Reliable**
- R_orig ≤ median AND R_val ≤ median → **Consensus Echo**

### Resolution schedule [LOCKED]

- **7-day check:** PENDING → CONSENSUS_ABSORBED if Tier 1/2 picked it up fast
- **30-day check:** PENDING → CONSENSUS_ABSORBED if threshold crossed
- **90-day check:** PENDING → CONSENSUS_ABSORBED or forced UNRESOLVED (terminal)
- **Daily snapshots:** One row per (source, vertical) written unconditionally each day — this is what enables the reputation time machine view

---

## SECTION 5: DATA & SOURCES

### Source panel design [LOCKED]

Two distinct roles:

- **Consensus pool** — Tier 1 and Tier 2 sources. Their aggregate output defines consensus reality. A claim at ≥ threshold% of pool = consensus baseline.
- **Tracked panel** — All tiers. The reputation ledger is computed for all sources. Tier 3/4/5 sources are the analytically interesting ones.

### Active panel (37 sources across 5 tiers) [LOCKED]

| Tier | Role | Sources |
|---|---|---|
| 1 — Wire/Consensus Anchor | Consensus pool | Reuters, AP, BBC, NPR, The Guardian (5 sources) |
| 2 — Mainstream Editorial | Consensus pool | Fox News, Politico, The Economist, NYT, Washington Post, CNN, CBS News, ABC News (8 sources) |
| 3 — International | Tracked only | Al Jazeera, Deutsche Welle, NHK World, Global Times, France24, Buenos Aires Times, The Straits Times, The Hindu, Premium Times NG, Times of Israel, Vanguard NGR, The Reporter Ethiopia, The Namibian, Punch NG, Jamaica Observer, MercoPress, Tehran Times (17 sources) |
| 4 — Independent/Investigative | Tracked only | The Intercept, ProPublica, Bellingcat, African Arguments (4 sources) |
| 5 — Contrarian | Tracked only | ZeroHedge, The Grayzone, Sputnik Globe (3 sources) |

**Total active: 37 sources.** Source of truth: `SELECT tier, COUNT(*) FROM sources GROUP BY tier` → T1:5, T2:8, T3:17, T4:4, T5:3 = 37. Previously described as "~20" or "20 default sources" — corrected to the actual panel size.

### Topic verticals [LOCKED]

Three verticals at launch. Sports excluded.
- **GEOPOLITICS** — international affairs, conflicts, diplomacy, elections
- **ECONOMICS** — markets, central bank policy, trade, corporate earnings with systemic implications
- **TECHNOLOGY** — AI policy, semiconductors, cybersecurity, platform governance

A story can match multiple verticals. Reputation scores are tracked independently per source per vertical.

### Scraping stack [LOCKED priority order]

1. `feedparser` — RSS discovery (Tier 1+2, free, unlimited)
2. `newspaper4k` — article body extraction (free, unlimited)
3. RSS `<content:encoded>` field — for full-text RSS sources like ProPublica
4. DuckDuckGo search — find source-specific article URLs
5. Firecrawl free tier — fallback for persistent failures (1,000 credits/month cap)
6. RSS summary fallback — paywalled sources, last resort

### Paywall handling [LOCKED]

Sources where the full body is unavailable (`BODY_UNAVAILABLE`) are:
- Excluded from Omission Index computation (shown as `OI_EXCLUDED` in UI)
- Still included in consensus pool voting via RSS summary text
- Not penalized in reputation scoring for what they couldn't provide

---

## SECTION 6: FRONTEND — PAGES AND VIEWS

### Navigation [LOCKED]

Sticky app-level nav bar on every page (`src/components/AppNav.tsx:7-14`):

`Narrative Nexus [logo] | Sources | Pipeline | Investigate | Panel | · | Stories | [scraper status] | Settings | [? help]`

Notes:
- **Source Profile** is NOT in the nav — it is accessed by clicking a source card from the Sources page (navigates to `/source/{domain}`).
- **Cluster Report** and **Timeline** are NOT in the nav — they are reached via the Stories page cards (UX40). Timeline links are gated on data completeness: `distinctDays > 1` AND zero empty `first_seen_at` values (UX26/UX27).
- **Stories** was added to the nav in UX40 — it displays story-cluster cards for the current flagship stories.
- The `?` icon re-opens the onboarding glossary dialog.

### Pages [LOCKED]

**Sources (home)** — Reputation leaderboard + scatter plot. The landing page. Archetype filter pills, sortable columns, cross-linked hover between table and scatter markers. Shapes in the scatter encode outlet format; color encodes behavior archetype. UX2 comprehension layer: full-width intro strip ("Not the truth — consensus reality." + one-sentence description), reusable tooltips on intro strip/source count/vertical label/axes/labels/archetype legend items.

**Source Profile** — Radar chart (6 axes, percentile-oriented, outward = favorable), archetype badge, title block with tier name and description, two-tier stat panel (source vs tier average), outlier waterfall with convergence-type breakdown, silent edit log with list UI. **(Not in nav bar — reached by clicking source cards on Sources page.)**

**Cluster Report** — 3-zone forensic report (consensus summary / distortion matrix / forensic analysis). Version indicator. Config-change banner. Consensus-reality language throughout — no "source was right/wrong" copy anywhere.

**Timeline** — Horizontal Day 0–90 animation per claim. Echo-mimic dots (dashed connection to origin). CONSENSUS-ABSORBED vertical line. UNRESOLVED claims fade at Day 90. Story-specific — reached via Stories page cards, not in top-level nav. Timeline links are gated on data completeness (distinctDays > 1 AND zero empty first_seen_at).

**Pipeline Flow ("The Machine")** — Animated pipeline diagram showing live status. Each stage node shows a dropdown selector for its compute provider, with an AMD 1-click shortcut button to switch all agents to AMD-backed providers. Replay mode for past clusters.

**Investigate** — Ad-hoc forensic query tool. Accepts an article URL or pasted text. Runs through pipeline stages 1–3 (Intake & Clustering → Forensic Extraction → Consensus Alignment) as a read-only analysis. Displays extracted atomic claims, cross-source matches, and consensus baseline comparison inline. Results persist in localStorage and survive navigation, refresh, and browser restarts. Snapshot banner: "Claim resolution states are not available for ad-hoc reports." Does not write to reputation tables. Does not require database persistence for results.

**Panel Management** — Activate/deactivate sources. Category balance indicator. Archived sources retain full history.

**Stories** — Story-cluster cards for the flagship stories. Each card shows: coverage window, tempo descriptor, article/claims/sources/absorbed counts, consensus statements, median time-to-consensus. CTAs: "View timeline →" (gated on data completeness — distinctDays > 1 AND zero empty first_seen_at) and "Full cluster report →". Reached via the nav bar.

**Settings** — Consensus thresholds (per vertical), font scale slider (rem-based, persisted to localStorage), theme/skin selector, system health panel, manual pipeline trigger.

### Visual tone → See `docs/design-tokens.md`

The visual design language is defined in `docs/design-tokens.md`, extracted from the mock HTML files via `designlang`. That file is the single source of truth for colors, fonts, spacing, and component patterns. This section kept only for historical reference of the build order.

**Build order:** `style.css` → `pipeline.html` → `index.html` → `source.html` → `cluster.html` → `timeline.html` → `investigate.html` → `panel.html` → `settings.html`

### Onboarding [LOCKED]

On first launch, a **glossary dialog** (`src/components/OnboardingDialog.tsx`) appears with 6 vocabulary terms and lucide-react icons, matching §1 vocabulary. The dialog includes a "Don't show on startup" checkbox persisted via Zustand store (`onboardingComplete`). Re-accessible from the `?` icon in the nav bar.

The v1.2 doc referenced a "5-step walkthrough" — this was replaced by the single glossary dialog + the Sources page intro strip/tooltip comprehension layer (UX2). There is no multi-step walkthrough; the glossary dialog + intro strip jointly serve the onboarding function.

---

## SECTION 7: DEMO STRATEGY

### Core principle [LOCKED]

**There is no demo mode.** The application always works the same way — it reads from SQLite and serves all pages normally. The database is pre-seeded with data spanning 90 days by processing curated article URLs through the real pipeline before demo day. The app is unaware it is being demonstrated.

### How the database gets data [LOCKED]

The database (`data/demo/demo.db`) ships pre-loaded with 358 articles from 37 sources, processed through the full pipeline. Fingerprint: 378 claims / 10 absorbed / 358 articles / 17 clusters / 13,653 snapshots, spanning 2026-03-03 → 2026-07-03. The scraper is paused on ship; toggling Start in Settings begins live collection into this same database.

The seed process follows the pipeline's full chain: ingest → Agent 1 (BGE clustering, eps=0.35, blob guard at MAX_CLUSTER_SIZE=60) → Agent 2 (Fireworks extraction) → match_all_clusters (nomic claim matching, sim=0.85) → Agent 3 (consensus) → snapshot backfill (all 6 R-dimensions, every calendar day unconditionally). The full reset-recluster-rematch-consensus sequence is documented in the nn-dev-workflow skill under "Full Reconciliation-Verdict Pipeline (O9 Pattern)."

### What the demo must show [LOCKED]

1. **The scatter plot landing state** — four quadrant labels, sources plotted, shapes encoding format. Judge immediately sees the idea without reading anything.

2. **A reputation radar in motion** — scrub through 90 days on one source, watch the polygon morph, archetype badge change, event markers fire (claim absorbed / silent edit detected). This is the "this doesn't exist anywhere else" moment.

3. **The pipeline replay** — the animated diagram showing which stage ran on which provider (Fireworks, OpenCode Zen, DeepSeek, OpenAI, Local CPU). Dropdown selectors on each stage node. This is the "configurable architecture is real, not decorative" moment.

4. **One live forensic pass (conditional — backup beat only):** The Investigate page's claim extraction stage has a known unresolved uvicorn transport bug (500 errors from Fireworks from uvicorn-served requests; identical calls work from standalone Python). This conflicts with the "never show live network calls that could fail mid-demo" rule. If the bug is resolved before submission, this can be a backup beat; otherwise, skip it.

### What the demo must NOT do [LOCKED]

- Never imply a source "was right" or "was wrong"
- Never show live network calls that could fail mid-demo
- Never show the pipeline running for the first time on unknown data

---

## SECTION 8: CONTAINERIZATION

### Status [LOCKED]

Docker Compose is included as an optional deployment convenience — it is NOT a Track 3 submission requirement (see §2). The `docker-compose.yml` and `Dockerfile.app` exist and are maintained for users who prefer containerized deployment.

### Service split [LOCKED architecture, PENDING exact image details]

```
services:
  app:          # FastAPI server — scheduler, API endpoints, frontend serving
  worker:       # Optional — AMD GPU pod for embedding models via ROCm
                # When not present, app calls external embedding APIs
  db:           # SQLite volume (or file mount on app container)
```

The `app` and `worker` containers communicate over HTTP when both are present. All external API calls (Fireworks, OpenCode, DeepSeek, OpenAI) originate from `app`. No GPU access needed in `app`.

The `worker` container requires ROCm base image and `sentence-transformers`. It is the only AMD GPU-dependent component, and is omitted when embeddings are served via external APIs.

**Note:** The `.readonly` sentinel guard was removed in UX36 (replaced by per-endpoint confirmation modals for destructive scraper controls). `NN_READONLY` env var no longer exists.

**[PENDING]:** Exact ROCm base image tag for the hackathon's Radeon GPU pod. Confirm at access time.

---

## SECTION 9: OPEN QUESTIONS [RESOLVED]

All questions that blocked specific implementation decisions at design time have been resolved by hackathon access and two weeks of development. The table below is kept as useful history.

| # | Question | Blocks | How to resolve | Resolution |
|---|---|---|---|---|
| 1 | Exact hardware: what Radeon GPU pods does the hackathon provide? VRAM? | Worker container image, model size ceiling | Access + AMD support | 48GB GPU per hackathon FAQ |
| 2 | What LLM models are available on each provider and at what token cost? | Model selection for Agents 2/3/4 | Test with each provider's API | MiniMax + Kimi-K2P5 on Fireworks; DeepSeek V4 family chosen for extraction |
| 3 | What are the "additional hackathon launch credits"? | Budget for dev vs demo inference | Revealed at kickoff | Revealed |
| 4 | Which provider+model gives best JSON extraction reliability? | Agent 2 and 3 prompt design | Benchmark once API access arrives | DeepSeek V4 family chosen; JSON reliability sufficient via response_format |
| 5 | Is fine-tuning worth attempting on Track 3 within the timeline? | Stretch scope | Decide after initial pipeline is stable | Out of scope (§10) |
| 6 | How should the provider abstraction layer handle fallback if the primary provider is unreachable? | Pipeline reliability | Test failover during integration | Provider fallback built (see providers.json matrix) |
| 7 | What's the optimal config for provider/model per agent for demo day? | Demo strategy | Benchmark with seed script data | All-Fireworks (deepseek-v4-pro for agents, BGE + nomic for embeddings) |

---

## SECTION 10: WHAT IS EXPLICITLY OUT OF SCOPE

To prevent scope creep:

- No fine-tuning in MVP (Section 9 Q5 is a stretch only)
- No FAISS GPU index (Python set math is sufficient and FAISS ROCm build is unverified)
- No Celery/Redis (APScheduler in-process is sufficient for hackathon)
- No Postgres (SQLite WAL mode is sufficient)
- No email/webhook alerts
- No back-test engine at launch (reputation scores start from day one of the shipped dataset)
- No Rense.com custom parser
- Sports vertical excluded
- The "two AMD models only" restriction does not apply to Track 3 — do not artificially constrain model choice

---

## SECTION 11: SUCCESS CRITERIA

**For the hackathon judge (the demo visitor):**
They land on the Sources page, immediately see the scatter plot with four labeled quadrants, click an Early Breaker source, see their radar chart, click through to a cluster, watch the timeline animate Day 0 → Day 90. They understand the core idea in under 2 minutes without reading documentation.

**For the Analyst (the actual user):**
They return daily. They check new silent edit flags. They watch whether a source they've been tracking is drifting toward Unmatched Breaker territory. They run ad-hoc investigations on breaking news. The data changes their editorial or risk decisions.

**For the judges' Business Value criterion:**
The pitch is concrete: media risk intelligence for institutional buyers (hedge funds, PR firms, geopolitical analysts) who currently have no systematic way to track *how* sources behave over time — only *what* they publish. No competitor product exists. The moat is longitudinal behavioral data, not a one-shot analysis.

---

## CHANGELOG — v1.2 → v1.3

### DV1.1 — Default provider corrected: "OpenCode Zen" → "Fireworks AI"

**Evidence:** `config/providers.json:56-62` — all agent defaults are `"fireworks"`: agent1_llm, agent1_embedding, agent2_llm, agent4_llm, claim_matching_embedding.

**Change:** All 4 agent descriptions in §3 updated from "Default: OpenCode Zen" to "Default: Fireworks AI" with providers.json line citations. Compute allocation table §3 updated from "Defaults to OpenCode Zen for dev" to "Defaults to Fireworks AI (BAAI/bge-base-en-v1.5)". Added claim matching embedding row to compute table.

### DV1.2 — Locked pipeline parameters added to §4

**Evidence:**
- eps=0.35: `pipeline/agent1_intake.py:43`
- min_samples=2: `pipeline/agent1_intake.py:43`
- sim_threshold=0.85: `pipeline/claim_matching.py:65`
- MAX_CLUSTER_SIZE=60: `pipeline/agent1_intake.py:34`
- EPS_FLOOR=0.25: `pipeline/agent1_intake.py:36`
- MIN_CORROBORATION=2: `pipeline/consensus.py:8`, `pipeline/resolution.py:5`
- D1 absorption rule: `pipeline/resolution.py:28`
- D2 R_val 7-day window: `pipeline/snapshots.py:66` — `AND date(c.created_at) <= date(?, '-7 days')`
- time_window=14 days: `pipeline/agent1_intake.py:138`
- Embedding model BAAI/bge-base-en-v1.5: `config/providers.json:7`, STATUS.md §RESOLVED
- Claim matching embedding nomic: `config/providers.json:13,58`

**Change:** Added "Locked pipeline parameters" subsection to §4 with table of all 13 locked parameters + values + code citations. §4 previously had no locked parameter documentation.

### DV1.3 — R-score status corrected: "NULL until agents built" → all 6 live

**Evidence:**
- `pipeline/snapshots.py:184` — `compute_r_edit_raw()` — computed, wired
- `pipeline/snapshots.py:227` — `compute_r_correct_raw()` — computed, wired
- `pipeline/snapshots.py:258` — `compute_r_frame_raw()` — computed, wired
- `pipeline/runner.py:176-178` — all three wired into `_compute_and_write_snapshots()`
- DB: 13,653 snapshots total — r_frame=855 populated
- **Note:** Prior v1.3 changelog entries reference nn.db-era counts (44,955 snapshots). These are corrected in the post-v1.3 amendments. The demo DB fingerprint is 378/10/358/17/13,653.

**Change:** §3 data format contracts updated: removed "R_frame, R_edit, R_correct until their respective agents are built" claim. Replaced with: all 6 dimensions live, R_frame has partial coverage (855/13,653) due to incomplete LLM framing backfill.

### DV1.4 — Nav corrected: no "Source Profile" in nav bar; onboarding is glossary dialog, not 5-step walkthrough

**Evidence:**
- `src/components/AppNav.tsx:7-14` — nav items: Sources, Cluster Report, Timeline, Pipeline, Investigate, Panel
- Settings and `?` help icon are right-aligned after scraper status
- Source Profile accessed via click on source card, not a nav link
- `src/components/OnboardingDialog.tsx` — single dialog with 6 glossary terms, "Don't show on startup" checkbox, not a multi-step walkthrough

**Change:** §6 nav string updated to match actual AppNav.tsx items. Added notes: Source Profile not in nav, Cluster/Timeline link to cluster 966, `?` reopens glossary. Onboarding description changed from "5-step first-launch walkthrough" to "glossary dialog with 6 vocabulary terms + intro strip/tooltip comprehension layer."

### DV1.5 — Source panel: "20 defaults" → 37 sources across 5 tiers

**Evidence:** `SELECT tier, COUNT(*) FROM sources GROUP BY tier` → T1:5, T2:8, T3:17, T4:4, T5:3 = 37. Full source listing per tier from STATUS.md Source Tier Reference.

**Change:** §1 pitch: "~20 news outlets" → "37 news outlets." §5 panel table: expanded from 20 sources to full 37 with all tier members. "Total default active: 20 sources" → "Total active: 37 sources."

### DV1.6 — Version bump, sweep corrections

**Change:**
- Version bumped to v1.3, dated 2026-07-07
- "Supersedes v1.2" added to header
- CHANGELOG added (this section)
- §7 seed script description updated from `scripts/seed-demo.py` + fiction to the actual demo DB process (O9 full reconciliation pipeline)
- Demo DB fingerprint added (378/10/358/17/13,653)
- UX2 comprehension layer acknowledged in Sources page description

### Flagged, not changed (for human review)

- §2 "OpenCode Zen" still appears as a fallback provider mention — the config has it (`providers.json:38`), so this is technically correct even though it's not the default.
- §7 demo requirements #4 mentions "four outlets" for live forensic pass — actual Investigate page may handle more; not verified.
- §8 Docker compose service split mentions a `worker` container — actual Dockerfile may differ; not verified (D1 gate marked CANNOT COMPLY for container runtime).
- §9 open questions may now be obsolete (hackathon is in 4 days, questions 1-7 likely resolved or moot); not verified against current state.
- §6 build order references `style.css` and HTML mock files — actual build uses Vite + React; this may be a historical artifact.

---

*"Narrative Nexus tracks consensus reality, not truth."*