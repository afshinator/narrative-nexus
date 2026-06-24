# NARRATIVE NEXUS — Project Specification v1.1
**Hackathon:** AMD Developer Hackathon: ACT II | Ends July 11, 2026
**Track:** Track 3 — Unicorn (creativity, originality, product/market potential)
**Status:** Working draft. Supersedes all prior versions.

---

## STATUS KEY

Throughout this document:
- **[LOCKED]** — decided, does not change when access arrives
- **[PENDING]** — waiting on hardware/API access to confirm
- **[DECISION]** — a real open choice we must make, flagged at the right time

---

## SECTION 1: WHAT THIS IS

### The Pitch [LOCKED]

**Narrative Nexus** is a B2B Media Risk and OSINT workflow platform for hedge funds, PR firms, and geopolitical analysts. It monitors a curated panel of ~20 news outlets and algorithmically measures their reporting behavior over time — not to judge who is "right," but to answer: *which sources reliably break stories ahead of the mainstream consensus, which ones generate systematic noise, and which quietly rewrite history after publication?*

The system's foundational constraint — **it tracks consensus reality, not truth** — is both an ethical design decision and a feature. It makes the system defensible and non-partisan, which is a genuine competitive moat in the media analytics space.

### What it produces [LOCKED]

A **living reputation ledger** for each monitored source, built from measurable behavior across hundreds of stories. The ledger answers:

- Does this source break outlier claims that later become mainstream consensus? (**Early Breaker**)
- Does this source produce high-volume claims that never get confirmed? (**Noise Generator**)
- Does this source cover stories selectively, but accurately? (**Selective but Accurate**)
- Does this source stay close to the mainstream view? (**Consensus Follower**)
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

- **All submissions must be containerized.** Docker is the delivery format, not an optional nice-to-have. This affects how every component is structured from day one.
- **Track 3 judging criteria:** Creativity · Originality · Product/Market Potential · Business Value · Application of Technology · Presentation.
- **Model restriction:** The "two AMD-hardware models only" restriction applies to Tracks 1 and 2 only. Track 3 explicitly says "any open-source models and frameworks." We are not model-restricted.
- **No benchmark scoring.** There is no throughput or accuracy score. The demo *is* the submission.

### Credits [LOCKED amounts, PENDING activation]

| Resource | Amount | How used |
|---|---|---|
| AMD Developer Cloud credits | $100 | GPU pod for embedding workloads |
| Fireworks AI API credits | $50 | LLM inference |
| Hackathon launch bonus credits | Unknown | TBD at kickoff |

---

## SECTION 3: SYSTEM ARCHITECTURE

### Design principle [LOCKED]

The pipeline is framed as a **coordinated swarm of specialized AI Agents**, not a batch processing pipeline. This framing is correct (agents have specific instructions, schemas, and tools) and aligns directly with the hackathon's stated theme of "intelligent workflows, automation, and real AI applications."

### The four agents [LOCKED]

**Agent 1 — Intake & Clustering Agent**
Ingests article text, generates embeddings, clusters articles about the same event into unified story threads using semantic similarity. Runs on AMD GPU pod (embedding workload, VRAM-light).

**Agent 2 — Forensic Extraction Agent**
Takes raw article text, strips editorial framing, and extracts atomic factual claims as structured JSON. Runs via Fireworks AI API. Enforces strict output schema — no freeform text output, only parseable claim arrays.

**Agent 3 — Consensus Alignment Agent**
Takes claims from all sources covering the same story, computes cross-source agreement, identifies the consensus baseline, and classifies each claim as consensus-absorbed, developing, or outlier. Pure Python set math — no GPU or LLM required for the core computation. LLM involved only for the final forensic synthesis narrative.

**Agent 4 — Silent Auditor Agent**
Compares historical snapshots of article body text to detect significant unreported edits. Runs as a background job. Flags candidates for human review.

### Compute allocation [LOCKED architecture, PENDING exact hardware specs]

