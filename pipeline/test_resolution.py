"""Tests for pipeline.resolution — state machine transitions."""
from pipeline.resolution import determine_state


class TestResolutionStateMachine:
    def test_absorbed_when_above_threshold(self):
        # Any day, threshold met → absorbed
        assert determine_state(baseline_pct=75.0, threshold=65, day=5) == "CONSENSUS_ABSORBED"

    def test_pending_before_day_90(self):
        # Before day 90, below threshold → still pending
        assert determine_state(baseline_pct=40.0, threshold=65, day=30) == "PENDING"

    def test_unresolved_at_day_90(self):
        # At day 90, below threshold → unresolved (terminal)
        assert determine_state(baseline_pct=40.0, threshold=65, day=90) == "UNRESOLVED"

    def test_absorbed_at_day_90(self):
        # At day 90, threshold met → absorbed
        assert determine_state(baseline_pct=80.0, threshold=65, day=90) == "CONSENSUS_ABSORBED"

    def test_day_7_check(self):
        assert determine_state(baseline_pct=70.0, threshold=65, day=7) == "CONSENSUS_ABSORBED"
        assert determine_state(baseline_pct=60.0, threshold=65, day=7) == "PENDING"

    # ── Phase 2 (T1): reporting corroboration tests ─────────────────────

    def test_single_source_below_min_corroboration_day_89(self):
        """Single-source claim (reporting=1 < MIN=2) stays PENDING even at 100%."""
        assert determine_state(
            baseline_pct=100.0, threshold=65, day=89, reporting=1,
        ) == "PENDING"

    def test_single_source_below_min_corroboration_day_90(self):
        """Single-source claim at day 90 → UNRESOLVED (was zombie bug)."""
        assert determine_state(
            baseline_pct=100.0, threshold=65, day=90, reporting=1,
        ) == "UNRESOLVED"

    def test_two_source_at_threshold_absorbed(self):
        """Two sources, pct meets threshold → ABSORBED."""
        assert determine_state(
            baseline_pct=65.0, threshold=65, day=5, reporting=2,
        ) == "CONSENSUS_ABSORBED"

    def test_two_source_below_threshold_pending(self):
        """Two sources, pct below threshold → PENDING."""
        assert determine_state(
            baseline_pct=64.0, threshold=65, day=5, reporting=2,
        ) == "PENDING"

    def test_two_source_below_threshold_day_90_unresolved(self):
        """Two sources, pct below threshold at day 90 → UNRESOLVED."""
        assert determine_state(
            baseline_pct=64.0, threshold=65, day=90, reporting=2,
        ) == "UNRESOLVED"
