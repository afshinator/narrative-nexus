#!/usr/bin/env python3
"""Backfill correction detection for all article bodies.

Scans every article body for known correction patterns (AP, CNN, NYT-style)
and stores matches in the corrections table.

Usage:
  python scripts/backfill_corrections.py [--db data/nn.db]
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.connection import get_db
from db.corrections import init_corrections_table, insert_correction
from pipeline.corrections import detect_corrections


def main():
    parser = argparse.ArgumentParser(description="Backfill correction detection")
    parser.add_argument("--db", default="data/nn.db",
                        help="Database path (default: data/nn.db)")
    args = parser.parse_args()

    db_path = os.path.abspath(args.db)
    if not os.path.exists(db_path):
        print(f"Database not found: {db_path}")
        sys.exit(1)

    conn = get_db(db_path)
    init_corrections_table(conn)
    conn.close()

    conn = get_db(db_path)
    conn.row_factory = None  # tuples
    try:
        rows = conn.execute(
            """SELECT a.id, a.body FROM articles a
               WHERE a.body IS NOT NULL AND a.body != ''
                 AND a.id NOT IN (SELECT article_id FROM corrections)
               ORDER BY a.id"""
        ).fetchall()
    finally:
        conn.close()

    total = len(rows)
    print(f"Articles to scan: {total}")

    found = 0
    for article_id, body in rows:
        corrections = detect_corrections(body or "")
        if corrections:
            conn = get_db(db_path)
            try:
                for c in corrections:
                    insert_correction(
                        conn,
                        article_id=article_id,
                        detected_pattern=c["pattern"],
                        matched_text=c["matched_text"],
                    )
                    found += 1
            finally:
                conn.close()

    print(f"Done. Found {found} corrections across {total} articles.")
    if found > 0:
        conn = get_db(db_path)
        try:
            per_pattern = conn.execute(
                "SELECT detected_pattern, COUNT(*) as cnt FROM corrections GROUP BY detected_pattern ORDER BY cnt DESC"
            ).fetchall()
            print("By pattern:")
            for pattern, cnt in per_pattern:
                print(f"  {pattern}: {cnt}")
        finally:
            conn.close()


if __name__ == "__main__":
    main()
