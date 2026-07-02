"""T6b: Dry run claim matching on 5 largest multi-source clusters.

Runs against a COPY of data/nn.db so the production DB is untouched.
"""

import os, sys, asyncio, shutil, sqlite3, time
from pathlib import Path
_PROJ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJ))
from dotenv import load_dotenv
load_dotenv(_PROJ / ".env")

from pipeline.claim_matching import match_claims_in_cluster
from pipeline.embedding_client import EmbeddingClient


async def main():
    # Copy DB
    src = _PROJ / "data" / "nn.db"
    dst = "/tmp/dryrun.db"
    print(f"Copying {src} → {dst}...")
    shutil.copy2(src, dst)
    print(f"Done ({os.path.getsize(dst):,} bytes)")

    conn = sqlite3.connect(dst)
    conn.row_factory = sqlite3.Row

    # Ensure claim_variants table exists
    conn.execute("""CREATE TABLE IF NOT EXISTS claim_variants (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        canonical_claim_id INTEGER NOT NULL REFERENCES claims(id),
        source_id INTEGER NOT NULL REFERENCES sources(id),
        article_id INTEGER NOT NULL REFERENCES articles(id),
        text TEXT NOT NULL, first_seen_at TEXT NOT NULL
    )""")

    # Find 5 largest multi-source clusters
    clusters = conn.execute("""
        SELECT c.id, c.title, COUNT(DISTINCT a.source_id) as src_cnt, COUNT(*) as claim_cnt
        FROM clusters c
        JOIN claims cl ON cl.cluster_id = c.id
        JOIN articles a ON a.id = cl.article_id
        GROUP BY c.id
        HAVING src_cnt >= 2
        ORDER BY claim_cnt DESC
        LIMIT 5
    """).fetchall()

    api_key = os.environ.get("FIREWORKS_API_KEY", "")
    embed_client = EmbeddingClient(
        {"id": "fireworks", "name": "Fireworks AI",
         "model": "nomic-ai/nomic-embed-text-v1.5", "amd": True},
        api_key=api_key,
    )

    for cl in clusters:
        cid = cl["id"]
        print(f"\n{'='*60}")
        print(f"Cluster {cid}: {cl['title'][:80]}")
        print(f"  Sources: {cl['src_cnt']}, Claims: {cl['claim_cnt']}")

        t0 = time.time()
        result = await match_claims_in_cluster(conn, cid, embed_client, sim_threshold=0.85)
        elapsed = time.time() - t0

        print(f"  Claims before: {result['claims_before']}")
        print(f"  Canonicals after: {result['canonicals_after']}")
        print(f"  Merges: {result['merges']}")
        print(f"  Time: {elapsed:.2f}s")

        if result["merges"] > 0:
            # Show 3 example merged pairs
            pairs = conn.execute("""
                SELECT cl.text as original, cv.text as variant, cl.id as canonical_id
                FROM claim_variants cv
                JOIN claims cl ON cl.id = cv.canonical_claim_id
                WHERE cl.cluster_id = ?
                LIMIT 3
            """, (cid,)).fetchall()
            print(f"  Example merged pairs ({len(pairs)} total):")
            for p in pairs:
                print(f"    Canonical: {p['original'][:100]}")
                print(f"    Variant:   {p['variant'][:100]}")
                print()

    conn.close()
    print("\nDone.")

asyncio.run(main())