| Workload | Where it runs | Why |
|---|---|---|
| Sentence transformer embeddings (BERTopic, entity clustering, vertical classification) | AMD GPU pod via ROCm | GPU-accelerated, VRAM-light (< 2GB), fits any Radeon |
| LLM inference: framing neutralization, claim extraction, forensic synthesis | Fireworks AI API | AMD Instinct MI325X/MI355X-backed; no self-hosting needed |
| Consensus math, reputation scoring, claim resolution | CPU (app server) | Pure Python, no GPU required |
| Article scraping, RSS polling, scheduling | CPU (app server) | I/O bound, no GPU required |
| SQLite database | App server volume | Sufficient for hackathon scale |

**Note on Fireworks/AMD story:** Calling Fireworks IS using AMD Instinct hardware. Fireworks runs MI325X and MI355X under a multi-year AMD partnership. This is actually a stronger AMD integration story for judges than self-hosting on a pod: you get data-center-class Instinct inference without the operational overhead.

**[PENDING]:** Exact VRAM of hackathon Radeon GPU pods. Expected 16–48GB based on ROCm-on-Radeon documentation. All planned GPU workloads (embedding models) fit well within this.

**[DECISION when access arrives]:** Which Fireworks model for extraction (Llama 3.3 70B vs DeepSeek-V4-Pro) and synthesis. Benchmark JSON output reliability on both before committing. DeepSeek-V4-Pro is the leading alternative to Llama for structured extraction tasks.

---

## SECTION 4: THE ANALYTICAL MODEL

*This section is the moat. Do not simplify it for the demo.*

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

Six dimensions tracked per source per vertical. All six shown simultaneously; no composite rank.

| Dimension | Symbol | Polarity | What it measures |
|---|---|---|---|
| Outlier Origination Rate | R_orig | Trait (no favorable direction) | How often a source breaks outlier claims |
| Outlier Validation Rate | R_val | Graded — high is favorable | Of claims originated, how many became absorbed |
| Speed Premium | R_speed | Graded — low (days) is favorable | Median days between origination and absorption |
| Framing Consistency | R_frame | Graded — low stddev is favorable | Consistency of editorial framing across stories |
| Silent Edit Rate | R_edit | Graded — low is favorable | Rate of significant unreported article edits |
| Formal Correction Rate | R_correct | Trait (no favorable direction) | Rate of formal published corrections |

**Archetype assignment** (from R_orig and R_val relative to panel median):
- R_orig > median AND R_val > median → **Early Breaker**
- R_orig > median AND R_val ≤ median → **Noise Generator**
- R_orig ≤ median AND R_val > median → **Selective but Accurate**
- R_orig ≤ median AND R_val ≤ median → **Consensus Follower**

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

### Default active panel [LOCKED]

| Tier | Role | Default sources |
|---|---|---|
| 1 — Wire/Consensus Anchor | Consensus pool | Reuters, AP, BBC, NPR, The Guardian |
| 2 — Mainstream Editorial | Consensus pool + tracked | Fox News, Politico, The Economist, NYT, Washington Post |
| 3 — International | Tracked only | Al Jazeera, Deutsche Welle, NHK World, Global Times, France24 |
| 4 — Independent/Investigative | Tracked only | The Intercept, ProPublica, Bellingcat |
| 5 — Contrarian | Tracked only | ZeroHedge, The Gray Zone |

**Total default active: 20 sources.** All others in the pre-vetted catalog are inactive by default but activatable by the user.

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

Sticky app-level nav bar on every page:
`Narrative Nexus [logo] | Sources | Source Profile | Cluster Report | Timeline | Pipeline | Investigate | Panel | [spacer] | Settings`

### Pages [LOCKED]

**Sources (home)** — Reputation leaderboard + scatter plot. The landing page. Archetype filter pills, sortable columns, cross-linked hover between table and scatter markers. Shapes in the scatter encode outlet format; color encodes behavior archetype.

