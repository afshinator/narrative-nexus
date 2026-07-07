# UX2 — Comprehension Layer: Production Implementation

**Date:** 2026-07-06
**Parent commit:** [HEAD~1] (UX1-B)
**Status:** COMPLETE — committed (2b6bafb). STATUS.md updated (uncommitted).

---

## U1 — Intro Strip

Full-width strip outside the max-w-[1340px] page container, rendered above the Sources page header. "Not the truth — consensus reality." in Space Grotesk navy bold, with one-sentence app description. Tooltip on "consensus reality" from design-v1.2 §1.

**Source:** Sources.tsx:288-300
**Copy source:** design-v1.2 §1 (pitch + footer)

---

## U2 — Reusable Tooltip Component

**File:** `src/components/Tooltip.tsx` — hover-triggered popup with CSS group-hover, design-token styling (surface bg, border, text colors, 8px radius, shadow).

**7 tooltips wired in Sources.tsx:**

| # | Element | Copy | Design doc |
|---|---------|------|------------|
| 1 | "Not the truth — consensus reality." | Consensus reality: the version of events agreed upon by the majority of the panel at a given threshold. Not 'the truth.' | §1 vocab |
| 2 | Source count "{N} monitored outlets" | Curated panel of wire services, mainstream editorial, international, investigative, and contrarian sources across 5 tiers. | §5 tiers |
| 3 | "{Geopolitics} vertical" | Topic vertical: stories categorized by domain keywords into geopolitics, economics, and technology. | §5 verticals |
| 4 | X-axis "Origination (0–100)" | Outlier claim origination: how often a source breaks claims before the rest of the panel reports them. | §4 R_orig |
| 5 | Y-axis "Validation (0–100)" | Consensus-absorbed: a claim that has entered the consensus version of events. Terminal state. | §1 vocab |
| 6 | "Early Breaker" legend item | High origination + high validation. Consistently breaks outlier claims that later become consensus-absorbed by the panel. | §4 archetype |
| 7 | "Noise Generator" legend item | High origination, low validation. Frequently breaks claims that never enter consensus — systematic noise. | §1 |
| 8 | "Selective but Accurate" legend item | Low origination, high validation. Late to stories but their claims reliably enter consensus. | §4 |
| 9 | "Consensus Follower" legend item | Low origination, low validation. Stays close to the mainstream view without independent breakout claims. | §1 |

(9 total — 4 legend items have tooltips + 5 other placements)

---

## U3 — Tier Legend Rewrite

**Before:** "Shapes: ● Circle (T1) · ■ Square (T2) · ◆ Diamond (T3) · ▲ Triangle (T4) · ✚ Cross (T5)"
**After:** "Shapes: ● Wire/Consensus Anchor · ■ Mainstream Editorial · ◆ International · ▲ Investigative · ✚ Contrarian"

**Copy source:** design-v1.2 §5 tier table

**Source:** Sources.tsx:407

---

## U4 — POC Server Kill

```
Killed proc_9356fee36b04 (PID 5501)
```
POC file at `docs/mock-ux1-comprehension-poc.html` kept per instruction (cleanup in H1).

---

## Verification

| Check | Result |
|-------|--------|
| `npm run build` | PASS (485ms, all modules) |
| `tsc --noEmit` | PASS (no errors) |
| Vitest | 126 pass, 13 fail (all pre-existing: 11 router-shell + 1 schema/better-sqlite3 stale + 1 docker/D2 volume) |

### Pre-existing vitest failures
- `src/__tests__/router-shell.test.tsx` — 11 tests (pre-existing jsdom/route issues)
- `db/__tests__/schema.test.ts` — stale since D3 (better-sqlite3 removed)
- `src/__tests__/docker/compose.test.ts` — stale since D2 (volume mount removed)

---

## Rendered Copy (exact JSX)

**Intro strip:**
```
Not the truth — consensus reality. Narrative Nexus tracks how news
outlets originate, validate, and correct claims across geopolitics,
economics, and technology — scoring each source 0–100 on six
independent reputation dimensions.
```

**Tier legend:**
```
Shapes: ● Wire/Consensus Anchor · ■ Mainstream Editorial ·
◆ International · ▲ Investigative · ✚ Contrarian
```

---

## Commit

```
2b6bafb UX2: intro strip, tooltips, tier legend
 src/__tests__/sources-page.test.tsx |  4 +--
 src/components/Tooltip.tsx          | 19 ++++++++++++++
 src/pages/Sources.tsx               | 52 ++++++++++++++++++++++++++++++-------
 3 files changed, 64 insertions(+), 11 deletions(-)
```

---

## Compliance Table

| # | Requirement | Copy Source | Met? | Evidence |
|---|------------|-------------|------|----------|
| U1 | Full-width intro strip under app header, "Not the truth — consensus reality." prominent | design-v1.2 §1 (pitch + footer) | YES | Sources.tsx:288-300 |
| U2 | Reusable Tooltip component + ≥7 tooltips, copy from design-v1.2 §1 vocab table | design-v1.2 §1 (vocab), §4 (dimensions), §5 (tiers) | YES | src/components/Tooltip.tsx + 9 tooltips in Sources.tsx |
| U3 | Legend shape rewrite: meaningful labels from design-v1.2 §5 tier table | design-v1.2 §5 | YES | Sources.tsx:407, 5 tier role names |
| U4 | Kill POC server, paste PID + confirmation | — | YES | PID 5501 killed |
| Verify | npm run build + vitest (pre-existing failures listed) | — | YES | Build 485ms, vitest 126/143 pass |
| Commit | "UX2: intro strip, tooltips, tier legend" + git log -1 --stat | — | YES | 2b6bafb, 3 files, +64/-11 |
| No push | No git push attempted | — | YES | STAYED LOCAL |
