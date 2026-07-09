# Round 133 — UX53: design-v1.3.md sync to today's paradigm pivots

**Date:** 2026-07-09
**Order:** UX53
**Status:** COMPLETE
**Branch:** main
**Mode:** DOC-ONLY — no code or DB changes

## Task 1 — §2 Hackathon requirements

- "All submissions must be containerized" → "Track 3 submission format: GitHub repository + 5-minute demo video + slide deck. Docker Compose included as deployment convenience, not a requirement."

## Task 2 — §8 Containerization

- Header: "Requirement [LOCKED]" → "Status [LOCKED]"
- First sentence: rewrote to "Docker Compose is included as an optional deployment convenience..."
- Added note: `.readonly` sentinel removed in UX36, `NN_READONLY` no longer exists.

## Task 3 — §7 Demo strategy

- Item 3 (pipeline replay): "GPU pod / Fireworks / OpenCode / CPU" → "Fireworks, OpenCode Zen, DeepSeek, OpenAI, Local CPU" (matches PipelineFlow.tsx dropdowns)
- Item 4 (live forensic pass): marked conditional. Notes uvicorn transport bug (500 from Fireworks, works from standalone Python), conflicts with "no live calls that could fail" rule. Backup beat only.

## Task 4 — §6 Source Profile

- Removed "30-day sparklines, Vf trend" (cut in UX14, per STATUS.md)
- Replaced with: "title block with tier name and description, two-tier stat panel (source vs tier average)"
- Verified against src/pages/SourceProfile.tsx sections: title block, radar chart, StatPanel, outlier waterfall, silent edit log

## Task 5 — §9 Open questions

- Section header: "OPEN QUESTIONS" → "OPEN QUESTIONS [RESOLVED]"
- Added Resolution column to table
- All 7 questions resolved: 48GB GPU, DeepSeek V4 + MiniMax/Kimi-K2P5 models, credits revealed, JSON reliability sufficient, fine-tuning out of scope, provider fallback built, all-Fireworks chosen for demo

## Task 6 — §10 + sweep

- §10: "demo corpus" → "shipped dataset"
- Full-file grep results:
  - "demo corpus": 1 hit (amendments note — "removed from all docs", legitimate)
  - "frozen": 1 hit (amendments note — "'Frozen' language removed", legitimate)
  - ".readonly": 2 hits (amendments + §8 note — both say "removed", legitimate)
  - "must be containerized": 0 hits

## Task 7 — Amendments note extended

Added 7 new bullets covering: one-DB paradigm, .readonly removal, scraper relocation to Settings, nav indicator live, Docker optional, 924 timeline, §9 resolved.

## Task 8 — Verify

### Fingerprint

```
claims 378 | absorbed 10 | articles 358 | clusters 17 | snapshots 13653
```
Clean at start and end.

### Post-edit grep

All banned-term hits are in amendments/changelog notes that SAY the term was removed — no live references.

### No code changes

## Files Changed

```
docs/design-v1.3.md  | §2, §6, §7, §8, §9, §10, amendments note — 7 edits
docs/STATUS.md       | UX53 phase line added
```
