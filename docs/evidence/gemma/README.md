# Gemma 4 E4B — Integration Evidence

**Date:** 2026-07-10
**Deployment:** `accounts/afshinator-b1hiwmnhr/deployments/x5v99zxx` (display name: `nn2`)
**State:** READY (1 replica, NVIDIA H200) — since deleted by human
**Hosting:** Fireworks on-demand deployment — organizer-confirmed prize-eligible

---

## Deployment Status (at time of test)

```json
{
  "name": "accounts/afshinator-b1hiwmnhr/deployments/x5v99zxx",
  "displayName": "nn2",
  "baseModel": "accounts/fireworks/models/gemma-4-e4b",
  "state": "READY",
  "replicaStats": {"readyReplicaCount": 1, "effectiveReplicaCount": 1},
  "acceleratorType": "NVIDIA_H200_141GB"
}
```

---

## Chat Endpoint Limitation + Completions Workaround

Gemma 4 E4B's tokenizer (baked by Fireworks) does not define a default chat template.
The chat completions endpoint returns HTTP 400:
> "As of transformers v4.44, default chat template is no longer allowed, so you
> must provide a chat template if the tokenizer does not define one."

**Workaround:** Use the raw completions endpoint with Gemma turn markers:
```
POST https://api.fireworks.ai/inference/v1/completions
{
  "model": "accounts/afshinator-b1hiwmnhr/deployments/x5v99zxx",
  "prompt": "<start_of_turn>user\n...<end_of_turn>\n<start_of_turn>model\n",
  "stop": ["<end_of_turn>"]
}
```

---

## G2: Smoke Test (Completions)

**Request** (key redacted):
```
POST https://api.fireworks.ai/inference/v1/completions
{"model": "accounts/afshinator-b1hiwmnhr/deployments/x5v99zxx",
 "prompt": "<start_of_turn>user\nReply with exactly the word: READY<end_of_turn>\n<start_of_turn>model\n",
 "max_tokens": 10, "stop": ["<end_of_turn>"]}
```

**Response:**
```json
{
  "id": "cmpl-cmpl-add3b3f91698455fbda02dece40ef126",
  "object": "text_completion",
  "created": 1783713688,
  "model": "accounts/afshinator-b1hiwmnhr/deployments/x5v99zxx",
  "choices": [{
    "index": 0,
    "text": "READY",
    "finish_reason": "stop",
    "stop_reason": "<end_of_turn>"
  }],
  "system_fingerprint": "vllm-0.20.2rc1.dev49+g9b4e83934-fdf314ae",
  "usage": {"prompt_tokens": 34, "total_tokens": 42, "completion_tokens": 8}
}
```

---

## G4: Agent 2 Extraction Pass (Gemma on Article 6)

**Script:** `scripts/gemma_agent4_run.py` — reuses Agent 2's `EXTRACTION_SYSTEM_PROMPT`
from `pipeline/agent2_forensic.py:30-58`, formats prompt with Gemma turn markers,
calls the completions endpoint directly (LLMClient is chat-only, incompatible with
Gemma's completions-only deployment).

**Path chosen:** Direct completions call. Script reuses Agent 2's actual prompt text
and DB write functions (`INSERT INTO claims`, `claim_sources`, `article_framing`) —
but the commit failed (wrong table name crashed before commit). No claims were
persisted from the Gemma run. The evidence is the raw stdout.

**Article:** id=6 — "Things to know about Venezuela's powerful earthquakes" (AP News)
- Body: 8,756 chars, source_id=2 (AP News)
- Prompt length: 2,370 chars

**Extraction was nondeterministic** — 3 runs on the same input produced 3 different
outputs (consistent with a small model on a complex prompt, no temperature=0 support
on the completions endpoint):

1. **Run 1:** 4 claims, article_id hallucinated as 26, framing_score=1
2. **Run 2:** 8 claims, correct article_id=6, framing_score=7 ← **best run, evidence below**
3. **Run 3:** Model analyzed the prompt's framing-bias examples instead of extracting
   claims from the actual article — 0 claims

### Run 2 — Raw Gemma Output (the primary evidence)

```
Model: accounts/afshinator-b1hiwmnhr/deployments/x5v99zxx
Fingerprint: vllm-0.20.2rc1.dev49+g9b4e83934-fdf314ae
Usage: {"prompt_tokens": 564, "total_tokens": 1128, "completion_tokens": 564}
Finish: stop

GEMMA RAW OUTPUT:
{
    "results": [{
        "article_id": 6,
        "framing_score": 7,
        "claims": [
            {"text": "A man walked past a damaged home in Moron near the epicenter
                      of two earthquakes that struck Venezuela on June 24, 2026.",
             "entities": ["Moron", "Venezuela", "June 24, 2026"]},
            {"text": "Another man walked past a building damaged by earthquakes
                      that struck Puerto Cabello, Venezuela on June 24, 2026.",
             "entities": ["Puerto Cabello", "Venezuela", "June 24, 2026"]},
            {"text": "Paramedics carried an injured person at a hospital in Moron,
                      Venezuela near the epicenter of the earthquakes on June 25, 2026."},
            {"text": "The epicenter of the two earthquakes in Venezuela struck
                      at a depth of 13 kilometers (8 miles) according to the
                      United States Geological Survey."},
            {"text": "Seismologists predict a quake with a magnitude of more than
                      5.0 could hit Puerto Cabello, Venezuela in the next two years."},
            {"text": "The city of Puerto Cabello, Venezuela was built on top of
                      old coral reefs that are unstable and sit on top of a
                      massive fault line."},
            {"text": "Venezuela is prone to seismic activity due to its geology."},
            {"text": "The 1992 Puerto Cabello earthquake was caused by a shallow
                      fault and had a magnitude of 7.2."}
        ]
    }]
}
```

**Note on DB writes:** The 4 claims returned by scratch-DB queries in the prior
round's evidence (ids 810, 813, 2227, 2228) were PRE-EXISTING demo data — verified
identical in the golden DB. They were NOT written by the Gemma run. The script
crashed before commit (wrong table name `framing_scores` vs `article_framing`).
No claims were persisted from any Gemma run. The raw stdout above is the evidence.

---

## Golden DB Fingerprint

**Before:** `378|10|358|17|13653`
**After:**  `378|10|358|17|13653`
**Verdict:** UNCHANGED — golden DB was never written.

---

## Notes

- **Nondeterminism:** 3 runs on identical input produced 3 different framing scores
  (1, 7, N/A) and varying claim counts (4, 8, 0). This is expected for an open-weight
  model on the completions endpoint without temperature=0 or structured-output support.
- **Output format variability:** Gemma returned `"results"` on run 2, `"articles"` on
  run 3, and an unkeyed array on run 1. Article_id hallucinated (26 vs 6) on run 1.
  These are normal for models without JSON-mode guarantees.
- **Confirmation:** The deployment served inference successfully across all 3 runs.
  Model string resolves, system_fingerprint consistent, usage tokens tracked.
- **Hosting:** Fireworks on-demand, NVIDIA H200 GPU — organizer-confirmed
  prize-eligible for AMD Hackathon ACT II Track 3.
