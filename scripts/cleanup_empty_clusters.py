"""T5c: Delete empty clusters — clusters with zero claims AND zero article linkages.

Phase 1: removal of 3,620 empty clusters created by DBSCAN noise promotion.
These are clusters where noise points (-1 labels) got singleton clusters
created, but no claims were ever extracted for those articles.

Idempotent: safe to re-run.
"""

import sqlite3
import sys


def delete_empty_clusters(db_path: str = "data/nn.db") -> int:
    conn = sqlite3.connect(db_path)
    try:
        # Count empty clusters (zero claims linked)
        count = conn.execute("""
            SELECT COUNT(*)
            FROM clusters c
            WHERE c.id NOT IN (
                SELECT DISTINCT cluster_id FROM claims
            )
        """).fetchone()[0]

        if count == 0:
            print("No empty clusters found.")
            return 0

        # Delete empty clusters
        conn.execute("""
            DELETE FROM clusters
            WHERE id NOT IN (
                SELECT DISTINCT cluster_id FROM claims
            )
        """)
        conn.commit()
        print(f"Deleted {count} empty clusters.")
        return count
    finally:
        conn.close()


if __name__ == "__main__":
    db = sys.argv[1] if len(sys.argv) > 1 else "data/nn.db"
    delete_empty_clusters(db)
