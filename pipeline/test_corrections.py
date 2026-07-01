"""Tests for pipeline.corrections — inline correction pattern detection."""
import pytest
from pipeline.corrections import (
    CORRECTION_PATTERNS,
    detect_corrections,
    is_false_positive,
)


class TestCorrectionPatterns:
    def test_all_patterns_compile(self):
        for pattern, name in CORRECTION_PATTERNS:
            import re
            re.compile(pattern)

    def test_ap_correction(self):
        text = "CORRECTION: Corrects month to June, instead of July."
        results = detect_corrections(text)
        assert len(results) == 1
        assert results[0]["pattern"] == "ap_correction"

    def test_cnn_update(self):
        text = "This story has been updated with additional information."
        results = detect_corrections(text)
        assert len(results) == 1
        assert results[0]["pattern"] == "cnn_update"

    def test_nyt_earlier_version(self):
        text = "An earlier version of this article misstated the day."
        results = detect_corrections(text)
        assert len(results) == 1
        assert results[0]["pattern"] == "nyt_earlier_version"

    def test_nyt_corrected_on(self):
        text = "Corrected on June 29, 2026: An earlier version misstated..."
        results = detect_corrections(text)
        # Matches both nyt_corrected_on AND nyt_earlier_version
        assert len(results) >= 1
        patterns = [r["pattern"] for r in results]
        assert "nyt_corrected_on" in patterns

    def test_previous_version(self):
        text = "A previous version of this report incorrectly stated..."
        results = detect_corrections(text)
        assert len(results) == 1
        assert results[0]["pattern"] == "previous_version"

    def test_this_article_has_been_corrected(self):
        text = "This article has been corrected to reflect the updated figures."
        results = detect_corrections(text)
        assert len(results) == 1

    def test_this_post_has_been_updated(self):
        text = "This post has been updated with new information from the White House."
        results = detect_corrections(text)
        assert len(results) == 1

    def test_empty_text_no_matches(self):
        assert detect_corrections("") == []
        assert detect_corrections("   ") == []

    def test_no_corrections_in_neutral_text(self):
        text = "The president signed the bill into law Tuesday afternoon."
        assert detect_corrections(text) == []

    def test_multiple_corrections_in_one_article(self):
        text = (
            "CORRECTION: Fixed the date. "
            "Also, this story has been updated with additional context."
        )
        results = detect_corrections(text)
        assert len(results) == 2


class TestFalsePositiveGuard:
    def test_editors_note_not_correction(self):
        """Editor's Note at paragraph start is an editorial intro, not correction."""
        text = "Editor's Note: Having enjoyed a long history, friendly exchanges..."
        assert detect_corrections(text) == []

    def test_editors_note_with_colon(self):
        text = "Editor's Note: Videos featuring Feng Shi, in which the renowned..."
        assert detect_corrections(text) == []

    def test_editors_note_lowercase(self):
        text = "editor's note: this is an introduction to the article series."
        assert detect_corrections(text) == []

    def test_correction_in_same_text_as_editors_note(self):
        """Editor's Note elsewhere shouldn't block correction detection elsewhere."""
        text = (
            "Editor's Note: This is part of a series.\n"
            "CORRECTION: An earlier version misstated the date.\n"
            "The president signed the bill."
        )
        results = detect_corrections(text)
        assert len(results) == 1
        assert results[0]["pattern"] == "ap_correction"
