# 003 — GEMMA-1F: Final verification (BLOCKED at F3)

**Round:** GEMMA-1F (Work Order)
**Date:** 2026-07-10
**Status:** BLOCKED at F3 STOP GATE B — Gemma deployment requires chat template

---

## F1 — Golden Fingerprint (before)

**ECHO:** Baseline fingerprint check.

```
sqlite3 "file:data/demo/demo.db?mode=ro" "SELECT ..."
378|10|358|17|13653
```

PASS — matches expected.

---

## F2 — Deployment Status

**ECHO:** Confirm deployment READY + current ID.

```
scripts/gemma_check.sh → nn2 READY
```

**Full API response (key fields):**
```
deployment_id:    x5v99zxx                    (changed from weygkcy6)
displayName:      nn2                         (was nn1)
state:            READY
baseModel:        accounts/fireworks/models/gemma-4-e4b
readyReplicaCount: 1
MODEL_STRING:     accounts/fireworks/models/gemma-4-e4b#accounts/afshinator-b1hiwmnhr/deployments/x5v99zxx
```

Deployment ID CHANGED from `weygkcy6` to `x5v99zxx` (human redeployed). State is READY, 1 replica.

---

## F3 — Smoke Test

**ECHO:** Single chat-completion call, prompt "READY", max_tokens 10.

### Attempt 1: deployment path as model
```
Model:     accounts/afshinator-b1hiwmnhr/deployments/x5v99zxx
Request:   POST https://api.fireworks.ai/inference/v1/chat/completions
           {"model": "...deployments/x5v99zxx", "messages": [{"role":"user","content":"Reply with exactly the word: READY"}], "max_tokens": 10}
```

**Response:**
```json
{
  "error": {
    "message": "As of transformers v4.44, default chat template is no longer allowed, so you must provide a chat template if the tokenizer does not define one.",
    "type": "BadRequestError",
    "param": null,
    "code": 400
  }
}
```

### Attempt 2: baseModel#deployment format
```
Model:     accounts/fireworks/models/gemma-4-e4b#accounts/afshinator-b1hiwmnhr/deployments/x5v99zxx
Request:   POST https://api.fireworks.ai/inference/v1/chat/completions
           (same payload, different model string)
```

**Response:** Identical HTTP 400 — same chat template error.

### STOP GATE B — both attempts failed

Same error both times. The model is deployed and reachable, but the deployment lacks a chat template configuration required by transformers v4.44+.

**Root cause:** Gemma 4 E4B was baked with a tokenizer that doesn't define a default chat template. Fireworks on-demand deployments need the chat template explicitly configured in the deployment shape or passed via the API. This is a deployment-level configuration issue.

---

## F4 — Sync providers.json

**NOT DONE** — deployment ID changed (weygkcy6 → x5v99zxx) but smoke test failed. Not syncing until model string is verified working.

## F5 — Agent 2 Extraction Pass

**NOT DONE** — blocked on F3 gate.

## F6 — Evidence File

**NOT DONE** — blocked on F3 gate. Partial content ready for when smoke test passes.

---

## Compliance Table

| task/constraint | met EXACTLY? | evidence pointer |
|---|---|---|
| F1 — Golden fingerprint (before) | YES | `378\|10\|358\|17\|13653` |
| F2 — Deployment READY + ID | YES | `x5v99zxx`, `nn2`, state=READY, 1 replica |
| F3 — Smoke test | CANNOT COMPLY | HTTP 400: chat template required (2 attempts, same error) |
| F4 — Sync providers.json | NOT DONE | blocked on F3 — model string unverified |
| F5 — Agent 2 extraction | NOT DONE | blocked on F3 |
| F6 — Evidence file | NOT DONE | blocked on F3 |
| HC1 — Golden DB read-only | YES | fingerprint unchanged; read-only mode |
| HC2 — Don't change defaults | YES | not touched |
| HC3 — No scraper | YES | not triggered |
| HC4 — No git operations | YES | no add/commit/push |
| HC5 — Scope wall | YES | nothing beyond F1-F3 executed |

---

## Proposed Fix

The human needs to add a chat template to the deployment. Fireworks docs suggest one of:

1. **In the Fireworks dashboard:** Edit the deployment and add a chat template in the deployment shape configuration. The standard Gemma chat template is:
   ```
   {{ bos_token }}{% for message in messages %}{% if message['role'] == 'user' %}{{ '<start_of_turn>user\n' + message['content'] + '<end_of_turn>\n<start_of_turn>model\n' }}{% elif message['role'] == 'system' %}{{ '<start_of_turn>system\n' + message['content'] + '<end_of_turn>\n' }}{% endif %}{% endfor %}
   ```

2. **Alternative:** Redeploy with a deployment shape that includes the chat template baked in, or use a different deployment shape that already has it configured.

3. **Server-side workaround (if available):** Some Fireworks endpoints accept a `chat_template` parameter in the request body — but this requires API support.

After fixing, re-run `scripts/gemma_check.sh` to get the new deployment ID (may change on redeploy), then re-issue GEMMA-1F from F3.
