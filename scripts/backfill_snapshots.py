"""Backfill daily snapshots for a date range — all 6 R-dimensions.

Iterates the FULL calendar range (--since to --until/today), writing one
row per source/vertical/day unconditionally (REQ-046). Days with no articles
still get snapshots — R values carry forward as None/0.

Usage: python3 scripts/backfill_snapshots.py --db data/nn.db --since 2026-04-01 [--until 2026-07-04]
"""

import argparse
import sys
from datetime import datetime, timedelta

sys.path.insert(0, ".")
import sqlite3
from pipeline.runner import _compute_and_write_snapshots


def main():
    parser = argparse.ArgumentParser(description="Backfill snapshots over full calendar range")
    parser.add_argument("--db", default="data/demo/demo.db", help="Database path")
    parser.add_argument("--since", required=True, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--until", default=None, help="End date (YYYY-MM-DD, default: today)")
    args = parser.parse_args()

    start = datetime.strptime(args.since, "%Y-%m-%d").date()
    end = datetime.strptime(args.until, "%Y-%m-%d").date() if args.until else datetime.now().date()

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row

    # Delete existing snapshots in range for clean recompute
    deleted = conn.execute("DELETE FROM snapshots WHERE date >= ? AND date <= ?", (args.since, end.isoformat())).rowcount
    conn.commit()
    print(f"Deleted {deleted} existing snapshots in range", file=sys.stderr)

    total_rows = 0
    current = start
    dates_done = 0
    while current <= end:
        date_str = current.isoformat()
        rows = _compute_and_write_snapshots(conn, date_str=date_str, as_of=date_str + "T23:59:59+00:00")
        conn.commit()
        total_rows += rows
        dates_done += 1
        if dates_done % 20 == 0:
            print(f"  [{dates_done}] {date_str} — {total_rows} rows so far", file=sys.stderr)
        current += timedelta(days=1)

    conn.close()
    print(f"Done. {dates_done} dates, {total_rows} rows.")


if __name__ == "__main__":
    main()
