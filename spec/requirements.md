# Narrative Nexus — Development Requirements
**Source:** `docs/design-v1.2.md` (v1.2)
**Tag system:** [desired] = grep-verifiable | [compromise] = verified tradeoff | [stack-bound] = informational | [aspirational] = excluded from checks
**Grep scope:** `src/` (recursive)

---

## SECTION 1: PRODUCT IDENTITY

[desired] [REQ-001] The application footer must display the tagline "tracks consensus reality, not truth".
[desired] [REQ-002] The term "consensus reality" must be defined in UI tooltip or onboarding copy.
[desired] [REQ-003] The vocabulary terms "Consensus-absorbed", "Cross-source convergent", "Self-consistent", "Unresolved", and "Outlier claim" must appear in UI documentation or tooltips.
[desired] [REQ-004] The footer tagline "Narrative Nexus tracks consensus reality, not truth" must appear on every page.
[stack-bound] [REQ-005] The product is positioned as B2B Media Risk and OSINT workflow platform for hedge funds, PR firms, and geopolitical analysts.
[stack-bound] [REQ-006] The system tracks consensus reality, not truth — this is a foundational ethical design constraint.

---

## SECTION 2: HACKATHON CONSTRAINTS

[desired] [REQ-007] The application must be containerized with a docker-compose.yml at the project root.
[desired] [REQ-008] The Docker Compose file must define at least three services: app, worker, and db.
[stack-bound] [REQ-009] Track 3 judging criteria: Creativity, Originality, Product/Market Potential, Business Value, Application of Technology, Presentation.
[stack-bound] [REQ-010] Track 3 has no model restriction — any open-source models and frameworks are permitted.
[stack-bound] [REQ-011] No benchmark scoring is required — the demo is the submission.
[stack-bound] [REQ-012] AMD Developer Cloud credits: $100. Fireworks AI API credits: $50.

---

## SECTION 3: SYSTEM ARCHITECTURE — AGENTS & COMPUTE

[desired] [REQ-013] The system must implement an IntakeClusteringAgent that ingests articles, generates embeddings, and clusters articles by semantic similarity.
[desired] [REQ-014] The system must implement a ForensicExtractionAgent that strips editorial framing and extracts atomic factual claims as structured JSON.
[desired] [REQ-015] The system must implement a ConsensusAlignmentAgent that computes cross-source agreement and classifies claims.
[desired] [REQ-016] The system must implement a SilentAuditorAgent that compares historical article snapshots to detect unreported edits.
[desired] [REQ-017] Sentence transformer embeddings must run on AMD GPU via ROCm.
[compromise] [REQ-018] LLM inference for framing neutralization and claim extraction must use the Fireworks API.
[compromise] [REQ-019] Consensus math and reputation scoring must run on CPU (pure Python, no GPU required).
[stack-bound] [REQ-020] The pipeline is framed as a coordinated swarm of specialized AI Agents.
[stack-bound] [REQ-021] Fireworks AI runs on AMD Instinct MI325X and MI355X hardware — calling the API uses AMD hardware.

---

## SECTION 4: ANALYTICAL MODEL

### Consensus Thresholds

[desired] [REQ-022] The consensus baseline must be computed over Tier 1 and Tier 2 sources the consensus pool.
[desired] [REQ-023] A claim enters the consensus baseline when it appears in more than threshold percent of the pool source graphs for that story.
[desired] [REQ-024] Default consensus thresholds must be GEOPOLITICS 65 percent ECONOMICS 75 percent TECHNOLOGY 75 percent.
[desired] [REQ-025] Consensus thresholds must be configurable at runtime.
[desired] [REQ-026] Threshold values must be stored with each cluster run for historical comparison validity.

### Claim Lifecycle

[desired] [REQ-027] Claims must follow a state machine with lifecycle state PENDING.
[desired] [REQ-028] Claims must transition from PENDING to CONSENSUS_ABSORBED terminal state.
[desired] [REQ-029] Claims must transition from PENDING to UNRESOLVED terminal state forced at 90 day check.
[desired] [REQ-030] Each absorbed claim must be classified with convergence type CROSS_SOURCE_CONVERGENT or SELF_CONSISTENT.
[desired] [REQ-031] Convergence type SELF_CONSISTENT must be implemented.

### Reputation Dimensions

