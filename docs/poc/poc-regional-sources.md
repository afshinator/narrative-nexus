# PoC 4b — Regional Source Expansion (Africa, Caribbean, LatAm, Asia)

**Date:** 2026-06-26
**Status:** IMPLEMENTED — 14 sources added to panel (slice 11). Tier A + Tier B + Tehran Times all shipped. Panel at 37 sources.
**Method:** RSS feed discovery + Firecrawl extraction testing
**Feeds tested:** 45 candidates across Africa, Caribbean, Latin America, Middle East, Asia
**Working RSS + extractable bodies:** 15 sources

## Top candidates by region

### Africa (7 working feeds)

| Source | Country | RSS | Body chars | Paras | Verdict |
|--------|---------|-----|------------|-------|---------|
| **African Arguments** | Pan-African | 10/poll | 14,204 | ~40 | EXCELLENT — deep analysis |
| **Premium Times** | Nigeria | 15/poll | 9,052 | 41 | EXCELLENT — investigative |
| **Vanguard** | Nigeria | 20/poll | 7,385 | ~25 | EXCELLENT — daily news |
| **The Reporter** | Ethiopia | 10/poll | 5,853 | ~20 | GOOD — Horn of Africa |
| **Namibian** | Namibia | 12/poll | 4,914 | ~15 | GOOD — Southern Africa |
| **Punch** | Nigeria | 30/poll | 3,078 | 17 | DECENT — highest volume |
| Lusaka Times | Zambia | 10/poll | 3,075 | 16 | Decent |
| Daily News Egypt | Egypt | 10/poll | 1,835 | 6 | Marginal — North Africa |
| Africanews | Pan-African | 50/poll | 1,123 | 3 | Low body (short wire) |

### Caribbean (3 working feeds)

| Source | Country | RSS | Body chars | Verdict |
|--------|---------|-----|------------|---------|
| **Jamaica Observer** | Jamaica | 37/poll | 2,267 | DECENT — highest Carib volume |
| Barbados Today | Barbados | 10/poll | ~9,000 | Body present but heavy nav noise |
| St. Lucia Times | St. Lucia | 10/poll | — | Untested body extraction |

### Latin America (2 working feeds)

| Source | Country | RSS | Body chars | Paras | Verdict |
|--------|---------|-----|------------|-------|---------|
| **Buenos Aires Times** | Argentina | 100/poll | 9,409 | 10 | EXCELLENT — huge volume + quality |
| MercoPress | S. Atlantic | 10/poll | 3,119 | 7 | GOOD — Falklands/Patagonia |

### Middle East / North Africa (3 working feeds)

| Source | Country | RSS | Body chars | Verdict |
|--------|---------|-----|------------|---------|
| **Times of Israel** | Israel | 15/poll | 7,591 | EXCELLENT |
| Tehran Times | Iran | 30/poll | 590 | Low (sports article tested) |
| Daily News Egypt | Egypt | 10/poll | 1,835 | Marginal |

### Asia (3 working feeds)

| Source | Country | RSS | Body chars | Verdict |
|--------|---------|-----|------------|---------|
| **The Hindu** | India | 60/poll | 4,719 | GOOD |
| **Straits Times** | Singapore | 50/poll | 7,855 | EXCELLENT |
| Nikkei Asia | Japan | 50/poll | 1,237 | Marginal (lifestyle article) |

### Europe / Other (2 working feeds)

| Source | Country | RSS | Body chars | Verdict |
|--------|---------|-----|------------|---------|
| Sputnik | Russia | 100/poll | 3,164 | GOOD (Tier 5 contrarian) |
| SCMP | Hong Kong | 50/poll | ~800 | Marginal (nav noise) |

---

## Recommended additions (tiered by priority)

### Tier A — Immediate add (high quality + high volume)

| Source | Tier | Region | Est. bodies/poll |
|--------|------|--------|-----------------|
| Buenos Aires Times | 3 | Latin America | 100 |
| Straits Times | 3 | SE Asia | 50 |
| The Hindu | 3 | South Asia | 60 |
| African Arguments | 4 | Africa (analysis) | 10 |
| Premium Times NG | 3 | West Africa | 15 |
| Times of Israel | 3 | Middle East | 15 |
| Vanguard NG | 3 | West Africa | 20 |
| **Subtotal** | | | **~270 bodies/poll** |

### Tier B — Add if volume needed

| Source | Tier | Est. bodies/poll |
|--------|------|-----------------|
| The Reporter (Ethiopia) | 3 | 10 |
| Namibian | 3 | 12 |
| Punch NG | 3 | 30 |
| Jamaica Observer | 3 | 37 |
| MercoPress | 3 | 10 |
| Sputnik | 5 | 100 |

---

## Impact on panel richness

```
                                Before     After Tier A    After All
                                ------     ------------    ---------
Total sources                    23         30              39
Articles/poll                  1,321       ~1,591          ~1,790
Working bodies/poll             ~524       ~794            ~993
Africa coverage                    0          5               8
Caribbean coverage                 0          1               1
Latin America coverage             0          2               2
Middle East (non-Israel)           0          1               2
South/SE Asia coverage             0          3               3
```

Adding just Tier A (7 sources) nearly doubles our working bodies. Adding all 16 candidates pushes ~1,000 working bodies/poll — truly rich data.

---

## Dead ends (RSS broken or no body)

- AllAfrica — RSS 404
- News24 SA — RSS 404
- Daily Nation KE — 403
- The East African — 403
- GhanaWeb — 404
- Mail & Guardian SA — 404
- New Times RW — 404
- Sudan Tribune — 403
- Trinidad Express — 429
- Jamaica Gleaner — RSS 404
- Arab News — 403
- Haaretz — 404
- Brazil Report — RSS broken
- Korea Herald — RSS broken
- Phnom Penh Post — RSS broken
- Jordan Times — RSS broken
- Semafor — RSS 404

---

## How to reproduce

```bash
# Test any source
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"firecrawl_scrape","arguments":{"url":"https://...","formats":["markdown"],"onlyMainContent":true}}}' | npx firecrawl-mcp
```
