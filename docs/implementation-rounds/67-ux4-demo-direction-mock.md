# UX4 — Demo Direction Mock

**Date:** 2026-07-06
**Status:** COMPLETE — static HTML mock created. No app code changes. No commits.

**File:** `docs/mocks/demo-direction-mock.html`
**Access:** `http://localhost:3015/demo-direction-mock.html` (Python http.server, PID 9512)

---

## Section A — Sources Header Revision

Recreates the current Sources page top area (post-UX3, post-human-tweaks) with two changes:

1. **Vertical pills removed** — replaced by static pill label: `"Vertical: Geopolitics (demo corpus)"`. The pills are misleading when all three verticals return identical data (UX3 X2 finding).

2. **Corpus provenance line** — added near intro strip: `"Demo corpus: 358 articles · 37 sources · Mar–Jul 2026 · curated for verification"`. Gives the demo viewer context that this is a curated snapshot.

**Visual state matched from current code:**
- Two-column intro strip with pipe divider (Sources.tsx:289-301)
- Tagline: "Rating not the truth — but identifying consensus reality" (Sources.tsx:292)
- Font base: 1.1rem per UX3 rebase (index.css:189)
- Legend unified (Sources.tsx:414-416): color + shapes in one block, 0.82rem
- Ungraded copy: X4 rewrite (Sources.tsx:454-456) — "panel-composition characteristic, not quality judgment"
- Ungraded source list: 11 sources from real DB query (those with R_orig or R_val NULL)

---

## Section B — Near-Consensus Exhibit

**CANNOT COMPLY** — similarity scores are not persisted in the demo DB.

The BGE semantic matching runs at ingestion time (greedy merge at cosine 0.85) via `pipeline/claim_matcher.py`. Only matched pairs (sim ≥ 0.85) result in claim_sources links. Pairs in the 0.786–0.815 near-miss band are evaluated in-memory and discarded — no similarity column exists in any table.

**Tables checked:**
- `claim_sources` — columns: claim_id, source_id, first_seen_at (no similarity)
- `claim_variants` — columns: id, canonical_claim_id, source_id, article_id, text, first_seen_at (no similarity)
- `claims` — no similarity column

**Query attempted (returns nothing):**
```sql
SELECT * FROM claim_sources WHERE claim_id = ANY(SELECT id FROM claims); -- no sim col
```

**Mock uses clearly-marked placeholder text.** Each pair is labeled "CANNOT COMPLY" with an explanation of what's missing. Visual design (sim bar vs 0.85 threshold line) is prototyped.

**To make this real:** the pipeline would need to log rejections (sim in [0.786, 0.815) range) or add a `similarity REAL` column to `claim_variants`. A one-time extraction script could re-run BGE on known claim pairs and write the output.

---

## Section C — Absorption Integrity Strip

**Real data from demo.db for claim 2799:**

| Field | Value |
|-------|-------|
| Text | "On Tuesday, the U.S. and Israel launched airstrikes against Iran." |
| State | CONSENSUS_ABSORBED |
| Convergence | CROSS_SOURCE_CONVERGENT |
| Sources | reuters.com (T1), theguardian.com (T1) |
| Cluster | 966 |
| Pool sources (T1+T2 in cluster 966) | AP News (T1), Reuters (T1), The Guardian (T1) — 3 total |
| Absorption math | 2/3 = 66.7% ≥ 65% geopolitics threshold |

**Verbatim query output:**

```
$ SELECT * FROM claims WHERE id = 2799
2799|940|966|On Tuesday, the U.S. and Israel launched airstrikes against Iran.|CONSENSUS_ABSORBED|CROSS_SOURCE_CONVERGENT|2026-07-05T18:57:28.402773+00:00|2026-03-10T00:00:00+00:00

$ SELECT s.domain, s.tier FROM claim_sources cs JOIN sources s ON s.id = cs.source_id WHERE cs.claim_id = 2799
reuters.com|1
theguardian.com|1

$ SELECT DISTINCT s.domain, s.tier FROM claims c JOIN claim_sources cs ON cs.claim_id = c.id JOIN sources s ON s.id = cs.source_id WHERE c.cluster_id = 966 AND s.tier <= 2
apnews.com|1
reuters.com|1
theguardian.com|1

$ SELECT COUNT(*) FROM sources WHERE tier IN (1,2)
13
```

**Design-v1.2 vocabulary used throughout:**
- "consensus reality" (not "truth")
- "consensus-absorbed" (terminal state)
- "cross-source convergent" (independent corroboration)
- "outlier claim" (present in few sources)
- No "right/wrong" language anywhere

---

## Deviations from design-tokens.md

| Token doc says | Current code (post-UX3 + human tweaks) | Carried over? |
|---------------|----------------------------------------|---------------|
| Body: 16px (1rem) | 1.1rem base per UX3 rebase (index.css:189) | YES — mock uses `font-size: 1.1rem` on `:root` |
| h1: 32px (2rem) | 2rem (unchanged) | Unchanged |
| h2: 18.4px (1.15rem) | 1.15rem (unchanged) | Unchanged |
| Body color: `var(--text)` | Current Sources.tsx uses `var(--nn-text-dim)` for subtitle text | YES — mock matches current dim text |
| Cards: radius 12px, pad 20-24px | Production cards use radius 14px | YES — mock uses 14px |
| Legend layout not defined | Unified color+shapes block, 0.82rem per X3 | YES — mock uses unified layout |
| Intro strip layout not defined | Two-column with pipe divider per UX2 human direction | YES — mock matches |
| Badges: 0.66rem, 10% opacity bg | 0.66rem, 12% opacity (slightly more visible) | YES — mock uses 12% |
| Nav: 52px, sticky | 52px, sticky (unchanged) | Unchanged |
| Footer: 0.7rem, letter-spacing 0.04em | Unchanged | Unchanged |

---

## Bounds Compliance

| Rule | Met? |
|------|------|
| Read-only DB access | YES — all queries SELECT only |
| Query output pasted verbatim | YES — section C queries shown |
| Copy from design-v1.2 vocabulary | YES — consensus reality, absorbed, outlier, convergent |
| No app code changes (src/, app/, pipeline/) | YES — static HTML only |
| No existing mock changes | YES — new file in docs/mocks/ |
| No commits | YES — uncommitted |

---

## ROUND OBJECTIVE

**One static HTML mock for human browser review, A/B/C sections, DB-grounded.** CANNOT COMPLY on section B (near-miss pairs — similarity scores not stored). Section A uses real layout/copy from current app. Section C uses real claim 2799 data. No code changes. No commits.

**ROUND OBJECTIVE MET:** YES (with CANNOT COMPLY on B, documented)
