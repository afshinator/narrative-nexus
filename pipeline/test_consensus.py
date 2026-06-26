"""Tests for pipeline.consensus — baseline and classification."""
from pipeline.consensus import compute_baseline_pct, classify_claim


class TestComputeBaselinePct:
    def test_zero_when_no_sources(self):
        assert compute_baseline_pct(reporting_sources=0, pool_size=10) == 0.0

    def test_full_pool(self):
        assert compute_baseline_pct(reporting_sources=10, pool_size=10) == 100.0

    def test_half_pool(self):
        assert compute_baseline_pct(reporting_sources=5, pool_size=10) == 50.0


class TestClassifyClaim:
    def test_absorbed_when_above_threshold(self):
        assert classify_claim(75.0, 65) == "CONSENSUS_ABSORBED"

    def test_pending_when_below_threshold(self):
        assert classify_claim(40.0, 65) == "PENDING"

    def test_exact_threshold(self):
        assert classify_claim(65.0, 65) == "CONSENSUS_ABSORBED"
