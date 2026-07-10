# Round 008 — GEMMA-2R: Upgrade README Gemma section to batch-run evidence

**Date:** 2026-07-10
**Phase:** GEMMA-2R
**Fingerprint:** 378|10|358|17|13653 (unchanged, DB untouched)
**Scope:** README.md only

---

## ECHO

Work order: GEMMA-2R — upgrade README.md Gemma section from single-article evidence to batch-run evidence (61-article Venezuela cluster, 268 claims). Read-only, no API calls, no git ops.

---

## Compliance Table

| Task | Status | Evidence |
|---|---|---|
| **R1** Verify numbers from batch_results.json | **YES** | `python3 -c` recompute: 61 articles, 36 parse_ok, 268 claims (sum n_claims), 268 claims (len arrays), tie-out PASS |
| **R2** Replace Gemma paragraph in README.md | **YES** | `patch` applied at README.md:46-50. Old: "one demo article... token usage — is in". New: "full 61-article Venezuela story cluster... 268 structured claims... batch summary — is in" |
| **R3** git diff + final section | **YES** | `git diff README.md`: +7/-4. Final section pasted below. |
| **No git ops** | **YES** | No add/commit/push |
| **No API calls** | **YES** | Deployment idle/deleted |
| **Scope wall** | **YES** | Only README.md touched |

---

## R1 — Raw evidence

```
$ python3 -c "
import json
with open('docs/evidence/gemma/batch_results.json') as f:
    results = json.load(f)
total = len(results)
parse_ok = sum(1 for r in results if r['parse_ok'])
claims_sum = sum(r['n_claims'] for r in results)
claims_len = sum(len(r['claims']) for r in results)
print(f'articles: {total}')
print(f'parse_ok: {parse_ok}')
print(f'claims (sum n_claims): {claims_sum}')
print(f'claims (len arrays):  {claims_len}')
print(f'tie-out: {\"PASS\" if claims_sum == claims_len else \"FAIL\"}')
"
articles: 61
parse_ok: 36
claims (sum n_claims): 268
claims (len arrays):  268
tie-out: PASS
```

---

## R3 — git diff

```
README.md | 11 +++++++----
 1 file changed, 7 insertions(+), 4 deletions(-)

@@ -43,10 +43,13 @@
 -visible in the Pipeline page dropdowns). In a verified test run, Gemma
 -executed Narrative Nexus's Agent 2 claim-extraction prompt on a demo
 -article and returned valid structured claims. Full evidence — model
 -string, smoke test, extraction output, and token usage — is in
 +visible in the Pipeline page dropdowns). In verified test runs, Gemma
 +executed Narrative Nexus's Agent 2 claim-extraction prompt across the
 +full 61-article Venezuela story cluster, returning 268 structured claims
 +(36 of 61 articles parsed cleanly — per-article results and token usage
 +in [`docs/evidence/gemma/batch_results.json`](docs/evidence/gemma/batch_results.json)).
 +Full evidence — model string, smoke test, extraction output, and batch
 +summary — is in
  [`docs/evidence/gemma/README.md`](docs/evidence/gemma/README.md).
  Gemma is an optional provider; the shipped database was built with the
  default Fireworks/DeepSeek configuration.
```

---

## R3 — Final section as it reads

```
**Gemma 4 E4B** (deployed on-demand via Fireworks AI) is integrated as a
selectable LLM provider (`fireworks-gemma` in `config/providers.json`,
visible in the Pipeline page dropdowns). In verified test runs, Gemma
executed Narrative Nexus's Agent 2 claim-extraction prompt across the
full 61-article Venezuela story cluster, returning 268 structured claims
(36 of 61 articles parsed cleanly — per-article results and token usage
in [`docs/evidence/gemma/batch_results.json`](docs/evidence/gemma/batch_results.json)).
Full evidence — model string, smoke test, extraction output, and batch
summary — is in
[`docs/evidence/gemma/README.md`](docs/evidence/gemma/README.md).
Gemma is an optional provider; the shipped database was built with the
default Fireworks/DeepSeek configuration.
```

---

## PROPOSED

No further action. README.md Gemma section now references batch-run evidence.