[desired] [REQ-032] The system must track reputation dimension R_orig Outlier Origination Rate.
[desired] [REQ-033] The system must track reputation dimension R_val Outlier Validation Rate.
[desired] [REQ-034] The system must track reputation dimension R_speed Speed Premium.
[desired] [REQ-035] The system must track reputation dimension R_frame Framing Consistency.
[desired] [REQ-036] The system must track reputation dimension R_edit Silent Edit Rate.
[desired] [REQ-037] The system must track reputation dimension R_correct Formal Correction Rate.
[desired] [REQ-038] Trait dimensions R_orig and R_correct must render in neutral color never green amber or red.

### Archetype Assignment

[desired] [REQ-039] Archetype assignment must classify sources as EARLY_BREAKER based on R_orig above median and R_val above median.
[desired] [REQ-040] Archetype assignment must classify sources as NOISE_GENERATOR based on R_orig above median and R_val at or below median.
[desired] [REQ-041] Archetype assignment must classify sources as SELECTIVE_ACCURATE based on R_orig at or below median and R_val above median.
[desired] [REQ-042] Archetype assignment must classify sources as CONSENSUS_FOLLOWER based on R_orig at or below median and R_val at or below median.

### Resolution Schedule

[desired] [REQ-043] The system must perform a 7 day resolution check: PENDING to CONSENSUS_ABSORBED if Tier 1 or 2 picked up the claim.
[desired] [REQ-044] The system must perform a 30 day resolution check: PENDING to CONSENSUS_ABSORBED if threshold crossed.
[desired] [REQ-045] The system must perform a 90 day resolution check: PENDING to CONSENSUS_ABSORBED or forced UNRESOLVED.
[desired] [REQ-046] Daily snapshots one row per source and vertical must be written unconditionally each day.

---

## SECTION 5: DATA & SOURCES

### Source Panel

[desired] [REQ-047] The source panel must distinguish between consensus pool Tier 1 plus 2 and tracked panel all tiers.
[desired] [REQ-048] Default active sources must include Reuters AP BBC NPR The Guardian Tier 1.
[desired] [REQ-049] Default active sources must include Fox News Politico The Economist NYT Washington Post Tier 2.
[desired] [REQ-050] Default active sources must include Al Jazeera Deutsche Welle NHK World Global Times France24 Tier 3.
[desired] [REQ-051] Default active sources must include The Intercept ProPublica Bellingcat Tier 4.
[desired] [REQ-052] Default active sources must include ZeroHedge The Gray Zone Tier 5.
[desired] [REQ-053] Total default active sources must be 20.

### Topic Verticals

[desired] [REQ-054] The system must support GEOPOLITICS vertical.
[desired] [REQ-055] The system must support ECONOMICS vertical.
[desired] [REQ-056] The system must support TECHNOLOGY vertical.
[desired] [REQ-057] Sports vertical must be excluded.

### Scraping Stack

[desired] [REQ-058] The scraping stack must use feedparser for RSS discovery.
[desired] [REQ-059] The scraping stack must use newspaper4k for article body extraction.
[desired] [REQ-060] The scraping stack must include Firecrawl as fallback with 1000 credits per month cap.
[desired] [REQ-061] Paywall handling: sources where body is unavailable must be marked BODY_UNAVAILABLE.
[desired] [REQ-062] BODY_UNAVAILABLE sources must show OI_EXCLUDED in UI and not be penalized in reputation scoring.
[stack-bound] [REQ-063] Sources use RSS summary text for consensus pool voting even when body is unavailable.

---

## SECTION 6: FRONTEND — PAGES & DESIGN

### Navigation

[desired] [REQ-064] The app must have sticky nav bar AppNav on every page: Logo Sources Source Profile Cluster Report Timeline Pipeline Investigate Panel Settings.
[desired] [REQ-065] The nav bar must link to a Sources page home landing implemented as SourcesPage component.
[desired] [REQ-066] The nav bar must link to a Source Profile page implemented as SourceProfilePage component.
[desired] [REQ-067] The nav bar must link to a Cluster Report page implemented as ClusterReportPage component.
[desired] [REQ-068] The nav bar must link to a Timeline page implemented as TimelinePage component.
[desired] [REQ-069] The nav bar must link to a Pipeline Flow page implemented as PipelineFlowPage component.
[desired] [REQ-070] The nav bar must link to an Investigate page implemented as InvestigatePage component.
[desired] [REQ-071] The nav bar must link to a Panel Management page implemented as PanelPage component.
[desired] [REQ-072] The nav bar must link to a Settings page implemented as SettingsPage component.

