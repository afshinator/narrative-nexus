"""Track B Phase 2 — Investigate SSE endpoint (separate module to avoid main.py corruption)."""

import asyncio
import json
import os
import re
import sqlite3
import time
from typing import Any

from fastapi import Request
from sse_starlette.sse import EventSourceResponse

from db.sources import list_sources
from pipeline.firecrawl_search import search_news
from pipeline.investigate import (
    fetch_article,
    embed_texts,
    extract_claims,
    match_claims_across_articles,
    compute_consensus,
)


def _get_embed_provider() -> dict:
    """Return the configured embedding provider from providers.json."""
    from pathlib import Path
    cfg_path = Path(__file__).parent.parent / "config" / "providers.json"
    cfg = json.loads(cfg_path.read_text())
    default_id = cfg.get("defaults", {}).get("agent1_embedding", "fireworks")
    for emb in cfg.get("providers", {}).get("embeddings", []):
        if emb.get("id") == default_id:
            prov = dict(emb)
            if prov.get("id") == "fireworks":
                prov["base_url"] = "https://api.fireworks.ai/inference/v1"
            return prov
    raise ValueError(f"Provider '{default_id}' not found")


def _get_extraction_provider() -> dict:
    return {
        "id": "fireworks", "name": "Fireworks AI",
        "model": "accounts/fireworks/models/kimi-k2p5",
        "base_url": "https://api.fireworks.ai/inference/v1",
    }


async def _fetch_one(search_result: dict) -> dict:
    """Fetch one article — URL is already resolved to source article by news_search."""
    result = await fetch_article(search_result["url"])
    result["article_id"] = hash(search_result["url"]) & 0x7FFFFFFF
    result["title"] = search_result.get("title", "") or result.get("title", "")
    result["status"] = "ok" if result.get("body") else "error"
    return result


async def _extract_one(
    article: dict, provider: dict, api_key: str, sem: asyncio.Semaphore,
) -> dict:
    async with sem:
        return await extract_claims(article, provider, api_key)


async def investigate_stream_endpoint(request: Request):
    """POST /api/investigate/stream — live pipeline via SSE."""
    try:
        body = await request.json()
    except Exception:
        async def _bad():
            yield {"event": "error", "data": json.dumps({"message": "Invalid JSON body"})}
        return EventSourceResponse(_bad())

    query = (body.get("query") or "").strip()
    if not query:
        async def _e():
            yield {"event": "error", "data": json.dumps({"message": "Empty query"})}
        return EventSourceResponse(_e())
    if len(query) > 200:
        async def _e():
            yield {"event": "error", "data": json.dumps({"message": "Query too long (max 200 chars)"})}
        return EventSourceResponse(_e())
    if re.search(r"[\n;|&$`]", query):
        async def _e():
            yield {"event": "error", "data": json.dumps({"message": "Query contains invalid characters"})}
        return EventSourceResponse(_e())

    embed_provider = _get_embed_provider()
    extract_provider = _get_extraction_provider()
    api_key = os.environ.get("FIREWORKS_API_KEY", "")
    if not api_key:
        async def _e():
            yield {"event": "error", "data": json.dumps({"message": "FIREWORKS_API_KEY not set"})}
        return EventSourceResponse(_e())

    async def event_stream():
        t0 = time.time()
        DEADLINE = 45.0

        def _timed_out():
            return time.time() - t0 > DEADLINE

        yield {"event": "stage_start", "data": json.dumps({"stage": "search", "index": 1, "total": 6})}
        try:
            results = await asyncio.wait_for(search_news(query, limit=6), timeout=DEADLINE)
        except asyncio.TimeoutError:
            yield {"event": "error", "data": json.dumps({"stage": "timeout", "message": f"Pipeline exceeded {DEADLINE}s deadline"})}
            return
        yield {"event": "search_result", "data": json.dumps({
            "urls": [
                {"title": r["title"], "url": r["url"], "source_domain": r["source_domain"]}
                for r in results
            ]
        })}
        if len(results) < 3:
            yield {"event": "warning", "data": json.dumps({"stage": "search", "message": f"Only {len(results)} panel sources"})}
            yield {"event": "error", "data": json.dumps({"stage": "search", "message": "Not enough panel sources"})}
            return

        yield {"event": "stage_start", "data": json.dumps({"stage": "fetch", "index": 2, "total": 6})}
        fetched = await asyncio.gather(*[_fetch_one(r) for r in results])
        for f in fetched:
            yield {"event": "fetch_progress", "data": json.dumps(f)}
        articles = [f for f in fetched if f.get("body")]
        if len(articles) < 3:
            yield {"event": "warning", "data": json.dumps({"stage": "fetch", "message": f"Only {len(articles)} successful fetches"})}
            yield {"event": "error", "data": json.dumps({"stage": "fetch", "message": "Not enough successful fetches"})}
            return

        yield {"event": "stage_start", "data": json.dumps({"stage": "embed", "index": 3, "total": 6})}
        texts = [f"{a.get('title','')} {a.get('body','')[:1000]}" for a in articles]
        try:
            vecs = await embed_texts(texts, embed_provider)
            yield {"event": "embed_done", "data": json.dumps({
                "count": len(texts), "dim": int(vecs.shape[1]),
                "model": embed_provider.get("model", "?"),
            })}
        except Exception as exc:
            yield {"event": "error", "data": json.dumps({"stage": "embed", "message": str(exc)})}
            return

        yield {"event": "stage_start", "data": json.dumps({"stage": "extract", "index": 4, "total": 6})}
        sem = asyncio.Semaphore(6)
        extracted = await asyncio.gather(*[_extract_one(a, extract_provider, api_key, sem) for a in articles])
        for er in extracted:
            yield {"event": "extract_result", "data": json.dumps(er)}
        successful = [er for er in extracted if er.get("claims")]
        if not successful:
            yield {"event": "error", "data": json.dumps({"stage": "extract", "message": "No claims extracted"})}
            return

        yield {"event": "stage_start", "data": json.dumps({"stage": "match", "index": 5, "total": 6})}
        try:
            canonical = await match_claims_across_articles(successful, embed_provider=embed_provider)
            yield {"event": "match_result", "data": json.dumps({"canonical_claims": canonical})}
        except Exception as exc:
            yield {"event": "error", "data": json.dumps({"stage": "match", "message": str(exc)})}
            return

        yield {"event": "stage_start", "data": json.dumps({"stage": "consensus", "index": 6, "total": 6})}
        db_path = os.environ.get("NN_DB_PATH", "data/demo/demo.db")
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        panel: dict[str, dict] = {}
        for src in list_sources(conn):
            panel[src["domain"]] = {"name": src["name"], "tier": src.get("tier", 99)}
        conn.close()
        cr = compute_consensus(canonical, panel)
        yield {"event": "consensus_result", "data": json.dumps({
            "per_claim": cr,
            "thresholds": {"geopolitics": 65, "economics": 75, "technology": 75},
            "pool_size": cr[0]["pool_size"] if cr else 0,
            "min_corroboration": 2,
        })}

        total_ms = int((time.time() - t0) * 1000)
        yield {"event": "done", "data": json.dumps({
            "total_ms": total_ms,
            "articles_analyzed": len(articles),
            "successful_articles": len(successful),
            "claims_matched": len(canonical),
        })}

    return EventSourceResponse(
        event_stream(),
        # E4: 45s timeout kills the stream if any stage stalls
        sep="\n",
    )
