#!/usr/bin/env python3
"""R2.9d — Full downstream rebuild: reset → match → Agent 3 → snapshots."""
import asyncio
import os
import sys
import sqlite3
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DB = "data/demo/demo.db"

# ── 0. Verify DB target ───────────────────────────────────────────
print(f"DB target: {DB}")
assert DB == "data/demo/demo.db", f"DESTRUCTIVE OPS ON WRONG DB: {DB}"

# ── 1. RESET CLAIM STATE (adapted from scripts/reset_claim_state.py) ──
print("\n=== STEP 1: reset_claim_state ===")
conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
c = conn.cursor()

c.execute("SELECT COUNT(*) FROM claims"); claims_before = c.fetchone()[0]
c.execute("SELECT COUNT(*) FROM claim_sources"); cs_before = c.fetchone()[0]
c.execute("SELECT COUNT(*) FROM claim_variants"); cv_before = c.fetchone()[0]
print(f"Before: claims={claims_before}, claim_sources={cs_before}, claim_variants={cv_before}")

# Restore claim_variants as independent claims
restored = 0
variants = c.execute("""SELECT canonical_claim_id, source_id, article_id, text, first_seen_at
    FROM claim_variants""").fetchall()

for v in variants:
    article_row = c.execute("SELECT cluster_id FROM claims WHERE article_id = ? LIMIT 1",
                            (v["article_id"],)).fetchone()
    if article_row and article_row["cluster_id"] is not None:
        cluster_id = article_row["cluster_id"]
    else:
        canonical_row = c.execute("SELECT cluster_id FROM claims WHERE id = ?",
                                  (v["canonical_claim_id"],)).fetchone()
        cluster_id = canonical_row["cluster_id"] if canonical_row else None

    c.execute("""INSERT INTO claims (article_id, cluster_id, text, state, created_at)
        VALUES (?, ?, ?, 'PENDING',
            COALESCE(?, (SELECT published_at FROM articles WHERE id = ?), datetime('now')))""",
        (v["article_id"], cluster_id, v["text"], v["first_seen_at"], v["article_id"]))
    restored += 1

print(f"Restored {restored} claim_variant rows as independent claims")

c.execute("UPDATE claims SET state='PENDING', absorbed_at=NULL, convergence_type=NULL")
print(f"Reset {c.rowcount} claims to PENDING")

c.execute("DELETE FROM claim_variants")
print(f"Deleted {c.rowcount} claim_variant rows")

c.execute("DELETE FROM claim_sources")
print(f"Deleted {c.rowcount} claim_sources rows")

c.execute("""INSERT INTO claim_sources (claim_id, source_id, first_seen_at)
    SELECT c.id, a.source_id, a.published_at
    FROM claims c JOIN articles a ON a.id = c.article_id""")
print(f"Inserted {c.rowcount} claim_sources rows")

c.execute("SELECT COUNT(*) FROM claims"); claims_after = c.fetchone()[0]
c.execute("SELECT COUNT(*) FROM claim_sources"); cs_after = c.fetchone()[0]
c.execute("SELECT COUNT(*) FROM claim_variants"); cv_after = c.fetchone()[0]
print(f"After: claims={claims_after}, claim_sources={cs_after}, claim_variants={cv_after}")

assert claims_after == cs_after, f"TIE-OUT FAIL: claims={claims_after} != claim_sources={cs_after}"
tieout1 = claims_before + restored
print(f"Tie-out: claims_before({claims_before}) + restored({restored}) = {tieout1} == claims_after({claims_after}): {'PASS' if tieout1 == claims_after else 'FAIL'}")
assert tieout1 == claims_after, f"TIE-OUT FAIL: {tieout1} != {claims_after}"

conn.commit()
conn.close()

# ── 2. MATCH ALL CLUSTERS (sim=0.85 LOCKED) ─────────────────────
print("\n=== STEP 2: match_all_clusters ===")

from pipeline.claim_matching import match_all_clusters, get_claim_matching_embed_client

# Must set FIREWORKS-NOMIC_API_KEY (hyphen, not underscore)
os.environ["FIREWORKS-NOMIC_API_KEY"] = os.environ.get("FIREWORKS_API_KEY", "")

embed_client = get_claim_matching_embed_client("config/providers.json")

conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row

# Pre-match claim count
c = conn.cursor()
c.execute("SELECT COUNT(*) FROM claims"); claims_pre_match = c.fetchone()[0]
c.execute("SELECT COUNT(DISTINCT cluster_id) FROM claims WHERE cluster_id IS NOT NULL")
clusters_with_claims = c.fetchone()[0]
print(f"Claims before match: {claims_pre_match}")
print(f"Clusters with claims: {clusters_with_claims}")

result = asyncio.run(match_all_clusters(conn, embed_client, sim_threshold=0.85))

c.execute("SELECT COUNT(*) FROM claims"); claims_post_match = c.fetchone()[0]
c.execute("SELECT COUNT(*) FROM claim_variants"); cv_post = c.fetchone()[0]

