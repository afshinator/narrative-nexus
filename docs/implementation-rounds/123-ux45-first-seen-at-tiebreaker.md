# Round 123 — UX45: first_seen_at semantic tiebreaker (READ-ONLY)

**Date:** 2026-07-09
**Order:** UX45
**Status:** COMPLETE
**Branch:** main

## T1 — What do the pipeline-written rows say?

Comparing 88 originally-populated claim_sources rows (pre-ux43 backup) against two derivations:

```
Origin derivation (claim's article published_at):
  populated: 88 | match: 88 | differ: 0

Per-source derivation (MIN published_at from articles of that source
  having claims in the cluster):
  populated: 88 | match: 21 | differ: 67
```

The pipeline wrote values matching the origin derivation 88/88 times. Under per-source derivation, only 21/88 match — 67 of 88 rows would differ. The pipeline did NOT use per-source derivation.

## T2 — Where does the pipeline write first_seen_at?

**agent2_forensic.py:194,216:**
```python
# date_map built from article_id → articles.published_at (lines 163-170)
source_id = source_map.get(article_id)       # article's source
first_seen = date_map.get(article_id)        # article's published_at
# ...
add_claim_source(conn, claim_id=cid, source_id=source_id,
                 first_seen_at=first_seen)
```

**claim_matching.py:142,155:**
```python
first_seen = row["published_at"] if row["published_at"] else None
# row comes from the claims/articles JOIN in the match query
add_claim_source(conn, canonical_id, source_id, first_seen_at=first_seen)
```

Both write sites use `articles.published_at` — the claim's origin article date. This is origin derivation.

## Verdict

**Origin.** The pipeline uses `article.published_at` as `first_seen_at`. Both write sites (Agent 2 extraction + claim matching merge) agree. UX43 backfill matches pipeline behavior. Per-source derivation is incorrect for this schema — `claim_sources.source_id` records which source independently reported the claim, but `first_seen_at` means "when was the claim first seen by the pipeline," which is the origin article's publication date.
