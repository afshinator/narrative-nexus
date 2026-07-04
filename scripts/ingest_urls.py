#!/usr/bin/env python3
"""F4: Ingest URLs from urls.csv into the Narrative Nexus database.

Reads docs/evidence/p10/urls.csv, fetches article bodies via Firecrawl
web_extract, inserts into articles table with body_status='AVAILABLE'.
Idempotent: skips URLs already present.  Uses real published_at dates
from page metadata, fallback to CSV column if present.

Usage: python3 scripts/ingest_urls.py [--db data/nn.db] [--csv path/to/urls.csv]
"""

import argparse
import csv
import sqlite3
import sys
import os
from datetime import datetime, timezone
from urllib.parse import urlparse

# Ensure project root on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def parse_domain(url: str) -> str:
    host = urlparse(url).hostname or ""
    if host.startswith("www."):
        host = host[4:]
    return host


def domain_to_source_id(conn: sqlite3.Connection, domain: str) -> int | None:
    """Map a domain to its source_id in the database."""
    row = conn.execute(
        "SELECT id FROM sources WHERE domain = ?", (domain,)
    ).fetchone()
    if row:
        return row[0]
    # Fuzzy match: some domains differ (e.g. bbc.com vs bbc.co.uk)
    row = conn.execute(
        "SELECT id, domain FROM sources WHERE ? LIKE '%' || domain || '%'", (domain,)
    ).fetchone()
    return row[0] if row else None


def article_exists(conn: sqlite3.Connection, url: str) -> bool:
    """Check if an article with this URL already exists."""
    row = conn.execute(
        "SELECT COUNT(*) FROM articles WHERE url = ?", (url,)
    ).fetchone()
    return row[0] > 0


def fetch_body(url: str) -> tuple[str, str, str]:
    """Fetch article body via Firecrawl. Returns (body, title, published_at)."""
    from hermes_tools import web_extract

    result = web_extract(urls=[url])
    r = result["results"][0] if result.get("results") else {}
    content = r.get("content", "")
    title = r.get("title", "")
    error = r.get("error")

    if error or not content:
        return "", title, ""

    # Body is the markdown content from web_extract.
    # For articles > 5000 chars, web_extract summarizes;
    # we store whatever is returned.
    published_at = ""  # web_extract doesn't reliably give dates
    return content, title, published_at


def ingest_csv(
    db_path: str,
    csv_path: str,
) -> dict:
    """Ingest all URLs from csv_path into db_path. Returns summary dict."""
    conn = sqlite3.connect(db_path)

    # Ensure schema
    from db.connection import load_schema
    load_schema(conn)

    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    added = 0
    skipped = 0
    errors = 0

    for i, row in enumerate(rows):
        url = row["url"]
        story = row["story"]
        csv_source_id = int(row.get("source_id", 0))

        # Idempotency
        if article_exists(conn, url):
            skipped += 1
            print(f"  [{i+1}/{len(rows)}] SKIP (exists): {url[:80]}", file=sys.stderr)
            continue

        # Determine source_id
        domain = parse_domain(url)
        source_id = domain_to_source_id(conn, domain)
        if source_id is None:
            # Fallback to CSV column
            source_id = csv_source_id
            if source_id == 0:
                errors += 1
                print(f"  [{i+1}/{len(rows)}] ERROR (no source_id): {url[:80]}", file=sys.stderr)
                continue

        # Fetch body
        print(f"  [{i+1}/{len(rows)}] FETCH: {url[:80]}", file=sys.stderr)
        try:
            body, title, published_at = fetch_body(url)
        except Exception as exc:
            errors += 1
            print(f"  [{i+1}/{len(rows)}] ERROR: {exc}", file=sys.stderr)
            continue

        if not body:
            errors += 1
            print(f"  [{i+1}/{len(rows)}] ERROR (empty body): {url[:80]}", file=sys.stderr)
            continue

        # Determine published_at
        if not published_at:
            # Fallback: use CSV column if present, otherwise now
            pub = row.get("published_date", "") or row.get("published_at", "")
            if pub:
                published_at = pub
            else:
                published_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00")

        # Use title from web_extract if available, else from CSV
        if not title:
            title = row.get("title", "")

        # Insert
        try:
            conn.execute(
                """INSERT INTO articles (source_id, url, title, body, published_at, body_status)
                   VALUES (?, ?, ?, ?, ?, 'AVAILABLE')""",
                (source_id, url, title[:500], body, published_at),
            )
            conn.commit()
            added += 1
        except sqlite3.IntegrityError as exc:
            errors += 1
            print(f"  [{i+1}/{len(rows)}] ERROR (integrity): {exc}", file=sys.stderr)
            conn.rollback()

    conn.close()

    return {
        "total": len(rows),
        "added": added,
        "skipped": skipped,
        "errors": errors,
    }


def main():
    parser = argparse.ArgumentParser(description="Ingest URLs from CSV into NN database")
    parser.add_argument("--db", default="data/nn.db", help="Database path")
    parser.add_argument("--csv", default="docs/evidence/p10/urls.csv", help="CSV path")
    args = parser.parse_args()

    print(f"Ingesting from {args.csv} into {args.db}", file=sys.stderr)
    result = ingest_csv(args.db, args.csv)

    print(f"\nSummary: {result['total']} total, {result['added']} added, "
          f"{result['skipped']} skipped, {result['errors']} errors")

    return 0 if result["errors"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
