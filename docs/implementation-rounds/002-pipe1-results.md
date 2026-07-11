# PIPE-1 Results — Config-driven Provider Resolution

**Date:** 2026-07-10
**Status:** Complete
**Work order:** PIPE-1 (rev2)

---

## Summary

Two hardcoded dicts in `pipeline/llm_client.py` (`PROVIDER_BASE_URLS` with 4 IDs, and `{ID}_API_KEY` key derivation) blocked any new provider ID from `config/providers.json` from working at runtime. Fix: each provider entry now carries `base_url` and `api_key_env` fields. Clients read from the provider dict, falling back to hardcoded maps for backward compatibility. Adding a new provider is now a JSON entry — zero code changes.

## Files Changed (6)

| File | Change |
|------|--------|
| `pipeline/llm_client.py` | +2 lines: `provider.get("base_url") or PROVIDER_BASE_URLS.get(id)`; `provider.get("api_key_env") or _env_key(id)` |
| `pipeline/embedding_client.py` | +3 lines: store `self._base_url`; use `self._base_url or _EMBEDDING_BASE_URLS.get(id)` |
| `pipeline/runner.py` | +3 lines: `provider.get("api_key_env") or f"{id}_API_KEY"` |
| `pipeline/test_llm_client.py` | +61 lines: 5 new tests |
| `pipeline/test_embedding_client.py` | +31 lines: 1 new test |
| `config/providers.json` | Rewritten: 10 LLM entries (7 Fireworks + opencode + deepseek + openai), base_url/api_key_env on all |

## Test Results

| Phase | Passed | Failed | Notes |
|-------|--------|--------|-------|
| P0 baseline | 286 | 20 | Captured to /tmp/pipe1_pytest_baseline.txt |
| P1 (RED) | 2 | 4 | 4 bug tests hit expected lines |
| P2 (GREEN) | 6 | 0 | All 6 new tests pass |
| P4 regression | 292 | 20 | Identical failures to baseline; +6 new tests |
| P0 vitest | 112 | 21 | Captured to /tmp/pipe1_vitest_baseline.txt |
| P4 vitest | 112 | 21 | Identical to baseline |

Tie-out: 286 + 6 = 292 ✓

## Config Changes

### New Fireworks LLM entries (5 added)
```
fireworks-glm-5p1    → accounts/fireworks/models/glm-5p1        (NOT execution-verified)
fireworks-glm-5p2    → accounts/fireworks/models/glm-5p2        (NOT execution-verified)
fireworks-gpt-oss    → accounts/fireworks/models/gpt-oss-120b   (NOT execution-verified)
fireworks-kimi-k2p5  → accounts/fireworks/models/kimi-k2p5      (NOT execution-verified)
fireworks-kimi-k2p6  → accounts/fireworks/models/kimi-k2p6      (NOT execution-verified)
```

### Existing entries updated
All existing provider entries gained `base_url` and `api_key_env` fields matching the hardcoded maps:

| Provider | base_url | api_key_env |
|----------|----------|-------------|
| fireworks | https://api.fireworks.ai/inference/v1 | FIREWORKS_API_KEY |
| fireworks-nomic | https://api.fireworks.ai/inference/v1 | FIREWORKS_API_KEY |
| openai | https://api.openai.com/v1 | OPENAI_API_KEY |
| local-cpu | (none) | (none) |
| opencode | https://opencode.ai/zen/v1 | OPENCODE_API_KEY |
| deepseek | https://api.deepseek.com/v1 | DEEPSEEK_API_KEY |

### Defaults: UNCHANGED
```
agent1_embedding: fireworks
claim_matching_embedding: fireworks-nomic
agent1_llm: fireworks
agent2_llm: fireworks
agent4_llm: fireworks
```

### Standby
`fireworks-gemma` retained (model: accounts/afshinator-b1hiwmnhr/deployments/x5v99zxx). NOT functional — Gemma uses completions endpoint, LLMClient is chat-based. Not wired as a default.

## Catalog Smoke

`curl http://localhost:3019/api/config/providers/available` returned all 10 LLM provider IDs:
```
deepseek, fireworks, fireworks-gemma, fireworks-glm-5p1, fireworks-glm-5p2,
fireworks-gpt-oss, fireworks-kimi-k2p5, fireworks-kimi-k2p6, openai, opencode
```

## DB State

Golden DB mutated by `app/test_routes.py:119` (scraper test) during full pytest run. Restored via `git checkout`. Fingerprint confirmed: 378|10|358|17|13653.

## Constraint Conflict (PROPOSED, not done)

`app/test_routes.py:119` — `TestScraperRoutes.test_start_stop` calls `POST /api/scraper/start` against the default DB. Running `pytest -m "not network"` includes this test. The work order constraints "run full suite" and "never start scraper" are in conflict. Fix: add `NN_DB_PATH=:memory:` or similar to the `client` fixture, or set `NN_DISABLE_SCRAPER=1` during test runs.

## Compliance Table

See inline above in session. All requirements met EXCEPT golden DB read-only (violated by test suite, restored after).
