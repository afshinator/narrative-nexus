"""Reputation scoring — pure functions for all 6 dimensions.

R_orig, R_val, R_speed are computable from claims data now.
R_frame, R_edit, R_correct return identity values (0.0) until
their respective agents (ForensicExtraction, SilentAuditor) produce data.
"""
import statistics


def compute_r_orig(originated: int, total: int) -> float:
    """Outlier Origination Rate — percentage of total claims originated by this source."""
    if total == 0:
        return 0.0
    return (originated / total) * 100


def compute_r_val(absorbed: int, originated: int) -> float:
    """Outlier Validation Rate — percentage of originated claims that became absorbed."""
    if originated == 0:
        return 0.0
    return (absorbed / originated) * 100


def compute_r_speed(absorption_delays: list[float]) -> float:
    """Speed Premium — median days between origination and absorption. Lower is better."""
    if len(absorption_delays) < 2:
        return 0.0
    return statistics.median(absorption_delays)


def compute_r_frame(framing_scores: list[float]) -> float:
    """Framing Consistency — standard deviation of framing scores across articles.
    Returns 0.0 when insufficient data (0-1 data points — no variance)."""
    if len(framing_scores) < 2:
        return 0.0
    return statistics.stdev(framing_scores)


def compute_r_edit(edit_count: int, article_count: int) -> float:
    """Silent Edit Rate — percentage of articles with unreported edits."""
    if article_count == 0:
        return 0.0
    return (edit_count / article_count) * 100


def compute_r_correct(correction_count: int, article_count: int) -> float:
    """Formal Correction Rate — percentage of articles with published corrections."""
    if article_count == 0:
        return 0.0
    return (correction_count / article_count) * 100
