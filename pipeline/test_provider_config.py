"""Tests for pipeline.provider_config — config loading and agent resolution."""
import json
import tempfile
import os
import pytest
from pipeline.provider_config import load_provider_config, get_provider_for_agent


# ── Test data ───────────────────────────────────────────────────────────

MINIMAL_CONFIG = {
    "providers": {
        "embeddings": [
            {"id": "local-cpu", "name": "Local CPU", "model": "all-MiniLM-L6-v2", "amd": False},
            {"id": "fireworks", "name": "Fireworks", "model": "nomic-embed-text-v1.5", "amd": True},
        ],
        "llm": [
            {"id": "opencode", "name": "OpenCode Zen", "model": "deepseek-v4-flash-free", "amd": False},
            {"id": "fireworks", "name": "Fireworks", "model": "deepseek-v3p1", "amd": True},
        ],
    },
    "defaults": {
        "agent1_embedding": "local-cpu",
        "agent1_llm": "opencode",
        "agent2_llm": "opencode",
        "agent4_llm": "opencode",
    },
}


def _write_config(data: dict) -> str:
    """Write a config dict to a temp JSON file, return path."""
    path = tempfile.mktemp(suffix=".json")
    with open(path, "w") as f:
        json.dump(data, f)
    return path


# ── load_provider_config ────────────────────────────────────────────────


class TestLoadProviderConfig:
    def test_loads_valid_config(self):
        path = _write_config(MINIMAL_CONFIG)
        cfg = load_provider_config(path)
        assert "providers" in cfg
        assert "defaults" in cfg
        assert len(cfg["providers"]["embeddings"]) == 2
        assert len(cfg["providers"]["llm"]) == 2

    def test_raises_on_missing_file(self):
        with pytest.raises(FileNotFoundError):
            load_provider_config("/nonexistent/providers.json")

    def test_validates_providers_section(self):
        bad = {"defaults": {}}
        path = _write_config(bad)
        with pytest.raises(ValueError, match="providers"):
            load_provider_config(path)

    def test_validates_defaults_section(self):
        bad = {"providers": {"embeddings": [], "llm": []}}
        path = _write_config(bad)
        with pytest.raises(ValueError, match="defaults"):
            load_provider_config(path)


# ── get_provider_for_agent ──────────────────────────────────────────────


class TestGetProviderForAgent:
    def test_returns_default_provider(self):
        cfg = MINIMAL_CONFIG
        p = get_provider_for_agent(cfg, "agent2_llm")
        assert p["id"] == "opencode"
        assert p["model"] == "deepseek-v4-flash-free"

    def test_returns_embedding_provider(self):
        cfg = MINIMAL_CONFIG
        p = get_provider_for_agent(cfg, "agent1_embedding")
        assert p["id"] == "local-cpu"
        assert p["model"] == "all-MiniLM-L6-v2"

    def test_raises_on_unknown_agent_slot(self):
        cfg = MINIMAL_CONFIG
        with pytest.raises(ValueError, match="unknown agent slot"):
            get_provider_for_agent(cfg, "agent9_llm")

    def test_raises_on_unknown_provider_id(self):
        cfg = MINIMAL_CONFIG
        bad_defaults = {
            "agent1_embedding": "local-cpu",
            "agent1_llm": "nonexistent",
            "agent2_llm": "opencode",
            "agent4_llm": "opencode",
        }
        cfg_bad = {**cfg, "defaults": bad_defaults}
        with pytest.raises(ValueError, match="not found"):
            get_provider_for_agent(cfg_bad, "agent1_llm")

    def test_falls_back_to_overrides(self):
        """Overrides dict takes precedence over defaults."""
        cfg = MINIMAL_CONFIG
        overrides = {"agent2_llm": "fireworks"}
        p = get_provider_for_agent(cfg, "agent2_llm", overrides=overrides)
        assert p["id"] == "fireworks"
        assert p["amd"] is True

    def test_overrides_dont_affect_other_agents(self):
        cfg = MINIMAL_CONFIG
        overrides = {"agent2_llm": "fireworks"}
        p = get_provider_for_agent(cfg, "agent1_llm", overrides=overrides)
        assert p["id"] == "opencode"  # still default