### Visual Design Tokens

[desired] [REQ-073] CSS custom properties for the Narrative Nexus design language must be defined per docs/design-tokens.md (extracted from mock HTML files). See that file for exact color values, which differ between light and dark modes.
[desired] [REQ-074] Covered by REQ-073 — all nn-* tokens defined in design-tokens.md.
[desired] [REQ-075] Covered by REQ-073.
[desired] [REQ-076] Covered by REQ-073.
[desired] [REQ-077] Covered by REQ-073.
[desired] [REQ-078] Covered by REQ-073.
[desired] [REQ-079] Covered by REQ-073.
[desired] [REQ-080] Covered by REQ-073.
[desired] [REQ-081] Covered by REQ-073.
[desired] [REQ-082] Polarity binding must assign color by dimension using getPolarityColor.
[desired] [REQ-083] Monospace font must be used for all data values labels and codes.
[desired] [REQ-084] The app must use the font families defined in docs/design-tokens.md (Space Grotesk for headings, IBM Plex Sans for body, IBM Plex Mono for monospace/data).

### Page Features

[desired] [REQ-085] The Sources page must display scatter plot with archetype filter pills and sortable columns leaderboard.
[desired] [REQ-086] The Source Profile page must display radar chart with 6 axes archetype badge 30 day sparklines.
[desired] [REQ-087] The Cluster Report page must display forensic report with consensus summary distortion matrix and analysis.
[desired] [REQ-088] The Timeline page must show horizontal Day 0 to 90 animation per claim with CONSENSUS_ABSORBED vertical line.
[desired] [REQ-089] The Pipeline Flow page must show animated pipeline diagram with AMD GPU versus Fireworks API execution labeling.
[desired] [REQ-090] The Investigate page must show snapshot banner about ad-hoc reports.
[desired] [REQ-091] The Panel Management page must allow activating and deactivating sources with category balance indicator.
[desired] [REQ-092] The Settings page must allow configuring consensus thresholds font scale slider and theme selector.

### Onboarding

[desired] [REQ-093] A 5 step first launch walkthrough must be implemented and stored in localStorage using onboardingComplete state.
[desired] [REQ-094] The onboarding walkthrough must be re accessible from onboarding icon in the nav bar.
[desired] [REQ-095] The onboarding walkthrough must define all vocabulary terms from spec section 1.

---

## SECTION 7: DEMO STRATEGY

[aspirational] [REQ-096] The demo must use a pre baked historical corpus of 3 to 4 stories.
[aspirational] [REQ-097] The demo landing state must display scatter plot with four labeled quadrants.
[aspirational] [REQ-098] The demo must show reputation radar in motion with 90 day scrubbing and polygon morphing.
[aspirational] [REQ-099] The demo must show pipeline replay with AMD GPU versus Fireworks API labeling.
[aspirational] [REQ-100] The demo must never imply a source was right or wrong.
[aspirational] [REQ-101] The demo must never show live network calls mid demo.

---

## SECTION 8: CONTAINERIZATION

[desired] [REQ-102] Docker Compose must define an app service for the FastAPI server.
[desired] [REQ-103] Docker Compose must define a worker service for the AMD GPU pod.
[desired] [REQ-104] Docker Compose must define a database service or volume with SQLite.
[desired] [REQ-105] The app and worker containers must communicate over HTTP.
[desired] [REQ-106] All Fireworks API calls must originate from the app container.
[desired] [REQ-107] The worker container must use ROCm base image and include sentence transformers.
[stack-bound] [REQ-108] No GPU access is needed in the app container.

---

## SECTION 9: EXPLICITLY OUT OF SCOPE

[stack-bound] [REQ-109] No model fine tuning in MVP.
[stack-bound] [REQ-110] No FAISS GPU index Python set math is sufficient.
[stack-bound] [REQ-111] No Celery or Redis APScheduler in process is sufficient.
[stack-bound] [REQ-112] No Postgres SQLite WAL mode is sufficient.
[stack-bound] [REQ-113] No email or webhook alerts.
[stack-bound] [REQ-114] No back test engine at launch reputation scores start from day one.
[stack-bound] [REQ-115] Sports vertical excluded only GEOPOLITICS ECONOMICS TECHNOLOGY.
[stack-bound] [REQ-116] No Rense com custom parser.
