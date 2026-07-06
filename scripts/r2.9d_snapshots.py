#!/usr/bin/env python3
"""R2.9d — Snapshot recompute only (reset+match+consensus already done)."""
import sqlite3
import sys, os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pipeline.runner import _compute_and_write_snapshots

DB = "data/demo/demo.db"

conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
c = conn.cursor()

# Delete existing snapshots
deleted = c.execute("DELETE FROM snapshots").rowcount
print(f"Deleted {deleted} existing snapshots")

# Get date range from articles
date_rows = c.execute(
    "SELECT MIN(published_at), MAX(published_at) FROM articles WHERE published_at IS NOT NULL"
).fetchone()
min_date_str = date_rows[0][:10]
max_date_str = date_rows[1][:10]
min_date = datetime.fromisoformat(min_date_str)
max_date = datetime.fromisoformat(max_date_str)
ndays = (max_date - min_date).days + 1
print(f"Date range: {min_date_str} → {max_date_str} ({ndays} days)")

current = min_date
total_snaps = 0
while current <= max_date:
    date_str = current.strftime("%Y-%m-%d")
    as_of = (current + timedelta(days=1)).isoformat()
    snap_count = _compute_and_write_snapshots(conn, date_str=date_str, as_of=as_of)
    total_snaps += snap_count
    current += timedelta(days=1)

conn.commit()

c.execute("SELECT COUNT(DISTINCT date) FROM snapshots")
nd = c.fetchone()[0]
c.execute("SELECT COUNT(*) FROM snapshots")
ns = c.fetchone()[0]
c.execute("SELECT MIN(date), MAX(date) FROM snapshots")
snap_range = c.fetchone()

print(f"Distinct dates: {nd}")
print(f"Total snapshots: {ns}")
print(f"Snapshot span: {snap_range[0]} → {snap_range[1]}")
expected_per_date = 111  # 37 sources × 3 verticals
print(f"Expected: {nd} × {expected_per_date} = {nd * expected_per_date}")
tieout_ok = ns == nd * expected_per_date
print(f"Tie-out: {'PASS' if tieout_ok else 'FAIL'}")

# Spot check
c.execute("SELECT date, COUNT(*) FROM snapshots GROUP BY date ORDER BY date DESC LIMIT 5")
for row in c.fetchall():
    print(f"  {row[0]}: {row[1]} rows")

conn.close()
print("Done.")
