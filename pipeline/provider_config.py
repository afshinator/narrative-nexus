"""Provider configuration — load config file and resolve agent→provider mapping.

config/providers.json is the single source of truth for available providers and
defaults.  Runtime overrides (from Pipeline Flow dropdowns) are passed as an
overrides dict that takes precedence over defaults.

This module is pure config logic — no HTTP, no env vars, no side effects.
Env vars for API keys are consumed by llm_client / embedding_client at call time.
"""

import json
from typing import Any

# ── Agent slots that map to provider categories ─────────────────────────
# Each slot name determines which provider category to search.
_SLOT_CATEGORY: dict[str, str] = {
    "agent1_embedding": "embeddings",
    "agent1_llm": "llm",
    "agent2_llm": "llm",
    "agent4_llm": "llm",
}


def load_provider_config(path: str) -> dict[str, Any]:
    """Load and validate the provider config JSON file.

    Returns the parsed dict (providers + defaults).  Raises FileNotFoundError
    if the file is missing, ValueError if the structure is invalid.
    """
    with open(path) as f:
        data = json.load(f)

    if "providers" not in data:
        raise ValueError("Missing 'providers' section in config")
    providers = data["providers"]
    for category in ("embeddings", "llm"):
        if category not in providers:
            raise ValueError(f"Missing 'providers.{category}' in config")
        if not isinstance(providers[category], list):
            raise ValueError(f"'providers.{category}' must be a list")

    if "defaults" not in data:
        raise ValueError("Missing 'defaults' section in config")

    return data


def get_provider_for_agent(
    cfg: dict[str, Any],
    agent_slot: str,
    *,
    overrides: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Resolve which provider should handle a given agent slot.

    Looks up the slot in overrides first, then defaults, then finds the
    provider definition in the appropriate category list.

    Returns the provider dict (id, name, model, amd).  Raises ValueError
    if the slot is unknown or the resolved provider id is not in the catalog.
    """
    if agent_slot not in _SLOT_CATEGORY:
        valid = ", ".join(sorted(_SLOT_CATEGORY))
        raise ValueError(f"unknown agent slot {agent_slot!r} (valid: {valid})")

    category = _SLOT_CATEGORY[agent_slot]

    # Resolve provider id: overrides > defaults
    provider_id = None
    if overrides and agent_slot in overrides:
        provider_id = overrides[agent_slot]
    else:
        provider_id = cfg["defaults"].get(agent_slot)

    if provider_id is None:
        raise ValueError(f"no default provider for agent slot {agent_slot!r}")

    # Find the provider definition in the category list
    for p in cfg["providers"][category]:
        if p["id"] == provider_id:
            return p

    raise ValueError(
        f"provider {provider_id!r} (for {agent_slot}) not found in "
        f"providers.{category}"
    )
