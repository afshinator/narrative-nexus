#!/usr/bin/env python3
"""D2: Near-miss claim pairs involving articles 943-945 — nomic cosine similarity."""
import asyncio, os, sys, sqlite3
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pipeline.claim_matching import get_claim_matching_embed_client

DB = "data/demo/demo.db"
TARGETS = {943, 944, 945}
SIM_THRESHOLD = 0.85

os.environ["FIREWORKS-NOMIC_API_KEY"] = os.environ.get("FIREWORKS_API_KEY", "")

async def main():
    # Get all claims in cluster 966 with source info
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("""
        SELECT c.id, c.text, c.article_id, s.name as source_name, a.published_at
        FROM claims c
        JOIN articles a ON a.id = c.article_id
        JOIN sources s ON s.id = a.source_id
        WHERE c.cluster_id = 966
        ORDER BY a.published_at, c.id
    """).fetchall()
    conn.close()

    print(f"Cluster 966: {len(rows)} claims")

    # Generate nomic embeddings (batched, same code path as matcher)
    client = get_claim_matching_embed_client("config/providers.json")
    texts = [r["text"] for r in rows]

    print(f"Generating nomic embeddings for {len(texts)} claims...")
    vectors = await client.embed(texts)
    vecs = np.array(vectors, dtype=np.float32)
    print(f"Embeddings shape: {vecs.shape}")

    # Compute pairwise cosine similarity for cross-source pairs involving 943-945
    pairs = []
    for i in range(len(rows)):
        if rows[i]["article_id"] not in TARGETS:
            continue
        for j in range(len(rows)):
            if i >= j:
                continue
            if rows[i]["article_id"] == rows[j]["article_id"]:
                continue  # same-source, not interesting
            sim = float(np.dot(vecs[i], vecs[j]) / (np.linalg.norm(vecs[i]) * np.linalg.norm(vecs[j])))
            pairs.append((sim, i, j))

    pairs.sort(key=lambda x: -x[0])

    print(f"\nTop 5 closest cross-source pairs involving 943-945 (threshold={SIM_THRESHOLD}):")
    for rank, (sim, i, j) in enumerate(pairs[:5]):
        a = rows[i]
        b = rows[j]
        merged = "WOULD MERGE" if sim >= SIM_THRESHOLD else "NO MERGE"
        print(f"\nPair {rank+1}: sim={sim:.4f} [{merged}]")
        print(f"  A (art {a['article_id']}, {a['source_name']}): {a['text'][:120]}")
        print(f"  B (art {b['article_id']}, {b['source_name']}): {b['text'][:120]}")

    # Also: did matcher actually try to merge these? Check claim_variants
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    variants = conn.execute("""
        SELECT cv.canonical_claim_id, cv.text, cv.article_id, s.name as source_name
        FROM claim_variants cv
        JOIN articles a ON a.id = cv.article_id
        JOIN sources s ON s.id = a.source_id
        WHERE cv.article_id IN (943, 944, 945)
    """).fetchall()
    conn.close()
    print(f"\nClaim variants from 943-945 (absorbed into canonicals): {len(variants)}")
    for v in variants:
        print(f"  Variant art {v['article_id']} ({v['source_name']}) -> canonical {v['canonical_claim_id']}: {v['text'][:100]}")

    # Claims from 943-945 that ARE canonicals (not variants)
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    canonicals = conn.execute("""
        SELECT c.id, c.text, c.article_id, s.name as source_name
        FROM claims c
        JOIN articles a ON a.id = c.article_id
        JOIN sources s ON s.id = a.source_id
        WHERE c.article_id IN (943, 944, 945)
        AND c.id NOT IN (SELECT canonical_claim_id FROM claim_variants)
    """).fetchall()
    conn.close()
    print(f"\n943-945 claims that survived as canonicals (not merged away): {len(canonicals)}")
    for cc in canonicals:
        print(f"  Canonical {cc['id']} (art {cc['article_id']}, {cc['source_name']}): {cc['text'][:120]}")

if __name__ == "__main__":
    asyncio.run(main())
