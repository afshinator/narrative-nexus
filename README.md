# Narrative Nexus

**A media-behavior measurement instrument.** Narrative Nexus monitors 37 news outlets across 6 continents and algorithmically measures their *reporting behavior* over time — not to judge who is "right," but to answer: which sources reliably break stories ahead of the mainstream consensus, which generate systematic noise, and which quietly rewrite their articles after publication?

Built for the AMD Developer Hackathon ACT II (Track 3 — Unicorn) by [team/name].

> *"Narrative Nexus tracks consensus reality, not truth."*

---

## What it does

Four AI agents run in sequence over live news:

1. **Intake & Clustering** — embeds articles from 37 outlets, groups them into story clusters by semantic similarity (DBSCAN over BGE embeddings, 14-day windows).
2. **Forensic Extraction** — strips editorial framing and extracts atomic factual claims as structured JSON via LLM.
3. **Consensus Alignment** — pure math: finds where ≥2 independent consensus-pool sources converge on the same claim. That convergence is "consensus reality."
4. **Silent Auditor** — re-reads old articles and flags significant unannounced edits.

The output is a **living reputation ledger**: six behavioral dimensions per source per topic vertical, no composite score. The Sources scatter plot splits the panel into four behavioral archetypes — Early Breakers, Noise Generators, Selective-but-Accurate, and Consensus Followers — visible at a glance.

## AMD Platform Usage

**All AI pipeline stages are configured to run on Fireworks AI, which serves inference on AMD Instinct accelerators.**

| Pipeline Stage | Default Provider | Evidence |
|----------------|-----------------|----------|
| Agent 1 — Embeddings & Clustering | Fireworks AI | `config/providers.json` (`"agent1_embedding": "fireworks"`) |
| Agent 1 — LLM Classification | Fireworks AI | `config/providers.json` (`"agent1_llm": "fireworks"`) |
| Agent 2 — Forensic Claim Extraction | Fireworks AI | `config/providers.json` (`"agent2_llm": "fireworks"`) |
| Agent 4 — Silent Auditor | Fireworks AI | `config/providers.json` (`"agent4_llm": "fireworks"`) |
| Claim Matching (cross-stage) | Fireworks AI (nomic-embed) | `config/providers.json` (`"claim_matching_embedding": "fireworks-nomic"`) |

Fireworks AI serves inference on AMD Instinct MI300X and MI250X accelerators. Every LLM inference and embedding call through the Fireworks provider routes through AMD Instinct hardware. The shipped database was constructed by running these agents — clustering, claim extraction, claim matching, and consensus — through Fireworks during hackathon week (July 3–5, 2026), using the hackathon-provided Fireworks credits.

**Provider configurability:** runtime provider selection is visible on the Pipeline page (`/pipeline`), where each agent stage shows a dropdown of available compute providers. Fireworks entries carry an `(AMD)` badge. The architecture is deliberately provider-agnostic — Fireworks/AMD is the default, not a hard dependency.

**Honest wording note:** we say "configured to run" because individual LLM responses carry no hardware attestation trail. The system routes AI workloads through Fireworks AI on AMD Instinct via `config/providers.json` defaults and the Pipeline page dropdowns.

## Quick start

```bash
# 1. Install
npm install
pip install -r requirements.txt

# 2. API keys (optional — the app ships with a pre-built database
#    and runs fully without keys; keys are needed only for live
#    collection and pipeline runs)
cat > .env << 'EOF'
FIREWORKS_API_KEY=fw-...
EOF

# 3. Backend
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# 4. Frontend
npm run build
npx vite preview --host 0.0.0.0 --port 5173
```

Open http://localhost:5173.

The app ships with a working database (`data/demo/demo.db`, the default path): 358 articles from 37 sources, 378 extracted claims, 17 story clusters, and a 123-day reputation snapshot series — all produced by the real pipeline. Nothing is mocked.

**To collect live data:** open Settings and press Start on the scraper. It polls RSS feeds from all 37 sources and runs new articles through the pipeline. Each clone is its own instance with its own database — collect as much or as little as you want.

## Where to look first

- **Sources** (`/`) — the reputation scatter. Every dot is an outlet, positioned by how often it breaks claims early (x) vs. how often those claims survive into consensus (y). Four labeled corners. Click any dot for that outlet's six-dimension profile.
- **Stories** (`/stories`) — two fully-traced story clusters:
  - *US-Iran War: March Escalation & April Ceasefire* — a 48-day arc from a single outlet's scoop to cross-source consensus, animated on its Timeline.
  - *Venezuela Emergency and Rescue Response* — a 5-day surge: 20 outlets, 138 claims, and the system separating corroborated facts from single-outlet outliers in real time.
- **Pipeline** (`/pipeline`) — the four-agent machine, live provider assignments, AMD badges.
- **Panel** (`/panel`) — the 37-source panel across 5 tiers and 7 regions; toggle sources on/off and watch the Sources page respond.

## Stack

| Layer | Tools |
|-------|-------|
| Frontend | React 19, TypeScript, Vite, Tailwind 4, shadcn |
| Routing / State | react-router, zustand |
| Visualizations | D3 (scatter, timeline, pipeline), Chart.js (radar) |
| Backend | FastAPI, SQLite (WAL), APScheduler |
| AI | Provider-agnostic LLM + embedding clients. Default: Fireworks AI (AMD Instinct). Alternatives: DeepSeek, OpenAI, local CPU via sentence-transformers |

## The analytical model, briefly

- A claim becomes **consensus-absorbed** only when ≥2 independent consensus-pool sources report it AND it crosses a per-vertical threshold (65–75%). Single-source claims can never self-validate.
- Sources are scored on six independent dimensions (origination rate, validation rate, speed, framing consistency, silent-edit rate, correction rate) — never collapsed into one ranking.
- The panel spans 5 tiers deliberately: wire services anchor the consensus baseline, while regional and contrarian outlets are tracked *against* it — that contrast is where the interesting signal lives.

Full model documentation: `docs/design-v1.3.md`. Data provenance and per-source stats: `docs/faq-pipeline-data.md`, `docs/faq-source-selection.md`.

## Docker (optional)

A Docker Compose setup is included for containerized deployment (`docker compose up`). It is not required — the quick start above runs everything on the host.

---

*"Narrative Nexus tracks consensus reality, not truth."*