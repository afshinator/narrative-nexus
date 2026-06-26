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
