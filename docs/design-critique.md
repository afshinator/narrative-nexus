# Narrative Probe — Design Critique

**Date:** 2026-06-20
**Target:** `docs/mocks/index.html`
**Skill:** frontend-specific/critique

---

## Anti-Patterns Verdict

**Partial fail.** The mock would pass the 2-second sniff test as "probably made by a person" due to authored content and specific layout choices, but it shows several AI-tells:

- Dark mode with glowing green accents — the single most common AI-generated aesthetic
- Inter + JetBrains Mono — the default pairing for "technical product"
- Cards wrapping everything (chart containers, story cards, zone sections) — generic container choice
- Hero metric layout on source profile (big number, small label) — listed as a DON'T
- No pure black/white, which is good, but the #0a0a0f + #00ff88 combo is the archetypal AI dark palette

What saves it: the scatter plot with detailed axis descriptions, the 3-zone coverage analysis layout, and the specific data (source names, article titles, edit descriptions) all feel authored rather than templated.

---

## Overall Impression

The mock has a coherent forensic identity and the core navigation flow works, but it's visually conservative — it plays the genre straight rather than making a statement. The single biggest opportunity is breaking free of the generic dark-terminal template to find a more distinctive visual lane.

---

## What's Working

- **The core concept is immediately readable.** Landing on the scatter plot with 4 quadrants and axis descriptions explains the product in seconds. The Coverage Analysis 3-zone layout tells a clear story. These aren't generic.

- **Navigation flow is intuitive.** Leaderboard → click source → Source Profile → click story → Coverage Analysis → Timeline forms a natural drill-down path. The stubs with back-links complete the IA picture.

- **Microcopy has voice.** The footer, the scatter plot explanations, the edit log action buttons ("Confirm Significant" / "Mark False Positive"), and the qualifier on zone 1 all sound like a real product, not placeholder copy.

---

## Priority Issues

### P1 — The mock looks like every other AI dark-mode dashboard

**What:** Dark terminal theme (#0a0a0f) + green accent (#00ff88) + Inter + JetBrains Mono + bordered cards everywhere is the 2024-2025 AI-generated default for "analytical product."

**Why it matters:** It undermines the product's own claim to be an authoritative forensic tool. The visual language says "generic template" while the content says "serious analysis."

**Fix:** Pick a more distinctive color strategy. The dark palette can stay — it fits the forensic genre — but shift the accent away from pure cyan/green (#00ff88 is too close to terminal green). A desaturated amber, a cooler blue-white, or even a muted crimson for alerts only would feel more authored. Lose the card borders on chart containers — use background-only and let the content breathe.

**Command:** `/recolor`

### P2 — Nav is missing Cluster Report and Timeline

**What:** The nav lists Leaderboard, Source Profile, Pipeline Flow, Ad-Hoc, Panel, Onboarding — but not Cluster Report or Timeline. These are full mocked pages that can only be reached by clicking through content, not from the nav.

**Why it matters:** New users can't discover two of the four functional pages from the primary navigation. The IA is incomplete.

**Fix:** Add Cluster Report and Timeline to the nav bar.

**Command:** Structural/content fix, not a design mode

### P3 — Interactive elements don't look interactive

**What:** Scatter plot dots are clickable but the cursor only changes on exact pixel hit. Timeline dots have no click behavior. Nav stubs don't change on hover. The help icon (?) on source profile is 20px and easy to miss.

**Why it matters:** Users won't discover interactions they can't see. The Timeline is described in the brief as a core demo feature but the dots are purely decorative.

**Fix:** Broaden scatter dot hit targets with invisible padding. Make timeline dots navigate to the coverage analysis page. Give stub nav links a subtle hover effect (slightly brighter text). Make the help icon larger or add a label.

**Command:** `/interaction`

### P4 — Stub pages are structurally empty

**What:** Pipeline Flow, Ad-Hoc, Panel, and Onboarding show "Contents TBD" centered in a box with a description. No layout skeleton, no sense of what the page will look like.

**Why it matters:** It breaks the illusion of a real product. Even a wireframe skeleton would communicate intent.

**Fix:** Give each stub a layout frame — a sidebar area on Panel showing a source list, a search bar on Ad-Hoc, a pipeline stage diagram placeholder on Pipeline Flow, step indicators on Onboarding.

**Command:** `/surface`

---

## Minor Observations

- `#00ff88` green on `#0a0a0f` background has roughly 13.5:1 contrast, which is fine for readability but the green is very intense. A slightly desaturated green would be easier to live with at scale.
- The intro accordion panel is well-implemented but the collapsible button (▲) is a thin target.
- Source profile country/category label uses a period separator ("United Kingdom · Wire Service") — clean but the country name is long and could wrap awkwardly on narrow screens.
- The edit log "Confirm Significant" and "Mark False Positive" buttons have no feedback state — clicking them does nothing.

---

## Questions to Consider

- **What if the scatter plot weren't the hero?** The table is the primary instrument — what if the landing page led with the data and tucked the chart into a toggle or side panel?
- **What would a confident version of this look like?** Right now it executes the genre correctly. What would it look like if it pushed past "correct" into "memorable" — a different color strategy, an unconventional layout, a typographic choice that isn't Inter?
- **Does "Leaderboard" fit the tone?** It's the landing page for an analytical tool, but the word implies gamification. The UX brief calls this the landing page. Would "Panel Overview" or "Source Compass" or just "Sources" fit better?
