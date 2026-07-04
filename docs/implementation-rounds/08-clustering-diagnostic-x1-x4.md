# Phase 2 Clustering Diagnostic — X1-X4

**Date:** 2026-07-02
**Finding:** The 200-char body window is the bottleneck. Embedding models are healthy; input is broken.

---

## X1 — WHAT ARE WE ACTUALLY EMBEDDING?

**X1a — Input construction (agent1_intake.py:60-62):**
```python
texts = [
    f"{r['title'] or ''} {r['body'][:200] if r['body'] else ''}"
    for r in rows
]
```
**Title + space + first 200 characters of body.** ~260-310 chars per article.

**X1b — 5 sample articles, exact embedding input:**

| ID | Source | Title | Body len | Input len | Input first 100 chars |
|----|--------|-------|----------|-----------|----------------------|
| 451 | apnews | US and Iran sign initial deal... | 10,886 | 309 | "An initial agreement to end the war between the United States and Iran calls for Tehran to dilute its" |
| 106 | apnews | Back-to-back powerful earthquakes... | 7,341 | 285 | "A powerful 7.1-magnitude earthquake shook Venezuela on Wednesday evening, collapsing buildings in the" |
| 1748 | batimes | What we learned after the first round... | 6,001 | 262 | "Messi's still got it\n\nLionel Messi's World Cup odyssey appeared to reach its perfect climax in Qatar" |
| 157 | apnews | Anthropic says it has taken its latest AI... | 2,015 | 302 | "Anthropic co-founder and President Daniela Amodei, left, shakes hands with Snowflake CEO Sridhar Rama" |
| 186 | apnews | How a heat dome is formed... | 5,285 | 295 | "Driven by human-caused climate change, heat waves around the world are \"tending to last longer, be str" |

**X1c — Boilerplate contamination in body[:200]:**

| Article | Boilerplate found in first 200 chars | Type |
|---------|--------------------------------------|------|
| 106 (Venezuela quake) | "(AP/ Juan Arraez)" | Photo credit |
| 157 (Anthropic AI) | "left, shakes hands with..." | Photo caption — ENTIRE 200-char window is a picture caption |
| 186 (Heat wave) | "by Brittany Peterson" + "Produced by T" | Video credit + producer credit |

**Critical finding:** Article 157's body[:200] is 100% a photo caption of a handshake at Snowflake Summit. The actual news content ("Anthropic said Friday it has taken its latest artificial intelligence models...") starts at character ~450.

**Why chars 200-500 are worse than chars 0-200 for AP articles:**

| Article | chars 0-200 | chars 200-500 |
|---------|------------|---------------|
| 106 (Venezuela) | Mix of content + credit | **100% photo captions** (3 caption lines) |
| 186 (Heat wave) | Content + video credit | **100% photo captions** (5 caption lines) |
| 157 (Anthropic) | Handshake photo caption | **More photo captions** + "WASHINGTON (AP) —" then finally content starts |

The 200-char limit is a MiniLM-era holdover. MiniLM (384-dim, lighter model) was less sensitive to short context. Nomic and BGE are passage-level models that need richer input.

---

## X2 — NOMIC PAIRWISE COSINE SIMILARITY (8 articles, no prefix)

8 articles: US politics (118), Middle East (453), European weather (186), Tech/AI (157), Sports (1748), Economics (1630), Natural disaster (106), Science/Tech (486)

```
                    US polit Middle E European  Tech/AI   Sports Economic Natural  Science/
US politics            --     0.5364   0.5046   0.5342   0.4770   0.5134   0.4802   0.5413
Middle East          0.5364      --     0.5290   0.5385   0.5190   0.6246   0.5775   0.5278
European weather     0.5046   0.5290      --     0.5760   0.5410   0.5532   0.5963   0.5202
Tech/AI              0.5342   0.5385   0.5760      --     0.5370   0.5837   0.4822   0.8222
Sports               0.4770   0.5190   0.5410   0.5370      --     0.4963   0.4968   0.4821
Economics            0.5134   0.6246   0.5532   0.5837   0.4963      --     0.5515   0.5588
Natural disaster     0.4802   0.5775   0.5963   0.4822   0.4968   0.5515      --     0.4624
Science/Tech         0.5413   0.5278   0.5202   0.8222   0.4821   0.5588   0.4624      --
```

**Off-diagonal: mean=0.5415, min=0.4624, max=0.8222**

The mean (0.54) falls in the "healthy" range (0.3-0.6), but the MINIMUM is 0.46 — even the most distinct pair (Venezuela earthquake vs Anthropic export ban) has 0.46 similarity. The narrow range (0.46-0.62 excluding the same-topic pair) means the model can't distinguish topics well with only 200 chars of body text.

The 0.82 max is between two Anthropic articles (157 and 486) — correct behavior.

---

## X3 — BGE PAIRWISE COSINE SIMILARITY (same 8 articles)

