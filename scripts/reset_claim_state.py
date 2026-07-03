#!/usr/bin/env python3
"""Phase 2 S2.3: Reset claim state for clean re-run.

- Claims: state='PENDING', absorbed_at=NULL, convergence_type=NULL
- DELETE FROM claim_variants
- Restore claim_sources to 1:1 (claim_id, article's source_id, first_seen_at=article.published_at)
"""
import sqlite3, sys

db_path = sys.argv[1] if len(sys.argv) > 1 else "/tmp/phase2.db"
conn = sqlite3.connect(db_path)
c = conn.cursor()

# Before counts
c.execute("SELECT COUNT(*) FROM claims")
claims_before = c.fetchone()[0]
c.execute("SELECT COUNT(*) FROM claim_sources")
cs_before = c.fetchone()[0]
c.execute("SELECT COUNT(*) FROM claim_variants")
cv_before = c.fetchone()[0]
print(f"Before: claims={claims_before}, claim_sources={cs_before}, claim_variants={cv_before}")

# Reset claims
c.execute("UPDATE claims SET state='PENDING', absorbed_at=NULL, convergence_type=NULL")
print(f"Reset {c.rowcount} claims to PENDING")

# Delete claim_variants
c.execute("DELETE FROM claim_variants")
print(f"Deleted {c.rowcount} claim_variant rows")

# Restore claim_sources to 1:1
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
