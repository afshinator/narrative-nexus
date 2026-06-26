"""Tests for pipeline.archetype — pure function, must match frontend src/utils/archetype.ts."""
from pipeline.archetype import get_archetype


class TestArchetype:
    def test_early_breaker(self):
        # R_orig above median, R_val above median
        assert get_archetype(80, 75, 50, 50) == "EARLY_BREAKER"

    def test_noise_generator(self):
        # R_orig above median, R_val at or below median
        assert get_archetype(80, 30, 50, 50) == "NOISE_GENERATOR"

    def test_selective_accurate(self):
        # R_orig at or below median, R_val above median
        assert get_archetype(30, 75, 50, 50) == "SELECTIVE_ACCURATE"

    def test_consensus_follower(self):
        # R_orig at or below median, R_val at or below median
        assert get_archetype(30, 30, 50, 50) == "CONSENSUS_FOLLOWER"

    def test_boundary_exact_median(self):
        # At exactly the median → at or below
        assert get_archetype(50, 50, 50, 50) == "CONSENSUS_FOLLOWER"
        assert get_archetype(50, 51, 50, 50) == "SELECTIVE_ACCURATE"
        assert get_archetype(51, 50, 50, 50) == "NOISE_GENERATOR"
