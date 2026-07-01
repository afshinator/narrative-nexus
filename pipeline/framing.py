"""Framing scorers — lexical, sentiment, and LLM-based editorial bias ratings.

All three scorers take article text and return a numeric score. Scores are
stored in article_framing for later comparison — the user picks which
scorer(s) to use for R_frame computation.
"""
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# ── Word lists for lexical scorer ────────────────────────────────────────
# Edit these lists to tune what counts as "loaded" language.

ADJECTIVES = {
    "controversial", "divisive", "embattled", "stunning", "disastrous",
    "catastrophic", "devastating", "unprecedented", "shocking", "dramatic",
    "sweeping", "bold", "aggressive", "radical", "extreme",
    "massive", "historic", "remarkable", "extraordinary", "staggering",
    "grim", "bleak", "dire", "alarming", "troubling",
    "brutal", "savage", "ruthless", "merciless", "heartless",
    "outrageous", "absurd", "ridiculous", "laughable", "pathetic",
    "crucial", "critical", "vital", "essential", "pivotal",
    "corrupt", "crooked", "fraudulent", "illegitimate", "scandalous",
}

HEDGES = {
    "arguably", "reportedly", "allegedly", "supposedly", "purportedly",
    "apparently", "seemingly", "ostensibly", "presumably", "possibly",
    "potentially", "conceivably", "perhaps", "maybe", "might",
    "could", "would", "should",  # modal hedges
}

# ── Sentiment scorer ─────────────────────────────────────────────────────

_analyzer: SentimentIntensityAnalyzer | None = None


def _get_analyzer() -> SentimentIntensityAnalyzer:
    global _analyzer
    if _analyzer is None:
        _analyzer = SentimentIntensityAnalyzer()
    return _analyzer


def score_sentiment(text: str) -> float:
    """VADER compound polarity score. -1 (negative) to +1 (positive)."""
    if not text or not text.strip():
        return 0.0
    return float(_get_analyzer().polarity_scores(text)["compound"])


# ── Lexical scorer ───────────────────────────────────────────────────────

def score_lexical(text: str) -> float:
    """Adjective + hedge word density as fraction of total words. 0-1."""
    if not text or not text.strip():
        return 0.0
    words = text.lower().split()
    if not words:
        return 0.0
    loaded = sum(1 for w in words if w in ADJECTIVES or w in HEDGES)
    return min(loaded / len(words), 1.0)


# ── LLM scorer (prompt only — caller handles API) ────────────────────────

def score_llm_prompt(article_text: str) -> str:
    """Build the framing-only prompt for backfill (no claims extraction)."""
    return f"""Rate the editorial framing bias of this news article on a scale of 1-10.

1 = Pure wire-service style. Just the facts, no adjectives, no opinion.
    Example: "The president signed the bill into law Tuesday afternoon."
3 = Mostly neutral with occasional loaded language.
    Example: "The controversial legislation, debated for months, was signed Tuesday."
5 = Moderate editorial framing. Clear word choices that steer interpretation.
    Example: "The embattled president reluctantly signed the deeply divisive bill into law."
7 = Heavy editorializing. Strong adjectives, clear author opinion, dramatic framing.
    Example: "In a stunning capitulation, the president caved to pressure and signed the disastrous bill."
10 = Pure opinion piece. Every sentence carries judgment.
    Example: "The corrupt administration rammed through yet another catastrophic policy Tuesday, proving once again that they answer only to their billionaire donors."

Article: {article_text}

Return JSON: {{"score": <integer 1-10>}}"""
