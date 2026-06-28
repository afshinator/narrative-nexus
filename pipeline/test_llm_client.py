"""Tests for pipeline.llm_client — provider-aware LLM client."""
import pytest
from unittest.mock import AsyncMock, patch

from pipeline.llm_client import LLMClient, PROVIDER_BASE_URLS


# ── Test fixtures ───────────────────────────────────────────────────────

SAMPLE_LLM_PROVIDER = {
    "id": "opencode",
    "name": "OpenCode Zen",
    "model": "deepseek-v4-flash-free",
    "amd": False,
}

SAMPLE_FIREWORKS_PROVIDER = {
    "id": "fireworks",
    "name": "Fireworks AI",
    "model": "deepseek-v3p1",
    "amd": True,
}

SAMPLE_DEEPSEEK_PROVIDER = {
    "id": "deepseek",
    "name": "DeepSeek API",
    "model": "deepseek-v4-flash",
    "amd": False,
}


# ── LLMClient.__init__ ──────────────────────────────────────────────────


class TestLLMClientInit:
    def test_creates_client_with_provider(self):
        client = LLMClient(SAMPLE_LLM_PROVIDER, api_key="test-key")
        assert client.provider_id == "opencode"
        assert client.model == "deepseek-v4-flash-free"
        assert client._openai is not None

    def test_raises_on_missing_api_key(self, monkeypatch):
        # Clear env var so the fallback doesn't rescue the test
        monkeypatch.delenv("OPENCODE_API_KEY", raising=False)
        with pytest.raises(ValueError, match="API key"):
            LLMClient(SAMPLE_LLM_PROVIDER, api_key="")

    def test_uses_correct_base_url_for_opencode(self):
        client = LLMClient(SAMPLE_LLM_PROVIDER, api_key="k")
        base = str(client._openai.base_url).rstrip("/")
        assert base == PROVIDER_BASE_URLS["opencode"].rstrip("/")

    def test_uses_correct_base_url_for_fireworks(self):
        client = LLMClient(SAMPLE_FIREWORKS_PROVIDER, api_key="k")
        base = str(client._openai.base_url).rstrip("/")
        assert base == PROVIDER_BASE_URLS["fireworks"].rstrip("/")

    def test_uses_correct_base_url_for_deepseek(self):
        client = LLMClient(SAMPLE_DEEPSEEK_PROVIDER, api_key="k")
        base = str(client._openai.base_url).rstrip("/")
        assert base == PROVIDER_BASE_URLS["deepseek"].rstrip("/")


# ── LLMClient.chat ──────────────────────────────────────────────────────


class TestLLMClientChat:
    @pytest.mark.asyncio
    async def test_chat_calls_openai_with_correct_params(self):
        with patch("pipeline.llm_client.openai.AsyncOpenAI") as mock_cls:
            mock_instance = mock_cls.return_value
            mock_completion = AsyncMock()
            mock_instance.chat.completions.create = mock_completion
            mock_completion.return_value.choices = [
                AsyncMock(message=AsyncMock(content='{"test": true}'))
            ]
            mock_completion.return_value.choices[0].finish_reason = "stop"

            client = LLMClient(SAMPLE_LLM_PROVIDER, api_key="k")
            result = await client.chat(
                messages=[{"role": "user", "content": "Hi"}],
                response_format={"type": "json_object"},
                temperature=0.0,
                max_tokens=500,
            )

            assert result == '{"test": true}'
            # Verify the call was made with the right model
            call_kwargs = mock_completion.call_args.kwargs
            assert call_kwargs["model"] == "deepseek-v4-flash-free"
            assert call_kwargs["temperature"] == 0.0
            assert call_kwargs["max_tokens"] == 500

    @pytest.mark.asyncio
    async def test_chat_returns_text_content(self):
        with patch("pipeline.llm_client.openai.AsyncOpenAI") as mock_cls:
            mock_instance = mock_cls.return_value
            mock_completion = AsyncMock()
            mock_instance.chat.completions.create = mock_completion
            mock_completion.return_value.choices = [
                AsyncMock(message=AsyncMock(content="plain text response"))
            ]

            client = LLMClient(SAMPLE_LLM_PROVIDER, api_key="k")
            result = await client.chat(messages=[{"role": "user", "content": "Hi"}])
            assert result == "plain text response"

    @pytest.mark.asyncio
    async def test_chat_handles_null_content(self):
        """Safety: Some providers may return content=None on tool calls etc."""
        with patch("pipeline.llm_client.openai.AsyncOpenAI") as mock_cls:
            mock_instance = mock_cls.return_value
            mock_completion = AsyncMock()
            mock_instance.chat.completions.create = mock_completion
            mock_completion.return_value.choices = [
                AsyncMock(message=AsyncMock(content=None))
            ]

            client = LLMClient(SAMPLE_LLM_PROVIDER, api_key="k")
            result = await client.chat(messages=[{"role": "user", "content": "Hi"}])
            assert result == ""  # null content → empty string


# ── LLMClient — provider lookup from config ─────────────────────────────


class TestLLMClientFromConfig:
    def test_from_config_resolves_provider(self):
        """Verify that LLMClient can be constructed from a full config dict."""
        from pipeline.provider_config import get_provider_for_agent

        cfg = {
            "providers": {"llm": [SAMPLE_LLM_PROVIDER, SAMPLE_FIREWORKS_PROVIDER]},
            "defaults": {"agent2_llm": "opencode"},
        }
        provider = get_provider_for_agent(cfg, "agent2_llm")
        assert provider["id"] == "opencode"
        client = LLMClient(provider, api_key="k")
        assert client.model == "deepseek-v4-flash-free"
