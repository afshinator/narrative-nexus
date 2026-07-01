"""Vertical classifier — embedding proximity to prototype descriptions.

Single place for all vertical classification logic. To adjust classification,
edit VERTICAL_PROTOTYPES below — richer descriptions improve accuracy.

Uses sentence-transformers (all-MiniLM-L6-v2, same as Agent 1 embeddings).
Prototype embeddings are computed once and cached in memory.
"""
from __future__ import annotations
from collections import Counter

import numpy as np

# ── Vertical prototypes ─────────────────────────────────────────────────
# Richer = better separation. These paragraphs define what each vertical
# "sounds like" in embedding space. Edit freely to tune classification.

VERTICAL_PROTOTYPES: dict[str, str] = {
    "geopolitics": (
        "International relations, diplomacy, military conflict and war, economic sanctions, "
        "government policy and legislation, elections and political campaigns, national security, "
        "treaties and alliances, border disputes, sovereignty, regime change, "
        "civil unrest and protests, human rights violations, humanitarian crises, refugees, "
        "immigration policy, terrorism, intelligence operations, defense spending, "
        "arms exports and military procurement, peace negotiations, UN resolutions"
    ),
    "economics": (
        "Financial markets and stock exchanges, currency exchange rates and forex, "
        "central bank monetary policy, interest rate decisions, inflation and deflation, "
        "GDP growth and recession indicators, unemployment rates and labor markets, "
        "international trade policy, tariffs and trade wars, global supply chains, "
        "commodity prices including oil gold and agriculture, corporate earnings reports, "
        "mergers and acquisitions, initial public offerings IPOs, fiscal policy, "
        "taxation reform, government budget deficits, sovereign debt, banking regulation, "
        "housing markets, consumer spending, retail sales, manufacturing output"
    ),
    "technology": (
        "Artificial intelligence and machine learning models, semiconductor chip manufacturing, "
        "software development and programming, cybersecurity breaches and defense, "
        "data privacy regulations, encryption standards, social media platforms, "
        "cloud computing infrastructure, startup funding rounds and venture capital, "
        "digital transformation of industries, autonomous vehicles and self-driving, "
        "quantum computing breakthroughs, biotechnology and genetic engineering, "
        "space technology and commercial spaceflight, telecommunications and 5G networks, "
        "consumer electronics product launches, app stores and mobile platforms, "
        "open source software, developer tools, tech industry layoffs and hiring"
    ),
}

# ── Lazy-loaded model + pre-computed prototypes ────────────────────────

_model: SentenceTransformer | None = None
_prototype_embeddings: dict[str, np.ndarray] | None = None


def _get_model() -> SentenceTransformer:
    """Lazy-load the embedding model (shared with Agent 1's local-cpu path)."""
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer  # lazy import — server doesn't need it
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def _get_prototypes() -> dict[str, np.ndarray]:
    """Pre-compute prototype embeddings once."""
    global _prototype_embeddings
    if _prototype_embeddings is None:
        model = _get_model()
        _prototype_embeddings = {
            vertical: model.encode(description)
            for vertical, description in VERTICAL_PROTOTYPES.items()
        }
    return _prototype_embeddings


def _cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
    """Cosine similarity between two vectors."""
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def classify_text(text: str) -> str:
    """Classify a single text into a vertical.

    Embeds the text and returns the vertical whose prototype embedding
    is closest (cosine similarity). Falls back to "geopolitics" if
    text is empty.
    """
    if not text or not text.strip():
        return "geopolitics"

    model = _get_model()
    text_emb = model.encode(text[:2000])  # ponytail: truncate to 2000 chars
    prototypes = _get_prototypes()

    best_vertical = "geopolitics"
    best_sim = -1.0
    for vertical, proto_emb in prototypes.items():
        sim = _cosine_sim(text_emb, proto_emb)
        if sim > best_sim:
            best_sim = sim
            best_vertical = vertical
    return best_vertical


def classify_cluster(texts: list[str]) -> str:
    """Classify a cluster by majority vote across its articles.

    Each article is classified individually, then the most common
    vertical wins. Ties go to the first vertical encountered.
    Falls back to "geopolitics" for empty input.
    """
    if not texts:
        return "geopolitics"
    votes = [classify_text(t) for t in texts]
    return Counter(votes).most_common(1)[0][0]


def get_vertical_list() -> list[str]:
    """Return the ordered list of supported verticals."""
    return list(VERTICAL_PROTOTYPES.keys())