**Source Profile** — Radar chart (6 axes, percentile-oriented, outward = favorable), archetype badge, 30-day sparklines, Vf trend, outlier waterfall with convergence-type breakdown, silent edit log with human review UI.

**Cluster Report** — 3-zone forensic report (consensus summary / distortion matrix / forensic analysis). Version indicator. Config-change banner. Consensus-reality language throughout — no "source was right/wrong" copy anywhere.

**Timeline** — Horizontal Day 0–90 animation per claim. Echo-mimic dots (dashed connection to origin). CONSENSUS-ABSORBED vertical line. UNRESOLVED claims fade at Day 90.

**Pipeline Flow ("The Machine")** — Animated pipeline diagram showing live status. Each stage node shows AMD GPU vs Fireworks API execution. Replay mode for past clusters.

**Investigate** — Ad-hoc one-off forensic query. Searches curated panel only, not open web. Snapshot banner: "Claim resolution states are not available for ad-hoc reports." Does not write to reputation tables.

**Panel Management** — Activate/deactivate sources. Category balance indicator. Archived sources retain full history.

**Settings** — Consensus thresholds (per vertical), LLM model config, font scale slider (rem-based, persisted to localStorage), theme/skin selector, Firecrawl budget display, system health panel, manual pipeline trigger.

### Visual tone [LOCKED]

Dark terminal / forensic intelligence console:

```
Background:  #0a0a0f    Surface:   #111118    Border:    #1e1e2e
Accent green: #00ff88   Amber:     #ffaa00    Red:       #ff4444
Neutral:      #4a4a6a   Text:      #e0e0e0    Dim text:  #888899
```

Polarity binding is normative: green = favorable, amber = middling, red = unfavorable. Trait metrics (R_orig, R_correct) always render in neutral purple-grey — never colored evaluatively.

Monospace for all data values, labels, codes. Sans-serif for prose. Purposeful animation only.

**Build order:** `style.css` → `pipeline.html` → `index.html` → `source.html` → `cluster.html` → `timeline.html` → `investigate.html` → `panel.html` → `settings.html`

### Onboarding walkthrough [LOCKED]

5-step first-launch walkthrough (stored in `localStorage`). Defines all five vocabulary terms. Re-accessible from `?` icon in nav. Dismissible.

---

## SECTION 7: DEMO STRATEGY

### Core principle [LOCKED]

**There is no demo mode.** The application always works the same way — it reads from SQLite and serves all pages normally. The database is pre-seeded with data spanning 90 days by processing curated article URLs through the real pipeline before demo day. The app is unaware it is being demonstrated.

### How the database gets 90 days of data [LOCKED]

A one-shot seed script (`scripts/seed-demo.py`) runs before demo day. It:

1. Accepts a list of ~80 article URLs organized by story (4 stories × ~20 sources each) — real articles from the last 90 days covering geopolitics, economics, and technology
2. Fetches each URL via `newspaper4k` (same library the scraping stack uses, REQ-059)
3. Feeds extracted text through the same pipeline functions the agents use: embeddings → claim extraction → consensus math → resolution checks
4. Writes database records with timestamps matching the original publication dates, so the 7d/30d/90d resolution checkpoints fire correctly against real timestamps
5. Populates daily reputation snapshots across the full 90-day span

The seed script shares code paths with the live scheduler — it imports from the same `pipeline/` module. It does not modify the scheduler, does not create a "demo mode" flag, and does not write to a separate database. After seeding, the scheduler can resume normally going forward (or stay off during the demo).

### What the demo must show [LOCKED]

1. **The scatter plot landing state** — four quadrant labels, sources plotted, shapes encoding format. Judge immediately sees the idea without reading anything.

2. **A reputation radar in motion** — scrub through 90 days on one source, watch the polygon morph, archetype badge change, event markers fire (claim absorbed / silent edit detected). This is the "this doesn't exist anywhere else" moment.

