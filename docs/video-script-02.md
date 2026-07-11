# Narrative Nexus — Video Script Revision (video-script-02)

## Part 1 — Section-by-section report on video-script-01.md

### [Open] — GOOD, one framing upgrade taken
The three questions match deck slide 1. The script was missing the deck's sharpest disambiguation line: *"It doesn't score bias — it scores behavior, measured over time."* That line pre-empts the "is this a bias tracker?" misread and is now added. No forbidden framing present.

### The machine — GEMMA BEAT ADDED; otherwise aligned
The four-agent description matches the deck's Pipeline Stages bullets, and the AMD/Fireworks claim strength matches. Gemma is slotted immediately after the "each stage's provider is configurable" line — Gemma is the evidence that configurability is real, which strengthens the section's existing "real engine, not a slideshow" close.

Claim-strength check for the Gemma wording (matched to the deck exactly):
- OK: Selectable provider, deployed on-demand via Fireworks — said.
- OK: Verified running the claim-extraction prompt across the full 61-article Venezuela cluster, 268 structured claims — said, **past tense**.
- OK: Evidence in the repo (`docs/evidence/gemma/`) — said.
- NEVER: Gemma powers the pipeline / is the default / is live-selectable in the dropdown. The script states explicitly that the shipped DB was built on the default Fireworks/DeepSeek config.

### The scatter — GOOD as-is
Archetype names are the canonical UX49 set (Early Breaker, Unmatched Breaker, Late but Reliable, Consensus Echo) — no stale names anywhere in the script. "Six behavioral dimensions, no single composite score" matches deck slide 8.

### The proof — THE NUMBER FIX + NEW 2,625->10 BEAT
- **"10 silent edits detected" -> "5 silent edits detected."** Required fix. The live Stories page shows *5 edits detected* on the Venezuela card, so voiceover and screen agree.
- **New:** the 2,625->10 self-validation-collapse beat (deck slide 7) is added here. It's the deck's most persuasive moment and directly reinforces the ">=2 sources, single-source claims can never self-validate" rule the proof section already carries. With no time constraint, it earns its place. Numbers used (2,625 -> 10; >=0.85; 96.8% is on the deck but spoken here as "almost all") are all in the frozen set.
- All other figures check against the frozen set: 20 outlets, 138 claims, 5-day surge, 48-day arc. The Maduro/Hindu/Global Times examples match deck slide 5 and never say "right"/"wrong."
- Investigate page: not mentioned; header direction retained.

### Close — GOOD, moat line restored
The close already had "one verified run," "nothing mocked," and "clones from the outliers." It was paraphrasing away the deck's slide-9 punchline — *"Run it continuously and that behavioral record only gets richer. The moat is time."* Restored.

### Deliberately still OUT (flagged, not changed)
- **Slide 6 findings** (paywalls, ~5 wires anchor everything, 9-of-17 single-voice, 90% Global North -> 37 sources / 7 regions). Strong on paper, weak on screen — no single view shows them, so they'd be voiceover over a static page. Left to the deck. Available if you want them.
- **Slide 8 "what we deliberately can't claim (yet)"** — the honest-broker beat. Intellectually the deck's strongest, but in a short sales video to a cold judge it risks reading as a disclaimer. Left out by default; flag if wanted.

---

## Part 2 — Revised script

# Narrative Nexus — Video Script v2

*Screen-record driving the live app. Never open the Investigate page.*

---

## [Open]
*Start on the Sources page, don't click yet.*

> Everyone can tell you *what* the news said today. Nobody can answer some questions you might want answered about who gives you the news: How mainstream is any given source? Which ones break real stories first — unique, and ahead of the pack? And which just echo consensus after it's already been published elsewhere? Narrative Nexus is an instrument that answers them. It doesn't score bias — it scores behavior, measured over time.

---

## [The machine]
*Navigate to Pipeline.*

> Four AI agents run in sequence. One reads articles from 37 news outlets across six continents and groups them by story. One strips the spin and extracts individual factual claims. One does pure math to find where independent outlets *converge* on the same claim — that convergence is what we call consensus reality. And one re-reads old articles to catch silent edits. *(gesture at the provider labels on each stage)* Every AI stage runs on Fireworks AI — that's inference on AMD Instinct hardware — and each stage's provider is configurable. And that configurability is tested, not decorative: we deployed Gemma 4 E4B on-demand through Fireworks and verified it running our claim-extraction prompt across the full sixty-one-article Venezuela cluster — 268 structured claims extracted, evidence in the repo. The shipped database itself was built on the default Fireworks DeepSeek configuration. This is a real engine, not a slideshow.

---

## [The scatter]
*Navigate to Sources, gesture across the plot.*

> Every dot is an outlet, placed by two behaviors: how often it breaks claims early, and how often those claims survive into consensus. That splits the world into four corners — Early Breakers, early and validated; Unmatched Breakers, early but uncorroborated; Late but Reliable; and Consensus Echoes. In two seconds you can see how 37 outlets *behave*, not what they say. *(click a dot)* Clicking any dot opens that outlet's full profile — six behavioral dimensions, no single composite score.

