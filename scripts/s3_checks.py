#!/usr/bin/env python3
"""S3: Acceptance checks against /tmp/phase2.db."""
import sqlite3, sys

db = "/tmp/phase2.db"
conn = sqlite3.connect(db)
conn.row_factory = sqlite3.Row

def query(label, sql, params=()):
    rows = conn.execute(sql, params).fetchall()
    print(f"\n{'='*60}")
    print(f"S3{label}")
    print(f"{'='*60}")
    for r in rows[:20]:
        d = dict(r)
        vals = " | ".join(f"{k}={v}" for k, v in d.items())
        print(f"  {vals}")
    if len(rows) > 20:
        print(f"  ... ({len(rows)} total rows)")
    return rows

# (a) Absorbed claims must be in multi-source clusters
rows_a = query("a: Absorbed in >=2 source clusters", """
    SELECT COUNT(*) as absorbed,
           SUM(CASE WHEN cluster_source_count >= 2 THEN 1 ELSE 0 END) as in_multi_src
    FROM (
        SELECT c.id, c.state,
               (SELECT COUNT(DISTINCT a2.source_id)
                FROM claims c2
                JOIN articles a2 ON a2.id = c2.article_id
                WHERE c2.cluster_id = c.cluster_id) as cluster_source_count
        FROM claims c
        WHERE c.state = 'CONSENSUS_ABSORBED'
    )
""")
row = rows_a[0]
absorbed = row["absorbed"]
multi = row["in_multi_src"]
pct = multi / absorbed * 100 if absorbed else 0
print(f"\n  RESULT: {multi}/{absorbed} absorbed claims in multi-source clusters = {pct:.1f}%")
print(f"  {'PASS' if pct == 100 else 'FAIL'}: MUST be 100%")

# (b) convergence_type non-null for absorbed
rows_b = query("b: convergence_type NULLs", """
    SELECT COUNT(*) as absorbed,
           SUM(CASE WHEN convergence_type IS NULL THEN 1 ELSE 0 END) as null_convergence
    FROM claims
    WHERE state = 'CONSENSUS_ABSORBED'
""")
row = rows_b[0]
null_ct = row["null_convergence"]
absorbed_ct = row["absorbed"]
pct2 = (absorbed_ct - null_ct) / absorbed_ct * 100 if absorbed_ct else 0
print(f"\n  RESULT: {absorbed_ct - null_ct}/{absorbed_ct} have convergence_type = {pct2:.1f}%")
print(f"  {'PASS' if pct2 == 100 else 'FAIL'}: MUST be 100%")

# (c) claim_sources > claims
cs = conn.execute("SELECT COUNT(*) FROM claim_sources").fetchone()[0]
cl = conn.execute("SELECT COUNT(*) FROM claims").fetchone()[0]
print(f"\n{'='*60}")
print("S3c: claim_sources vs claims")
print(f"{'='*60}")
print(f"  claim_sources: {cs}")
print(f"  claims: {cl}")
print(f"  ratio: {cs/cl:.2f}")
print(f"  {'PASS' if cs > cl else 'FAIL'}: claim_sources > claims")

# (d) Claims by state
query("d: Claims by state", """
    SELECT state, COUNT(*) as cnt FROM claims GROUP BY state ORDER BY cnt DESC
""")

# (e) Sources with absorbed claims
query("e: Sources with >=1 absorbed", """
    SELECT s.name, COUNT(*) as absorbed_claims
    FROM claims c
    JOIN articles a ON a.id = c.article_id
    JOIN sources s ON s.id = a.source_id
    WHERE c.state = 'CONSENSUS_ABSORBED'
    GROUP BY s.name
    ORDER BY absorbed_claims DESC
""")

# (f) Solo coverage share per source
print(f"\n{'='*60}")
print("S3f: Solo coverage share — top 10")
print(f"{'='*60}")
rows_f = conn.execute("""
    SELECT s.name,
           COUNT(*) as total_claims,
           SUM(CASE WHEN cluster_source_count = 1 THEN 1 ELSE 0 END) as solo,
           ROUND(100.0 * SUM(CASE WHEN cluster_source_count = 1 THEN 1 ELSE 0 END) / COUNT(*), 1) as solo_pct
    FROM (
        SELECT a.source_id,
               (SELECT COUNT(DISTINCT a2.source_id)
                FROM claims c2 JOIN articles a2 ON a2.id = c2.article_id
                WHERE c2.cluster_id = c.cluster_id) as cluster_source_count
        FROM claims c
        JOIN articles a ON a.id = c.article_id
    )
    JOIN sources s ON s.id = source_id
    GROUP BY s.name
    ORDER BY solo_pct DESC
    LIMIT 10
""").fetchall()
for r in rows_f:
    print(f"  {r['name']:20s} total={r['total_claims']:5d} solo={r['solo']:5d} ({r['solo_pct']:5.1f}%)")

print(f"\n  Bottom 10:")
rows_f2 = conn.execute("""
    SELECT s.name,
           COUNT(*) as total_claims,
           SUM(CASE WHEN cluster_source_count = 1 THEN 1 ELSE 0 END) as solo,
           ROUND(100.0 * SUM(CASE WHEN cluster_source_count = 1 THEN 1 ELSE 0 END) / COUNT(*), 1) as solo_pct
    FROM (
        SELECT a.source_id,
               (SELECT COUNT(DISTINCT a2.source_id)
                FROM claims c2 JOIN articles a2 ON a2.id = c2.article_id
                WHERE c2.cluster_id = c.cluster_id) as cluster_source_count
        FROM claims c
        JOIN articles a ON a.id = c.article_id
    )
    JOIN sources s ON s.id = source_id
    GROUP BY s.name
    ORDER BY solo_pct ASC
    LIMIT 10
""").fetchall()
for r in rows_f2:
    print(f"  {r['name']:20s} total={r['total_claims']:5d} solo={r['solo']:5d} ({r['solo_pct']:5.1f}%)")

# (g) UNRESOLVED single-source claims past 90 days
rows_g = query("g: UNRESOLVED old single-source", """
    SELECT COUNT(*) as unresolved_old
    FROM claims c
    WHERE c.state = 'UNRESOLVED'
      AND julianday('now') - julianday(c.created_at) >= 90
""")
unresolved = rows_g[0]["unresolved_old"]
print(f"\n  RESULT: {unresolved} old UNRESOLVED claims")
print(f"  {'PASS' if unresolved > 0 else 'FAIL'}: MUST be > 0")

# (h) Sources-per-cluster histogram
print(f"\n{'='*60}")
print("S3h: Sources-per-cluster histogram")
print(f"{'='*60}")
rows_h = conn.execute("""
    SELECT src_count, COUNT(*) as clusters
    FROM (
        SELECT c.id, COUNT(DISTINCT a.source_id) as src_count
        FROM clusters c
        LEFT JOIN claims cl ON cl.cluster_id = c.id
        LEFT JOIN articles a ON a.id = cl.article_id
        GROUP BY c.id
    )
    GROUP BY src_count
    ORDER BY src_count
""").fetchall()
total_clusters = sum(r["clusters"] for r in rows_h)
single_src = sum(r["clusters"] for r in rows_h if r["src_count"] in (0, 1))
for r in rows_h[:15]:
    print(f"  {r['src_count']:3d} source(s): {r['clusters']:6d} clusters")
pct_single = single_src / total_clusters * 100 if total_clusters else 0
print(f"\n  Single-source share: {single_src}/{total_clusters} = {pct_single:.1f}%")
print(f"  {'PASS' if pct_single < 70 else 'FAIL'}: Target below 70%")

conn.close()
