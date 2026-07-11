# Round 009 — Dynamic Provider Dropdowns (Plan)

**Status:** Plan — awaiting approval
**Date:** 2026-07-10

---

## Pain Point / Error Found

The Pipeline page (`/pipeline`) shows dropdowns to select the LLM provider for each agent stage. The dropdowns are wired to `PUT /api/config/providers`, which updates `app.state.providers` in memory. The provider resolution code (`provider_config.py:71-72`) correctly reads these overrides. **But if a user selects a provider ID not listed in two hardcoded dicts, the pipeline crashes at runtime.**

Specifically: `config/providers.json` defines `"fireworks-gemma"` (the Gemma 4 E4B deployment). If a user selects it from the dropdown and the pipeline runs (with `NN_ENABLE_PIPELINE=1`), `LLMClient.__init__` raises:

```
ValueError: Unknown provider id: 'fireworks-gemma'
```

Same for any new Fireworks model entry — the dropdown appears, the selection appears to work, but actual pipeline execution fails.

## Evidence: Two Hardcoded Dicts

### 1. `PROVIDER_BASE_URLS` in `pipeline/llm_client.py:27-32`

```python
PROVIDER_BASE_URLS: dict[str, str] = {
    "fireworks": "https://api.fireworks.ai/inference/v1",
    "opencode": "https://opencode.ai/zen/v1",
    "deepseek": "https://api.deepseek.com/v1",
    "openai": "https://api.openai.com/v1",
}
```

Only 4 IDs. `LLMClient.__init__:71-73` raises `ValueError(f"Unknown provider id: {self.provider_id!r}")` for any ID not in this dict. Adding `"fireworks-gemma"` to `config/providers.json` is not enough — `PROVIDER_BASE_URLS` must also be updated in code.

### 2. API key derivation in `pipeline/llm_client.py:37-38`

```python
def _env_key(provider_id: str) -> str:
    return f"{provider_id.upper()}_API_KEY"
```

For `"fireworks-gemma"` this becomes `FIREWORKS_GEMMA_API_KEY` — which doesn't exist. The gemma deployment uses the same `FIREWORKS_API_KEY`. The key name is mechanically derived from provider ID, but Fireworks variants all share one key.

### 3. Same pattern in `pipeline/embedding_client.py:51-54`

```python
_EMBEDDING_BASE_URLS: dict[str, str] = {
    "fireworks": "https://api.fireworks.ai/inference/v1",
    "fireworks-nomic": "https://api.fireworks.ai/inference/v1",
    "openai": "https://api.openai.com/v1",
}
```

Not currently blocking (no new embedding providers planned), but same anti-pattern.

### 4. API key in `pipeline/runner.py:119-121`

```python
api_key=os.environ.get(
    f"{a2_llm_provider['id'].upper()}_API_KEY", ""
)
```

Same `{id}_API_KEY` derivation, same problem.

## Targeted Fix

**Make `config/providers.json` the single source of truth.** Each provider entry carries its own `base_url` and optional `api_key_env`. `LLMClient` and `EmbeddingClient` read these from the provider dict instead of hardcoded maps. Fallback to hardcoded maps when fields are absent (backward compatibility).

**Outcome:** Adding a new provider is a JSON entry. Zero code changes. The dropdowns are fully config-driven.

### Config entry shape

| Field | Required | Description |
|-------|----------|-------------|
| `id` | Yes | Unique provider identifier (dropdown value) |
| `name` | Yes | Human-readable name (dropdown label) |
| `model` | Yes | Model ID passed to the API |
| `base_url` | No | API endpoint. Falls back to hardcoded map if absent. |
| `api_key_env` | No | Env var for API key. Falls back to `{ID}_API_KEY` if absent. |
| `amd` | Yes | Boolean for `(AMD)` badge in UI |

### New Fireworks entries (7 added)

```
accounts/fireworks/models/deepseek-v4-pro  → id: "fireworks"         (existing, renamed)
accounts/fireworks/models/glm-5p1          → id: "fireworks-glm-5p1"
accounts/fireworks/models/glm-5p2          → id: "fireworks-glm-5p2"
accounts/fireworks/models/gpt-oss-120b     → id: "fireworks-gpt-oss"
accounts/fireworks/models/kimi-k2p5        → id: "fireworks-kimi-k2p5"
accounts/fireworks/models/kimi-k2p6        → id: "fireworks-kimi-k2p6"
accounts/fireworks/models/gemma-4-e4b      → id: "fireworks-gemma"   (standby)
```

