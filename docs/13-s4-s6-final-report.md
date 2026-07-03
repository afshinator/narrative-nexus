# Phase 2 — S4-S6 Final Report

**Date:** 2026-07-02
**Live DB:** data/nn.db (28.9MB)
**Backup:** data/nn-pre-t5-2026-07-02.db (28.8MB)

---

## S4 — LIVE DB EXECUTION

### S4a — Backup ✅
```
data/nn-pre-t5-2026-07-02.db: 28.8M
data/nn.db: 28.9M
```

### S4b — Run Log

| Step | Description | Wall-clock | Result |
|------|-------------|-----------|--------|
| S2.2 | Embeddings cache cleared | — | Done |
| S2.3 | Reset claim state | — | claims=8,567, cs=8,567 ✅ |
| S2.4 | cleanup clusters | skipped | Replaced by recluster |
| S2.5 | recluster_all.py (BGE, eps=0.30) | ~40s | 1,112 clusters |
| S2.6 | claim_matching (0.85) | 344s | 932 merges, 407 links |
| S2.7 | Agent 3 consensus | 2.4s | 1,112 clusters, 1,501 classified |
| S2.8 | Snapshot recompute | 73s | 44,955 snapshots, 405 dates |

### S4c — Acceptance Checks

| Check | Copy DB | Live DB | Match? | Pass? |
|-------|---------|---------|--------|-------|
| (a) Absorbed in multi-source | 13/13 = 100% | 13/13 = 100% | ✅ | PASS |
| (b) convergence_type | 13/13 = 100% | 13/13 = 100% | ✅ | PASS |
| (c) cs > claims | 8,002 > 7,635 | 8,002 > 7,635 | ✅ | PASS |
| (d) Claims by state | P:6134 U:1488 A:13 | P:6134 U:1488 A:13 | ✅ | Record |
| (e) Sources w/ absorbed | guardian(6), ap(4), fox(2), bbc(1) | Same | ✅ | Record |
| (f) Solo coverage | 6 at 100%, politico/wp at 0% | Same | ✅ | Record |
| (g) UNRESOLVED > 0 | 1,488 | 1,488 | ✅ | PASS |
| (h) Single-source share | 93.9% | 93.9% | ✅ | Record |

**All numbers identical between copy and live — no drift.**

### S4d — Demo Candidates

**Multi-source cluster buckets:**
- 2 sources: 42 clusters
- 3-5 sources: 17 clusters
- 6-10 sources: 8 clusters
- 11+ sources: 1 cluster
- **Total multi-source (>=2): 68 clusters**

**Top multi-source clusters (>=3 sources):**

| Cluster | Sources | Claims | Vertical | Key Sources |
|---------|---------|--------|----------|-------------|
| 5835 | 29 | 561 | geopolitics | bbc, theguardian, apnews, nytimes, foxnews, aljazeera... |
| 6366 | 10 | 127 | technology | npr, theguardian, bbc, abcnews, cbsnews... |
| 6395 | 10 | 40 | geopolitics | npr, theguardian, bbc, foxnews... |
| 6392 | 9 | 44 | geopolitics | bbc, theguardian, npr, apnews, foxnews... |
| 6413 | 8 | 40 | geopolitics | dw, theguardian, bbc, npr... |
| 6368 | 7 | 37 | geopolitics | foxnews, npr, theguardian, apnews, bbc... |
| 6385 | 7 | 36 | technology | bbc, theguardian, npr, apnews... |

**Absorbed claims (13 total):**

| Source | Excerpt |
|--------|---------|
| apnews | President Donald Trump threatened a 100% tax on imports... |
| apnews | A giraffe named Gracie is missing in Texas. |
| apnews | Mark Carney was Prime Minister of Canada on June 25, 2026. |
| apnews | Bible stories have become required reading for 5M+ Texas students. |
| bbc | King Charles's tax bill is £12.9 million. |
| foxnews | A woman walked her dog in a wooded area in Canada. |
| foxnews | The woman made loud noises to scare the bear. |
| theguardian | Four people died from flash floods in Kentucky. |
| theguardian | Donald Trump will nominate Lance Schroyer as ICE director. |
| theguardian | Lance Schroyer has over 29 years of law enforcement experience. |
| theguardian | David Venturella had been performing ICE director duties. |
| theguardian | Offenders who kill partners face extra 10 years in prison. |
| theguardian | Thunderstorms caused severe delays to hundreds of Heathrow flights. |

---

## S5 — TRUTH SYNC

See `docs/faq-pipeline-data.md` and `docs/faq-source-selection.md` — both updated with:
- Methodology update (2026-07-02) section
- All numbers re-queried from live DB
- Self-validation artifact explanation

---

## CONTRADICTION CHECK

All copy-DB vs live-DB numbers match within 0%. No contradictions with design docs.

---

## POST-RUN SUMMARY

- **1,112 clusters** (68 multi-source, 1,044 single-source)
- **68 multi-source clusters** (>=2 distinct sources)
- **13 absorbed claims** (down from 2,792 — honest consensus now)
- **4 sources with absorption**: theguardian(6), apnews(4), foxnews(2), bbc(1)
- **1,488 UNRESOLVED claims** (zombie fix confirmed)
- **932 claim merges, 407 cross-source links** (matching working)
- **44,955 snapshots across 405 dates**

**Ready for Phase 3?** YES. The pipeline is correct: consensus math is honest (MIN_CORROBORATION=2 enforced), zombie bug fixed (1,488 UNRESOLVED), claim matching works (407 cross-source links), and 100% of absorbed claims are cross-source corroborated. The sparse absorption (13 claims) reflects the panel design — 25 of 37 sources are regional/contrarian outlets. Phase 3 should focus on expanding the source panel, tuning clustering, or building frontend features that showcase the honest (sparse) consensus data.

**Falsifier:** This run is defective if any absorbed claim belongs to a single-source cluster (currently 0/13).
