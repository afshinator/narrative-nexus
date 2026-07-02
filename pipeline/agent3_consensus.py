"""Consensus Alignment Agent — classifies claims, computes baseline, resolves states."""
from datetime import datetime, timezone
from pipeline.base_agent import BasePipelineAgent
from pipeline.consensus import compute_baseline_pct, DEFAULT_THRESHOLDS, MIN_CORROBORATION
from pipeline.resolution import determine_state
from db.connection import get_db, load_schema
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
        load_schema(conn)
        try:
            return self._run(conn, cluster_id)
        finally:
            conn.close()

    def run_all(self, conn) -> dict:
        """Run consensus alignment on all clusters. Returns summary."""
        from db.clusters import list_clusters
        clusters = list_clusters(conn, limit=0)  # 0 = no limit
        total_classified = 0
        for cluster in clusters:
            result = self._run(conn, cluster["id"])
            total_classified += result.get("classified", 0)
        return {"clusters": len(clusters), "classified": total_classified}

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
        pool_ids = {s["id"] for s in pool}

        claims = list_claims(conn, cluster_id=cluster_id, limit=0)

        # Denominator: T1+T2 sources that have at least one claim in this cluster
        # (review-03 H03 — not all T1+T2 sources, only those covering this story)
        cluster_source_ids: set[int] = set()
        for claim in claims:
            linked = list_claim_sources(conn, claim["id"])
            cluster_source_ids.update(cs["source_id"] for cs in linked)
        pool_size = len(pool_ids & cluster_source_ids)
        classified = 0
        max_pct = 0.0

        for claim in claims:
            linked = list_claim_sources(conn, claim["id"])
            reporting = len({cs["source_id"] for cs in linked if cs["source_id"] in pool_ids})
            pct = compute_baseline_pct(reporting, pool_size)
            max_pct = max(max_pct, pct)

            new_state = determine_state(pct, threshold=threshold, day=_days_since(claim["created_at"]))
            # D1: absorption requires >= MIN_CORROBORATION distinct sources
            if new_state == "CONSENSUS_ABSORBED" and reporting < MIN_CORROBORATION:
                new_state = "PENDING"
            if new_state != claim["state"]:
                absorbed = (
                    datetime.now(timezone.utc).isoformat()
                    if new_state == "CONSENSUS_ABSORBED"
                    else None
                )
                convergence = (
                    "CROSS_SOURCE_CONVERGENT"
                    if new_state == "CONSENSUS_ABSORBED"
                    else None
                )
                update_claim_state(conn, claim["id"], new_state, absorbed_at=absorbed, convergence_type=convergence)
                classified += 1

        baseline = {str(threshold): round(max_pct, 1)}
        return {"cluster_id": cluster_id, "baseline": baseline, "classified": classified}


def _days_since(date_str: str | None) -> int:
    from datetime import datetime, timezone
    if not date_str:
        return 0
    try:
        dt = datetime.fromisoformat(date_str)
    except (ValueError, TypeError):
        return 0
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)
    return (now - dt).days
