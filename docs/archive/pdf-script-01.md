Here is your PDF content cleaned up and formatted into structured Markdown.

The repeating footer has been removed from the individual sections, and its metadata is tagged right at the top.

---

```markdown
# NARRATIVE NEXUS

Everyone knows what the news said.  
Nobody profiles how the sources behave.

Some questions you might want answered about who gives you the news:
* How mainstream is any given news source?
* Which sources break real stories first — unique, and ahead of the pack?
* Which just echo consensus after it's already been published elsewhere?

Narrative Nexus is an instrument that answers them for anyone whose money or decisions ride on news — hedge funds, PR firms, risk analysts. 

*Constraint: Narrative Nexus tracks consensus reality, not truth.*

---

## THE INSTRUMENT

37 outlets, scored by behavior — not by opinion.

Every dot is a news outlet, placed by two measured behaviors: 
1. How often it breaks claims early ($x$-axis)
2. How often those claims survive into consensus ($y$-axis)

Four distinct archetypes emerge:
* **Early Breaker**
* **Unmatched Breaker**
* **Late but Reliable**
* **Consensus Echo**

There is no composite score, and no editorial judgment. 

> "Narrative Nexus tracks consensus reality, not truth."

---

## THE MACHINE · AMD

Four AI agents. All inference on AMD Instinct via Fireworks AI.

All AI stages are configured to run on Fireworks AI, serving inference on AMD Instinct MI300X/MI250X accelerators. The shipped database was built end-to-end through Fireworks during hackathon week using AMD hackathon credits. 

Provider-agnostic by design: every stage's provider and model is independently configurable.

### The Pipeline Stages
1. **Intake & Clustering** — Embeds articles, groups them into story clusters.
2. **Forensic Extraction** — Strips spin, extracts atomic factual claims via Large Language Models (LLMs).
3. **Consensus Alignment** — Pure mathematics: where do $\ge 2$ independent sources converge?
4. **Silent Auditor** — Re-reads old articles, flags unannounced post-publication edits.

---

## THE PROOF

One pipeline, run end-to-end on two real stories.

* **US-Iran War (A 48-day arc):** One outlet's scoop ripening into cross-source consensus, animated claim by claim on the Timeline.
* **Venezuela Emergency (A 5-day surge):** 20 outlets, 138 claims, 10 silent edits detected. Corroborated facts vs. single-outlet outliers — Maduro's arrest reported by one source, India's field hospital only by *The Hindu*, China's aid only by *Global Times*.

*Consensus requires $\ge 2$ independent sources. Single-source claims can never self-validate.*

---

## FINDING NO. 1

Collecting news is itself the first finding. Here is what we found just trying to get the news online at all:

* **Half the news is gated.** Of 358 articles collected, only 182 yielded full body text — the rest were paywalled or truncated RSS. Three major outlets started at 0% extraction.
* **A handful of wires anchor everything.** Consensus reality is effectively defined by ~5 wire services and public broadcasters; most outlets echo downstream.
* **Most stories have one voice.** 9 of 17 story clusters were covered by a single source. Corroboration is rarer than it looks.
* **Global coverage doesn't come free.** First panel draft was 90% Global North. We empirically tested 45 candidate feeds to reach 37 sources across 7 regions and 6 continents.

---

## FINDING NO. 2

Our first engine reported 2,625 consensus claims. **96.8% were an artifact.**

A claim from a single source, in a cluster with no other sources, computed 1-of-1 = 100% agreement $\rightarrow$ "consensus." The machine was agreeing with itself.

### The Fix
Consensus now requires $\ge 2$ independent consensus-pool sources reporting the same claim, matched semantically across outlets using cosine similarity ($\ge 0.85$ — A/B tested; $0.80$ introduced factually wrong merges).

Every threshold in the pipeline is empirically calibrated:
* Clustering `eps` swept against hand-labeled story groups.
* Cluster-size guards applied against cross-story blobs.
* Custom per-vertical consensus thresholds enforced.

$$\text{2,625 Claims (Artifact)} \longrightarrow \text{10 Claims (Real, Filtered Number)}$$

---

## DISCIPLINE

Built for scrutiny.

* **No composite score, ever:** Six independent behavioral dimensions are tracked; the user decides what matters.
* **"Consensus reality, not truth":** The system never says a source was right or wrong. That structural constraint is what makes it defensible and non-partisan.
* **Nothing mocked:** The shipped database is one verified pipeline run containing 358 articles, 378 claims, and 13,653 daily reputation snapshots. Every number on every page traces directly to a database query.
* **Live by design:** The same pipeline can collect, cluster, extract, and score continuously. Pressing *Start* in Settings activates the ingestion. Each clone functions as its own standalone instance.

---

## THE INSTRUMENT

The product isn't the run. **It's the instrument.**

What you've seen is one verified pass over a real news corpus — 358 articles, 37 sources, 6 continents, processed by the real pipeline. Nothing mocked. This run was short by design — enough to prove the pipeline works end-to-end.

The real product is the instrument itself: as far as we've found, nobody is measuring how news outlets behave over time the way this does. Run it continuously and that behavioral record only gets richer.

*An instrument for telling the clones from the outliers.*

```