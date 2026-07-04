#!/usr/bin/env python3
"""Phase 2 S2.3: Reset claim state for clean re-run — TRUE UN-MERGE.

Before deleting claim_variants, RESTORE each variant as a claim row
(original text, article_id, cluster_id from its article) and rebuild
claim_sources 1:1. This reverses the merge, returning to the pre-match
claim count.

- Claims: state='PENDING', absorbed_at=NULL, convergence_type=NULL
- claim_variants: restored as independent claims, then table cleared
- claim_sources: restored to 1:1 (claim_id, article's source_id, first_seen_at=article.published_at)
"""
import sqlite3, sys

db_path = sys.argv[1] if len(sys.argv) > 1 else "/tmp/phase2.db"
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
c = conn.cursor()

# Before counts
c.execute("SELECT COUNT(*) FROM claims")
claims_before = c.fetchone()[0]
c.execute("SELECT COUNT(*) FROM claim_sources")
cs_before = c.fetchone()[0]
c.execute("SELECT COUNT(*) FROM claim_variants")
cv_before = c.fetchone()[0]
print(f"Before: claims={claims_before}, claim_sources={cs_before}, claim_variants={cv_before}")

# ── STEP 1: Restore claim_variants as independent claims ──────────
restored = 0
variants = c.execute("""
    SELECT canonical_claim_id, source_id, article_id, text, first_seen_at
    FROM claim_variants
""").fetchall()

for v in variants:
    # Get cluster_id from the variant's article's current claim cluster,
    # or from the canonical claim if the article has no claims (merge artifact)
    article_row = c.execute(
        "SELECT cluster_id FROM claims WHERE article_id = ? LIMIT 1",
        (v["article_id"],)
    ).fetchone()
    if article_row and article_row["cluster_id"] is not None:
        cluster_id = article_row["cluster_id"]
    else:
        # Merge artifact: no claims left for this article — use canonical's cluster
        canonical_row = c.execute(
            "SELECT cluster_id FROM claims WHERE id = ?",
            (v["canonical_claim_id"],)
        ).fetchone()
        cluster_id = canonical_row["cluster_id"] if canonical_row else None

    # Insert the variant as a new claim
    # Use COALESCE to handle NULL first_seen_at safely
    c.execute(
        """INSERT INTO claims (article_id, cluster_id, text, state, created_at)
           VALUES (?, ?, ?, 'PENDING',
             COALESCE(?,
               (SELECT published_at FROM articles WHERE id = ?),
               datetime('now')))""",
        (v["article_id"], cluster_id, v["text"],
         v["first_seen_at"], v["article_id"]),
    )
    restored += 1

print(f"Restored {restored} claim_variant rows as independent claims")

# ── STEP 2: Reset all claims to PENDING ───────────────────────────
c.execute("UPDATE claims SET state='PENDING', absorbed_at=NULL, convergence_type=NULL")
print(f"Reset {c.rowcount} claims to PENDING")

# ── STEP 3: Delete claim_variants (now restored as claims) ────────
c.execute("DELETE FROM claim_variants")
print(f"Deleted {c.rowcount} claim_variant rows")

# ── STEP 4: Rebuild claim_sources 1:1 ─────────────────────────────
c.execute("DELETE FROM claim_sources")
print(f"Deleted {c.rowcount} claim_sources rows")

# Recreate claim_sources: one row per claim with its article's source_id
c.execute("""
    INSERT INTO claim_sources (claim_id, source_id, first_seen_at)
    SELECT c.id, a.source_id, a.published_at
    FROM claims c
    JOIN articles a ON a.id = c.article_id
""")
print(f"Inserted {c.rowcount} claim_sources rows")

# After counts
c.execute("SELECT COUNT(*) FROM claims")
claims_after = c.fetchone()[0]
c.execute("SELECT COUNT(*) FROM claim_sources")
cs_after = c.fetchone()[0]
c.execute("SELECT COUNT(*) FROM claim_variants")
cv_after = c.fetchone()[0]

print(f"After: claims={claims_after}, claim_sources={cs_after}, claim_variants={cv_after}")

# Verify: claim_sources = claims count
assert claims_after == cs_after, f"Mismatch: claims={claims_after} != claim_sources={cs_after}"
print(f"VERIFIED: claim_sources count ({cs_after}) == claims count ({claims_after})")

conn.commit()
conn.close()
print("Done.")
