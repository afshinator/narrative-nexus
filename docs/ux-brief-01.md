# Narrative Nexus — UX Brief

**Audience:** Hackathon judges, future users, and anyone who needs to understand what this system *feels like* to use.

---

## 1. The Core Idea

Narrative Nexus is a dashboard for the trustworthiness of news sources — not based on who you agree with, but on measurable behavior across hundreds of stories. It watches a curated panel of ~20 news outlets and tracks, for each one: Do they break stories early that later become the consensus view? Or do they generate a lot of noise that never pans out? Do they quietly edit articles without telling anyone? Do they issue formal corrections?

The most important rule of the interface: **the system never says a source is "right" or "wrong."** It shows you how a source's coverage relates to what the majority of the panel describes. The user makes their own judgment.

---

## 2. Who Uses This

**The Analyst (primary persona)** — Someone whose job is to understand the media landscape. Could be a journalist, an OSINT researcher, a policy analyst, or a newsroom data editor. They want to know which outlets reliably surface important stories early, which ones produce systematic noise, and whether a source has a habit of editing articles quietly after publication.

**The Demo Visitor (secondary persona)** — A hackathon judge or stakeholder walking through the system for the first time. They need to understand the core idea in 30 seconds and see compelling data within a few clicks. The walkthrough and default panel are designed for them.

---

## 3. The User's Journey

### 3.1 First Visit — Onboarding ( what step is this in the implementation? TBD )

A 5-step walkthrough explains what the system does and, just as importantly, what it does NOT do. Key message delivered in the persistent footer on every page:

> *"Narrative Nexus tracks consensus reality, not truth."*

The walkthrough defines the five terms the system uses:

- **Consensus reality** — The version of events agreed upon by the majority of the panel at a given threshold. Not "the truth" — just what most sources say.
- **Consensus-absorbed** — A claim that has entered the consensus version of events. Enough sources now report it that the system treats it as settled mainstream coverage.
- **Cross-source convergent** — A claim that was corroborated by one or more independent sources before becoming consensus-absorbed. Multiple outlets arrived at it separately.
- **Self-consistent** — A claim that became consensus-absorbed even though only the origin source published consistent follow-up. No independent corroboration, but the broader panel eventually agreed.
- **Unresolved** — A claim that never became consensus-absorbed after 90 days. Terminal state — the claim did not enter the mainstream version of events.

The user can dismiss the walkthrough or re-open it later from a help icon.

### 3.2 Landing — Sources

The user lands on the Sources page. They see a table of news sources with six columns of metrics, each colored by a signal palette. No composite score — the user decides which metric matters to them.

They immediately notice:
- Which sources are **Early Breakers** (high origination, high validation) — these surface stories early that become the consensus view
- Which are **Noise Generators** (high origination, low validation) — these make lots of claims that don't stick
- Which have a **silent editor** warning — they edit articles after publication without noting it

A scatter plot below the table shows the same data visually: origination rate on the X axis, validation rate on the Y axis. The four quadrants map directly to the four archetype labels. Users can filter by archetype pills above the table and sort by any column.

Key UX rule: there is no "this source is bad" badge. A source with low validation rate and high noise is described factually — their data speaks for itself.

### 3.3 Digging In — The Source Profile

The user clicks a source. They see:

- **Radar chart** — Six axes showing how this source compares to the panel. Outward = favorable. Previous month overlaid as a dashed polygon so the user sees whether the source is improving or declining.
- **Archetype tag** — Early Breaker / Noise Generator / Selective but Accurate / Consensus Follower, determined by where they sit relative to the panel median.
- **Framing volatility trend** — A line chart showing month-by-month how much this source's framing varies. Spikes suggest inconsistent editorial standards.
- **Outlier claim waterfall** — A breakdown of where this source's outlier claims ended up. How many became consensus reality? How many fizzled out? How many were copies of another source's scoop?
- **Silent edit log** — A timeline of detected edits with a review UI. Grey = minor, amber = moderate, red = significant confirmed edit. The user can click "Confirm Significant" or "Mark False Positive."

