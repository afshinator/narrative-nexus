#!/usr/bin/env python3
"""V2a: DB-only article search via embedding similarity."""
import asyncio, os, sqlite3, sys, time, numpy as np
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(".") / ".env")
sys.path.insert(0, ".")

from pipeline.embedding_client import EmbeddingClient

QUERIES = [
    "Iran deal US peace agreement nuclear negotiations",          # must use full engine
    "Venezuela earthquake Caracas damage casualties",             # same en
    "World Cup 2026 soccer tournament results",                  # en
    "Anthropic AI export controls Fable Mythos models ban",      # en (must match [Anthropic] in claim_matching)
    "SNAP benefits cuts food assistance program",               # en
]

async def main():
    provider = {"id":"fireworks","model":"BAAI/bge-base-en-v1.5","base_url":"https://api.fireworks.ai/inference/v1"}
    client = EmbeddingClient(provider)

    # Load cached embeddings from DB
    conn = sqlite3.connect("data/nn.db")
    conn.row_factory = sqlite3.Row
    emb_rows = conn.execute("SELECT article_id, vector FROM embeddings WHERE model LIKE '%bge%'").fetchall()
    print(f"Loaded {len(emb_rows)} cached embeddings")
    # Build matrix
    article_ids = []
    vectors = []
    for r in emb_rows:
        try:
            vec = np.array([float(x) for x in r["vector"].split(",")], dtype=np.float32)
            if len(vec) == 768:
                vectors.append(vec)
                article_ids.append(r["article_id"])
        except Exception:
            pass
    matrix = np.stack(vectors)
    matrix = matrix / np.linalg.norm(matrix, axis=1, keepdims=True)
    print(f"Matrix: {matrix.shape}")

    # Query metadata table
    aid_to_info = {}
    for row in conn.execute("SELECT a.id, a.title, s.name as sn, a.published_at FROM articles a JOIN sources s ON s.id=a.source_id WHERE a.id IN ({}))".format(",".join("?"*len(article_ids))), article_ids).fetchall():
        aid_to_info[row["id"]] = {"title": row["title"], "source": row["sn"], "date": row["published_at"]}
    conn.close()

    for q in QUERIES:
        print(f"\n=== Query: {q[:50]}... ===")
        t0 = time.time()
        vecs = await client.embed([q])
        qvec = np.array(vecs[0], dtype=np.float32)
        qvec = qvec / np.linalg.norm(qvec)
        sims = np.dot(matrix, qvec)
        top = np.argsort(sims)[-10:][::-1]
        t = time.time() - t0
        print(f"  Time: {t:.1f}s")
        for rank, idx in enumerate(top):
            aid = article_ids[idx]
            info = aid_to_info.get(aid, {})
            print(f"  {rank+1}. sim={sims[idx]:.4f} [{info.get("source","?")}] {info.get("title","?")[:70]}")

asyncio.run(main())
