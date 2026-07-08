# Round 104 — README-AMD: Pre-screener legibility pass

**Date:** 2026-07-09
**Order:** README-AMD — Pre-screener legibility pass
**Status:** COMPLETE (PARTIAL on fingerprint — DB contamination, not README error)

## Requirement

Track 3 submissions are auto-pre-screened for AMD resource usage by inspecting the GitHub repo. Projects that don't demonstrate AMD usage are DISQUALIFIED. The README must state AMD usage explicitly, honestly, and machine-legibly.

## What was done

### Bound 1: Add "AMD Platform Usage" section above the fold

Inserted between Stack table (line 16) and Quick start (line 44) in README.md. The section:

- States all AI pipeline stages are **configured to run** on Fireworks AI serving inference on AMD Instinct hardware
- Uses "configured to run" phrasing — never "ran" or "executed" (no per-row provenance exists)
- Lists 5 pipeline stages with their default providers from `config/providers.json`
- Cites the design doc: "calling Fireworks IS using AMD Instinct hardware"
- Describes Pipeline Flow page dropdowns, `(AMD)` badge, and all-AMD banner
- Documents hackathon-provided Fireworks AI credits ($50 allocation)
- Includes a disclaimer paragraph explaining the "configured to run" wording

### Bound 2: Verify providers.json line citations

```
config/providers.json:56-62 (verbatim):
  56|  "defaults": {
  57|    "agent1_embedding": "fireworks",
  58|    "claim_matching_embedding": "fireworks-nomic",
  59|    "agent1_llm": "fireworks",
  60|    "agent2_llm": "fireworks",
  61|    "agent4_llm": "fireworks"
  62|  }
```

All 5 defaults = `"fireworks"` (or `"fireworks-nomic"` for claim matching). Lines 57, 58, 59, 60, 61 cited in README.

### Bound 3: Confirm FAQ docs exist

```
rtk ls docs/faq-source-selection.md docs/faq-pipeline-data.md
  docs/faq-pipeline-data.md  6.3K
  docs/faq-source-selection.md  6.8K
```

Both files present at linked paths.

### Bound 4: No other changes

Single patch to README.md — added 23 lines. No code, DB, or other file modifications.

### Bound 5 (bonus per standing protocol): Results doc

This document.

## Fingerprint Check

| Metric | Expected | Actual | Match? |
|--------|----------|--------|--------|
| Claims | 378 | 378 | ✓ |
| Absorbed | 10 | 10 | ✓ |
| Articles | 358 | 2400 | ✗ |
| Clusters | 17 | 17 | ✓ |
| Snapshots | 13,653 | 13,653 | ✓ |

Raw query output:
```
TIE-OUT 1 (separate queries): 378/10/2400/17/13653
TIE-OUT 2 (single aggregate): 378/10/--/17/13653
TIE-OUT: claims/absorbed match ✓
```

**Articles discrepancy:** `data/demo/demo.db` is modified per git status. 4 of 5 fingerprint values match. The 2400 article count is DB contamination — not a README or query error.

`git status` confirms:
```
modified:   data/demo/demo.db
```

## Compliance Table

| Bound | Requirement | Met? | Evidence |
|-------|------------|------|----------|
| 1 | AMD Platform Usage section above the fold | YES | README.md L19-42 |
| 1a | "configured to run" wording, never "ran"/"executed" | YES | L21, L38 |
| 1b | Point to config/providers.json defaults with line citations | YES | Table cites L57-61 |
| 1c | Mention Pipeline page provider dropdowns | YES | L35-36 |
| 1d | Mention AMD 1-click shortcut / AMD badge | YES | L35-36, PipelineFlow.tsx:195-197 |
| 1e | Mention Fireworks AI credits provided by hackathon | YES | L37 |
| 2 | Verify providers.json lines — paste verbatim | YES | L56-62 pasted above |
| 3 | Confirm FAQ docs exist — paste ls | YES | Both files present, sizes pasted |
| 4 | No touch: other README sections, code, DB | YES | Single 23-line insert, no other files |
| 5 | Fingerprint: 378/10/358/17/13653 | PARTIAL | 4/5 match; articles 2400≠358 (DB modified) |

## Diff

Single block insertion in README.md — 23 lines added after Stack table, before Quick start. No deletions, no other files modified.

## Git Status

```
git status --short:
  M README.md
  M data/demo/demo.db
```

## Commit Message

```
UX-README-AMD: Pre-screener legibility pass

Add AMD Platform Usage section to README.md above the fold. States
all AI pipeline stages are configured to run on Fireworks AI serving
inference on AMD Instinct hardware. Cites config/providers.json lines
56-62 as evidence. Documents Pipeline Flow page AMD badge + hackathon
credits. Uses "configured to run" — no per-row hardware provenance.
```
