"""Formal correction detection — inline marker patterns in article bodies.

Scans article body text for known correction phrases (AP style "CORRECTION:",
CNN style "This story has been updated", NYT style "An earlier version...").
Returns a list of detected patterns with matched text snippets.
"""
import re
from typing import Any

# ── Detection patterns ──────────────────────────────────────────────────
# (regex, pattern_name) pairs. Ordered — first match wins per pattern group.

CORRECTION_PATTERNS: list[tuple[str, str]] = [
    (r'\bCORRECTION:\s*(.+?)(?:\.\s+|\n|$)', 'ap_correction'),
    (r'\bThis (?:article|story|post) has been (?:updated|corrected)\b', 'cnn_update'),
    (r'\bAn earlier version of this article\b', 'nyt_earlier_version'),
    (r'\bCorrected on \w+ \d{1,2}, \d{4}\b', 'nyt_corrected_on'),
    (r'\bA previous version\b', 'previous_version'),
]

# Patterns that are NOT corrections (editorial intros, etc.)
_FALSE_POSITIVE_PATTERNS = [
    r"^Editor'?s\s+Note:",
]


def is_false_positive(line: str) -> bool:
    """Check if a line is a known false positive (editorial intro, not correction)."""
    for pattern in _FALSE_POSITIVE_PATTERNS:
        if re.search(pattern, line, re.IGNORECASE):
            return True
    return False


def detect_corrections(text: str) -> list[dict[str, Any]]:
    """Detect formal corrections in article body text.

    Returns a list of dicts with keys: pattern (str), matched_text (str).
    Empty list if no corrections found.
    """
    if not text or not text.strip():
        return []

    results: list[dict[str, Any]] = []
    seen_spans: set[tuple[int, int]] = set()

    for pattern, name in CORRECTION_PATTERNS:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            start, end = match.span()

            # Skip if this span overlaps with an already-matched correction
            if any(s <= end and start <= e for s, e in seen_spans):
                continue

            # False positive guard: skip if the matching line is an editorial intro
            line_start = text.rfind('\n', 0, start) + 1
            line_end = text.find('\n', end)
            if line_end == -1:
                line_end = len(text)
            line = text[line_start:line_end]
            if is_false_positive(line):
                continue

            matched = match.group(0)[:200]  # ponytail: truncate long matches
            results.append({
                "pattern": name,
                "matched_text": matched,
            })
            seen_spans.add((start, end))

    return results
