"""Pipeline runner — sequences all four agents + daily snapshots.

ponytail: Sequential execution, single-threaded.  Each agent reads from and
writes to the DB, so the next agent has fresh data.
ponytail: geopolitics hardcoded until agent 1/2 support multi-vertical.
"""

import os
from datetime import datetime, timezone
from typing import Any

from db.connection import get_db
from db.sources import list_sources
from pipeline.provider_config import load_provider_config, get_provider_for_agent
from pipeline.agent1_intake import IntakeClusteringAgent
from pipeline.agent2_forensic import ForensicExtractionAgent
from pipeline.agent3_consensus import ConsensusAlignmentAgent
from pipeline.agent4_silent import SilentAuditorAgent
from pipeline.snapshots import (
    compute_panel_medians,
    compute_r_orig_raw,
    compute_r_speed_raw,
    compute_r_val_raw,
    percentile_rank,
    write_daily_snapshots,
)
from pipeline.archetype import get_archetype


# ── Config path ──────────────────────────────────────────────────────────

_DEFAULT_CONFIG_PATH = os.path.join(
    os.path.dirname(__file__), "..", "config", "providers.json"
)


def _load_providers() -> dict[str, Any]:
    """Load provider config from JSON file.

    Returns the full config (providers catalog + defaults).  Runtime
    overrides come from the caller via `provider_overrides` dict.
    """
    try:
        path = os.environ.get("NN_PROVIDERS_CONFIG", _DEFAULT_CONFIG_PATH)
        return load_provider_config(path)
    except (FileNotFoundError, ValueError) as exc:
        print(f"[pipeline] provider config unavailable: {exc}")
        return {
            "providers": {
                "embeddings": [
                    {"id": "local-cpu", "name": "Local CPU",
                     "model": "all-MiniLM-L6-v2", "amd": False},
                ],
                "llm": [
                    {"id": "opencode", "name": "OpenCode Zen",
                     "model": "deepseek-v4-flash-free", "amd": False},
                ],
            },
            "defaults": {
                "agent1_embedding": "local-cpu",
                "agent1_llm": "opencode",
                "agent2_llm": "opencode",
                "agent4_llm": "opencode",
            },
        }


def run_daily_pipeline(
    db_path: str,
    *,
    provider_overrides: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Run the full 4-agent pipeline in sequence.

    1. Agent 1 — Intake & Clustering (embeddings + DBSCAN)
    2. Agent 2 — Forensic Extraction (LLM claim extraction)
    3. Agent 3 — Consensus Alignment (pure Python math)
    4. Agent 4 — Silent Auditor (re-fetch + diff)
    5. Write daily reputation snapshots

    Args:
      db_path: Path to the SQLite database.
      provider_overrides: Optional dict of agent_slot → provider_id overrides
                          from runtime config (Pipeline Flow dropdowns).
                          If None, defaults from config/providers.json are used.

    Returns summary dict with per-agent counts.
    """
    cfg = _load_providers()

    summary: dict[str, Any] = {}

    # ── Agent 1: Intake & Clustering ──────────────────────────────────
    a1_embedding_provider = get_provider_for_agent(
        cfg, "agent1_embedding", overrides=provider_overrides,
    )
    a1 = IntakeClusteringAgent(
        db_path=db_path,
        embedding_provider=a1_embedding_provider,
    )
    import asyncio
    a1_result = asyncio.run(a1.run())
    summary["agent1"] = a1_result
    article_map = a1_result.get("article_map", {})

    # ── Agent 2: Forensic Extraction ─────────────────────────────────
    if article_map:
        a2_llm_provider = get_provider_for_agent(
            cfg, "agent2_llm", overrides=provider_overrides,
        )
        a2 = ForensicExtractionAgent(
            db_path=db_path,
            llm_provider=a2_llm_provider,
            # Env var fallback for API key
            api_key=os.environ.get(
                f"{a2_llm_provider['id'].upper()}_API_KEY", ""
            ),
        )
        a2_result = asyncio.run(a2.run(article_map=article_map))
        summary["agent2"] = a2_result
    else:
        summary["agent2"] = {"claims_extracted": 0, "articles_processed": 0}

    # ── Agent 3: Consensus Alignment ─────────────────────────────────
    conn = get_db(db_path)
    try:
        agent3 = ConsensusAlignmentAgent(db_path=db_path)
        a3_result = agent3.run_all(conn)
        summary["agent3"] = a3_result
    finally:
        conn.close()

    # ── Agent 4: Silent Auditor ──────────────────────────────────────
    a4 = SilentAuditorAgent(db_path=db_path)
    a4_result = asyncio.run(a4.run())
    summary["agent4"] = a4_result

    # ── Daily snapshots ──────────────────────────────────────────────
    conn2 = get_db(db_path)
    try:
        snap_count = _compute_and_write_snapshots(conn2)
        summary["snapshots_written"] = snap_count
    finally:
        conn2.close()

    return summary


# ── Snapshot computation (unchanged from original runner) ─────────────────


def _compute_and_write_snapshots(conn) -> int:
    """Compute reputation dimensions and write one snapshot per source per vertical.

    Pure function — no API keys, no external deps.
    """
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    sources = list_sources(conn)
    active_ids = {s["id"] for s in sources if s.get("active", 1)}

    # Compute raw values
    r_orig_raw = {k: float(v) for k, v in compute_r_orig_raw(conn).items()}
    r_val_raw = compute_r_val_raw(conn)
    r_speed_raw = compute_r_speed_raw(conn)

    # Percentile rank to 0-100
    r_orig = percentile_rank({k: v for k, v in r_orig_raw.items() if v is not None})
    r_val = percentile_rank({k: v for k, v in r_val_raw.items() if v is not None})
    r_speed = percentile_rank(
        {k: v for k, v in r_speed_raw.items() if v is not None}
    )

    # Panel medians for archetype assignment
    median_orig, median_val = compute_panel_medians(r_orig, r_val, active_ids)

    # Archetype per source
    archetypes: dict[int, str] = {}
    for sid in active_ids:
        orig = r_orig.get(sid)
        val = r_val.get(sid)
        if orig is not None and val is not None:
            archetypes[sid] = get_archetype(orig, val, median_orig, median_val)

    # Write snapshots for each vertical (ponytail: geopolitics hardcoded
    # until agent 1/2 can classify other verticals)
    total = 0
    for vertical in ["geopolitics"]:
        total += write_daily_snapshots(
            conn,
            date_str=date_str,
            vertical=vertical,
            r_orig=r_orig,
            r_val=r_val,
            r_speed=r_speed,
            archetypes=archetypes,
        )

    return total
