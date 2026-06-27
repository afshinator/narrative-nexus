# PoC 4 — Firecrawl Extraction (Keyless Mode)

**Date:** 2026-06-26
**Tool:** Firecrawl MCP v3.22.1 (keyless — `firecrawl_scrape` + `firecrawl_search` free, rate-limited per IP)
**Scope:** Test whether Firecrawl cloud scraping can extract article bodies from paywalled/weak sources that newspaper4k can't handle.

## Headline

**Firecrawl rescues 2 dead sources and unlocks 4 new candidates.** Politico goes from 0% to 39k chars. WaPo from 438-char summaries to 5,856-char bodies. Four new regional sources (The Hindu, Times of Israel, SCMP, Sputnik) all extract. NYT and Fox News remain blocked. The Economist gets 1 paragraph (better than 0, but not rich).

---

## Paywall rescue — existing panel sources

| Source | newspaper4k | Firecrawl | Verdict |
|--------|-------------|-----------|---------|
| Politico | 0% (paywall) | **39,564 chars** — full article | RESCUED |
| Washington Post | 438 chars (summaries) | **5,856 chars** — real body text | RESCUED |
| The Economist | 0% (paywall) | 4,304 chars — 1 paragraph then gate | Partial |
| NYT | 0% (paywall) | BLOCKED — site unsupported | No change |
| Fox News | 20% (mostly paywalled) | BLOCKED — sidebar links only | No change |
| BBC | 100% (5,050 chars) | 200, 5,032 chars body | Redundant |
| DW | 100% (4,832 chars) | 200, 4,330 chars body | Redundant |
| NPR | 100% (2,751 chars) | 200, ~14,000 chars body | Redundant |

### Politico — 39,564 chars

Full article extraction. This is the biggest win — Politico was a hard 0% with newspaper4k and is now fully extractable via Firecrawl. Body quality: standard news article, clean text.

### Washington Post — 5,856 chars

Real article body text (not the 438-char RSS summaries newspaper4k was getting). Sample:

> "Authorities in occupied Crimea, the Black Sea peninsula that Russia annexed illegally from Ukraine in 2014, declared a state of emergency Friday following..."

The extraction ends at the paywall gate, so only the free-visible portion is captured. Still a massive upgrade — 5,856 chars is ~2,000 words, enough for claim extraction.

### The Economist — 1 paragraph

Firecrawl gets the lede paragraph ("IN RECEnT weeks more than 1,800 maths and science lecturers...") but the paywall gate cuts in immediately after. The remaining 4,000+ chars are "Subscribe" nags + "Explore more" links. Better than 0 chars, but not enough for claim extraction without an API key.

---

## New candidate sources

Tested 10 candidate RSS feeds for regional diversity; 4 have working feeds + extractable bodies.

| Source | Region | RSS entries | Firecrawl body | Quality |
|--------|--------|-------------|----------------|---------|
| **Times of Israel** | Middle East | 15 | **7,591 chars** | Excellent |
| **The Hindu** | India | 60 | 2,559 chars | Good (subscription nag, but body extracts) |
| **Sputnik** | Russia | 100 | 3,164 chars | Good (nav noise, body extracts) |
| **SCMP** | Hong Kong | 50 | ~800 chars body | Marginal (heavy nav noise, body truncated) |
| TRT World | Turkey | — | — | No RSS feed |
| Middle East Eye | Middle East | — | — | No RSS feed |
| Anadolu Agency | Turkey | — | — | No RSS feed |
| AllAfrica | Africa | — | — | No RSS feed |
| Jakarta Post | Indonesia | — | — | No RSS feed |
| Semafor | Global | — | — | No RSS feed |

### Times of Israel — standout

7,591 chars of clean body text. Israel/Middle East perspective absent from current panel. 15 articles/poll is sparse volume but the per-article quality is very high.

### The Hindu

India's newspaper of record. 60 articles/poll — strong volume. 2,559 chars body is on the lower end but extracts reliably. Adds critical South Asia perspective.

### Sputnik

Russian state media (Tier 5 — contrarian). 100 articles/poll max. Body extraction works but includes navigation noise. Adds a non-Western framing that competes with GlobalTimes for the "state-aligned" slot.

### SCMP

Hong Kong-based, historically independent (though under pressure). 50 articles/poll but Firecrawl body extraction is weak (~800 chars real body + heavy nav). Margins for claim extraction.

---

## Impact on panel richness

```
                     Before          After (with Firecrawl)
                     -------         ----------------------
Working bodies/poll  ~524            ~524 + Politico(30) + WaPo(7) = ~561
                                                                  + new sources if added
Rescued sources      0               2 (Politico, WaPo)
Dead remains         3 (NYT, Econ, Fox)  3 (same — NYT and Fox still dead)
New candidates       0               4 (ToI, Hindu, Sputnik, SCMP)
```

Adding Politico and WaPo via Firecrawl would recover ~37 bodies/poll from sources that were previously dead. Adding Times of Israel, The Hindu, Sputnik would add ~175 articles/poll with extractable bodies.

Conservative estimate for "rich" pipeline: swap newspaper4k for Firecrawl on Politico + WaPo, add The Hindu + Times of Israel → ~700+ working bodies/poll.

---

## Keyless limitations

- Rate-limited per IP — production use needs an API key
- `onlyMainContent` filter unreliable on some sites (SCMP, Sputnik nav noise)
- NYT and Fox News explicitly blocked
- No `firecrawl_extract` (LLM) — needs API key for structured extraction
- Free tier: 500 credits/month. Scrapes cost 1-5 credits each depending on formats

## Recommendations

1. **Immediate (keyless):** Add Politico and WaPo to Firecrawl extraction path; add The Hindu and Times of Israel as new panel sources
2. **Short-term (free API key):** Get free key from firecrawl.dev to enable `firecrawl_extract` for LLM-structured extraction, higher rate limits
3. **Economist/NYT:** Still need API keys (NYT Developer API, Economist subscription) — Firecrawl can't bypass these paywalls

---

## How to reproduce

```bash
# Test Firecrawl against a URL
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"firecrawl_scrape","arguments":{"url":"https://...","formats":["markdown"],"onlyMainContent":true}}}' | npx firecrawl-mcp
```

Firecrawl MCP is registered in Hermes config at `~/.hermes/config.yaml` under `mcp_servers.firecrawl`.
