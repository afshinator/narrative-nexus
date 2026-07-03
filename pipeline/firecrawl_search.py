"""Track B Phase 2C — Firecrawl search integration (replaces Google News RSS).

Uses Firecrawl's search endpoint to find real article URLs, then resolves
them to panel sources.  Same signature as news_search.py for drop-in swap.
"""

import os
import asyncio
import logging
from typing import Any
from urllib.parse import urlparse

from firecrawl import AsyncFirecrawl

# 37 panel domains (same set as news_search.py)
_PANEL_DOMAINS: set[str] = {
    "reuters.com", "apnews.com", "bbc.com", "bbc.co.uk",
    "nytimes.com", "washingtonpost.com", "wsj.com", "npr.org",
    "cbsnews.com", "abcnews.go.com", "nbcnews.com", "cnn.com",
    "politico.com", "thehill.com", "theguardian.com", "independent.co.uk",
    "dw.com", "france24.com", "aljazeera.com", "aljazeera.net",
    "japantimes.co.jp", "timesofisrael.com", "tehrantimes.com",
    "tass.com", "sputnikglobe.com", "vaticannews.va",
    "nhk.or.jp", "thehindu.com", "presstv.ir", "rt.com",
    "foxnews.com", "breitbart.com", "zerohedge.com", "infowars.com",
    "punchng.com", "vanguardngr.com", "premiumtimesng.com",
    "namibian.com.na", "jamaicaobserver.com",
    "mercopress.com",
}

logger = logging.getLogger("narrative_nexus.news_search")


def _extract_domain(url: str) -> str:
    host = urlparse(url).hostname or ""
    if host.startswith("www."):
        host = host[4:]
    return host


async def search_news(query: str, limit: int = 6) -> list[dict[str, Any]]:
    """Search via Firecrawl for a subject query, filter to panel sources."""
    from dotenv import load_dotenv
    from pathlib import Path
    load_dotenv(Path(__file__).parent.parent / ".env")

    api_key = os.environ.get("FIRECRAWL_API_KEY", "")
    if not api_key:
        logger.warning("FIRECRAWL_API_KEY not set")
        return []
    client = AsyncFirecrawl(api_key=api_key)

    try:
        results = await client.search(
            query,
            limit=limit * 3,  # overfetch to ensure enough panel matches
            timeout=10000,  # 10s in ms
        )
    except Exception as exc:
        logger.warning("firecrawl_search failed: %s", exc)
        return []

    # Handle pydantic SearchData model (v4.x SDK returns typed objects)
    web_results = getattr(results, "web", None) or []
    if isinstance(web_results, list):
        web_items = web_results
    elif callable(getattr(web_results, "__iter__", None)):
        web_items = list(web_results)
    else:
        web_items = []

    out: list[dict[str, Any]] = []
    seen_urls: set[str] = set()

    for item in web_items:
        if isinstance(item, dict):
            url = item.get("url", "")
            title = item.get("title", "")
            pub = item.get("publishedDate", "")
        else:
            url = getattr(item, "url", "")
            title = getattr(item, "title", "")
            pub = getattr(item, "publishedDate", "")
        domain = _extract_domain(url)
        if domain not in _PANEL_DOMAINS:
            continue
        if url in seen_urls:
            continue
        seen_urls.add(url)
        out.append({
            "title": title,
            "url": url,
            "source_domain": domain,
            "published_at": pub,
        })
        if len(out) >= limit:
            break

    return out
