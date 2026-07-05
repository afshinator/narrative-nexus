# A2 April Arc Absorption Diagnostic

**Date:** 2026-07-05
**Read-only.** No DB writes, no parameter changes. sim=0.85 LOCKED.

Question: why did the April arc (articles 943, 944, 945) produce zero absorptions?

---

## D1 — Cluster Membership

All three articles are in cluster 966 (geopolitics):

```
Cluster 966: geopolitics, 20 claims, 6 articles, 3 sources
Articles: 940(reuters), 941(guardian), 942(AP), 943(AP), 944(AP), 945(guardian)
Sources:  reuters(T1), theguardian(T1), apnews(T1)
Pool:     3 T1 sources
Absorbed: 1 (claim 2799, article 940, reuters)
```

### Claims for articles 943-945

**Article 943 (AP News, Apr 7):**
- 2815: "The U.S. and Iran agreed to a two-week ceasefire."
- 2816: "Trump said in an online post Tuesday morning: 'A whole civilization will die tonight, never to be brought back again, if a deal isn't reached.'"

**Article 944 (AP News, Apr 20):**
- 2818: "President Trump made statements about the U.S. war against Iran."
- 2820: "Trump said on Truth Social: 'I am under no pressure whatsoever, although, it will all happen, relatively quickly.'"
- 2821: "An Iranian official said: 'We do not accept negotiations under the shadow of threats.'"

**Article 945 (theguardian, Apr 27):**
- 2822: "Iran's foreign ministry stated that the US seizure of two Iranian-linked oil tankers constitutes the legalization of piracy and armed robbery on the high seas."
- 2823: "Esmail Baghaei accused the US of lawless behavior that strikes at the heart of international law and international free trade."
- 2824: "Trump met with his national security team on Monday morning to discuss a new Iranian proposal."

---

## D2 — Near-Miss Claim Pairs (nomic cosine similarity)

Computed via `pipeline/claim_matching.py` `get_claim_matching_embed_client()` — same `fireworks-nomic` provider, same `nomic-ai/nomic-embed-text-v1.5` model, same code path as the matcher. Threshold: 0.85.

5 closest cross-source pairs involving articles 943-945:

| Rank | Sim | A (art, source) | B (art, source) |
|------|-----|-----------------|-----------------|
| 1 | 0.8152 | 944, AP: "President Trump made statements about the U.S. war against Iran." | 945, theguardian: "Trump met with his national security team on Monday morning to discuss a new Iranian proposal." |
| 2 | 0.8085 | 944, AP: "An Iranian official said: 'We do not accept negotiations under the shadow of threats.'" | 945, theguardian: "Trump met with his national security team on Monday morning to discuss a new Iranian proposal." |
| 3 | 0.8083 | 943, AP: "The U.S. and Iran agreed to a two-week ceasefire." | 944, AP: "President Trump made statements about the U.S. war against Iran." |
| 4 | 0.7955 | 943, AP: "The U.S. and Iran agreed to a two-week ceasefire." | 944, AP: "An Iranian official said: 'We do not accept negotiations under the shadow of threats.'" |
| 5 | 0.7860 | 943, AP: "The U.S. and Iran agreed to a two-week ceasefire." | 945, theguardian: "Trump met with his national security team on Monday morning to discuss a new Iranian proposal." |

### Merges that DID occur

2 same-source AP variants were absorbed into canonical claim 2815:

```
Variant (art 943, AP): "Hours later, Trump said: 'Almost all of the various points of past contention have been agreed to...'" → 2815
Variant (art 944, AP): "A 14-day ceasefire between the U.S. and Iran approaches its Wednesday expiration." → 2815
```

7 of 9 original 943-945 claims survived as canonicals.

---

## D3 — Classification

- **Pairs 1-5 (0.786-0.815):** Genuine near-misses. All Iran-war-related but factually distinct sub-events — ceasefire agreement, Trump's social media posts, Iranian official statements, tanker seizures, national security meetings vs the earlier airstrikes and troop deployments. Correctly not merged at 0.85.
- **No evidence of AI-summary body as blocker.** Claims are semantically different, not identical facts phrased differently. The same-source AP merges into claim 2815 prove the matcher works normally on AI-summary content.
- **Ceasefire-specific cluster problem:** The April arc claims describe diplomatic/negotiation events (ceasefire, Trump posts about deal, Iran stance on negotiations) while the Mar 10-24 claims describe military events (airstrikes, troop deployments, oil blockade threats). Same arc, different sub-events — the 0.85 threshold correctly separates them.

---

## D4 — Findings

**Why zero April-arc absorptions:**

1. 943-945 claims cover different specific events (ceasefire diplomacy, Trump rhetoric, Iran tanker response) than the pre-April military-action claims
2. Cross-source sim scores range 0.786-0.815 — all below the 0.85 LOCKED threshold
3. Only same-source AP duplicates merged (2 variants into 2815)
4. Cluster 966's single absorption (claim 2799, Reuters Mar 10) predates the April arc
5. Pool is small (3 T1 sources), but that alone doesn't explain it — the claims simply aren't semantically close enough to merge

**No recommendation warranted.** The 0.85 threshold is doing its job: separating distinct sub-events within a broad story arc. Lowering it would risk factually wrong merges (per the P2 A/B sweep that rejected 0.80). No single article's AI-summary phrasing is identified as the blocker — the gap is in the event coverage, not in the body quality.

---

## STOP

No DB mutations. No parameter changes. Read-only diagnostic.
