"""Archetype assignment — pure function matching frontend src/utils/archetype.ts."""


def get_archetype(r_orig: float, r_val: float, median_orig: float, median_val: float) -> str:
    """Classify a source into one of four archetypes based on R_orig and R_val vs panel median.

    Matches the TypeScript implementation exactly:
    - R_orig > median AND R_val > median  → EARLY_BREAKER
    - R_orig > median AND R_val ≤ median  → NOISE_GENERATOR
    - R_orig ≤ median AND R_val > median  → SELECTIVE_ACCURATE
    - otherwise                           → CONSENSUS_FOLLOWER
    """
    if r_orig > median_orig and r_val > median_val:
        return "EARLY_BREAKER"
    if r_orig > median_orig and r_val <= median_val:
        return "NOISE_GENERATOR"
    if r_orig <= median_orig and r_val > median_val:
        return "SELECTIVE_ACCURATE"
    return "CONSENSUS_FOLLOWER"
