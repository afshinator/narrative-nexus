#!/usr/bin/env python3
"""Harvest story articles from source DB into demo DB with remapped IDs.

Usage:
  python3 scripts/harvest_story.py --source data/nn.db --db data/demo/demo.db \\
    --story Venezuela --ids 3,21,26,90,...

Copies article rows from source DB, remapping IDs to sequential auto-increment
in the demo DB. Preserves body, published_at, source_id, url, title, body_status.
Prints per-story stats: articles copied, distinct sources, distinct T1/T2 pool
sources, min/max published_at.
"""
import argparse
import sqlite3
import sys
from collections import defaultdict


def harvest(source_path: str, demo_path: str, story: str, ids: list[int]) -> dict:
    """Copy articles from source to demo DB, remapping IDs."""
    src = sqlite3.connect(source_path)
    src.row_factory = sqlite3.Row
    demo = sqlite3.connect(demo_path)
    demo.row_factory = sqlite3.Row

    # Fetch articles from source
    placeholders = ",".join("?" * len(ids))
    rows = src.execute(
        f"""SELECT id, source_id, url, title, body, published_at, body_status
            FROM articles WHERE id IN ({placeholders}) ORDER BY id""",
        ids,
    ).fetchall()

    id_map: dict[int, int] = {}  # old_id -> new_id
    copied = 0
    skipped = 0

    for r in rows:
        # Check if URL already exists in demo (idempotency from prior harvest or ingest)
        existing = demo.execute(
            "SELECT id FROM articles WHERE url = ?", (r["url"],)
        ).fetchone()
        if existing:
            id_map[r["id"]] = existing["id"]
            skipped += 1
            continue

        cur = demo.execute(
            """INSERT INTO articles (source_id, url, title, body, published_at, body_status)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (r["source_id"], r["url"], r["title"], r["body"],
             r["published_at"], r["body_status"] or "BODY_UNAVAILABLE"),
        )
        id_map[r["id"]] = cur.lastrowid
        copied += 1

    demo.commit()

    # Stats
    new_ids = list(id_map.values())
    if not new_ids:
        src.close()
        demo.close()
        return {"story": story, "copied": 0, "skipped": 0, "sources": 0,
                "pool_sources": 0, "min_date": "", "max_date": ""}

    placeholders_new = ",".join("?" * len(new_ids))
    distinct_sources = demo.execute(
        f"SELECT COUNT(DISTINCT source_id) FROM articles WHERE id IN ({placeholders_new})",
        new_ids,
    ).fetchone()[0]

    pool_sources = demo.execute(
        f"""SELECT COUNT(DISTINCT source_id) FROM articles
            WHERE id IN ({placeholders_new})
              AND source_id IN (SELECT id FROM sources WHERE tier IN (1, 2))""",
        new_ids,
    ).fetchone()[0]

    dates = demo.execute(
        f"SELECT MIN(published_at) as mn, MAX(published_at) as mx FROM articles WHERE id IN ({placeholders_new})",
        new_ids,
    ).fetchone()

    src.close()
    demo.close()

    return {
        "story": story,
        "copied": copied,
        "skipped": skipped,
        "sources": distinct_sources,
        "pool_sources": pool_sources,
        "min_date": str(dates["mn"] or ""),
        "max_date": str(dates["mx"] or ""),
        "id_map": id_map,
    }


def main():
    parser = argparse.ArgumentParser(description="Harvest story articles into demo DB")
    parser.add_argument("--source", default="data/nn.db", help="Source DB path")
    parser.add_argument("--db", required=True, help="Demo DB path")
    parser.add_argument("--story", required=True, help="Story name")
    parser.add_argument("--ids", required=True, help="Comma-separated article IDs from source DB")
    args = parser.parse_args()

    ids = [int(x) for x in args.ids.split(",") if x.strip()]
    result = harvest(args.source, args.db, args.story, ids)

    print(f"=== {result['story']} ===")
    print(f"  Articles copied: {result['copied']}")
    print(f"  Skipped (URL exists): {result['skipped']}")
    print(f"  Distinct sources: {result['sources']}")
    print(f"  Distinct T1/T2 pool sources: {result['pool_sources']}")
    print(f"  Min published_at: {result['min_date']}")
    print(f"  Max published_at: {result['max_date']}")
    if "id_map" in result:
        print(f"  ID map (old→new): {dict(list(result['id_map'].items())[:5])}...")


if __name__ == "__main__":
    main()
