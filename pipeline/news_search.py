"""Track B Phase 2 — Google News RSS search for Investigate page."""

import asyncio
import logging
from typing import Any
from urllib.parse import urlparse, quote_plus

import feedparser
import httpx

# 37 panel domains (covers the current DEFAULT_SOURCES + DB sources)
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


async def search_news(query: str, limit: int = 6) -> list[dict[str, Any]]:
    """Search Google News RSS for a subject query, filter to panel sources.

    Resolves Google redirect URLs to get actual source article URLs.
    """
    encoded = quote_plus(query)
    rss_url = (
        f"https://news.google.com/rss/search?q={encoded}"
        f"&hl=en-US&gl=US&ceid=US:en"
    )

    try:
        feed: Any = feedparser.parse(rss_url)
    except Exception as exc:
        logger.warning("news_search RSS parse failed: %s", exc)
        return []

    if feed.bozo and not feed.entries:
        logger.warning("news_search bozo feed, no entries: %s", feed.bozo_exception)
        return []

    results: list[dict[str, Any]] = []
    seen_urls: set[str] = set()

    async with httpx.AsyncClient(follow_redirects=True, timeout=10) as hc:
        for entry in feed.entries:
            # Extract source domain from RSS <source> element
            source_url = entry.get("source", {}).get("url", "") if isinstance(
                entry.get("source"), dict
            ) else ""
            source_domain = ""
            if source_url:
                source_domain = urlparse(source_url).hostname or ""
            if source_domain and source_domain.startswith("www."):
                source_domain = source_domain[4:]

            # Fallback: parse from link
            if not source_domain:
                link = entry.get("link", "")
                source_domain = urlparse(link).hostname or ""

            # Filter to panel domains
            if source_domain not in _PANEL_DOMAINS:
                continue

            # Resolve Google redirect URL to actual article URL
            url = entry.get("link", "")
            try:
                resp = await hc.get(url)
                resolved = str(resp.url)
                resolved_host = urlparse(resolved).hostname or ""
                if resolved_host and resolved_host != "news.google.com":
                    url = resolved
            except Exception:
                pass  # keep original Google redirect URL as fallback

            # Deduplicate
            if url in seen_urls:
                continue
            seen_urls.add(url)

            results.append({
                "title": entry.get("title", ""),
                "url": url,
                "source_domain": source_domain,
                "published_at": entry.get("published", ""),
            })

            if len(results) >= limit:
                break

    return results
