"""Claim resolution state machine — pure function per the LOCKED design §4 schedule."""

# Ponytail: import from consensus to avoid duplicating the constant.
# Circular import avoided — consensus.py has no imports from resolution.
MIN_CORROBORATION = 2


def determine_state(
    baseline_pct: float,
    threshold: int,
    day: int,
    *,
    reporting: int | None = None,
) -> str:
    """Determine claim state based on baseline percentage, threshold, day.

    Rules (design §4, LOCKED):
    - Any day: baseline_pct >= threshold AND reporting >= MIN_CORROBORATION
      → CONSENSUS_ABSORBED
    - Day 90: still below threshold OR insufficient corroboration → UNRESOLVED (terminal)
    - Otherwise: PENDING

    Phase 2 (T1): reporting parameter added to fix the 90-day zombie bug.
    A single-source claim always has pct=100 but must NOT be absorbed —
    it falls through to day-based logic so it can reach UNRESOLVED at day 90.
    """
    if baseline_pct >= threshold:
        if reporting is None or reporting >= MIN_CORROBORATION:
            return "CONSENSUS_ABSORBED"
        # Insufficient corroboration — fall through to day-based logic
        if day >= 90:
            return "UNRESOLVED"
        return "PENDING"
    if day >= 90:
        return "UNRESOLVED"
    return "PENDING"
