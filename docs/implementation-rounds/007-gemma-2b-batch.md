# Round 007 — GEMMA-2B: Batch extraction over Venezuela cluster

**Date:** 2026-07-10
**Phase:** GEMMA-2B
**Fingerprint:** 378|10|358|17|13653 → 378|10|358|17|13653 (UNCHANGED)
**Model:** accounts/afshinator-b1hiwmnhr/deployments/x5v99zxx (nn2)
**Script:** scripts/gemma_batch_extract.py
**Results:** docs/evidence/gemma/batch_results.json

---

## ECHO

Work order: GEMMA-2B — batch extraction over the full Venezuela cluster (61 articles) using Gemma 4 E4B via completions endpoint. Golden DB read-only, no scraper, no git ops, no defaults touched.

---

## Compliance Table

| Task | Status | Evidence |
|---|---|---|
| **B1** Fingerprint (before) | **YES** | `378\|10\|358\|17\|13653` — sqlite3 "file:data/demo/demo.db?mode=ro" SELECT |
| **B2** Deployment + smoke | **YES** | Deployment nn2 at x5v99zxx, state READY, 1 replica. Smoke: text='READY', 34/8/42 tokens, finish=stop. Cold-start: 4 min wait (503 scaling_up → poll → ready=1 → smoke OK). |
| **B3** Venezuela cluster ID | **YES** | Cluster 924 "Venezuela Emergency and Rescue Response", 61 articles, 138 claims, 20 sources. All 61 articles have body > 200 chars. |
| **B4** Batch extraction | **YES** | scripts/gemma_batch_extract.py: 61 articles processed, 36 parse OK, 25 parse failures, 0 API errors. 268 claims, tie-out PASS. Incremental saves to batch_results.json. 1 article truncated (body 8756→6000 chars). |
| **B5** Summarize honestly | **YES** | Re-computed from batch_results.json: 61 articles, 36 parse OK (59%), 25 parse failures (41%), 268 claims, min=0 med=9 max=24, 74,801 prompt + 43,517 completion = 118,318 total tokens. Claims tie-out PASS. Source breakdown: 18 sources, nytimes top at 78 claims. |
| **B6** Evidence + fingerprint (after) | **YES** | docs/evidence/gemma/README.md appended with batch run section. Final fingerprint 378\|10\|358\|17\|13653 — UNCHANGED. |
| **Golden DB read-only** | **YES** | All DB access via sqlite3 "file:data/demo/demo.db?mode=ro" / uri=True. No INSERT/UPDATE/DELETE. Fingerprint unchanged. |
| **Defaults untouched** | **YES** | config/providers.json not read, not written. |
| **No scraper** | **YES** | Scraper never started. |
| **No git ops** | **YES** | No add/commit/push. All changes uncommitted. |
| **Scope wall** | **YES** | Only Venezuela cluster (924) processed. No other clusters, no other tables touched. |

---

## B2 — Deployment + Smoke (raw evidence)

Polling log (condensed):
```
[14:17:35] attempt 1/10: ready=0 desired=1 state=READY
[14:18:36] attempt 2/10: ready=0 desired=1 state=READY
[14:19:36] attempt 3/10: ready=1 desired=0 state=READY
READY: 1 replicas available at 14:19:36
  → Smoke 503 (race condition)
[14:21:30] attempt 1/5: ready=0 desired=1
[14:22:31] attempt 2/5: ready=0 desired=1
[14:23:31] attempt 3/5: ready=1 desired=1
Smoke test at 14:23:31...
SMOKE SUCCESS
model: accounts/afshinator-b1hiwmnhr/deployments/x5v99zxx
text: 'READY'
usage: {"prompt_tokens": 34, "total_tokens": 42, "completion_tokens": 8, "prompt_tokens_details": null}
finish: stop
```

---

## B3 — Venezuela Cluster (raw evidence)

```
$ sqlite3 "file:data/demo/demo.db?mode=ro" "SELECT c.id, c.title, COUNT(DISTINCT cl.article_id) as articles, COUNT(*) as claims FROM clusters c JOIN claims cl ON cl.cluster_id=c.id GROUP BY c.id ORDER BY articles DESC LIMIT 5;"
924|Venezuela Emergency and Rescue Response|61|138

$ sqlite3 "file:data/demo/demo.db?mode=ro" "SELECT COUNT(*), SUM(CASE WHEN length(body)>200 THEN 1 ELSE 0 END) FROM articles WHERE id IN (SELECT DISTINCT article_id FROM claims WHERE cluster_id=924);"
61|61
```

---

## B4 — Batch output (raw evidence)

Log tail from docs/evidence/gemma/batch_run.log:
```
[14:34:14] ==================================================
[14:34:14] BATCH SUMMARY
[14:34:14]   Articles attempted:  61
[14:34:14]   Parse OK:            36
[14:34:14]   Parse failures:      25
[14:34:14]   Total claims (sum):  268
[14:34:14]   Total claims (alt):  268
[14:34:14]   Claims tie-out:      PASS
[14:34:14]   Claim count min:     0
[14:34:14]   Claim count median:  9.0
[14:34:14]   Claim count max:     24
[14:34:14]   Prompt tokens:       74801
[14:34:14]   Completion tokens:   43517
[14:34:14]   Total tokens:        118318
[14:34:14] ==================================================
```

---

## B5 — Honest summary (raw evidence)

```
Articles attempted: 61
Parse OK:          36
Parse failures:    25
API errors:        0
Total claims:      268
Claims tie-out:    PASS (268 vs 268)
Claim count min:   0
Claim count med:   9.0
Claim count max:   24
Prompt tokens:     74801
Completion tokens: 43517
Total tokens:      118318

By source:
  nytimes: 11 articles, 6 OK, 78 claims
  apnews: 8 articles, 4 OK, 12 claims
  theguardian: 7 articles, 5 OK, 55 claims
  bbc: 6 articles, 4 OK, 28 claims
  foxnews: 4 articles, 3 OK, 30 claims
  batimes: 4 articles, 3 OK, 11 claims
  MercoPress: 4 articles, 0 OK, 0 claims
  npr: 2 articles, 0 OK, 0 claims
  cbsnews: 2 articles, 2 OK, 11 claims
  aljazeera: 2 articles, 2 OK, 4 claims
  NHK World: 2 articles, 2 OK, 29 claims
  thehindu: 2 articles, 0 OK, 0 claims
  sputnikglobe: 2 articles, 2 OK, 10 claims
  abcnews: 1 articles, 1 OK, 0 claims
  globaltimes: 1 articles, 0 OK, 0 claims
  france24: 1 articles, 0 OK, 0 claims
  jamaicaobserver: 1 articles, 1 OK, 0 claims
  theintercept: 1 articles, 1 OK, 0 claims
```

---

## B6 — Appended README section

See docs/evidence/gemma/README.md, section "Batch Run — Venezuela Cluster (924)".

Fingerprint after: `378|10|358|17|13653` — UNCHANGED.

---

## PROPOSED

No further action. Batch extraction complete. 268 claims from 36 of 61 articles (59% parse rate).

**REMINDER TO HUMAN: undeploy the Gemma deployment now — it bills while idle.**
