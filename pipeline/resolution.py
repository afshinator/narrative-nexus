"""Claim resolution state machine — pure function per the LOCKED design §4 schedule."""


def determine_state(baseline_pct: float, threshold: int, day: int) -> str:
    """Determine claim state based on baseline percentage, threshold, and day.

    Rules (design §4, LOCKED):
    - Any day: baseline_pct >= threshold → CONSENSUS_ABSORBED
    - Day 90: still below threshold → UNRESOLVED (terminal)
    - Otherwise: PENDING
    """
    if baseline_pct >= threshold:
        return "CONSENSUS_ABSORBED"
    if day >= 90:
        return "UNRESOLVED"
    return "PENDING"
