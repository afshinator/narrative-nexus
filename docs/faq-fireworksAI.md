# Fireworks AI — Hackathon Integration

**Key added to `.env`** as `FIREWORKS_API_KEY`. AMD hackathon credits.

## What Fireworks AI actually is

Fireworks AI is an **inference platform** — they run a global fleet of GPUs and host open-source/third-party models on it. They do NOT build their own models. Think of them as "cloud hosting for LLMs": they take models built by DeepSeek, Qwen, Kimi, Meta, etc. and serve them with a fast OpenAI-compatible API, prompt caching, and per-token billing. You never touch GPUs or infrastructure.

**They host DeepSeek V4 Pro/Flash, yes.** That's why the pricing table below lists DeepSeek models — Fireworks runs DeepSeek's open-weight models on their own hardware. Same model, different host (and faster, with AMD credits).

This is NOT Google Fireworks (the visualization tool). Completely unrelated.

## Architecture

Fireworks speaks the OpenAI chat/completions protocol. Our `pipeline/llm_client.py` already wraps `openai.AsyncOpenAI` with per-provider base URLs. Fireworks is at:

```
https://api.fireworks.ai/inference/v1
```

Authentication: `Bearer` token in `Authorization` header.

## What changed

| # | What | Was | → Now |
|---|---|---|---|
| 1 | `.env` key | `DEEPSEEK_API_KEY` only | `FIREWORKS_API_KEY` added |
| 2 | `config/providers.json` defaults | `opencode` (free tier) | `fireworks` (AMD credits) |
| 3 | LLM model in providers.json | `deepseek-v3p1` (outdated) | `deepseek-v4-pro` or `deepseek-v4-flash` |

## Our agents — which ones use LLMs

| Agent | Role | Uses LLM? | Task complexity |
|---|---|---|---|
| Agent 1 (Intake) | Clustering, noise detection, vertical classification | Yes | Moderate — binary classify + labels |
| Agent 2 (Forensic) | Claim extraction + framing scoring (combined prompt) | Yes | **High** — structured JSON extraction from news text |
| Agent 3 (Consensus) | Cross-source claim alignment | No | Pure math, no LLM |
| Agent 4 (Silent Auditor) | Text diff comparison | No | `difflib.SequenceMatcher`, no LLM |

Only Agents 1 and 2 matter for model selection.

## Available Fireworks models

From Fireworks serverless pricing (July 2026). All model IDs are prefixed `accounts/fireworks/models/`.

| Model | ID suffix | Input / Cached / Output (per 1M) | Reasoning quality |
|---|---|---|---|
| DeepSeek V4 Flash | `deepseek-v4-flash` | $0.14 / $0.028 / $0.28 | Good — fast classification, simple JSON |
| GPT OSS 120B | `gpt-oss-120b` | $0.15 / $0.015 / $0.60 | Good — OpenAI architecture |
| MiniMax M3 | `minimax-m3` | $0.30 / $0.06 / $1.20 | Good — balanced |
| Qwen 3.7 Plus | `qwen3p7-plus` | $0.40 / $0.08 / $1.60 | Strong — good all-rounder |
| DeepSeek V4 Pro | `deepseek-v4-pro` | $1.74 / $0.145 / $3.48 | **Best** — complex reasoning, structured output |
| Kimi K2.6 | `kimi-k2p6` | $0.95 / $0.16 / $4.00 | Excellent — agentic/tool-calling |
| GLM 5.2 | `glm-5p2` | $1.40 / $0.14 / $4.40 | Strong |

Embedding model (Agent 1): `nomic-ai/nomic-embed-text-v1.5` — $0.10/1M input tokens.

## Preset stacks

Pick a tier and set both `agent1_llm` and `agent2_llm` in `config/providers.json` defaults to the same provider (Fireworks), just change the model per agent.

### 💰 Cheap — ~$0.30 per daily pipeline run

| Agent | Model | Monthly est. (daily runs) |
|---|---|---|
| Agent 1 (noise + classify) | `deepseek-v4-flash` | ~$0.05 |
| Agent 2 (claims + framing) | `deepseek-v4-flash` | ~$0.25 |
| **Total** | | **~$0.30** |

Best for: testing, backfill, framing scorer. Claims extraction quality will be lower.

### ⚖️ Moderate — ~$2.50 per daily pipeline run

| Agent | Model | Monthly est. (daily runs) |
|---|---|---|
| Agent 1 (noise + classify) | `deepseek-v4-flash` | ~$0.05 |
| Agent 2 (claims + framing) | `deepseek-v4-pro` | ~$2.50 |
| **Total** | | **~$2.50** |

Best for: production quality claims extraction on a budget. The claim extraction is the quality bottleneck — spend there.

### 🏆 Best — ~$5.00 per daily pipeline run

| Agent | Model | Monthly est. (daily runs) |
|---|---|---|
| Agent 1 (noise + classify) | `qwen3p7-plus` | ~$0.50 |
| Agent 2 (claims + framing) | `deepseek-v4-pro` or `kimi-k2p6` | ~$4.50 |
| **Total** | | **~$5.00** |

Best for: hackathon demos where quality matters more than cost.

## Cost estimate (backfill)

~1,500 articles still need LLM framing scores. At ~3K tokens/article (prompt + response):

| Model | Total cost |
|---|---|
| DeepSeek V4 Flash | ~$0.25 |
| DeepSeek V4 Pro | ~$3.00 |
| Qwen 3.7 Plus | ~$1.00 |

## Known gotchas

- **Fireworks has a hard rate limit** (~200 calls before 429 errors). The budget resets on their timer (unknown interval). DeepSeek API has no rate limit with a 2s delay between calls — better for bulk backfill.
- **DeepSeek API is faster** (~1.5s/call) than Fireworks (~6s/call) for simple framing prompts. Fireworks serverless has cold-start overhead.
- For production pipeline: use Fireworks for Agents 1+2 (quality), DeepSeek for bulk framing backfill (speed + no rate limits).

## Reference

- Docs: https://docs.fireworks.ai/
- Pricing: https://docs.fireworks.ai/serverless/pricing
- Chat completions: https://docs.fireworks.ai/api-reference/post-chatcompletions
- Full doc index: https://docs.fireworks.ai/llms.txt
