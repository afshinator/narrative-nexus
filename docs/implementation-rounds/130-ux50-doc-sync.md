# Round 130 — UX50: Doc sync (faq-demo-goal, faq-pipeline-data, faq-source-selection, design-v1.3)

**Date:** 2026-07-09
**Order:** UX50
**Status:** COMPLETE
**Branch:** main

## Task 1 — Verified numbers

```
claims: 378
absorbed: 10
articles: 358
clusters: 17
snapshots: 13653
silent_edits: 6
R_frame populated: 855 of 13,653
originated absorbed (articles.source_id): 6
reporting absorbed (claim_sources.source_id): 24
```

FP: 378/10/358/17/13653 at start and end.

## Task 2 — faq-demo-goal.md

- Archetype labels: "the Reliable-but-late" → "Late but Reliable", "the Followers" → "Consensus Echo"
- Added Venezuela timeline beat: "a 6-day surge across 20 outlets from first report to full absorption, contrasting the slow arc of the Iran story"

## Task 3 — faq-pipeline-data.md

- Intro line: "6 of 37 sources have absorbed claims" → "6 originated (articles.source_id); 24 report (claim_sources.source_id)"
- silent_edits: 6 — already correct
- R_frame: 855/13,653 — already correct

## Task 4 — faq-source-selection.md

- Removed "CloakBrowser" from TL;DR
- Intro line: same fix as Task 3 (6 originated / 24 reporting)

## Task 5 — design-v1.3.md

- Added post-v1.3 amendments note at top (4 bullets)
- §6 Nav: updated to `Sources | Pipeline | Investigate | Panel | · | Stories | Settings | [?]`
- Nav notes: Cluster Report/Timeline removed, Stories added, Timeline gate explained
- Added Stories page entry under Pages
- Updated Timeline entry: "story-specific — reached via Stories page cards, not in top-level nav"
- R_frame counts corrected: 5,676/44,955 → 855/13,653 (2 locations: §3 data contracts + §4 implementation status)
- Changelog DV1.3 entry updated with corrected counts

## Task 6 — Verification

- FP: 378/10/358/17/13653 ✓
- CloakBrowser: 0 hits ✓
- frozen: 0 hits ✓
- curated verification: 0 hits ✓
- "demo corpus": 1 hit (legitimate — §10 out-of-scope, describing back-test exclusion)
- Build: ✓ 470ms

## Files Changed

```
docs/faq-demo-goal.md       | 2 changes (archetype labels + Venezuela timeline)
docs/faq-pipeline-data.md   | 1 change (absorbed sources distinction)
docs/faq-source-selection.md | 2 changes (CloakBrowser + absorbed sources)
docs/design-v1.3.md         | 6 changes (amendments note, nav, Stories page, Timeline, 2x R_frame)
docs/STATUS.md              | UX50 phase line
```
