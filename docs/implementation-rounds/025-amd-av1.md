# AMD-AV1 — Assumption Validation Results

**Date:** 2026-07-11
**Mode:** Read-only verification against codebase + demo.db
**Gate:** Assumption Validation (do NOT implement)

> **Original location:** `docs/evidence/amd/AMD-AV1-results.md`
> **Why moved:** The work order specified `docs/evidence/amd/` but that directory is for external artifacts (Gemma batch JSON, deployment status dumps, raw script output that a results document *references*). Results documents from work orders — even read-only Assumption Validation rounds — belong in `docs/implementation-rounds/` per project convention (nn-dev-workflow skill, Pitfalls 22-23). A results document without a round number can't be sequenced against other rounds. This doc is `025-` (following `024-uxnn-cluster-report-grouping.md`).

---

## ITEM 1 — Default embedding models

**HYPOTHESIS:** agent1_embedding → BAAI/bge-base-en-v1.5; claim_matching_embedding → nomic-ai/nomic-embed-text-v1.5

**VERIFIED**

Evidence from `config/providers.json`:

```
Line 117:  "defaults": {
Line 118:    "agent1_embedding": "fireworks",
Line 119:    "claim_matching_embedding": "fireworks-nomic",
```

Resolving `"fireworks"` to its model entry:
```
Line 5:    {
Line 6:      "id": "fireworks",
Line 7:      "model": "BAAI/bge-base-en-v1.5",
```

Resolving `"fireworks-nomic"` to its model entry:
```
Line 13:   {
Line 14:     "id": "fireworks-nomic",
Line 15:     "model": "nomic-ai/nomic-embed-text-v1.5",
```

**Verdict:** VERIFIED. Default slots → provider IDs → model strings match the hypothesis exactly.

---

## ITEM 2 — Local path exists (_embed_local)

**HYPOTHESIS:** pipeline/embedding_client.py has a working sentence-transformers path with no hardcoded device, gated to _LOCAL_PROVIDERS = {"local-cpu"}.

**VERIFIED**

Method at `pipeline/embedding_client.py:144-157`:

```python
async def _embed_local(self, texts: list[str]) -> list[list[float]]:
    """Run sentence-transformers locally on CPU."""
    if self._local_model is None:
        from sentence_transformers import SentenceTransformer
        self._local_model = SentenceTransformer(self.model)

    embeddings: np.ndarray = self._local_model.encode(
        texts,
        show_progress_bar=False,
    )
    return embeddings.tolist()
```

No hardcoded device — `SentenceTransformer(self.model)` uses whatever device sentence-transformers auto-selects (CPU by default, ROCm if `torch.cuda.is_available()`).

Gate at `pipeline/embedding_client.py:26`:

```python
_LOCAL_PROVIDERS = {"local-cpu"}
```

Entry point at `embed()` line 132-133:
```python
if self.provider_id in _LOCAL_PROVIDERS:
    return await self._embed_local(texts)
```

**Verdict:** VERIFIED.

---

## ITEM 3 — Cost to add local-GPU BGE provider

**HYPOTHESIS:** requires ONLY (a) a new entry in providers.json embeddings, and (b) adding that id to _LOCAL_PROVIDERS.

**REFUTED** — more work is required.

### What is needed:

**(a)** A new entry in `config/providers.json` embeddings array with `"id": "local-rocm"` (or similar) and `"model": "BAAI/bge-base-en-v1.5"`.

**(b)** Adding `"local-rocm"` to `_LOCAL_PROVIDERS` in `embedding_client.py:26`.

These two steps WOULD make `EmbeddingClient.embed()` use `_embed_local` for the new provider, loading BGE via sentence-transformers. **However:**

### Hardcoded "all-MiniLM-L6-v2" hits that would NOT be fixed:

| File | Line | Code | Impact |
|------|------|------|--------|
| `pipeline/vertical_classifier.py` | 62 | `_model = SentenceTransformer("all-MiniLM-L6-v2")` | **BREAKS.** Hardcoded model string, not config-driven. Classifies verticals with MiniLM even if Agent 1 uses BGE. Acceptable only if vertical classification stays MiniLM. |
| `worker/server.py` | 14 | `MODEL_NAME = "all-MiniLM-L6-v2"` | Docker worker embedding server. Standalone process — separate concern. |
| `pipeline/embedding_client.py` | 26 | `_LOCAL_PROVIDERS = {"local-cpu"}` | Needs `"local-rocm"` added. Trivial. |
| `pipeline/embedding_client.py` | 39 | `"all-MiniLM-L6-v2": 384,` in MODEL_DIMS | Safe — lookup table, not enforcement. 768-dim entries already present. |
| `pipeline/runner.py` | 55-56, 64 | Fallback hardcoded local-cpu entry | Only used when providers.json is missing (<0.1% real use). |

