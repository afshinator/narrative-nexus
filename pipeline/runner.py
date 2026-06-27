"""Pipeline runner — sequences agent 3 (consensus) then daily snapshot computation.

Scheduled daily via APScheduler. No class — one function.
"""
from datetime import datetime, timezone

from db.connection import get_db
from db.sources import list_sources
from pipeline.agent3_consensus import ConsensusAlignmentAgent
from pipeline.snapshots import (
    compute_panel_medians,
    compute_r_orig_raw,
    compute_r_speed_raw,
    compute_r_val_raw,
    percentile_rank,
    write_daily_snapshots,
)
from pipeline.archetype import get_archetype


def run_daily_pipeline(db_path: str) -> dict:
    """Run consensus alignment on all clusters, then write daily snapshots.

    Returns summary dict with counts.
    """
    conn = get_db(db_path)
    try:
        agent = ConsensusAlignmentAgent(db_path=db_path)
        agent_result = agent.run_all(conn)

        snap_count = _compute_and_write_snapshots(conn)
        return {
            "clusters_processed": agent_result.get("clusters", 0),
            "claims_classified": agent_result.get("classified", 0),
            "snapshots_written": snap_count,
        }
    finally:
        conn.close()


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

    # Write snapshots for each vertical (ponytail: geopolitics hardcoded until
    # agent 1/2 can classify other verticals)
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
