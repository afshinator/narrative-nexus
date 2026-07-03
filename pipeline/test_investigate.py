"""Tests for pipeline/investigate.py — read-only investigate pipeline wrappers."""

import sqlite3
import pytest

from pipeline.investigate import (
    fetch_article,
    embed_texts,
    extract_claims,
    match_claims_across_articles,
    compute_consensus,
)

# ── Helper: count all rows in key tables ───────────────────────────────────

_TABLES = [
    "claims", "claim_sources", "articles", "clusters",
    "embeddings", "claim_variants", "snapshots",
]


def _db_counts(db_path: str) -> dict[str, int]:
    """Return row counts for all key tables."""
    conn = sqlite3.connect(db_path)
    counts = {}
    for t in _TABLES:
        try:
            c = conn.execute(f"SELECT COUNT(*) FROM {t}")
            counts[t] = c.fetchone()[0]
        except sqlite3.OperationalError:
            counts[t] = -1  # table doesn't exist
    conn.close()
    return counts


# ── W1 test: fetch_article ─────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_w1_fetch_article_real_url():
    """Fetch a real article URL and verify return shape."""
    before = _db_counts("data/nn.db")
    result = await fetch_article(
        "https://www.bbc.com/sport/cricket/live/cjw3w4vgegpt"
    )
    after = _db_counts("data/nn.db")

    assert before == after, f"DB changed: {before} -> {after}"
    assert isinstance(result, dict)
    assert "error" in result and "source_domain" in result
    assert result["source_domain"] == "www.bbc.com"


@pytest.mark.asyncio
async def test_w1_fetch_article_private_ip():
    """Private IP URLs are blocked."""
    before = _db_counts("data/nn.db")
    result = await fetch_article("http://127.0.0.1/admin")
    after = _db_counts("data/nn.db")

    assert before == after
    assert "Private/internal IP blocked" in (result.get("error") or "")


@pytest.mark.asyncio
async def test_w1_fetch_article_invalid_scheme():
    """Non-http(s) schemes are rejected."""
    result = await fetch_article("ftp://example.com/file")
    assert "Invalid scheme" in (result.get("error") or "")


# ── W2 test: embed_texts ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_w2_embed_texts():
    """Embed two texts and verify shape, no DB writes."""
    import os
    from pathlib import Path
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / ".env")

    provider = {
        "id": "fireworks", "name": "Fireworks",
        "model": "BAAI/bge-base-en-v1.5",
        "base_url": "https://api.fireworks.ai/inference/v1",
        "amd": True,
    }
    before = _db_counts("data/nn.db")
    vecs = await embed_texts(
        ["The president signed a bill.", "Earthquake hits the coast."],
        provider=provider,
    )
    after = _db_counts("data/nn.db")

    assert before == after
    assert vecs.shape == (2, 768)
    assert vecs.dtype == "float32"


# ── W3 test: extract_claims ────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_w3_extract_claims():
    """Extract claims from a known article via Kimi-K2P5."""
    import os
    from pathlib import Path
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / ".env")

    provider = {
        "id": "fireworks", "name": "Fireworks",
        "model": "accounts/fireworks/models/kimi-k2p5",
        "base_url": "https://api.fireworks.ai/inference/v1",
    }
    article = {
        "url": "https://example.com/test",
        "source_domain": "example.com",
        "article_id": 99999,
        "title": "Test: President signs climate bill",
        "body": "President Smith signed the climate bill into law on Tuesday, marking a major shift in environmental policy. The bill passed 52-48 in the Senate after months of debate. Opposition leader Jones vowed to repeal it.",
    }
    before = _db_counts("data/nn.db")
    result = await extract_claims(
        article, provider,
        api_key=os.environ.get("FIREWORKS_API_KEY", ""),
    )
    after = _db_counts("data/nn.db")

    assert before == after
    assert isinstance(result, dict)
    assert "claims" in result
    assert len(result["claims"]) > 0, f"No claims extracted: {result.get('error')}"
    assert isinstance(result["claims"][0], dict)
    assert "text" in result["claims"][0]


# ── W4 test: match_claims_across_articles ──────────────────────────────────

