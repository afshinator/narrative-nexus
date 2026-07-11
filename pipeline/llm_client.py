"""Provider-agnostic LLM client — one `openai.AsyncOpenAI` per provider.

All providers (Fireworks, OpenCode Zen, DeepSeek, OpenAI) expose
OpenAI-compatible chat completions endpoints.  This module wraps the openai
library with per-provider base URLs and API keys.

Env vars for credentials:
  FIREWORKS_API_KEY, OPENCODE_API_KEY, DEEPSEEK_API_KEY, OPENAI_API_KEY

Usage:
  provider = get_provider_for_agent(cfg, "agent2_llm")
  client = LLMClient(provider, api_key=os.environ["OPENCODE_API_KEY"])
  output = await client.chat(messages=[...], response_format={"type": "json_object"})
"""

import os
import logging
from typing import Any

import openai

logger = logging.getLogger("narrative_nexus.llm")

# ── Provider → base URL mapping ─────────────────────────────────────────
# Every provider speaks the OpenAI chat/completions protocol.

PROVIDER_BASE_URLS: dict[str, str] = {
    "fireworks": "https://api.fireworks.ai/inference/v1",
    "opencode": "https://opencode.ai/zen/v1",
    "deepseek": "https://api.deepseek.com/v1",
    "openai": "https://api.openai.com/v1",
}

# ── Env var naming convention: {PROVIDER_ID}_API_KEY (uppercase) ─────────


def _env_key(provider_id: str) -> str:
    return f"{provider_id.upper()}_API_KEY"


class LLMClient:
    """Unified async LLM client backed by openai.AsyncOpenAI.

    Each instance is bound to one provider + model.  For per-agent provider
    switching, create a new LLMClient per agent run.
    """

    def __init__(self, provider: dict[str, Any], *, api_key: str = ""):
        """Create an LLM client for a specific provider and model.

        Args:
          provider: Dict with id, name, model fields (from config/providers.json).
          api_key: API key for the provider.  If empty, the env var
                   {PROVIDER_ID}_API_KEY is tried as a fallback.

        Raises:
          ValueError: if api_key is empty and the env var is also unset.
        """
        self.provider_id: str = provider["id"]
        self.model: str = provider["model"]
        self.provider_name: str = provider["name"]

        if not api_key:
            key_env = provider.get("api_key_env") or _env_key(self.provider_id)
            api_key = os.environ.get(key_env, "")
        if not api_key:
            raise ValueError(
                f"No API key for provider {self.provider_id!r}. "
                f"Set {_env_key(self.provider_id)} env var or pass api_key=."
            )

        base_url = provider.get("base_url") or PROVIDER_BASE_URLS.get(self.provider_id)
        if base_url is None:
            raise ValueError(f"Unknown provider id: {self.provider_id!r}")

        self._openai = openai.AsyncOpenAI(
            base_url=base_url,
            api_key=api_key,
            timeout=60.0,
        )

    async def chat(
        self,
        *,
        messages: list[dict[str, str]],
        response_format: dict[str, str] | None = None,
        temperature: float = 0.0,
        max_tokens: int = 2000,
    ) -> str:
        """Send a chat completion request and return the text content.

        Returns empty string if the response content is None (e.g. tool-call
        responses).  This is a safety measure — the callers should validate
        output when response_format is used.

        Providers that support structured output will respect
        response_format={"type": "json_object"}.
        """
        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if response_format is not None:
            kwargs["response_format"] = response_format

        completion = await self._openai.chat.completions.create(**kwargs)
        content = completion.choices[0].message.content

        # T3: log token usage for credit budgeting
        if completion.usage:
            logger.info(
                "llm_call provider=%s model=%s prompt_tokens=%d completion_tokens=%d",
                self.provider_id, self.model,
                completion.usage.prompt_tokens,
                completion.usage.completion_tokens,
            )

        return content if content is not None else ""