print(f"Clusters with claims: {result['clusters_with_claims']}")
print(f"Clusters processed:   {result['clusters_processed']}")
print(f"Total merges:         {result['total_merges']}")
print(f"Sources linked:       {result['total_sources_linked']}")
print(f"Elapsed:              {result['elapsed_seconds']}s")
print(f"Claims after:         {claims_post_match}")
print(f"Claim variants:       {cv_post}")

tieout2 = claims_pre_match - result['total_merges']
print(f"Tie-out: claims_before({claims_pre_match}) - merges({result['total_merges']}) = {tieout2} == claims_after({claims_post_match}): {'PASS' if tieout2 == claims_post_match else 'FAIL'}")
assert tieout2 == claims_post_match, f"TIE-OUT FAIL: {tieout2} != {claims_post_match}"

conn.commit()
conn.close()

# ── 3. AGENT 3 — CONSENSUS ───────────────────────────────────────
print("\n=== STEP 3: Agent 3 Consensus ===")

from pipeline.agent3_consensus import ConsensusAlignmentAgent

conn = sqlite3.connect(DB)
c = conn.cursor()
c.execute("SELECT COUNT(*) FROM claims WHERE state='CONSENSUS_ABSORBED'")
absorbed_before = c.fetchone()[0]
print(f"Absorbed before Agent 3: {absorbed_before}")

agent3 = ConsensusAlignmentAgent(db_path=DB)
conn2 = sqlite3.connect(DB)
conn2.row_factory = sqlite3.Row
a3_result = agent3.run_all(conn2)
print(f"Clusters: {a3_result.get('clusters', 0)}")
print(f"Claims classified: {a3_result.get('classified', 0)}")
conn2.close()

conn = sqlite3.connect(DB)
c = conn.cursor()
c.execute("SELECT COUNT(*) FROM claims WHERE state='CONSENSUS_ABSORBED'")
absorbed_after = c.fetchone()[0]
c.execute("SELECT COUNT(*) FROM claims")
total_claims = c.fetchone()[0]
print(f"Absorbed after Agent 3: {absorbed_after}")
print(f"Total claims: {total_claims}")

# ── Pool arithmetic for every absorbed claim ──────────────────────
print("\n=== Pool Arithmetic ===")
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

# Group by cluster
from collections import defaultdict
cluster_claims = defaultdict(list)
for r in rows:
    cluster_claims[r["cluster_id"]].append(r)

for cid, cclaims in sorted(cluster_claims.items()):
    print(f"\nCluster {cid} ({cclaims[0]['vertical']}):")
    for cc in cclaims:
        # Get supporters for this claim from claim_sources
        supporters = conn.execute("""
            SELECT s.name, s.tier
            FROM claim_sources cs
            JOIN sources s ON s.id = cs.source_id
            WHERE cs.claim_id = ?
        """, (cc["claim_id"],)).fetchall()
        
        t1t2 = [s for s in supporters if s["tier"] in (1, 2)]
        print(f"  Claim {cc['claim_id']}: {cc['text'][:80]}...")
        print(f"    Supporters: {[s['name'] for s in supporters]}")
        print(f"    T1/T2: {len(t1t2)}/{len(supporters)} = {len(t1t2)/len(supporters)*100:.1f}%")

conn.close()

# ── 4. SNAPSHOT RECOMPUTE ────────────────────────────────────────
print("\n=== STEP 4: Snapshot Recompute ===")

from pipeline.runner import _compute_and_write_snapshots

conn = sqlite3.connect(DB)
c = conn.cursor()

# Delete existing snapshots
deleted = c.execute("DELETE FROM snapshots").rowcount
print(f"Deleted {deleted} existing snapshots")

# Get date range
date_rows = c.execute("SELECT MIN(published_at), MAX(published_at) FROM articles WHERE published_at IS NOT NULL").fetchone()
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

print(f"Total snapshots: {total_snaps}")

# Verify
c.execute("SELECT COUNT(DISTINCT date) FROM snapshots")
nd = c.fetchone()[0]
c.execute("SELECT COUNT(*) FROM snapshots")
ns = c.fetchone()[0]
print(f"Distinct dates: {nd}")
print(f"Total snapshots: {ns}")

# Check for any dates with unexpected count
bad_dates = c.execute("""
    SELECT date, COUNT(*) as n FROM snapshots
    GROUP BY date HAVING n != (SELECT COUNT(DISTINCT source_id) * COUNT(DISTINCT vertical)
        FROM snapshots WHERE date = snapshots.date)
""").fetchall()
print(f"Dates with unexpected count: {len(bad_dates)}")

c.execute("SELECT MIN(date), MAX(date) FROM snapshots")
snap_range = c.fetchone()
print(f"Snapshot span: {snap_range[0]} → {snap_range[1]}")

conn.commit()
conn.close()

print("\n=== R2.9d COMPLETE ===")
