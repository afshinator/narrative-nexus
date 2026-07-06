#!/usr/bin/env python3
"""R2.9d continuation — pool arithmetic + snapshot recompute (steps 1-2 already done)."""
import sqlite3
import sys
import os
from datetime import datetime, timedelta
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DB = "data/demo/demo.db"

# ── Pool arithmetic for every absorbed claim ──────────────────────
print("=== Pool Arithmetic ===")
conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
c = conn.cursor()

c.execute("SELECT COUNT(*) FROM claims WHERE state='CONSENSUS_ABSORBED'")
absorbed = c.fetchone()[0]
print(f"Absorbed claims: {absorbed}")

rows = c.execute("""
    SELECT c.id as claim_id, c.text, c.cluster_id, cl.vertical,
           c.convergence_type, c.absorbed_at,
           a.source_id, s.name as source_name
    FROM claims c
    JOIN articles a ON a.id = c.article_id
    JOIN sources s ON s.id = a.source_id
    JOIN clusters cl ON cl.id = c.cluster_id
    WHERE c.state = 'CONSENSUS_ABSORBED'
    ORDER BY c.id
""").fetchall()

cluster_claims = defaultdict(list)
for r in rows:
    cluster_claims[r["cluster_id"]].append(r)

for cid, cclaims in sorted(cluster_claims.items()):
    # Get cluster sources info
    cl_srcs = c.execute("""
        SELECT DISTINCT s.name, s.tier
        FROM claims cl2
        JOIN articles a2 ON a2.id = cl2.article_id
        JOIN sources s ON s.id = a2.source_id
        WHERE cl2.cluster_id = ?
    """, (cid,)).fetchall()
    pool_size = len(cl_srcs)
    
    print(f"\nCluster {cid} ({cclaims[0]['vertical']}, pool_size={pool_size}):")
    for cc in cclaims:
        supporters = c.execute("""
            SELECT s.name, s.tier
            FROM claim_sources cs
            JOIN sources s ON s.id = cs.source_id
            WHERE cs.claim_id = ?
        """, (cc["claim_id"],)).fetchall()
        
        t1t2 = [s for s in supporters if s["tier"] in (1, 2)]
        pct = len(t1t2) / pool_size * 100 if pool_size > 0 else 0
        print(f"  Claim {cc['claim_id']}: {cc['text'][:100]}")
        print(f"    Supporters ({len(supporters)}): {[s['name'] for s in supporters]}")
        print(f"    T1/T2: {len(t1t2)}/{pool_size} = {pct:.1f}%")
        
# Check if any absorbed claim involves articles 940-945
print("\n=== Absorbed claims with articles 940-945 ===")
new_absorbed = c.execute("""
    SELECT c.id, c.text, c.cluster_id, a.id as article_id, s.name as source_name
    FROM claims c
    JOIN articles a ON a.id = c.article_id
    JOIN sources s ON s.id = a.source_id
    WHERE c.state = 'CONSENSUS_ABSORBED'
    AND c.article_id >= 940
""").fetchall()
if new_absorbed:
    for na in new_absorbed:
        print(f"  Claim {na['id']} (art {na['article_id']}, {na['source_name']}): {na['text'][:100]}")
else:
    print("  NONE — no absorbed claim originates from articles 940-945")
    # Check cluster 966 for claims that might support absorption
    c966 = c.execute("""
        SELECT c.id, c.text, c.state, s.name as source_name
        FROM claims c
        JOIN articles a ON a.id = c.article_id
        JOIN sources s ON s.id = a.source_id
        WHERE c.cluster_id = 966
        ORDER BY c.state, c.id
    """).fetchall()
    print(f"  Cluster 966 claims ({len(c966)}):")
    for cc in c966[:10]:
        print(f"    Claim {cc['id']} [{cc['state']}] ({cc['source_name']}): {cc['text'][:100]}")

# Check clusters with articles 940-945
print("\n=== Clusters containing articles 940-945 ===")
cl940 = c.execute("""
    SELECT DISTINCT c.cluster_id, cl.vertical, COUNT(*) as n_claims,
           COUNT(DISTINCT a.source_id) as n_sources
    FROM claims c
    JOIN articles a ON a.id = c.article_id
    JOIN clusters cl ON cl.id = c.cluster_id
    WHERE c.article_id >= 940
    GROUP BY c.cluster_id
""").fetchall()
for cl in cl940:
    print(f"  Cluster {cl['cluster_id']} ({cl['vertical']}): {cl['n_claims']} claims, {cl['n_sources']} sources")

conn.close()

# ── 4. SNAPSHOT RECOMPUTE ────────────────────────────────────────
print("\n=== Snapshot Recompute ===")

from pipeline.runner import _compute_and_write_snapshots

conn = sqlite3.connect(DB)
c = conn.cursor()

# Delete existing snapshots
deleted = c.execute("DELETE FROM snapshots").rowcount
print(f"Deleted {deleted} existing snapshots")

# Get date range
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
print(f"Distinct dates: {nd}")
print(f"Total snapshots: {ns}")

c.execute("SELECT MIN(date), MAX(date) FROM snapshots")
snap_range = c.fetchone()
print(f"Snapshot span: {snap_range[0]} → {snap_range[1]}")

# Verify all dates have consistent counts
c.execute("SELECT COUNT(DISTINCT date) FROM snapshots")
total_dates = c.fetchone()[0]
c.execute("SELECT COUNT(*) FROM snapshots")
total_rows = c.fetchone()[0]
# Expected: 37 sources × 3 verticals = 111 per date
expected_per_date = 111
print(f"Expected per date: {expected_per_date}")
print(f"Total = {total_dates} × {expected_per_date} = {total_dates * expected_per_date}")
print(f"Actual: {total_rows}")
print(f"Tie-out: {'PASS' if total_rows == total_dates * expected_per_date else 'FAIL'}")

# Spot check one date
c.execute("SELECT date, COUNT(*) FROM snapshots GROUP BY date ORDER BY date DESC LIMIT 5")
print("Last 5 dates:")
for row in c.fetchall():
    print(f"  {row[0]}: {row[1]} rows")

conn.close()
print("\n=== R2.9d COMPLETE ===")
