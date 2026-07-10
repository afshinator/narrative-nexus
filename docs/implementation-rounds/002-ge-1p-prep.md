# 002 — GEMMA-1P: Prep tasks (deployment CREATING → READY)

**Round:** GEMMA-1P (Work Order)
**Date:** 2026-07-10
**Status:** COMPLETE — P1, P2, P3 all done

---

## P1 — Poll Script

**ECHO:** Write `scripts/gemma_check.sh`, run once, paste output.

**Script:** `scripts/gemma_check.sh` — curls deployments API, prints displayName + state.

**Run output:**
```
nn1 READY
```

**Deployment details (from API):**
```json
{
  "name": "accounts/afshinator-b1hiwmnhr/deployments/weygkcy6",
  "displayName": "nn1",
  "baseModel": "accounts/fireworks/models/gemma-4-e4b",
  "state": "READY",
  "replicaStats": {"readyReplicaCount": 1, "effectiveReplicaCount": 1},
  "createTime": "2026-07-10T19:16:09.655062Z"
}
```

---

## P2 — Provider Entry

**ECHO:** Append gemma entry to `llm` array, don't touch defaults.

**Diff:**
```diff
 config/providers.json | 6 ++++++
 1 file changed, 6 insertions(+)
@@ -50,6 +50,12 @@
+      },
+      {
+        "id": "fireworks-gemma",
+        "name": "Fireworks AI (Gemma 4 E4B)",
+        "model": "accounts/fireworks/models/gemma-4-e4b#accounts/afshinator-b1hiwmnhr/deployments/weygkcy6",
+        "amd": true
       }
     ]
   },
```

**JSON validation:** `python -c "import json;json.load(open('config/providers.json'))"` → valid.

**Note:** Model string is UNVERIFIED until smoke test (T3) passes.

---

## P3 — Scratch DB + Agent 4 Recon

**ECHO:** Copy DB, recon Agent 4, write invocation script, don't run, re-check fingerprint.

### Step 1: Scratch DB copy
```
cp data/demo/demo.db /tmp/gemma-scratch.db

ls -la:
-rw-rw-r-- 1 afshin afshin 5570560 data/demo/demo.db
-rw-r--r-- 1 afshin afshin 5570560 /tmp/gemma-scratch.db

sha256sum (MATCH):
10b56d24dab46c23ca04954a7e492ded29fc4ed7dd2c744aca7934b52008a9e7  data/demo/demo.db
10b56d24dab46c23ca04954a7e492ded29fc4ed7dd2c744aca7934b52008a9e7  /tmp/gemma-scratch.db
```

### Step 2: Agent 4 recon

**File:** `pipeline/agent4_silent.py`
**Class:** `SilentAuditorAgent`
**Entry point:** `SilentAuditorAgent(db_path=str)` → `await agent.run()` → `dict[str, int]`
**LLM usage: NONE** — line 50: "No LLM, no GPU — pure Python text diffing." Uses `difflib.SequenceMatcher`.
**Provider selection:** Does not select an LLM provider — no LLM calls at all.

**Conclusion:** Agent 4 is NOT suitable for a Gemma inference test. T5 will need the Agent 2 fallback.

**Agent 2 entry point (for T5 fallback):**
- Class: `ForensicExtractionAgent` in `pipeline/agent2_forensic.py`
- Constructor: `ForensicExtractionAgent(db_path=str, llm_provider=dict, api_key=str)`
- Run: `await agent.run(article_map={article_id: 0})` — extracts claims from article via LLM

**Test article:** id=6 — AP News, Venezuela earthquake — has body + claims, suitable for extraction.

**Note:** `LLMClient` resolves base URL via `PROVIDER_BASE_URLS[provider["id"]]`. The script uses `id: "fireworks"` to hit the Fireworks API, with `model` set to the Gemma deployment string.

**Invocation script:** `scripts/gemma_agent4_run.py` — written, syntax OK, NOT RUN.

### Step 3: Golden fingerprint re-check
```
sqlite3 "file:data/demo/demo.db?mode=ro" "SELECT ..."
378|10|358|17|13653
```
Unchanged — PASS.

---

## Compliance Table

| task/constraint | met EXACTLY? | evidence pointer |
|---|---|---|
| P1 — Poll script + run | YES | `nn1 READY` output; deployment state=READY, readyReplicaCount=1 |
| P2 — Add provider entry | YES | `git diff config/providers.json` shows +6 lines; JSON valid; model string UNVERIFIED |
| P3.1 — Scratch DB copy | YES | sha256sum match: `10b56d2...a9e7` both files |
| P3.2 — Agent 4 recon | YES | `pipeline/agent4_silent.py` — no LLM; Agent 2 fallback entry point documented; invocation script written |
| P3.3 — Golden fingerprint re-check | YES | `378\|10\|358\|17\|13653` unchanged |
| HC1 — Golden DB read-only | YES | fingerprint unchanged; read-only mode used throughout |
| HC2 — Don't change defaults | YES | defaults block untouched; only `llm` array appended |
| HC3 — Don't re-run pipeline | YES | not triggered |
| HC4 — API key from env | YES | key from `~/.hermes/.env`, never printed |
| HC5 — Scope wall P1-P3 | YES | nothing beyond P1-P3 executed |
