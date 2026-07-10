# 005 — GEMMA-1E: Evidence integrity fix

**Round:** GEMMA-1E (Work Order)
**Date:** 2026-07-10
**Status:** COMPLETE

---

## E1 — Provenance

**Query golden DB:**
```
sqlite3 "file:data/demo/demo.db?mode=ro" "SELECT id, substr(text,1,60) FROM claims WHERE id IN (810,813,2227,2228);"

810|A home in Moron, Venezuela, was damaged.
813|Paramedics carried an injured person at a hospital in Moron,
2227|Moron is near the epicenter of the earthquakes.
2228|A man walked past a damaged home in Moron on June 25, 2026.
```

```
sqlite3 "file:data/demo/demo.db?mode=ro" "SELECT * FROM article_framing WHERE article_id=6;"
6|1.0|0.0|-0.978|2026-07-04 21:39:16
```

**Verdict: All 4 claims (810, 813, 2227, 2228) and the article_framing row are PRE-EXISTING demo data.** Identical rows exist in the golden DB (which was never written by any Gemma run). The scratch DB `cp` copy carried them over. Prior round G4.3/G4.4 incorrectly attributed them to the Gemma extraction run.

---

## E2 — Corrected Evidence File

**File:** `docs/evidence/gemma/README.md` rewritten.

Key corrections:
- Scratch-DB rows claim REMOVED — they were pre-existing demo data
- Run 2 raw stdout promoted as primary evidence (8 valid claims, article_id=6, framing_score=7, token usage 564/564/1128)
- Nondeterminism disclosed: 3 runs, 3 different outputs (4 claims wrong id / 8 claims correct / 0 claims)
- Honest line added: "No claims were persisted from any Gemma run. The raw stdout is the evidence."
- No DB write evidence claimed — script crashed before commit

---

## Prior Round Correction

Round 004's G4.3 and G4.4 compliance rows (asserting "4 claims committed to scratch DB" as Gemma evidence) were overstated. The claims were pre-existing demo data, not Gemma-written. Corrected in this round's evidence file. The actual Gemma evidence — Run 2's raw stdout with 8 extracted claims and token usage — stands.

---

## Compliance Table

| task/constraint | met EXACTLY? | evidence pointer |
|---|---|---|
| E1 — Determine provenance | YES | Claims 810,813,2227,2228 exist in golden DB → pre-existing demo data |
| E2 — Correct evidence file | YES | `docs/evidence/gemma/README.md` rewritten (6654 bytes) |
| HC1 — Golden DB read-only | YES | read-only queries only |
| HC2 — No scraper | YES | not triggered |
| HC3 — No git operations | YES | no add/commit/push |
| HC4 — No API calls | YES | zero calls to Gemma/Fireworks |
| HC5 — Scope wall | YES | nothing beyond E1-E2 executed |

---

## Prior Round Overstatement

| round | row | claimed | actual |
|---|---|---|---|
| 004 | G4.3 | "4 claims committed to scratch DB" | Claims were pre-existing demo data, not Gemma-written |
| 004 | G4.4 | Scratch DB rows as Gemma evidence | Same rows exist in golden DB (never touched by Gemma) |
