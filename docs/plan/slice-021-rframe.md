# Slice 021 — R_frame Framing Scorers

**Status:** Plan  
**Date:** 2026-06-30  
**Depends on:** Agent 2 (forensic extraction), LLM client (provider-agnostic), article bodies in DB

---

## Scope

Build 3 framing scorers, store per-article scores, run backfill on existing articles. Do NOT wire into snapshot pipeline yet — user compares results first, then we pick which scorer(s) to use for R_frame computation.

---

## Files to create

1. `pipeline/framing.py` — 3 scoring functions + backfill orchestrator
2. `pipeline/test_framing.py` — unit tests for lexical + sentiment (LLM mocked)
3. `scripts/backfill_framing.py` — standalone script to score all existing articles
4. `db/framing.py` — DB helpers (create table, insert/read scores)

## Files to modify

5. `pipeline/agent2_forensic.py` — call framing scorers for new articles during claim extraction
6. `db/schema.py` — add `article_framing` table to schema init

---

## Architecture

### New table: `article_framing`

```sql
CREATE TABLE IF NOT EXISTS article_framing (
    article_id INTEGER PRIMARY KEY REFERENCES articles(id),
    llm_score REAL,         -- LLM 1-10 score (NULL if not computed)
    lexical_score REAL,     -- adjective/hedge density (0-1)
    sentiment_score REAL,   -- VADER compound (-1 to +1)
    computed_at TEXT NOT NULL DEFAULT (datetime('now'))
);
```

### Score definitions

**lexical_score (0-1):** Adjective density + hedge word density. Counts words from hardcoded adjective and hedge word lists as fraction of total words. Higher = more loaded/hedged language. Word-list avoids NLTK dependency.

**sentiment_score (-1 to +1):** VADER compound polarity. Only needs `vaderSentiment` (pip install, no model download). -1 = extremely negative, +1 = extremely positive. News articles cluster around 0, but polarization matters — stddev across articles is the interesting signal.

**llm_score (1-10):** Short LLM prompt asking for editorial bias rating. Uses existing Agent 2 LLM provider. Returns `{"score": <1-10>}`. 1 = completely neutral wire-service style, 10 = heavily opinionated/editorialized.

### Integration with Agent 2

Agent 2 currently batches 5 articles per LLM call, returns claims JSON. Add one field:

**Updated system prompt (rate → strip → extract):** 
```
You are a forensic claim extractor. For each article you receive:

STEP 1 — Rate editorial framing bias on a scale of 1-10:
  1 = Pure wire-service style. Just the facts, no adjectives, no opinion. 
      Example: "The president signed the bill into law Tuesday afternoon."
  3 = Mostly neutral with occasional loaded language.
      Example: "The controversial legislation, debated for months, was signed Tuesday."
  5 = Moderate editorial framing. Clear word choices that steer reader interpretation.
      Example: "The embattled president reluctantly signed the deeply divisive bill into law."
  7 = Heavy editorializing. Strong adjectives, clear author opinion, dramatic framing.
      Example: "In a stunning capitulation, the president caved to pressure and signed the disastrous bill."
  10 = Pure opinion piece. Every sentence carries judgment. 
      Example: "The corrupt administration rammed through yet another catastrophic policy Tuesday, proving once again that they answer only to their billionaire donors."

STEP 2 — Strip editorial framing (remove adjectives, hedges, passive-voice attribution).

STEP 3 — Extract every atomic, verifiable factual claim from the neutralized text.

Rules for claims:
  1. Each claim must be a single self-contained statement that CAN be verified or falsified
  2. Claims must be atomic — one fact per claim, not compound statements
  3. Do NOT summarize, paraphrase, or add commentary
  4. Do NOT include opinions, predictions, or value judgments
  5. Include named entities (people, organizations, locations) in each claim

Return JSON with a "results" array — one object per article:
  - "article_id": the integer ID provided with the article
  - "framing_score": integer 1-10 from STEP 1
  - "claims": array of claim objects, each with "text" (string) and "entities" (array of strings)
```

**Parsing:** Read `framing_score` via `result.get("framing_score")`. Coerce to int with try/except — if missing or unparseable, store NULL. Same `.get()` pattern as existing `article_id`/`claims` parsing (safe against missing fields).

**Response format:** `{"results": [{"article_id": N, "claims": [...], "framing_score": 7}]}`

**One call, two outputs.** No extra API calls. The LLM already has article text in context — rating bias adds negligible cognitive load vs claim extraction.

Agent 2 stores `framing_score` to `article_framing.llm_score` alongside claims. Lexical + sentiment scores are computed locally (no API) and stored at the same time.

### Backfill script

`scripts/backfill_framing.py`:
1. Reads all articles with bodies that don't have a row in `article_framing`
2. For each article, calls `score_lexical()` and `score_sentiment()` (instant, no API)
3. For `llm_score`: standalone framing-only prompt per article using the same anchored 1-10 scale (same examples as Agent 2 prompt). Old articles already have claims — can't use the combined prompt.
4. Batch-inserts results every 100 articles
5. `--delay` flag for rate limiting (default 0.5s)

---

## Testing strategy

### Unit tests (`test_framing.py`)

- `score_lexical`: empty text → 0, neutral text → low score, loaded text → higher score
- `score_sentiment`: positive text → positive, negative text → negative, neutral → ~0
- `score_llm`: mock LLMClient, verify prompt format, verify JSON parse, verify error handling

### Integration

- Backfill on a test DB with 5 articles → verify table populated
- Agent 2 integration: existing test DB → verify framing scores stored alongside claims

---

## Dependencies

- `vaderSentiment` — `pip install vaderSentiment`, pure Python, no model download (~1MB). Add to `requirements.txt`.
- NLTK — NOT needed. Word-list approach avoids POS tagging dependency.
- LLM client — already built, provider-agnostic

---

## Verification checklist

1. `npm run build` — no regressions
2. `pytest -m "not network"` — all tests pass (LLM tests behind network marker)
3. `vitest run` — no regressions
4. `ponytail-review` against diff
5. Backfill dry-run on 10 articles against live DB

---

## Resolved design decisions

1. **Lexical scorer: word-list, not NLTK POS.** Three hardcoded word lists (adjectives, hedges, intensifiers) — ~50 words each. Deterministic, zero downloads. Swap to POS tagging later if accuracy matters; same `score_lexical()` interface.

2. **LLM backfill delay: 0.5s default.** Configurable via `--delay` flag. 2,028 articles × 0.5s ≈ 17 minutes. Safe for OpenCode Zen free tier.

3. **Separate `article_framing` table, not claims columns.** Framing is per-article (same body, same score regardless of source). Claims are per-source-per-article. Separate table avoids duplication.

4. **Agent 2 uses a single LLM call per batch.** One prompt extracts claims AND rates framing bias (1-10). Zero extra API calls. The framing field is optional in parsing — if the LLM omits it, `llm_score` stays NULL.
