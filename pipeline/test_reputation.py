"""Tests for pipeline.reputation — pure scoring functions."""
import pytest
from pipeline.reputation import (
    compute_r_orig,
    compute_r_val,
    compute_r_speed,
    compute_r_frame,
    compute_r_edit,
    compute_r_correct,
)


class TestROrig:
    def test_returns_zero_with_no_claims(self):
        assert compute_r_orig(originated=0, total=0) == 0.0

    def test_computes_percentage(self):
        assert compute_r_orig(originated=5, total=20) == 25.0

    def test_hundred_percent(self):
        assert compute_r_orig(originated=10, total=10) == 100.0


class TestRVal:
    def test_returns_zero_with_no_originated(self):
        assert compute_r_val(absorbed=0, originated=0) == 0.0

    def test_computes_ratio(self):
        assert compute_r_val(absorbed=7, originated=10) == 70.0


class TestRSpeed:
    def test_returns_zero_with_insufficient_data(self):
        assert compute_r_speed([]) == 0.0
        assert compute_r_speed([5.0]) == 0.0

    def test_computes_median_days(self):
        assert compute_r_speed([3.0, 5.0, 7.0]) == 5.0


class TestRFrame:
    def test_returns_zero_with_insufficient_data(self):
        assert compute_r_frame([]) == 0.0
        assert compute_r_frame([0.5]) == 0.0

    def test_computes_stdev(self):
        result = compute_r_frame([1.0, 2.0, 3.0])
        assert result > 0


class TestREdit:
    def test_returns_zero_with_no_articles(self):
        assert compute_r_edit(edit_count=0, article_count=0) == 0.0

    def test_computes_rate(self):
        assert compute_r_edit(edit_count=3, article_count=100) == 3.0


class TestRCorrect:
    def test_returns_zero_with_no_articles(self):
        assert compute_r_correct(correction_count=0, article_count=0) == 0.0

    def test_computes_rate(self):
        assert compute_r_correct(correction_count=2, article_count=50) == 4.0