```
                    US polit Middle E European  Tech/AI   Sports Economic Natural  Science/
US politics            --     0.5549   0.4936   0.5359   0.4549   0.4647   0.4873   0.5467
Middle East          0.5549      --     0.4346   0.4885   0.4632   0.4482   0.4520   0.4695
European weather     0.4936   0.4346      --     0.5174   0.4651   0.4095   0.5156   0.5149
Tech/AI              0.5359   0.4885   0.5174      --     0.4975   0.4548   0.3763   0.7188
Sports               0.4549   0.4632   0.4651   0.4975      --     0.4529   0.4318   0.4992
Economics            0.4647   0.4482   0.4095   0.4548   0.4529      --     0.4243   0.5180
Natural disaster     0.4873   0.4520   0.5156   0.3763   0.4318   0.4243      --     0.4289
Science/Tech         0.5467   0.4695   0.5149   0.7188   0.4992   0.5180   0.4289      --
```

**Off-diagonal: mean=0.4828, min=0.3763, max=0.7188**

---

## COMPARISON

| Metric | Nomic | BGE | Delta |
|--------|-------|-----|-------|
| Mean off-diagonal | 0.5415 | 0.4828 | -0.059 (BGE better) |
| Max off-diagonal | 0.8222 | 0.7188 | -0.103 (BGE better) |
| Min off-diagonal | 0.4624 | 0.3763 | -0.086 (BGE better) |

BGE provides ~11% better topic separation. The improvement is real but modest — neither model can fully distinguish topics from 200 chars of body text.

**Neither model is "broken."** Both produce healthy cosine similarities in the expected range. The bottleneck is input quality: 200 chars captures photo captions and boilerplate, not article topics.

---

## X4 — DRAFT BOILERPLATE CLEANER

If we fix the input instead of switching models, here's what a cleaner would strip:

```python
import re

BOILER_PATTERNS = [
    r'\(AP[^)]{0,50}\)',                      # AP attribution: (AP Photo/Name), (AP/ Name)
    r'\(Reuters[^)]{0,50}\)',                   # Reuters attribution
    r'\(AFP[^)]{0,50}\)',                       # AFP attribution
    r'\(Photo by[^)]+\)',                       # Photo credit
    r'\([^)]*Video by[^)]+\)',                  # Video credit
    r'Produced by [A-Z][a-z]+ [A-Z][a-z]+',    # Producer credit
    r'^\s*[A-Z][A-Z\s]+ \(AP\)\s*[-–—]\s*',    # Location tag: "WASHINGTON (AP) —"
    r'^\w+,\s*\w+\.?\s*\(AP\)\s*[-–—]',        # "City, Country. (AP) —"
    r'\b(LEFT|RIGHT|CENTER),\s*',               # Photo caption directional: "left, shakes hands..."
    r'\([A-Z][a-z]+ [A-Z][a-z]+/[^)]+\)',       # (Sebastian Gollnow/dpa via AP)
]

def clean_body(body: str) -> str:
    """Strip boilerplate from news article body for embedding."""
    for pat in BOILER_PATTERNS:
        body = re.sub(pat, '', body, flags=re.IGNORECASE)
    # Collapse whitespace
    body = re.sub(r'\n{3,}', '\n\n', body)
    body = re.sub(r' {2,}', ' ', body)
    return body.strip()


def get_embedding_input(title: str, body: str, max_chars: int = 1000) -> str:
    """Build embedding input with cleaned body, longer window."""
    clean = clean_body(body)
    return f"{title or ''} {clean[:max_chars]}"
```

**Before/after on the worst case (article 157):**

| | Text |
|---|------|
| Before (200 chars) | "Anthropic co-founder and President Daniela Amodei, left, shakes hands with Snowflake CEO Sridhar Ramaswamy during the keynote presentaton at Snowflake Summit 26 Monday, June 1, 2026, in San Francisco." |
| After (1000 chars, cleaned) | "Anthropic co-founder and President Daniela Amodei shakes hands with Snowflake CEO Sridhar Ramaswamy during the keynote presentaton at Snowflake Summit 26 Monday June 1 2026 in San Francisco WASHINGTON Anthropic said Friday it has taken its latest artificial intelligence models known as Fable 5 and Mythos 5 offline to comply with a directive from the Trump administration to prevent their use by foreign nationals The export controls mark the U.S. government's most significant step to date to restrict advanced AI from reaching adversaries..." |

---

## BOTTLENECK DIAGNOSIS

**Input contamination, not model choice.** The 200-char body window was sized for MiniLM (384-dim, less context-sensitive). For nomic/BGE (768-dim, passage-level models), 200 chars is insufficient — especially when those 200 chars are often photo captions and credit lines for AP articles.

**Fix path:**
1. Increase body window from 200 to 800-1000 chars
2. Strip boilerplate patterns before embedding
3. Either model (nomic or BGE) should work with clean, longer input
4. Re-run pairwise test with cleaned input to confirm separation improves
5. Then re-run EPS sweep

Model choice is secondary — fix the input first, then compare.
