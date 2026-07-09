"""Track B Phase 2 — Read-only Investigate pipeline wrappers.

Every function here is proven read-only: it does not insert, update, or delete
any rows in the Narrative Nexus database.  All analysis is in-memory only.
"""

import asyncio
import json
import ipaddress
import logging
import time
import re
from typing import Any
from urllib.parse import urlparse

import numpy as np

from pipeline.extractor import ArticleExtractor
from pipeline.cleaner import get_embedding_input
from pipeline.embedding_client import EmbeddingClient
from pipeline.llm_client import LLMClient
from pipeline.agent2_forensic import EXTRACTION_SYSTEM_PROMPT
from pipeline.consensus import DEFAULT_THRESHOLDS, MIN_CORROBORATION

logger = logging.getLogger("narrative_nexus.investigate")

# ── W1: fetch_article ──────────────────────────────────────────────────────

ARTICLE_TIMEOUT = 10
_BLOCKED_NETWORKS = [
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("169.254.0.0/16"),
]


async def fetch_article(url: str) -> dict:
    """Fetch article body from a URL via newspaper4k.

    Returns dict with keys: title, body, published_at, source_domain, error.
    On failure, error is set and body is empty string.
    """
    result: dict[str, Any] = {
        "title": "", "body": "", "published_at": None,
        "source_domain": "", "error": None,
    }

    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        result["error"] = f"Invalid scheme: {parsed.scheme}"
        return result

    # SSRF guard
    if parsed.hostname:
        try:
            addr = ipaddress.ip_address(parsed.hostname)
        except ValueError:
            pass
        else:
            for net in _BLOCKED_NETWORKS:
                if addr in net:
                    result["error"] = "Private/internal IP blocked"
                    return result
    else:
        result["error"] = "No hostname in URL"
        return result

    result["source_domain"] = parsed.hostname

    try:
        body, status = await asyncio.to_thread(
            ArticleExtractor().extract, url
        )
    except Exception as exc:
        result["error"] = str(exc)
        return result

    if status == "AVAILABLE" and body:
        result["body"] = body
        # newspaper4k article object is consumed inside the thread;
        # title extraction requires a second parse or we accept body-only.
        # For Investigate, the Google News RSS entry already carries a title,
        # so we rely on the caller to supply it.
        return result

    result["error"] = f"Body extraction failed (status={status})"
    return result


# ── W2: embed_texts ────────────────────────────────────────────────────────

async def embed_texts(texts: list[str], provider: dict) -> np.ndarray:
    """Embed a list of texts via the configured Fireworks provider.

    Uses the same input-cleaning as Agent 1 (get_embedding_input),
    then batches all texts in a single API call.

    Returns (N, dim) float32 numpy array.
    """
    # Agent 1 uses get_embedding_input(title, body, max_body_chars=1000)
    # per pipeline/agent1_intake.py:62-64
    cleaned = [get_embedding_input("", t, max_body_chars=1000) for t in texts]
    client = EmbeddingClient(provider)
    vecs = await client.embed(cleaned)
    return np.array(vecs, dtype=np.float32)


# ── W3: extract_claims ─────────────────────────────────────────────────────