3. **The pipeline replay** — the animated diagram showing which stage ran on the AMD GPU pod vs which called the Fireworks API. This is the "AMD integration is real, not decorative" moment.

4. **One live forensic pass** (if demo environment permits) — the live neutralization + claim extraction + threshold slider demo already built. Four outlets, one event, drag the threshold, watch claims snap between consensus-absorbed and outlier.

### What the demo must NOT do [LOCKED]

- Never imply a source "was right" or "was wrong"
- Never show live network calls that could fail mid-demo
- Never show the pipeline running for the first time on unknown data

---

## SECTION 8: CONTAINERIZATION

### Requirement [LOCKED]

All submissions must be containerized. Docker Compose is the target format.

### Service split [LOCKED architecture, PENDING exact image details]

```
services:
  app:          # FastAPI server — scheduler, API endpoints, frontend serving
  worker:       # AMD GPU pod — embedding models via ROCm
  db:           # SQLite volume (or file mount on app container)
```

The `app` and `worker` containers communicate over HTTP. All Fireworks API calls originate from `app`. No GPU access needed in `app`.

The `worker` container requires ROCm base image and `sentence-transformers`. It is the only AMD GPU-dependent component.

**[PENDING]:** Exact ROCm base image tag for the hackathon's Radeon GPU pod. Confirm at access time.

---

## SECTION 9: OPEN QUESTIONS

These block specific implementation decisions but do not block design, frontend, or analytical layer work.

| # | Question | Blocks | How to resolve |
|---|---|---|---|
| 1 | Exact hardware: what Radeon GPU pods does the hackathon provide? VRAM? | Worker container image, model size ceiling | Access + AMD support |
| 2 | What LLM models are available on Fireworks for Track 3 and at what token cost? | Model selection for Agents 2/3 | First thing to test with API key |
| 3 | What are the "additional hackathon launch credits"? | Budget for dev vs demo inference | Revealed at kickoff |
| 4 | DeepSeek-V4-Pro vs Llama 3.3 70B for structured JSON extraction? | Agent 2 and 3 prompt design | Benchmark once API access arrives |
| 5 | Is fine-tuning worth attempting on Track 3 within the timeline? | Stretch scope | Decide after initial pipeline is stable |

---

## SECTION 10: WHAT IS EXPLICITLY OUT OF SCOPE

To prevent scope creep:

- No fine-tuning in MVP (Section 9 Q5 is a stretch only)
- No FAISS GPU index (Python set math is sufficient and FAISS ROCm build is unverified)
- No Celery/Redis (APScheduler in-process is sufficient for hackathon)
- No Postgres (SQLite WAL mode is sufficient)
- No email/webhook alerts
- No back-test engine at launch (reputation scores start from day one of the demo corpus)
- No Rense.com custom parser
- Sports vertical excluded
- The "two AMD models only" restriction does not apply to Track 3 — do not artificially constrain model choice

---

## SECTION 11: SUCCESS CRITERIA

**For the hackathon judge (the demo visitor):**
They land on the Sources page, immediately see the scatter plot with four labeled quadrants, click an Early Breaker source, see their radar chart, click through to a cluster, watch the timeline animate Day 0 → Day 90. They understand the core idea in under 2 minutes without reading documentation.

**For the Analyst (the actual user):**
They return daily. They check new silent edit flags. They watch whether a source they've been tracking is drifting toward Noise Generator territory. They run ad-hoc investigations on breaking news. The data changes their editorial or risk decisions.

**For the judges' Business Value criterion:**
The pitch is concrete: media risk intelligence for institutional buyers (hedge funds, PR firms, geopolitical analysts) who currently have no systematic way to track *how* sources behave over time — only *what* they publish. No competitor product exists. The moat is longitudinal behavioral data, not a one-shot analysis.

---

*"Narrative Nexus tracks consensus reality, not truth."*