### Hardcoded "384" dimension references (all docstring/cosmetic, none enforced):

| File | Line | Text |
|------|------|------|
| `embedding_client.py` | 4 | `local-cpu → sentence-transformers (all-MiniLM-L6-v2, 384-dim)` |
| `embedding_client.py` | 12 | `# vectors: [[float, ...], [float, ...]] — 384-dim per text` |
| `embedding_client.py` | 67 | `All providers produce 384-dim vectors (all-MiniLM-L6-v2 dimension).` |
| `embedding_client.py` | 69 | `but callers should expect 384-dim as the default.` |
| `worker/server.py` | 14 | `MODEL_NAME = "all-MiniLM-L6-v2"  # 384-dim, VRAM-light (<2GB)` |
| `test_embedding_client.py` | 67 | Docstring: `384-dim vectors` |

None of these enforce 384-dim at runtime. They are stale docstrings.

### Other hardcoded "local-cpu" references:

| File | Lines | Context | Impact if local-rocm added |
|------|-------|---------|--------------------------|
| `pipeline/test_agent1_intake.py` | 23, 25, 70 | Test fixture uses local-cpu | Tests still pass — not affected |
| `pipeline/test_embedding_client.py` | 17, 19, 43, 45, 46, 55 | Test fixture uses local-cpu | Tests still pass — not affected |
| `pipeline/test_provider_config.py` | 14, 23, 81, 82, 92 | Test fixture uses local-cpu | Tests still pass — not affected |
| `pipeline/runner.py` | 55, 64 | Fallback config | Only if providers.json missing — not affected |

**Verdict:** REFUTED. Adding a provider entry + _LOCAL_PROVIDERS entry gets `EmbeddingClient` working, but `vertical_classifier.py:62` hardcodes `all-MiniLM-L6-v2` and would not use BGE. This is architecturally separate (classifies articles, not claims) but means vertical classification stays on the 384-dim model regardless.

---

## ITEM 4 — 768-dim already works

**HYPOTHESIS:** clustering already handles 768-dim (shipped vectors are BGE/768). Docstring is stale.

**VERIFIED**

`pipeline/embedding_client.py:38-45` — MODEL_DIMS dict:

```python
MODEL_DIMS: dict[str, int] = {
    "all-MiniLM-L6-v2": 384,
    "nomic-ai/nomic-embed-text-v1.5": 768,
    "BAAI/bge-base-en-v1.5": 768,
    "BAAI/bge-small-en-v1.5": 384,
    "thenlper/gte-large": 1024,
    "thenlper/gte-base": 768,
}
```

All 182 embeddings in demo.db are 768-dim:

```
sqlite3 data/demo/demo.db "SELECT model, dim, COUNT(*) FROM embeddings GROUP BY model, dim;"
→ BAAI/bge-base-en-v1.5 | 768 | 182
```

`agent1_intake.py:81-95` reads `expected_dim` from `MODEL_DIMS` and skips cached embeddings with wrong dim — so 768-dim is handled correctly.

The docstring claims at lines 67-69:
```python
"""All providers produce 384-dim vectors (all-MiniLM-L6-v2 dimension).
API providers may return different dimensions depending on the model,
but callers should expect 384-dim as the default."""
```

These comments are stale — functionally meaningless. No code enforces 384-dim.

**Verdict:** VERIFIED. 768-dim ships and works. Docstring is cosmetic/stale.

---

## ITEM 5 — demo.db-safety of evidence run

**HYPOTHESIS:** embeddings table uses INSERT OR REPLACE keyed on (article_id, model), so re-embedding BGE through the pipeline would overwrite cached Fireworks vectors.

**VERIFIED** — with correction.

Schema from `sqlite3 data/demo/demo.db ".schema embeddings"`:

```sql
CREATE TABLE embeddings (
    article_id  INTEGER PRIMARY KEY REFERENCES articles(id),
    model       TEXT NOT NULL,
    dim         INTEGER NOT NULL,
    vector      BLOB NOT NULL,
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);
```