### 3.4 The Story Level — Coverage Analysis

The user clicks a cluster (a story covered by multiple sources). They see a three-zone report:

**Zone 1 — What the consensus says**
The version of events agreed upon by the majority of the panel, framed explicitly as "what most sources described," not as objective truth.

**Zone 2 — How each source differed**
A matrix showing each outlet, their omission index (how much of the consensus story they left out), their framing volatility, and any notable divergence. Sources marked as BODY_UNAVAILABLE are clearly labeled — the system couldn't access their full article body.

**Zone 3 — Forensic analysis**
Warning banners for sources that triggered reputation alerts on this story. Outlier claim cards showing which sources broke stories that later became or didn't become consensus reality. Reality fracture indicators where sources described events in structurally contradictory ways.

A version indicator at the top shows which version of the report the user is viewing, and whether it was a config change or a real corpus update.

### 3.5 The Timeline

For any cluster, the user can switch to a timeline view. Articles appear as dots along a horizontal calendar, with sources stacked vertically. Outlier claims are highlighted. When consensus absorption happens (a claim enters the mainstream reality), a vertical line marks it.

The user watches the story unfold: which source broke it first, who followed, who copied, and which claims faded away. This is the demo centerpiece.

### 3.6 The Machine — Pipeline Flow

A dedicated page shows the live pipeline as an animated diagram. Particles flow from RSS feeds through clustering, neutralization, graph extraction, and into the reputation ledger. It's eye candy for the demo visitor but also functional — each stage node shows status and throughput. There's a replay mode where the user can watch a past cluster's journey through the pipeline.

### 3.7 Ad-Hoc Investigation

The user enters a search query. The system finds matching articles from its curated panel only (not the open web), runs the full pipeline on them as a one-off snapshot, and returns a forensic report. A banner makes clear: *"This is a current-moment snapshot. Claim resolution states are not available for ad-hoc reports."*

The user sees how different sources are covering a topic right now, without having to read 20 individual articles.

### 3.8 Panel Management

The user can activate or deactivate sources from the pre-vetted catalog. A statistical note warns if the panel drops below 12. A category balance indicator shows ideological/geographic coverage. Archived sources retain all their history — reactivating them picks up where they left off.

---

## 4. What the System Does NOT Do

These constraints are as important as the features:

- **Does not tell you who is "right."** No source gets a truth score. The closest the system comes is "this source published an outlier claim that later became consensus reality" — which means *eventually most sources agreed*, not *it was objectively true*.
- **Does not censor or hide sources.** Every source's data is visible. DEGRADED sources show a badge but remain fully accessible. The user decides which sources to trust.
- **Does not enforce ideological balance.** The category indicators are advisory. The user composes their panel freely.
- **Does not rank sources.** There is no composite score. Six independent dimensions, no single "good vs bad" axis.

---

## 5. Visual Tone

Settings page will have controls not only for font-size adjustments (that apply to every page and persisted via localstorage), but also theme/skin selection. Some themes have both light and dark variation, see design-brief document.


The nav bar is sticky at the top and lists all 7 app sections plus a Settings link. Mocked pages are active links; non-mocked pages are muted with `(coming)` treatment but navigable to layout stubs.

Every page carries the footer: *"Narrative Nexus tracks consensus reality, not truth."* ,
if time permits we'll animate this going across the screen, ticker-tape effect.

---

## 6. What Success Looks Like

**For the hackathon judge:** They land, see the scatter plot with four labeled quadrants, click an Early Breaker, see their radar chart showing strong validation, click a cluster from their history, and watch the timeline animate from Day 0 to Day 90. They walk away understanding the core idea in under 2 minutes.

**For the analyst:** They return daily. They check which sources have new silent edit flags. They see whether a source they've been watching is drifting toward Noise Generator territory. They run ad-hoc investigations on breaking news to see how the panel is covering it. The data changes their editorial decisions.
