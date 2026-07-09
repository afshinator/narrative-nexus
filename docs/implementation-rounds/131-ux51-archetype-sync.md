# Round 131 — UX51: Sync old archetype names to new canonical set

**Date:** 2026-07-09
**Order:** UX51
**Status:** COMPLETE — no code changes needed
**Branch:** main

## Task 1 — Find all occurrences

### Old names grep (excluding docs/implementation-rounds/ and STATUS.md history)

```
Noise Generator        — 1 hit:  docs/design-v1.3.md:9 (changelog line)
Selective but Accurate — 1 hit:  docs/design-v1.3.md:9 (changelog line)
Consensus Follower     — 1 hit:  docs/design-v1.3.md:9 (changelog line)
```

All three hits are the SAME line — the post-v1.3 amendments changelog:
> "Archetype labels updated throughout: Noise Generator → Unmatched Breaker, Selective but Accurate → Late but Reliable, Consensus Follower → Consensus Echo (UX49)."

This is a legitimate historical documentation of the transition, not a stale reference.

### New names mapped

| New name | Live in |
|----------|---------|
| Unmatched Breaker | Sources.tsx legend, ArchetypePills.tsx, sources-page.test.tsx, design-v1.3.md (§1, §4, §11), faq-demo-goal.md, design-v1.2.md (§1), design-tokens.md |
| Late but Reliable | Sources.tsx legend, ArchetypePills.tsx, sources-page.test.tsx, design-v1.3.md, faq-demo-goal.md, design-v1.2.md, design-tokens.md |
| Consensus Echo | Sources.tsx legend, ArchetypePills.tsx, sources-page.test.tsx, design-v1.3.md, faq-demo-goal.md, design-v1.2.md, design-tokens.md |

### Surfaces confirmed clean of old names

| Surface | File | Has archetypes? |
|---------|------|----------------|
| Sources legend | Sources.tsx | ✓ new names |
| Filter pills | ArchetypePills.tsx | ✓ new labels |
| SVG quadrants | ScatterPlot.tsx | ✓ uppercased new |
| Tests | sources-page.test.tsx | ✓ new names |
| Onboarding dialog | OnboardingDialog.tsx | ✗ no archetypes |
| FAQ pipeline | faq-pipeline-data.md | ✗ no archetypes |
| FAQ source | faq-source-selection.md | ✗ no archetypes |

### DB storage — PROPOSED (not done)

`snapshots.archetype` stores internal pipeline constants, NOT display labels:

```sql
SELECT archetype, COUNT(*) FROM snapshots GROUP BY archetype ORDER BY COUNT(*) DESC;
-- NULL:              12,225
-- NOISE_GENERATOR:      870
-- EARLY_BREAKER:        372
-- CONCENSUS_FOLLOWER:   129
-- SELECTIVE_ACCURATE:    57
-- Total:             13,653
```

These are programming identifiers emitted by `pipeline/archetype.py:14-19`, stored pre-computed, and read by `app/main.py:120` in API responses. The frontend maps internal constants to display labels in `ArchetypePills.tsx` — `NOISE_GENERATOR` → "Unmatched Breaker", etc. The internal constants never reach the user's screen.

**Change not applied:** Renaming 1,428 stored rows would require a full pipeline re-run (snapshot backfill) on all 13,653 snapshots. The mapping layer in the frontend handles the translation. For hackathon scope, this is a non-issue.

## Task 3 — Verify

### Fingerprint

```
claims: 378 | absorbed: 10 | articles: 358 | clusters: 17 | snapshots: 13653
```
Clean at start and end.

### Build

✓ 454ms

### Vitest

```
Test Files  3 failed | 15 passed | 1 skipped (19)
     Tests  12 failed | 121 passed | 4 skipped (137)
```

Baseline: 12 pre-existing failures (11 router-shell + 1 docker). No new failures. Sources page tests (20/20) all pass with new archetype labels.

### Post-edit grep

Old names found ONLY in:
- `docs/design-v1.3.md:9` — changelog line (legitimate historical documentation)
- `docs/STATUS.md:6` — UX49 phase line documenting the rename (legitimate)

Zero stale display-surface references across src/, app/, pipeline/, config/.

## Files Changed

```
NONE — all display labels were already synced in UX49/UX50.
docs/STATUS.md (phase line added below)
```