---

## [The proof]
*Navigate to Stories.*

> Two real stories, processed end to end. *(open the Venezuela cluster report)* The Venezuela emergency — a five-day surge: 20 outlets, 138 claims, 5 silent edits detected. At the top, the facts independent outlets converged on. Below, the interesting part — single-outlet claims the system refuses to self-validate: one source alone reporting Maduro was taken into custody, India's field hospital covered only by The Hindu, China's aid only by Global Times. That refusal isn't cosmetic — it's the hardest lesson we learned. Our first engine reported 2,625 consensus claims; almost all of them were an artifact — a single source in a cluster of one, agreeing with itself at a hundred percent. We rebuilt it: consensus now requires at least two independent sources reporting the same claim, matched across outlets at cosine similarity of point-eight-five or higher. Twenty-six hundred claims collapsed to 10 real ones. *(back to Stories, open the US-Iran timeline)* And the US-Iran war — a 48-day arc, animated claim by claim, from one outlet's first report to cross-source consensus.

---

## [Close]
*Back on Sources.*

> What you've seen is one verified run over a real news corpus — nothing mocked; every number traces back to a query. This run was short by design, to prove the pipeline works end to end. The real product is the instrument itself — as far as we've found, nobody profiles how news sources behave over time the way this does. Run it continuously and that behavioral record only gets richer: the moat is time. Built to tell the clones from the outliers, Narrative Nexus tracks consensus reality — not truth.

---

## Part 3 — Screen/narration sync notes (what must be visible when)

1. **Gemma line (machine):** Stay on the Pipeline page, static. **Do NOT open, hover, or gesture at any provider dropdown while the Gemma sentence is spoken** — Gemma is not selectable in the functional dropdown, and the dropdowns on screen read "Fireworks AI — DeepSeek V4 Pro." That on-screen DeepSeek label *supports* the very next sentence ("the shipped database itself was built on the default Fireworks DeepSeek configuration"), so let the camera rest on the stage cards. Gesture at provider labels only during the earlier "each stage's provider is configurable" clause. Optional: cut briefly to the repo's `docs/evidence/gemma/README.md`, then back to Pipeline — only if the cut is clean; static Pipeline is the zero-risk choice.
2. **Silent-edits number (proof):** The "5 edits detected" stat lives on the **Stories card**, not the cluster report header. To have the number on screen as it's said, speak the "five-day surge: 20 outlets, 138 claims, 5 silent edits" clause while the **Stories page (Venezuela card)** is still visible, then click into the cluster report for the consensus/outlier beats. Recommended: linger ~2s on the Stories card before clicking.
3. **2,625->10 beat (proof):** Speak this while the **Venezuela cluster report** is open — its Consensus Summary panel already reads "138 claims / 3 absorbed / 135 pending" and "cross-source convergent, not self-validating," which visually backs the "refuses to self-validate" and the >=0.85 matching claim. The 2,625 and 10 figures are corpus-level, not on this screen — that's fine; they're spoken, not shown, and the on-screen "not self-validating" line is the supporting evidence.
4. **Timeline beat:** Return to Stories and use the Venezuela card -> US-Iran card -> View Timeline path (Timeline is not in the top nav).
5. **Never on screen:** the Investigate page (the nav link is visible — just don't click it), any scraper Start action, any provider dropdown opened.
6. **Close:** end on the Sources scatter with the footer visible if possible — the footer tagline matches the final spoken line.

---

## Compliance check against the work order

| Requirement | Status |
|---|---|
| 10 -> 5 silent edits (Venezuela) | Done — proof section |
| Gemma beat added, deck claim-strength exactly, past tense, no dropdown/live/default claims | Done — machine section + sync note 1 |
| Lead with instrument, "moat is time," "one verified run" | Preserved; moat line restored to close |
| No source "right"/"wrong" | Clean |
| Canonical archetype names only | Clean (no stale names found) |
| No Investigate mention | Clean; header direction retained |
| Frozen numbers only | All figures from the canonical set (incl. 2,625->10, >=0.85, 268/61); no new numbers introduced |

---

## Appendix — to run the LEAN variant (no 2,625->10 beat)

In the proof section, delete this stretch:

> *That refusal isn't cosmetic — it's the hardest lesson we learned. Our first engine reported 2,625 consensus claims; almost all of them were an artifact — a single source in a cluster of one, agreeing with itself at a hundred percent. We rebuilt it: consensus now requires at least two independent sources reporting the same claim, matched across outlets at cosine similarity of point-eight-five or higher. Twenty-six hundred claims collapsed to 10 real ones.*

The sentence before it ("...China's aid only by Global Times.") flows straight into "*back to Stories, open the US-Iran timeline*" with no other edit needed. Sync note 3 becomes irrelevant; all other notes stand.