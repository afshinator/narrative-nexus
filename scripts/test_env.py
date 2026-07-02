"""Verify .env loading works — FIREWORKS_API_KEY must be available at startup."""
import os
import sys

def test_env_loaded():
    """.env file is loaded by app/main.py at import time."""
    from dotenv import load_dotenv
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env_path = os.path.join(project_root, ".env")
    assert os.path.isfile(env_path), f".env not found at {env_path}"
    load_dotenv(env_path)
    key = os.environ.get("FIREWORKS_API_KEY", "")
    assert key, "FIREWORKS_API_KEY not set in .env or environment"
    assert key.startswith("fw"), f"FIREWORKS_API_KEY doesn't look like a Fireworks key: {key[:6]}..."

def test_provider_config_loads():
    """config/providers.json is valid and defaults to fireworks."""
    import json
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(project_root, "config", "providers.json")
    with open(config_path) as f:
        cfg = json.load(f)
    defaults = cfg["defaults"]
    for slot in ("agent1_llm", "agent2_llm", "agent4_llm"):
        assert defaults[slot] == "fireworks", f"{slot} defaults to {defaults[slot]}, expected fireworks"

    # Verify fireworks provider exists with a valid model
    llm_providers = {p["id"]: p for p in cfg["providers"]["llm"]}
    assert "fireworks" in llm_providers, "fireworks provider not in providers.llm"
    model = llm_providers["fireworks"]["model"]
    assert model.startswith("accounts/fireworks/models/"), f"Unexpected model: {model}"

def test_llm_client_creates():
    """LLMClient can be instantiated with the fireworks provider."""
    import json
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(os.path.join(project_root, "config", "providers.json")) as f:
        cfg = json.load(f)
    fireworks = next(p for p in cfg["providers"]["llm"] if p["id"] == "fireworks")

    from pipeline.llm_client import LLMClient
    client = LLMClient(fireworks)
    assert client.provider_id == "fireworks"
    assert "deepseek" in client.model.lower(), f"Unexpected model: {client.model}"


if __name__ == "__main__":
    # Also test from app/main.py import to verify it loads .env
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import app.main  # triggers load_dotenv at module level

    test_env_loaded()
    test_provider_config_loads()
    test_llm_client_creates()
    print("PASS: .env loaded, providers configured, FIREWORKS_API_KEY available")
