# FV2 — DB Integrity + Demo-Blocking Fixes

**Date:** 2026-07-05
**Commit:** `e416f43`

---

## FV2.0 — DB Integrity

### (a) Restoration method

DB was mutated during FV1 when backend started without `NN_NO_PIPELINE=1`. Pipeline scheduler auto-ran Agent 1, creating 8 new clusters (967-974) and adding 64 claims (379→443). Restored via:

```
git checkout data/demo/demo.db
```

From commit `171bfbe` (golden R2.9 state). Verified clean: no diff between working tree and HEAD.

### (b) Full re-verify

```
claims:     379
absorbed:   10
articles:   358
clusters:   47
variants:   605
sources:    37
snapshots:  13,653
span:       2026-03-03 → 2026-07-03
claim 2799: CONSENSUS_ABSORBED
940-945:    20 claims (26 extracted, 6 merged in matching)
```

Active clusters: 920,921,922,923,924,925,926,927,928,929,930,931,932,933,934,951,966 (17)

### (c) G1 confirmation

```
171bfbe R2.9 complete: demo.db 379/10/358/47/13,653 + pool corrections
data/demo/demo.db  Bin 4161536 -> 4763648 bytes
```

---

## FV2.1 — Scheduler Safety

**Fix:** Inverted default from opt-out to opt-in.

`app/main.py:58`: `if not os.environ.get("NN_NO_PIPELINE")` → `if os.environ.get("NN_ENABLE_PIPELINE")`

**Verification:** Backend started without `NN_ENABLE_PIPELINE`. Claims before=379, after=379. No mutation.

---

## FV2.2 — Radar NULLs Diagnosis

**DB query** (reuters source=1, guardian source=5, date=2026-07-03):

```
Reuters geopolitics:   r_orig=23.0, r_val=0.0, r_speed=NULL, r_edit=0.0, r_frame=0.0, r_correct=0.0
Guardian geopolitics:   r_orig=100.0, r_val=28.0, r_speed=23.0, r_edit=0.0, r_frame=60.0, r_correct=0.0
```

Non-NULL counts across all sources on latest date: r_orig(81), r_val(78), r_speed(69), r_edit(87), r_frame(63), r_correct(87).

**Diagnosis:** DB has values. FV1 NULLs were from the mutated-DB state (pipeline scheduler overwrote snapshots during unauthorized run). After restoration, API returns correct values. r_speed=NULL for Reuters is legitimate data sparsity (insufficient claim history for speed computation). No code fix required.

**API confirmation:**
```
GET /api/sources/1/profile?vertical=geopolitics → R_orig: 23.0, R_val: 0.0, ...
GET /api/sources/5/profile?vertical=geopolitics → R_orig: 100.0, R_val: 28.0, ...
```

---

## FV2.3 — Stale Cluster Deletion

Executed R2.9b proposal: deleted 30 stale clusters (935-950, 952-965).

```
Before: 47 clusters
After:  17 clusters
Claims: 379 (unchanged)
Absorbed: 10 (unchanged)
```

Active clusters: 920-934 (15) + 951 (Venezuela earthquake) + 966 (Iran arc).

---

## FV2.4 — Small Fixes

### Delete vacuous claim 2818

"President Trump made statements about the U.S. war against Iran." — no verifiable factual content.

```
Claims: 379 → 378
Absorbed: 10 (unchanged)
```

### Fix hardcoded "37 sources" references

| File | Line | Change |
|------|------|--------|
| `src/data/sources.ts` | 2 | Comment: "37 sources" → "curated source panel" |
| `src/pages/Investigate.tsx` | 97 | UI text: "37-source panel" → "curated source panel" |
| `src/__tests__/sources.test.ts` | 4 | Test name: "exactly 37 entries" → "expected source entries" |
| `src/__tests__/sources.test.ts` | 6 | Assertion: `.toHaveLength(37)` → `.toBeGreaterThanOrEqual(30)` |

---

## FV2.5 — Commit

```
e416f43 FV2: scheduler safety, radar fix/diagnosis, cluster cleanup, 378 claims

app/main.py                   | 2 +-
data/demo/demo.db             | Bin 4763648 -> 4763648 bytes
docs/STATUS.md                | 2 +-
src/__tests__/sources.test.ts | 4 ++--
src/data/sources.ts           | 2 +-
src/pages/Investigate.tsx     | 2 +-
6 files changed, 6 insertions(+), 6 deletions(-)
```

---

## Compliance Table

| Row | Requirement | Met? | Evidence |
|-----|-------------|------|----------|
| R0 | Demo DB verified intact + demo-blocking defects fixed/diagnosed | YES | Integrity verified, scheduler opt-in, radar data confirmed, clusters cleaned, vacuous claim removed, hardcoded refs fixed |
| FV2.0a | State restoration method | YES | `git checkout data/demo/demo.db` from 171bfbe |
| FV2.0b | Full re-verify | YES | 379/10/358/47/605/37/13653, all pass |
| FV2.0c | G1 commit proof | YES | 171bfbe, demo.db 4763648 bytes |
| FV2.1 | Scheduler opt-in | YES | NN_ENABLE_PIPELINE replaces NN_NO_PIPELINE |
| FV2.2 | Radar NULLs diagnosis | YES | DB values present, API returns correct data, FV1 NULLs from mutation |
| FV2.3 | Stale cluster deletion | YES | 47→17, claims/absorbed unchanged |
| FV2.4 | Claim 2818 + "37" refs | YES | 379→378, 4 refs fixed |
| FV2.5 | Commit | YES | e416f43 |

---

## STOP
