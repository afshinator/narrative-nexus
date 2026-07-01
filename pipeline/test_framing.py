"""Tests for pipeline.framing — lexical, sentiment, and LLM framing scorers."""
import pytest
from pipeline.framing import (
    ADJECTIVES,
    HEDGES,
    score_lexical,
    score_sentiment,
    score_llm_prompt,
)


class TestWordLists:
    def test_adjectives_not_empty(self):
        assert len(ADJECTIVES) > 10

    def test_hedges_not_empty(self):
        assert len(HEDGES) > 5

    def test_no_overlap_between_lists(self):
        overlap = set(ADJECTIVES) & set(HEDGES)
        assert len(overlap) == 0, f"Overlapping words: {overlap}"


class TestScoreLexical:
    def test_empty_text_returns_zero(self):
        assert score_lexical("") == 0.0
        assert score_lexical("   ") == 0.0

    def test_neutral_text_low_score(self):
        text = "The president signed the bill into law Tuesday afternoon."
        score = score_lexical(text)
        assert 0.0 <= score < 0.3, f"Expected low score, got {score}"

    def test_loaded_text_higher_score(self):
        text = (
            "The embattled president reluctantly signed the deeply divisive "
            "and controversial bill into law Tuesday."
        )
        score = score_lexical(text)
        assert score > 0.15, f"Expected higher score, got {score}"

    def test_hedge_words_increase_score(self):
        text = "The policy might arguably lead to possibly significant changes."
        score = score_lexical(text)
        assert score > 0.1, f"Expected hedge-heavy score, got {score}"

    def test_score_bounded_0_to_1(self):
        text = "controversial controversial controversial " * 50
        score = score_lexical(text)
        assert 0.0 <= score <= 1.0

    def test_case_insensitive(self):
        lower = score_lexical("The Controversial Bill was signed.")
        upper = score_lexical("the controversial bill was signed.")
        assert lower == upper


class TestScoreSentiment:
    def test_neutral_text_near_zero(self):
        text = "The president signed the bill into law Tuesday."
        score = score_sentiment(text)
        assert -0.5 < score < 0.5, f"Expected near-zero, got {score}"

    def test_positive_text(self):
        text = "The wonderful breakthrough will save countless lives and bring hope to millions."
        score = score_sentiment(text)
        assert score > 0, f"Expected positive, got {score}"

    def test_negative_text(self):
        text = "The disastrous policy will destroy the economy and ruin millions of lives."
        score = score_sentiment(text)
        assert score < 0, f"Expected negative, got {score}"

    def test_empty_text_returns_zero(self):
        assert score_sentiment("") == 0.0
        assert score_sentiment("   ") == 0.0

    def test_score_bounded(self):
        text = "terrible horrible awful disastrous catastrophic " * 20
        score = score_sentiment(text)
        assert -1.0 <= score <= 1.0


class TestScoreLlmPrompt:
    def test_prompt_includes_anchored_scale(self):
        prompt = score_llm_prompt("Test article text")
        assert "1-10" in prompt
        assert "framing" in prompt
        assert "Test article text" in prompt

    def test_prompt_includes_examples(self):
        prompt = score_llm_prompt("Test")
        assert "wire-service" in prompt
        assert "embattled" in prompt  # example at scale 5
        assert "capitulation" in prompt  # example at scale 7
