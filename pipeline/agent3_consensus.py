"""Consensus Alignment Agent — classifies claims, computes baseline, resolves states."""
from pipeline.base_agent import BasePipelineAgent
from pipeline.consensus import compute_baseline_pct, DEFAULT_THRESHOLDS
from pipeline.resolution import determine_state
from db.connection import get_db
from db.clusters import get_cluster
from db.sources import list_sources
from db.claims import list_claims, update_claim_state
from db.claim_sources import list_claim_sources


class ConsensusAlignmentAgent(BasePipelineAgent):
    """Classifies claims within a cluster against the panel consensus threshold."""

    def __init__(self, db_path: str = ":memory:"):
        self.db_path = db_path

    async def run(self, cluster_id: int | None = None) -> dict:
        conn = get_db(self.db_path)
        try:
            return self._run(conn, cluster_id)
        finally:
            conn.close()

    def _run(self, conn, cluster_id: int | None) -> dict:
        if cluster_id is None:
            return {"cluster_id": None, "baseline": {}, "classified": 0}

        cluster = get_cluster(conn, cluster_id)
        if cluster is None:
            return {"cluster_id": cluster_id, "baseline": {}, "classified": 0}

        vertical = cluster["vertical"]
        threshold = DEFAULT_THRESHOLDS.get(vertical, 75)

        all_sources = list_sources(conn)
        pool = [s for s in all_sources if s["tier"] in (1, 2) and s.get("active", 1)]
        pool_size = len(pool)
        pool_ids = {s["id"] for s in pool}

        claims = list_claims(conn, cluster_id=cluster_id)
        classified = 0
        max_pct = 0.0

        for claim in claims:
            linked = list_claim_sources(conn, claim["id"])
            reporting = len({cs["source_id"] for cs in linked if cs["source_id"] in pool_ids})
            pct = compute_baseline_pct(reporting, pool_size)
            max_pct = max(max_pct, pct)

            new_state = determine_state(pct, threshold=threshold, day=_days_since(claim["created_at"]))
            if new_state != claim["state"]:
                update_claim_state(conn, claim["id"], new_state)
                classified += 1

        baseline = {str(threshold): round(max_pct, 1)}
        return {"cluster_id": cluster_id, "baseline": baseline, "classified": classified}


def _days_since(date_str: str | None) -> int:
    from datetime import datetime, timezone
    if not date_str:
        return 0
    dt = datetime.fromisoformat(date_str)
    now = datetime.now(timezone.utc)
    return (now - dt).days