async def extract_claims(article: dict, provider: dict, api_key: str) -> dict:
    """Extract claims from a single article via LLM (Kimi-K2P5).

    Uses the EXACT production call shape from Agent 2:
    pipeline/agent2_forensic.py:131-148 — user message is
    f"Articles:{articles_text}" where articles_text = \n--- ARTICLE {id} ---\n{title}\n{body[:400]}\n
    """
    result: dict[str, Any] = {
        "url": article.get("url", ""),
        "source_domain": article.get("source_domain", ""),
        "claims": [],
        "framing_score": None,
        "error": None,
    }

    title = article.get("title", "") or ""
    body = article.get("body", "") or ""
    article_id = article.get("article_id", 0)

    articles_text = (
        f"\n--- ARTICLE {article_id} ---\n"
        f"{title}\n"
        f"{body[:400]}\n"
    )
    user_content = f"Articles:{articles_text}"

    client = LLMClient(provider, api_key=api_key)
    try:
        raw = await client.chat(
            messages=[
                {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            response_format={"type": "json_object"},
            temperature=0.0,
            max_tokens=2000,
        )
    except Exception as exc:
        result["error"] = str(exc)
        return result

    try:
        parsed = json.loads(raw)
        results = parsed.get("results", [])
        if isinstance(results, list) and results:
            r0 = results[0]
            claims = r0.get("claims", [])
            result["claims"] = [
                c for c in claims
                if isinstance(c, dict) and c.get("text", "").strip()
            ]
            result["framing_score"] = r0.get("framing_score")
    except (json.JSONDecodeError, Exception) as exc:
        result["error"] = f"JSON parse failed: {exc}"

    return result


# ── W4: match_claims_across_articles ────────────────────────────────────────

def _cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
    """Cosine similarity between two normalised vectors."""
    return float(np.dot(a, b))


async def match_claims_across_articles(
    articles: list[dict],
    embed_provider: dict,
    sim_threshold: float = 0.85,
) -> list[dict]:
    """In-memory greedy claim matching across articles.

    Adapted from pipeline/claim_matching.py::match_claims_in_cluster (line 42).
    The production version persists to claim_variants tables; this version
    returns canonical claims as dicts without any DB writes.

    Algorithm:
    1. Collect all claim texts across all articles
    2. Embed all claim texts in one batched call
    3. Greedy merge: for each claim, if its closest neighbour has
       cosine similarity >= sim_threshold, merge into that canonical;
       otherwise create a new canonical.
    """
    # Collect all (article, claim_text, claim) tuples
    all_claims: list[dict] = []
    article_lookup: dict[str, dict] = {}
    for art in articles:
        src = art.get("source_domain", "unknown")
        art_id = art.get("url", "")
        art_title = art.get("title", "")
        for c in art.get("claims", []):
            text = c.get("text", "").strip()
            if text:
                all_claims.append({
                    "article": art_id,
                    "source": src,
                    "title": art_title,
                    "text": text,
                })
                article_lookup[text] = {"article": art_id, "source": src,
                                        "title": art_title}

    if not all_claims:
        return []

    texts = [c["text"] for c in all_claims]
    vecs = await embed_texts(texts, embed_provider)
    # Normalise
    norms = np.linalg.norm(vecs, axis=1, keepdims=True)
    norms[norms == 0] = 1
    vecs = vecs / norms

    # Greedy matching
    used = set()
    canonicals: list[dict] = []

    for i, (vec_i, claim_i) in enumerate(zip(vecs, all_claims)):
        if i in used:
            continue

        # Find best matching unclaimed claim
        best_j = -1
        best_sim = 0.0
        for j in range(i, len(all_claims)):
            if j in used or j == i:
                continue
            sim = _cosine_sim(vec_i, vecs[j])
            if sim >= sim_threshold and sim > best_sim:
                best_sim = sim
                best_j = j

        # Build canonical group
        group = [claim_i]
        used.add(i)

        if best_j >= 0:
            # Recursively add matched claims
            stack = [best_j]
            while stack:
                j = stack.pop()
                if j in used:
                    continue
                group.append(all_claims[j])
                used.add(j)
                # Find more claims matching this one
                for k in range(j + 1, len(all_claims)):
                    if k in used:
                        continue
                    if _cosine_sim(vecs[j], vecs[k]) >= sim_threshold:
                        stack.append(k)

        canonicals.append({
            "text": group[0]["text"],
            "source_count": len(set(c["source"] for c in group)),
            "variants": [
                {
                    "source": c["source"],
                    "article": c["article"],
                    "text": c["text"],
                }
                for c in group
            ],
        })

    return canonicals


# ── W5: compute_consensus ──────────────────────────────────────────────────

def compute_consensus(
    canonical_claims: list[dict],
    panel_sources: dict[str, dict],
    vertical: str = "geopolitics",
) -> list[dict]:
    """Compute per-claim consensus math — pure function, no DB.

    For each canonical claim:
    - reporting_sources: distinct sources that reported this claim
    - t1t2_reporting: how many of those are in the T1/T2 consensus pool
    - pool_size: how many T1/T2 sources exist among all article sources
    - pct: t1t2_reporting / max(pool_size, 1) * 100
    - would_absorb: True if t1t2_reporting >= MIN_CORROBORATION
      AND pct >= DEFAULT_THRESHOLDS[vertical]
    """
    threshold = DEFAULT_THRESHOLDS.get(vertical, 65)

    # Count T1/T2 sources across all articles
    pool_size = sum(
        1 for s in panel_sources.values()
        if s.get("tier", 99) in (1, 2)
    )

    results = []
    for cc in canonical_claims:
        sources = set(v["source"] for v in cc.get("variants", []))
        t1t2 = sum(
            1 for s in sources
            if panel_sources.get(s, {}).get("tier", 99) in (1, 2)
        )
        pct = (t1t2 / max(pool_size, 1)) * 100
        would_absorb = (
            t1t2 >= MIN_CORROBORATION and pct >= threshold
        )

        results.append({
            "claim_text": cc["text"],
            "source_count": len(sources),
            "t1t2_reporting": t1t2,
            "pool_size": pool_size,
            "pct": round(pct, 1),
            "threshold": threshold,
            "would_absorb": would_absorb,
            "would_need_for_absorption": (
                f"need {MIN_CORROBORATION} T1/T2 sources reporting "
                f"AND >= {threshold}% of pool ({pool_size})"
            ),
        })

    return results
