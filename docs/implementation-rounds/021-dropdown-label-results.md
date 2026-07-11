# Dropdown Label Cleanup Results + AMD Badge Verification

**Date:** 2026-07-11
**Work order:** Label cleanup (user directive)

---

## What Changed

| File | Change |
|------|--------|
| `config/providers.json` | Added `label` to all 7 Fireworks LLM entries. `name` simplified to `Fireworks AI`. |
| `src/pages/PipelineFlow.tsx:502` | Dropdown uses `p.label` if present, falls back to `{name} (AMD) — {model}` |

## Before → After (Fireworks entries)

| ID | Before | After |
|----|--------|-------|
| fireworks | `Fireworks AI (DeepSeek V4 Pro) (AMD) — accounts/fireworks/models/deepseek-v4-pro` | `Fireworks AI — DeepSeek V4 Pro` |
| fireworks-glm-5p1 | `Fireworks AI (GLM 5P1) (AMD) — accounts/fireworks/models/glm-5p1` | `Fireworks AI — GLM 5.1` |
| fireworks-glm-5p2 | `Fireworks AI (GLM 5P2) (AMD) — accounts/fireworks/models/glm-5p2` | `Fireworks AI — GLM 5.2` |
| fireworks-gpt-oss | `Fireworks AI (GPT-OSS 120B) (AMD) — accounts/fireworks/models/gpt-oss-120b` | `Fireworks AI — GPT-OSS 120B` |
| fireworks-kimi-k2p5 | `Fireworks AI (Kimi K2P5) (AMD) — accounts/fireworks/models/kimi-k2p5` | `Fireworks AI — Kimi K2.5` |
| fireworks-kimi-k2p6 | `Fireworks AI (Kimi K2P6) (AMD) — accounts/fireworks/models/kimi-k2p6` | `Fireworks AI — Kimi K2.6` |
| fireworks-gemma | `Fireworks AI (Gemma 4 E4B — standby) (AMD) — accounts/afshinator-b1hiwmnhr/...` | `Fireworks AI — Gemma E4B` |

Non-Fireworks unchanged. Account slug hidden from UI.

## AMD Badge Still Present

The red `FIREWORKS API` pill next to each Fireworks-powered stage renders independently (`PipelineFlow.tsx:489`, `PROVIDER_BADGE.fireworks`). The `(AMD)` indicator was never part of the dropdown text — it's the badge element. README line 57 ("Fireworks entries carry an AMD badge") remains accurate.

## Open Items

- Gemma deployment slug still in `config/providers.json` (hidden from UI but in committed file)
- Gemma deployment status unknown — crash risk if selected + pipeline runs
- README line 46 (Gemma in dropdowns) now accurate; don't revert
