"""Backfill r_frame column for all historical snapshots — targeted UPDATE only.

Recomputes only r_frame (not all 6 dimensions). Same percentile rank
logic as _compute_and_write_snapshots, but UPDATEs in-place.

Usage: python3 scripts/backfill_snapshots.py [--db data/nn.db]
"""

import sys
sys.path.insert(0, ".")
import sqlite3
from pipeline.snapshots import compute_r_frame_raw, percentile_rank


def main():
    db_path = sys.argv[2] if len(sys.argv) > 2 and sys.argv[1] == "--db" else "data/nn.db"
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    dates = [
        row["date"]
        for row in conn.execute(
            "SELECT DISTINCT date FROM snapshots ORDER BY date"
        ).fetchall()
    ]

    total_updated = 0

    for i, date in enumerate(dates):
        # Skip if this date already has r_frame populated
        done = conn.execute(
            "SELECT COUNT(*) FROM snapshots WHERE date = ? AND r_frame IS NOT NULL",
            (date,),
        ).fetchone()[0]
        if done > 0:
            if (i + 1) % 100 == 0:
                print(f"[{i+1}/{len(dates)}] {date} — skipping (already has r_frame)")
            continue

        # Compute r_frame for this date
        r_frame_raw = compute_r_frame_raw(conn, as_of=date)
        r_frame = percentile_rank(
            {k: v for k, v in r_frame_raw.items() if v is not None}
        )

        # UPDATE in place — same r_frame value for all verticals
        for sid, val in r_frame.items():
            conn.execute(
                "UPDATE snapshots SET r_frame = ? WHERE source_id = ? AND date = ?",
                (round(val), sid, date),
            )
        conn.commit()
        total_updated += len(r_frame)

        if (i + 1) % 100 == 0:
            print(f"[{i+1}/{len(dates)}] {date} — updated {len(r_frame)} sources")

    conn.close()
    print(f"Done. {total_updated} rows updated across {len(dates)} dates.")


if __name__ == "__main__":
    main()
