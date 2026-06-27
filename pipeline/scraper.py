"""RSS feed polling for all 37 Narrative Nexus sources."""
import feedparser
from datetime import datetime, timezone


FEED_CONFIG: dict[str, dict] = {
    # Tier 1 — Wire / Consensus Anchor
    "reuters":         {"url": "https://news.google.com/rss/search?q=site:reuters.com&hl=en-US&gl=US&ceid=US:en", "type": "google_news", "domain": "reuters.com", "tier": 1},
    "ap":              {"url": "https://news.google.com/rss/search?q=site:apnews.com&hl=en-US&gl=US&ceid=US:en", "type": "google_news", "domain": "apnews.com", "tier": 1},
    "bbc":             {"url": "https://feeds.bbci.co.uk/news/rss.xml", "type": "native", "domain": "bbc.com", "tier": 1},
    "npr":             {"url": "https://feeds.npr.org/1001/rss.xml", "type": "native", "domain": "npr.org", "tier": 1},
    "the-guardian":    {"url": "https://www.theguardian.com/world/rss", "type": "native", "domain": "theguardian.com", "tier": 1},
    # Tier 2 — Mainstream Editorial
    "fox-news":        {"url": "https://moxie.foxnews.com/google-publisher/world.xml", "type": "native", "domain": "foxnews.com", "tier": 2},
    "cnn":             {"url": "http://rss.cnn.com/rss/cnn_topstories.rss", "type": "native", "domain": "cnn.com", "tier": 2},
    "cbs-news":        {"url": "https://www.cbsnews.com/latest/rss/main", "type": "native", "domain": "cbsnews.com", "tier": 2},
    "abc-news":        {"url": "https://abcnews.go.com/abcnews/topstories", "type": "native", "domain": "abcnews.go.com", "tier": 2},
    "politico":        {"url": "https://rss.politico.com/politics-news.xml", "type": "native", "domain": "politico.com", "tier": 2},
    "the-economist":   {"url": "https://www.economist.com/international/rss.xml", "type": "native", "domain": "economist.com", "tier": 2},
    "nyt":             {"url": "https://rss.nytimes.com/services/xml/rss/nyt/World.xml", "type": "native", "domain": "nytimes.com", "tier": 2},
    "washington-post": {"url": "https://feeds.washingtonpost.com/rss/world", "type": "native", "domain": "washingtonpost.com", "tier": 2},
    # Tier 3 — International
    "al-jazeera":      {"url": "https://www.aljazeera.com/xml/rss/all.xml", "type": "native", "domain": "aljazeera.com", "tier": 3},
    "deutsche-welle":  {"url": "https://rss.dw.com/rdf/rss-en-all", "type": "native", "domain": "dw.com", "tier": 3},
    "nhk-world":       {"url": "https://news.google.com/rss/search?q=site:nhk.or.jp&hl=en-US&gl=US&ceid=US:en", "type": "google_news", "domain": "www3.nhk.or.jp", "tier": 3},
    "global-times":    {"url": "https://news.google.com/rss/search?q=site:globaltimes.cn&hl=en-US&gl=US&ceid=US:en", "type": "google_news", "domain": "globaltimes.cn", "tier": 3},
    "france24":        {"url": "https://www.france24.com/en/rss", "type": "native", "domain": "france24.com", "tier": 3},
    "buenos-aires-times": {"url": "https://batimes.com.ar/feed/", "type": "native", "domain": "batimes.com.ar", "tier": 3},
    "straits-times":   {"url": "https://www.straitstimes.com/news/asia/rss.xml", "type": "native", "domain": "straitstimes.com", "tier": 3},
    "the-hindu":       {"url": "https://www.thehindu.com/news/international/feeder/default.rss", "type": "native", "domain": "thehindu.com", "tier": 3},
    "premium-times-ng": {"url": "https://www.premiumtimesng.com/feed", "type": "native", "domain": "premiumtimesng.com", "tier": 3},
    "times-of-israel": {"url": "https://www.timesofisrael.com/feed/", "type": "native", "domain": "timesofisrael.com", "tier": 3},
    "vanguard-ng":     {"url": "https://www.vanguardngr.com/feed/", "type": "native", "domain": "vanguardngr.com", "tier": 3},
    "the-reporter-et": {"url": "https://www.thereporterethiopia.com/feed/", "type": "native", "domain": "thereporterethiopia.com", "tier": 3},
    "namibian":        {"url": "https://www.namibian.com.na/feed/", "type": "native", "domain": "namibian.com.na", "tier": 3},
    "punch-ng":        {"url": "https://punchng.com/feed/", "type": "native", "domain": "punchng.com", "tier": 3},
    "jamaica-observer": {"url": "https://www.jamaicaobserver.com/feed/", "type": "native", "domain": "jamaicaobserver.com", "tier": 3},
    "mercopress":      {"url": "https://en.mercopress.com/rss", "type": "native", "domain": "en.mercopress.com", "tier": 3},
    "tehran-times":    {"url": "https://www.tehrantimes.com/rss", "type": "native", "domain": "tehrantimes.com", "tier": 3},
    # Tier 4 — Independent / Investigative
    "the-intercept":   {"url": "https://theintercept.com/feed/?lang=en", "type": "native", "domain": "theintercept.com", "tier": 4},
    "propublica":      {"url": "https://www.propublica.org/feeds/propublica/main", "type": "native", "domain": "propublica.org", "tier": 4},
    "bellingcat":      {"url": "https://www.bellingcat.com/feed/", "type": "native", "domain": "bellingcat.com", "tier": 4},
    "african-arguments": {"url": "https://africanarguments.org/feed/", "type": "native", "domain": "africanarguments.org", "tier": 4},
    # Tier 5 — Contrarian
    "zerohedge":       {"url": "https://feeds.feedburner.com/zerohedge/feed", "type": "feedburner", "domain": "zerohedge.com", "tier": 5},
    "the-gray-zone":   {"url": "https://thegrayzone.com/feed/", "type": "native", "domain": "thegrayzone.com", "tier": 5},
    "sputnik":         {"url": "https://sputnikglobe.com/export/rss2/archive/index.xml", "type": "native", "domain": "sputnikglobe.com", "tier": 5},
}


class RSSPoller:
    """Parses RSS feeds and yields normalized article dicts. Pure data source — no DB access."""

    def fetch(self, source_name: str):
        """Yield normalized article dicts for a single source."""
        cfg = FEED_CONFIG.get(source_name)
        if cfg is None:
            return
        parsed = feedparser.parse(cfg["url"])
        for entry in parsed.entries:
            yield self._normalize(entry, cfg)

    def fetch_all(self):
        """Yield normalized article dicts for all sources."""
        for name in FEED_CONFIG:
            yield from self.fetch(name)

    def _normalize(self, entry, cfg: dict) -> dict:
        # ponytail: prefer feedparser's parsed time tuple over raw RFC 2822 string
        if entry.get("published_parsed"):
            published_at = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc).isoformat()
        else:
            published_at = datetime.now(timezone.utc).isoformat()
        body_status = "BODY_UNAVAILABLE" if cfg["type"] == "google_news" else "AVAILABLE"
        return {
            "title": entry.get("title", ""),
            "url": entry.get("link", ""),
            "published_at": published_at,
            "source_domain": cfg["domain"],
            "body_status": body_status,
        }
