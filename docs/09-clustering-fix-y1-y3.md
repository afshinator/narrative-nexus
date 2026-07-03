# Phase 2 Clustering Fix — Y1-Y3 Results

**Date:** 2026-07-02
**Verdict:** Input fix improved same-topic similarity but did NOT improve topic separation. Per Y3c: STOP and report.

---

## Y1 — CLEANER ✅

`pipeline/cleaner.py` — 127 lines. Strips AP Photo caption lines, inline credits, location tags, and producer credits. Safety cap at 30% removal.

**Tests: 9/9 pass**
- AP photo credit line removed entirely
- Reuters credit stripped from content line
- Location tag "WASHINGTON (AP) —" stripped
- "Left, shakes hands..." NOT stripped from prose
- "Produced by" mid-sentence kept
- No-boilerplate article passes through unchanged
- 1000-char window respected
- Photo captions removed from multi-line input
- Empty body returns title only

---

## Y2 — WIRED INTO AGENT 1 ✅

**Y2a:** `pipeline/agent1_intake.py:60-63` — now uses `get_embedding_input(title, body, max_body_chars=1000)` instead of raw `f"{title} {body[:200]}"`.

**Y2b:** Embeddings cache invalidated — 2,028 entries deleted from `/tmp/phase2.db` and `data/nn.db`.

**Y2c:** Nomic retained as embedding model.

---

## Y3 — VERIFICATION ❌ FAILED

**Input comparison (Article 157 — Anthropic, the worst case):**

| | Text |
|---|---|
| Old (200 chars, raw) | "Anthropic co-founder and President Daniela Amodei, left, shakes hands with Snowflake CEO Sridhar Ramaswamy during the keynote presentaton at Snowflake Summit 26 Monday, June 1, 2026, in San Francisco." |
| New (1000 chars, cleaned) | "AI giant Anthropic said Friday it has taken its latest artificial intelligence models, known as Fable 5 and Mythos 5, offline to comply with a directive from the Trump administration to prevent their use by foreign nationals. The export controls mark the U.S. government's most significant step to date to restrict access to the most advanced AI models..." |

The cleaner correctly removed the handshake photo caption. The model now sees real content.

**8x8 cosine similarity matrix (nomic, cleaned input, 1000-char window):**

```
                    US polit Middle E European  Tech/AI   Sports Economic Natural  Science/
US politics            --     0.5384   0.5035   0.5698   0.4650   0.5324   0.5195   0.5774
Middle East          0.5384      --     0.5475   0.5686   0.4569   0.6439   0.5986   0.5284
European weather     0.5035   0.5475      --     0.5324   0.5610   0.5578   0.6268   0.5559
Tech/AI              0.5698   0.5686   0.5324      --     0.4520   0.6274   0.5026   0.8801
Sports               0.4650   0.4569   0.5610   0.4520      --     0.4608   0.5175   0.5066
Economics            0.5324   0.6439   0.5578   0.6274   0.4608      --     0.5758   0.6020
Natural disaster     0.5195   0.5986   0.6268   0.5026   0.5175   0.5758      --     0.4830
Science/Tech         0.5774   0.5284   0.5559   0.8801   0.5066   0.6020   0.4830      --
```

**Off-diagonal: mean=0.5533, min=0.4520, max=0.8801**

**Comparison to X2 (old input):**

| Metric | X2 (200 chars) | Y3 (cleaned 1000) | Delta |
|--------|---------------|-------------------|-------|
| Mean off-diagonal | 0.5415 | 0.5533 | +0.012 WORSE |
| Min off-diagonal | 0.4624 | 0.4520 | −0.010 |
| Max off-diagonal | 0.8222 | 0.8801 | +0.058 |
| Same-topic (Anthropic) | 0.8222 | 0.8801 | +0.058 good |
| Venezuela vs Anthropic | 0.4624 | 0.5026 | +0.040 worse |

---

## BOTTLENECK DIAGNOSIS (updated)

The input fix worked mechanically (photo captions removed, content reaches the model) but topic separation did NOT improve. With more text, the nomic model makes articles MORE similar, not less. The mean off-diagonal went up from 0.5415 to 0.5533.

**Hypothesis:** Nomic-ai/nomic-embed-text-v1.5 encodes "journalistic writing style" as a strong signal. More text means more style signal, drowning out topic-specific keywords. The 200-char limit was accidentally helping by capturing only the most topic-specific opening sentence.

**The bottleneck is the embedding model, not the input.** Clean input with nomic still can't separate news topics well enough for clustering.

**Next step per Y3c:** STOPPED. Need decision: switch to BGE, try lower eps values with nomic, or consider a different approach.
