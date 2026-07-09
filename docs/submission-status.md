# SUBMISSION STATUS — snapshot 2026-07-09 (end of UI-polish chat)

**Deadline:** Fri Jul 11, 6pm CET = **9am PDT Friday** — effectively Thursday night.
**Track 3 required artifacts:** GitHub repo URL + demo video + slide deck (PDF).
Hosted URL optional-but-recommended. Pre-screener reads: repo, deck PDF text,
hosted URL. It does NOT read the video. AMD usage must be demonstrable or DQ.

## DONE (as of this snapshot)
- One-DB paradigm complete (UX34–UX37): demo.db is THE db, .readonly removed,
  scraper relocated to Settings behind confirmation modals, hygiene rules logged.
- 924 timeline backfilled + unsuppressed (UX42–UX47, other chat). Both stories
  have working timelines.
- Timeline page fixed (UX39): date axis (was 49 overlapping labels), numbered
  claim markers + legend.
- Nav restructured (UX40): no hardcoded /cluster/966 links; Stories page at
  /stories with story cards; Panel · Stories separator; /cluster and /timeline
  redirect to /stories.
- Stories cards data-driven (UX41): 924 title fixed in DB ("Venezuela Emergency
  and Rescue Response"), stats from API not hardcoded, time-to-consensus labeled.
- Archetype rename (human, direct): Early Breaker / Unmatched Breaker / Late
  but Reliable / Consensus Echo. Synced everywhere (UX50–51). DB stores internal
  constants (incl. typo CONCENSUS_FOLLOWER — harmless, internal only).
- Nav scraper indicator live + animated (UX52). Docs synced (UX50, UX53):
  design-v1.3 amendments, FAQs, CloakBrowser reference removed.
- README fully rewritten (human has draft — NOT YET COMMITTED). [team/name]
  placeholder needs "DreamTeam"; repo URL needed.
- 5 screenshots taken → docs/shots/ (01 sources, 02 pipeline, 03 venezuela
  cluster, 04 iran timeline, 05 stories).
- Deck copy drafted, 8 slides → see docs/deck-copy-v1.md (companion file).
- Team name confirmed: DreamTeam (lablab.ai page).

## IN FLIGHT (check STATUS.md phase lines for landing)
- UX55: footer stats not rendering in human's browser (endpoint works via curl;
  suspected vite proxy issue) + 0.7rem font-floor violation + vitest baseline
  repair (15 → must return to 12).
- UX56: keyless-run audit + .env.example + single-container Docker. May come
  back CANNOT COMPLY on build/smoke (worker had no container runtime in D1) —
  human runs smoke checklist locally on Linux Mint.
- Separate chat spun up for Docker/hosting follow-through.
- Separate chat exists for anything 924-backfill related (done, may be idle).

## NOT DONE — the critical path
1. **PDF deck build** — copy is drafted (docs/deck-copy-v1.md); needs assembly
   into dark-themed PDF with the 5 shots. Screenshots 01/05 have copy defects
   noted in deck-copy-v1.md; human may reshoot after UX55.
2. **Video script + record** — source material: docs/faq-demo-goal.md pitch
   script (update: both timelines now work; archetype names changed; Stories
   page exists — script says "I open the Venezuela earthquake cluster" which
   now routes through /stories). 2–3 min. Record Thu at latest.
3. **Uncommitted-diffs review → final commit.** git status showed a pile of
   modified files; some expected from rounds, some surprises (ScatterPlot.tsx,
   ArchetypePills.tsx, index.css, design-tokens.md, design-v1.2.md — the
   archetype rename explains several). Human must review diffs before the
   deadline commit. NOTHING IS COMMITTED BY WORKERS — human commits.
4. **README finalization** — fill DreamTeam + repo URL, verify Docker section
   matches whatever UX56 actually ships, commit.
5. **Investigate page** — BROKEN (extraction 500s; isolated to uvicorn-vs-
   direct-Python transport issue, 8 debug attempts documented round 129-130).
   Human wants to retry a fix; if unfixed by Thu, decide: hide from nav or
   leave (currently still in nav). DO NOT let this eat deck/video time.
6. **Scraper end-to-end test** — deck slide 7 claims "press Start and it
   collects continuously." NEVER VERIFIED under new paradigm. 10-min scratch-DB
   run, or soften the claim.
7. **Optional, last:** Fireworks DB rebuild (strengthens AMD claim; human
   wanted it "after everything else"). Only if everything above is done.

## KNOWN DEFECTS (small, judge-visible, fix if time permits)
- Timeline 966 header: "20 extracted claims over 6 days" — it's a 48-day arc
  with 6 distinct dates. Copy bug.
- Sources page hero: "(currently) 20 outlets" reads like panel size; panel is
  37 (20 = graded). Confusing copy.
- Stories page: "curated list for the demo" → human changed to "for the
  hackathon" and killed "Demo corpus" footer — verify landed, reshoot 05.

## STANDING RULES (non-negotiable, from STATUS.md)
- Golden fingerprint 378/10/358/17/13653 — paste at start/end of any round.
- Worker never git add/commit/push. Human commits.
- Scraper verifications: scratch DB only, never data/demo/demo.db (UX37).
- Evidence or void: pasted verbatim output; YES-on-failed-bound is the
  recurring worker failure (violations #24/26/27/30 + UX44/46 attempts) —
  keep requiring pasted output, it works.
- Propose-first on judge-visible design. Font floor 0.75rem. WCAG AA both themes.
- Consensus-reality language only; never "source was right/wrong."