All share `"base_url": "https://api.fireworks.ai/inference/v1"` and `"api_key_env": "FIREWORKS_API_KEY"`.

Model IDs verified via `GET https://api.fireworks.ai/inference/v1/models` (2026-07-10). Gemma-4-e4b not in live listing (standby deployment); model ID predicted from Fireworks naming convention.

### Default preserved

`defaults.agent2_llm` = `"fireworks"` → `accounts/fireworks/models/deepseek-v4-pro` — exactly what ships today.

## Evidence: How To Reach Target

### Files changed (7)

| # | File | Change |
|---|------|--------|
| 1 | `config/providers.json` | Add `base_url` + `api_key_env` to all existing provider entries. Add 7 Fireworks LLM entries. Remove deleted gemma deployment entry. |
| 2 | `pipeline/llm_client.py` | `__init__`: read `base_url` from provider dict, fall back to `PROVIDER_BASE_URLS`. Read `api_key_env` from provider dict, fall back to `{id.upper()}_API_KEY`. |
| 3 | `pipeline/embedding_client.py` | `__init__`: read `base_url` from provider dict, fall back to `_EMBEDDING_BASE_URLS`. |
| 4 | `pipeline/runner.py:119-121` | Derive API key using same fallback logic: `provider.get("api_key_env")` → `{id.upper()}_API_KEY`. |
| 5 | `pipeline/test_llm_client.py` | +4 tests (see TDD below). |
| 6 | `pipeline/test_embedding_client.py` | +1 test: base_url from provider dict. |
| 7 | `pipeline/test_provider_config.py` | +1 test: provider dict with new fields round-trips. |

### TDD Sequence

**Red — 6 new tests fail:**

| Test | File | Asserts |
|------|------|---------|
| Provider with `base_url` → LLMClient uses it | test_llm_client.py | `client._openai.base_url` matches dict's `base_url`, not `PROVIDER_BASE_URLS` |
| Provider with `api_key_env` → LLMClient reads that env var | test_llm_client.py | Monkeypatch `FIREWORKS_API_KEY`, verify client uses it when `api_key_env: "FIREWORKS_API_KEY"` |
| Provider WITHOUT `base_url` → falls back to `PROVIDER_BASE_URLS` | test_llm_client.py | Existing fixture (no `base_url` field) still resolves correctly |
| Provider WITHOUT `api_key_env` → falls back to `{ID}_API_KEY` | test_llm_client.py | Existing fixture (no `api_key_env` field) still resolves correctly |
| Provider with `base_url` → EmbeddingClient uses it | test_embedding_client.py | API provider fixture with `base_url` overrides `_EMBEDDING_BASE_URLS` |
| Provider with `base_url` + `api_key_env` → round-trips through `get_provider_for_agent` | test_provider_config.py | Provider config returns dict with new fields intact |

**Green — implement in llm_client.py, embedding_client.py, runner.py.**

`llm_client.py` change:
```python
# Before:
base_url = PROVIDER_BASE_URLS.get(self.provider_id)

# After:
base_url = provider.get("base_url") or PROVIDER_BASE_URLS.get(self.provider_id)
```

```python
# Before:
api_key = os.environ.get(_env_key(self.provider_id), "")

# After:
key_env = provider.get("api_key_env") or _env_key(self.provider_id)
api_key = os.environ.get(key_env, "")
```

### Regression verification

```bash
rtk pytest pipeline/test_llm_client.py pipeline/test_embedding_client.py pipeline/test_provider_config.py -v
rtk pytest app/test_routes.py -v
rtk pytest -m "not network" -v
rtk vitest run
rtk npm run build
```

All existing test fixtures lack `base_url` and `api_key_env` — fallback paths hit, zero regressions.

### End-to-end smoke test

```bash
# Verify catalog endpoint returns new entries
curl -s http://localhost:3015/api/config/providers/available | python3 -c "
import json, sys; d=json.load(sys.stdin)
llm_ids = [p['id'] for p in d['providers']['llm']]
print('LLM provider IDs:', sorted(llm_ids))
assert len(llm_ids) == 12, f'Expected 12 LLM providers, got {len(llm_ids)}'
print('OK: 12 LLM providers in catalog')
"
```

### Post-implementation: NN_ENABLE_PIPELINE

Note: The pipeline scheduled runner still gates on `NN_ENABLE_PIPELINE=1` (not set by default). The dropdown changes are stored but only take effect when the pipeline actually runs. This is existing behavior — not changed by this round.
