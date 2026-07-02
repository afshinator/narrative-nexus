"""Consensus baseline computation — pure threshold math."""

DEFAULT_THRESHOLDS = {"geopolitics": 65, "economics": 75, "technology": 75}

# D1: Minimum corroboration rule — a claim may only become CONSENSUS_ABSORBED
# if reported by >= 2 distinct consensus-pool (T1/T2) sources AND pct >=
# vertical threshold.  Single-source claims resolve to UNRESOLVED at 90 days.
MIN_CORROBORATION = 2


def compute_baseline_pct(reporting_sources: int, pool_size: int) -> float:
    """Percentage of the Tier 1+2 pool that has reported a claim."""
    if pool_size == 0:
        return 0.0
    return (reporting_sources / pool_size) * 100


def classify_claim(baseline_pct: float, threshold: int) -> str:
    """Classify a claim as CONSENSUS_ABSORBED or PENDING based on threshold."""
    if baseline_pct >= threshold:
        return "CONSENSUS_ABSORBED"
    return "PENDING"