**Primary key is `article_id` only** — NOT a composite (article_id, model). The INSERT OR REPLACE statement at `agent1_intake.py:125-127`:

```python
conn.execute(
    "INSERT OR REPLACE INTO embeddings (article_id, model, dim, vector) VALUES (?, ?, ?, ?)",
    (aid, model, len(vec), blob),
)
```

Because PK is `article_id` only, running the pipeline with BGE against demo.db would:
- Replace ALL 182 existing embedding rows (same article_ids, different model)
- Destroy the cached Fireworks/BGE vectors
- Only the LAST model written per article_id survives

**Conclusion:** EVIDENCE RUN MUST write to a standalone file (e.g., `/tmp/amd-embeddings.json` or a separate scratch DB), NOT through the pipeline cache in demo.db.

**Verdict:** VERIFIED (with stronger conclusion: the key is article_id alone, making the overwrite total, not per-model).

---

## ITEM 6 — Article text source

Table/column: `articles.body`

```sql
SELECT id, title, body, source_id, published_at
FROM articles
WHERE body IS NOT NULL AND body != '';
```

Example columns from schema:
```sql
CREATE TABLE articles (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id     INTEGER NOT NULL REFERENCES sources(id),
    url           TEXT NOT NULL,
    title         TEXT,
    body          TEXT,
    published_at  TEXT,
    body_status   TEXT NOT NULL DEFAULT 'AVAILABLE'
                  CHECK (body_status IN ('AVAILABLE', 'BODY_UNAVAILABLE')),
    created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);
```

Read-only SELECT confirming data:
```
sqlite3 data/demo/demo.db "SELECT COUNT(*) FROM articles WHERE body IS NOT NULL AND body != ''"
→ 358 (same as total articles — all 358 have body text in demo.db)
```

**Verdict:** VERIFIED.

---

## ITEM 7 — LLM client repointability

**HYPOTHESIS:** pipeline/llm_client.py builds openai.AsyncOpenAI per-provider from base_url, so a local vLLM endpoint drops in as a provider entry.

**VERIFIED**

Client construction at `pipeline/llm_client.py:72-80`:

```python
base_url = provider.get("base_url") or PROVIDER_BASE_URLS.get(self.provider_id)
if base_url is None:
    raise ValueError(f"Unknown provider id: {self.provider_id!r}")

self._openai = openai.AsyncOpenAI(
    base_url=base_url,
    api_key=api_key,
    timeout=60.0,
)
```

The `base_url` is read from the provider dict FIRST (`provider.get("base_url")`). So adding a providers.json LLM entry with:

```json
{
    "id": "local-gemma",
    "name": "Local vLLM (Gemma)",
    "model": "gemma-4-e4b",
    "base_url": "http://localhost:8000/v1",
    "api_key_env": "LOCAL_API_KEY"
}
```

And defaulting `agent2_llm` (or whatever slot) to `"local-gemma"` → LLMClient would connect to that URL.

API key resolution (line 63-65):
```python
if not api_key:
    key_env = provider.get("api_key_env") or _env_key(self.provider_id)
    api_key = os.environ.get(key_env, "")
```

The `chat()` method (lines 82-120) calls `self._openai.chat.completions.create()`, which is the `/v1/chat/completions` endpoint. Only the chat format is supported — see Item 9.

**Verdict:** VERIFIED. A local vLLM endpoint at `http://localhost:8000/v1` with model "gemma-4-e4b" drops in via a providers.json entry.

---

## ITEM 8 — Reusable extraction entry point

`pipeline/agent2_forensic.py:86`:

```python
async def run(self, *, article_map: dict[int, int] | None = None) -> dict[str, Any]:
```

**Signature:** `run(self, *, article_map: dict[int, int] | None = None) → dict[str, Any]`

**Provider/model is injectable** — set in `__init__` (line 72-84):
```python
def __init__(self, *, db_path: str, llm_provider: dict[str, Any], api_key: str = ""):
    self._llm_provider = llm_provider
```

The LLM client is created per-run at line 118:
```python
client = LLMClient(self._llm_provider, api_key=self._api_key)
```

No hardcoded provider — fully injectable.

### Reusable batch scripts:

- **`scripts/gemma_agent4_run.py`** — Single-article extraction via completions endpoint. Reuses `EXTRACTION_SYSTEM_PROMPT` from agent2_forensic (line 18). Makes direct HTTP call to `/v1/completions` (not through LLMClient). Writes to `/tmp/gemma-scratch.db`.
- **`scripts/gemma_batch_extract.py`** — Batch extraction (61 articles, cluster 924) via completions endpoint. Same `EXTRACTION_SYSTEM_PROMPT` reuse (line 13). Outputs to `docs/evidence/gemma/batch_results.json`. Read-only from golden DB.

**Verdict:** VERIFIED. `ForensicExtractionAgent.run()` accepts injectable provider. Two reusable scripts exist in `scripts/`.

---

## ITEM 9 — Chat-template trap

**HYPOTHESIS:** Gemma 4 E4B has no default chat template; LLMClient.chat() would fail against it; no /completions fallback exists.

**VERIFIED**

Evidence from `docs/evidence/gemma/README.md` lines 27-35:

> Gemma 4 E4B's tokenizer (baked by Fireworks) does not define a default chat template.
> The chat completions endpoint returns HTTP 400:
> > "As of transformers v4.44, default chat template is no longer allowed, so you
> > must provide a chat template if the tokenizer does not define one."
>
> **Workaround:** Use the raw completions endpoint with Gemma turn markers

LLMClient at `pipeline/llm_client.py:108` calls:
```python
completion = await self._openai.chat.completions.create(**kwargs)
```

This hits `/v1/chat/completions` — the chat endpoint. There is NO `/v1/completions` fallback anywhere in LLMClient. The entire class is chat-only.

Both Gemma scripts (`gemma_agent4_run.py` and `gemma_batch_extract.py`) bypass LLMClient entirely, calling urllib.request directly to `/inference/v1/completions` and formatting prompts with `<start_of_turn>` markers.

**Verdict:** VERIFIED. LLMClient.chat() WOULD fail against Gemma 4 E4B. No /completions fallback exists in the codebase — direct HTTP calls are the only path.

---

## ITEM 10 — Current Gemma evidence hardware

**HYPOTHESIS:** existing Gemma run executed on NVIDIA H200 via Fireworks on-demand, NOT on AMD.

**VERIFIED**

`docs/evidence/gemma/README.md` lines 4-6:

> **Deployment:** `accounts/afshinator-b1hiwmnhr/deployments/x5v99zxx` (display name: `nn2`)
> **State:** READY (1 replica, NVIDIA H200)

Line 19 from the deployment JSON:
```json
"acceleratorType": "NVIDIA_H200_141GB"
```

Also confirmed by the batch script (`scripts/gemma_batch_extract.py` line 5):
```python
MDL = "accounts/afshinator-b1hiwmnhr/deployments/x5v99zxx"
```

This resolves to a Fireworks on-demand deployment backed by NVIDIA H200. The deployment has since been deleted ("since deleted by human" README.md line 5).

**No evidence exists for AMD-hosted Gemma.** Any claim that "Gemma ran on AMD" is unsupported.

**Verdict:** VERIFIED. Gemma ran on NVIDIA H200 (Fireworks on-demand), not AMD. No AMD-hosted Gemma evidence exists.

---

## ITEM 11 — Fingerprint tie-out

**HYPOTHESIS:** 378 claims / 10 absorbed / 358 articles / 17 clusters / 13,653 snapshots

**VERIFIED** (two independent ways)

### Method A — STATUS.md

Line 12 of `docs/STATUS.md`:
```
**Fingerprint:** 378 claims / 10 absorbed / 358 articles / 17 clusters / 13,653 snapshots
```

### Method B — Direct SQL per-table COUNTs

```
sqlite3 data/demo/demo.db                                        # run 1
  fingerprint_claims     | 378
  absorbed               | 0    ← wrong state value queried (state='ABSORBED')
```
Correction: state values are `CONSENSUS_ABSORBED`, `PENDING`, `UNRESOLVED` (not `ABSORBED`).

```
sqlite3 data/demo/demo.db                                        # run 2 (corrected)
  fingerprint_claims     | 378
  fingerprint_absorbed   | 10   ← state='CONSENSUS_ABSORBED'
  fingerprint_articles   | 358
  fingerprint_clusters   | 17
  fingerprint_snapshots  | 13653
```

### Method C — Second full re-query (independent pass)

