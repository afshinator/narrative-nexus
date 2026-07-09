# Narrative Nexus — Deck Copy v1 (8 slides)
Drafted 2026-07-09 in the UI-polish chat. Human approved direction; final wording open to small edits.
Screenshots live in docs/shots/ (5 files, 01–05). Slides 1, 6, 7, 8 are text-only by design.
HARD REQUIREMENT: deck must be a PDF; the automated pre-screener parses its TEXT —
AMD/Fireworks usage on slide 3 must be real extractable text, not baked into an image.

---

## Slide 1 — The blind spot
**Headline:** Everyone knows *what* the news said. Nobody measures *how outlets behave.*

Which sources break real stories before everyone else? Which just make noise?
Which quietly rewrite their articles after the fact?

For anyone whose money or decisions ride on news — hedge funds, PR firms, risk
analysts — this is an unmeasured blind spot.

**Narrative Nexus is an instrument that measures it.**

Footer: DreamTeam — AMD Developer Hackathon ACT II · Track 3

---

## Slide 2 — The instrument
**Headline:** 37 outlets, scored by behavior — not by opinion.
**Visual:** 01-sources-page-scatter-plot.png

Every dot is a news outlet, placed by two measured behaviors: how often it
breaks claims early (x) vs. how often those claims survive into consensus (y).
Four archetypes emerge — **Early Breakers, Unmatched Breakers, Late but
Reliable, Consensus Echoes.**

No composite score. No editorial judgment.
*"Narrative Nexus tracks consensus reality, not truth."*

---

## Slide 3 — The machine (AMD) ← pre-screener payload slide
**Headline:** Four AI agents. All inference on AMD Instinct via Fireworks AI.
**Visual:** 02-pipeline-page.png

1. **Intake & Clustering** — embeds articles, groups them into story clusters
2. **Forensic Extraction** — strips spin, extracts atomic factual claims (LLM)
3. **Consensus Alignment** — pure math: where do ≥2 independent sources converge?
4. **Silent Auditor** — re-reads old articles, flags unannounced edits

**All AI stages are configured to run on Fireworks AI, serving inference on
AMD Instinct MI300X/MI250X accelerators.** The shipped database was built
end-to-end through Fireworks during hackathon week using AMD hackathon
credits. Provider-agnostic by design — AMD is the default, not a lock-in.

---

## Slide 4 — The proof: two stories, two tempos
**Headline:** Two real stories, two tempos, one pipeline.
**Visual:** 05-stories-page.png (primary); 03-venezuela-cluster.png optional split

**US-Iran War** — a 48-day arc: one outlet's scoop ripening into cross-source
consensus, animated claim by claim on the Timeline.

**Venezuela Emergency** — a 5-day surge: 20 outlets, 138 claims, 10 silent
edits detected. The system separates corroborated facts from single-outlet
outliers — Maduro's arrest reported by one source, India's field hospital only
by The Hindu, China's aid only by Global Times.

Consensus requires ≥2 independent sources. **Single-source claims can never
self-validate.**

---

## Slide 5 — Finding #1: Collecting news is itself the first finding
**Headline:** Collecting news is itself the first finding.
**Visual:** none, or Source Breakdown column crop from 03-venezuela-cluster.png

- **Half the news is gated.** Of 358 articles collected, only 182 yielded full
  body text — the rest paywalled or truncated RSS. Three major outlets started
  at 0% extraction.
- **A handful of wires anchor everything.** Consensus reality is effectively
  defined by ~5 wire services and public broadcasters; most outlets echo
  downstream.
- **Most stories have one voice.** 9 of 17 story clusters were covered by a
  *single* source. Corroboration is rarer than it looks.
- **Global coverage doesn't come free.** First panel draft: 90% Global North.
  We empirically tested 45 candidate feeds to reach 37 sources, 7 regions,
  6 continents.

---

## Slide 6 — Finding #2: We built a fake consensus machine first
**Headline:** Our first engine reported 2,625 consensus claims. 96.8% were an artifact.

A claim from a single source, in a cluster with no other sources, computed
1-of-1 = 100% agreement → "consensus." The machine was agreeing with itself.

**The fix:** consensus now requires **≥2 independent consensus-pool sources**
reporting the same claim, matched semantically across outlets (cosine ≥0.85 —
A/B tested; 0.80 introduced factually wrong merges).

**The honest result: 2,625 → 10.** Ten claims that genuinely cleared
cross-source corroboration. Smaller number. Real number.

*Every threshold in the pipeline is empirically calibrated — clustering eps
swept against hand-labeled story groups, cluster-size guards against
cross-story blobs, per-vertical consensus thresholds.*

---

## Slide 7 — Built for scrutiny
**Headline:** The discipline is part of the product.

- **No composite score, ever** — six independent behavioral dimensions; the
  user decides what matters.
- **"Consensus reality, not truth"** — the system never says a source was
  right or wrong. That constraint is what makes it defensible and non-partisan.
- **Nothing mocked** — the shipped database is one verified pipeline run:
  358 articles, 378 claims, 13,653 daily reputation snapshots. Every number on
  every page traces to a query.
- **Live by design** — press Start in Settings and the same pipeline collects,
  clusters, extracts, and scores continuously. Each clone is its own instance.
  ⚠ UNVERIFIED CLAIM: no end-to-end scraper run has been done under the new
  paradigm. Verify (scratch DB, 10-min run) before shipping this bullet, or
  soften it.

---

## Slide 8 — The moat
**Headline:** The product isn't the run. It's the instrument.

What you've seen is one verified pass over a real news corpus — 358 articles,
37 sources, 6 continents, processed by the real pipeline. Nothing mocked.

Point it at the live feed and it accumulates **longitudinal behavioral history
no competitor has** — because nobody else is measuring this.

**The moat is time.**

Footer: github.com/afshinator/[REPO-NAME-NEEDED] · DreamTeam · Built on AMD
Instinct via Fireworks AI

---

## Build notes
- Dark theme matching design-tokens.md: bg #0c0f0b, surface #161a12, text
  #d2e4c5, dim #858f7b, navy #7eb3e0, teal #5ebd8e, red #d97878, amber #c49a42.
- Fonts: Space Grotesk (headings), IBM Plex Sans (body), IBM Plex Mono (stats).
- Known screenshot defects (human may reshoot 01 and 05):
  - 01: "20 outlets" copy reads like panel size (it's graded-sources count; panel is 37)
  - 05: "curated list for the demo" wording was changed to "for the hackathon" AFTER
    the shot was taken; footer "Demo corpus" also removed after. Reshoot post-UX55.
  - 04: header says "over 6 days" for a 48-day arc (6 distinct dates) — copy defect,
    unfixed as of this writing.
- Open item: repo URL for slide 8 footer.