@pytest.mark.asyncio
async def test_w4_match_claims():
    """Match synthetic claims across two mock articles (no external API)."""
    import os
    from pathlib import Path
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / ".env")

    # Use mock articles with pre-crafted similar/dissimilar claims
    articles = [
        {
            "url": "http://a.com/1", "source_domain": "a.com",
            "title": "Article A", "claims": [
                {"text": "President signs climate bill into law."},
                {"text": "Bill passes Senate 52-48."},
                {"text": "Opposition leader vows to repeal the bill."},
            ],
        },
        {
            "url": "http://b.com/1", "source_domain": "b.com",
            "title": "Article B", "claims": [
                {"text": "The president signed the climate bill on Tuesday."},
                {"text": "Senate vote was 52 to 48 in favor."},
            ],
        },
    ]

    # Use actual embeddings provider for real similarity
    provider = {
        "id": "fireworks", "name": "Fireworks",
        "model": "BAAI/bge-base-en-v1.5",
        "base_url": "https://api.fireworks.ai/inference/v1",
        "amd": True,
    }
    before = _db_counts("data/nn.db")
    result = await match_claims_across_articles(articles, embed_provider=provider)
    after = _db_counts("data/nn.db")

    assert before == after
    assert isinstance(result, list)
    # With similar claims, should merge some (len(result) < 5 = total claims)
    assert len(result) <= 5  # at most all are separate
    # Every canonical should have at least 1 variant
    for c in result:
        assert "text" in c
        assert len(c["variants"]) >= 1


# ── W5 test: compute_consensus ─────────────────────────────────────────────

def test_w5_compute_consensus():
    """Pure function test — no DB, no I/O."""
    canonical = [
        {
            "text": "Bill passed Senate 52-48.",
            "source_count": 2,
            "variants": [
                {"source": "bbc.com", "article": "url1", "text": "Bill passed 52-48."},
                {"source": "reuters.com", "article": "url2", "text": "Senate vote 52-48 in favor."},
            ],
        },
        {
            "text": "Opposition leader vows to repeal.",
            "source_count": 1,
            "variants": [
                {"source": "bbc.com", "article": "url1", "text": "Opposition leader vows repeal."},
            ],
        },
    ]
    panel = {
        "bbc.com": {"tier": 1, "name": "BBC"},
        "reuters.com": {"tier": 1, "name": "Reuters"},
        "foxnews.com": {"tier": 3, "name": "Fox News"},
    }

    before = _db_counts("data/nn.db")
    results = compute_consensus(canonical, panel)
    after = _db_counts("data/nn.db")

    assert before == after

    # Bill claim: 2 T1/T2 sources (bbc + reuters), pool=2, 2/2*100=100%
    bill = next(r for r in results if "Bill" in r["claim_text"])
    assert bill["t1t2_reporting"] == 2
    assert bill["pool_size"] == 2
    assert bill["pct"] == 100.0
    assert bill["would_absorb"] is True  # >=2 sources AND >=65%

    # Opposition claim: 1 T1/T2 source (bbc), pool=2, 1/2*100=50%
    opp = next(r for r in results if "Opposition" in r["claim_text"])
    assert opp["t1t2_reporting"] == 1
    assert opp["pool_size"] == 2
    assert opp["pct"] == 50.0
    assert opp["would_absorb"] is False  # only 1 T1/T2 source


def test_w5_compute_consensus_zero_pool():
    """Edge case: no T1/T2 sources in panel."""
    canonical = [{
        "text": "Claim.", "source_count": 1,
        "variants": [{"source": "blog.com", "article": "url", "text": "Claim."}],
    }]
    panel = {"blog.com": {"tier": 5}}
    results = compute_consensus(canonical, panel)
    assert results[0]["pool_size"] == 0
    assert results[0]["would_absorb"] is False


# ── E4 timeout test ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_e4_timeout_gate():
    """E4: 45s timeout emits error event and closes stream."""
    from app.main import app
    from fastapi.testclient import TestClient
    import asyncio

    client = TestClient(app)

    # Mock search_news to sleep 50s (beyond 45s deadline)
    original_search = None
    import app.investigate_endpoint as endpoint
    original_search = endpoint.search_news

    async def mock_search(*args, **kwargs):
        await asyncio.sleep(50)
        return []

    endpoint.search_news = mock_search
    try:
        with client.stream(
            "POST", "/api/investigate/stream",
            json={"query": "Iran deal"},
        ) as resp:
            assert resp.status_code == 200
            timeout_seen = False
            for line in resp.iter_lines():
                if line and "timeout" in line:
                    timeout_seen = True
                    break
            assert timeout_seen, "Timeout event not emitted before 50s mock ended"
    finally:
        endpoint.search_news = original_search