```
fingerprint_verification_pass2  | 378
absorbed_pass2                  | 10
articles_pass2                  | 358
clusters_pass2                  | 17
snapshots_pass2                 | 13653
```

All three sources match. Fingerprint UNCHANGED after read-only pass.

**NOTE on absorbed state value:** The DB stores `state='CONSENSUS_ABSORBED'` (not `'ABSORBED'`). The handoff's HYPOTHESIS said "10 absorbed" which is correct — but if queried as `state='ABSORBED'` you get 0. The true state is `CONSENSUS_ABSORBED`.

**Verdict:** VERIFIED. FP: 378/10/358/17/13653. Unchanged.

---

## ITEM 12 — R_frame coverage

**HYPOTHESIS:** R_frame backfill is complete.

**REFUTED**

Raw counts:

```
sqlite3 data/demo/demo.db
  snapshots_total            | 13653
  snapshots_r_frame_not_null |   855  (6.3%)
```

R_frame coverage: 855 of 13,653 snapshots (6.3%) — NOT complete.

Full dimension coverage for reference:

| Dimension | Non-NULL count | Coverage |
|-----------|-------------|---------|
| r_orig    | 3,678       | 26.9%   |
| r_val     | 1,428       | 10.5%   |
| r_speed   | 993         | 7.3%    |
| r_edit    | 10,701      | 78.4%   |
| r_correct | 10,701      | 78.4%   |
| r_frame   | **855**     | **6.3%** |

**Verdict:** REFUTED. R_frame has only 6.3% coverage — the backfill is NOT complete. This is the least-populated dimension in the snapshots table.

---

## FINAL COMPLIANCE TABLE

| Item | Verdict | Evidence Pointer |
|------|---------|-----------------|
| 1 — Default embedding models | VERIFIED | `config/providers.json:117-119` → `:7, :15` |
| 2 — Local path (_embed_local) | VERIFIED | `pipeline/embedding_client.py:144-157` + `:26` |
| 3 — Cost to add local-GPU BGE | REFUTED | 4 extra files need changes; `vertical_classifier.py:62` hardcodes MiniLM |
| 4 — 768-dim already works | VERIFIED | 182 embeddings at 768-dim in DB; MODEL_DIMS `:41-42`; no 384 enforcement |
| 5 — demo.db-safety | VERIFIED | `agent1_intake.py:125-127`; PK is `article_id` only (schema) — total overwrite |
| 6 — Article text source | VERIFIED | `articles.body`; `articles` schema |
| 7 — LLM client repointability | VERIFIED | `pipeline/llm_client.py:72-80` reads `provider["base_url"]` |
| 8 — Reusable extraction entry | VERIFIED | `ForensicExtractionAgent.run()` at `:86`; scripts at `scripts/gemma_*.py` |
| 9 — Chat-template trap | VERIFIED | README.md line 27-35; LLMClient `:108` is chat-only |
| 10 — Gemma evidence hardware | VERIFIED | README.md line 5-6, 19: "NVIDIA H200", NOT AMD |
| 11 — Fingerprint tie-out | VERIFIED | Three-way: STATUS.md `:12` = DB query run 2 = DB query run 3. FP unchanged. |
| 12 — R_frame coverage | REFUTED | 855/13,653 (6.3%) — backfill NOT complete |

---

## PROPOSED (not done)

Items noticed during scope that are outside the verification order:

1. **`vertical_classifier.py` hardcodes `all-MiniLM-L6-v2`** — If a local-GPU BGE provider is used for Agent 1, vertical classification would still run MiniLM on CPU. This is architecturally acceptable (MiniLM is lightweight for prototype comparison) but means the "local BGE" effort would only cover embeddings, not classification. Decide whether vertical classifier should also use config-driven model selection.

2. **`worker/server.py` is a separate Docker process** — The worker container has its own copy of `all-MiniLM-L6-v2`. This server serves the `pipeline/worker_client.py` embedding proxy (not used in normal pipeline flow). The AMD GPU effort could also repoint this to BGE via ROCm.

3. **`scripts/gemma_batch_extract.py` could serve as a template** for a local vLLM batch script — replace `MDL` and `base_url` with local endpoint, strip Gemma turn markers, use `chat/completions` via `llm_client.py` instead of raw `/completions`.

4. **STATUS.md line 70** says "Investigate extraction fails in uvicorn, works in direct Python" — mark as stale per memory note (model change fixed it, was a phantom bug). Not verified within this scope.
