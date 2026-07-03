#!/usr/bin/env python3
"""Z1+Z2: Cross-source same-topic + across-group similarity analysis."""
import asyncio, os, sqlite3, sys, random
import numpy as np
from collections import defaultdict
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except ImportError:
    pass

import openai

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from pipeline.cleaner import get_embedding_input

# ── 5 groups with >=3 sources ────────────────────────────────────────────
GROUPS = {
    "US-Iran peace deal": [451, 1745, 1522, 1492, 345, 133, 2175, 789, 1255, 1842, 2199, 169, 189, 153, 2198],
    "Venezuela earthquakes": [1491, 1695, 106, 332, 2216, 2048, 2201, 1687, 2200, 1678, 772, 692, 567, 249, 1688],
    "World Cup 2026 (+Messi)": [1748, 1720, 1933, 1650, 1641, 838, 1263, 1328, 1275, 1276, 1230, 1340, 1723, 1719, 1708, 1752, 1746, 1737, 1732, 1727, 1726, 1703, 1698],
    "Trump birthright citizenship": [711, 2729, 2707, 2725, 3152, 2837, 2834, 312, 118],
    "Israel-Hezbollah conflict": [168, 2184, 2173, 453, 1861, 1239, 2148, 2123, 1885, 2910],
}

conn = sqlite3.connect("file:data/nn.db?mode=ro", uri=True)
conn.row_factory = sqlite3.Row

# Build article metadata
all_articles = {}
for name, aids in GROUPS.items():
    placeholders = ",".join("?" * len(aids))
    rows = conn.execute(f"SELECT a.id, a.title, a.body, s.name as sn FROM articles a JOIN sources s ON s.id=a.source_id WHERE a.id IN ({placeholders})", aids).fetchall()
    for r in rows:
        all_articles[r["id"]] = {"title": r["title"], "body": r["body"], "source": r["sn"], "group": name}

conn.close()

# Build input texts (cleaned, 1000-char)
inputs = {}
for aid, meta in all_articles.items():
    inputs[aid] = get_embedding_input(meta["title"], meta["body"] or "", max_body_chars=1000)

print(f"Total articles: {len(inputs)}")
print(f"Groups: {list(GROUPS.keys())}")
for name, aids in GROUPS.items():
    sources = {all_articles[aid]["source"] for aid in aids}
    print(f"  {name}: {len(sources)} sources, {len(aids)} articles")

key = os.environ.get("FIREWORKS_API_KEY", "")
client = openai.AsyncOpenAI(base_url="https://api.fireworks.ai/inference/v1", api_key=key, timeout=60)


async def embed_batch(model_id, aid_list):
    batch_inputs = [inputs[aid] for aid in aid_list]
    resp = await client.embeddings.create(model=model_id, input=batch_inputs)
    return {aid: np.array(d.embedding, dtype=np.float64) for aid, d in zip(aid_list, resp.data)}


def cosine(a, b):
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


async def analyze_model(model_id, model_name):
    print(f"\n{'='*70}")
    print(f"MODEL: {model_name} ({model_id})")
    print(f"{'='*70}")

    all_aids = list(inputs.keys())
    embeddings = await embed_batch(model_id, all_aids)

    # ── Z1a: Per-group article list ────────────────────────────────────
    print("\n--- Z1a: Articles and sources ---")
    for name, aids in GROUPS.items():
        print(f"\n  {name}:")
        for aid in aids:
            meta = all_articles[aid]
            print(f"    ID={aid:6d}  {meta['source']:20s}  {meta['title'][:80]}")

    # ── Z1b+c: Intra-group pairwise similarities ───────────────────────
    print(f"\n--- Z1c: Intra-group similarity distributions ---")
    for name, aids in GROUPS.items():
        sims = []
        for i in range(len(aids)):
            for j in range(i+1, len(aids)):
                v1 = embeddings[aids[i]]
                v2 = embeddings[aids[j]]
                sims.append(cosine(v1, v2))

        buckets = {0.85: 0, 0.75: 0, 0.70: 0, 0.65: 0, 0.60: 0}
        for s in sims:
            for t in sorted(buckets, reverse=True):
                if s >= t:
                    buckets[t] += 1
                    break

        total = len(sims)
        print(f"\n  {name} ({total} pairs):")
        print(f"    min={min(sims):.4f}  mean={np.mean(sims):.4f}  max={max(sims):.4f}")
        for t in sorted(buckets, reverse=True):
            pct = buckets[t] / total * 100 if total else 0
            print(f"    >= {t:.2f}: {buckets[t]:3d} pairs ({pct:5.1f}%)")

    # ── Z1d: 20 random across-group pairs ──────────────────────────────
    print(f"\n--- Z1d: 20 random across-group pairs ---")
    group_aids = {name: set(aids) for name, aids in GROUPS.items()}
    across_sims = []
    random.seed(42)
    pairs_done = set()
    attempts = 0
    while len(across_sims) < 20 and attempts < 1000:
        attempts += 1
        g1, g2 = random.sample(list(GROUPS.keys()), 2)
        aid1 = random.choice(list(group_aids[g1]))
        aid2 = random.choice(list(group_aids[g2]))
        pair_key = (min(aid1, aid2), max(aid1, aid2), g1, g2)
        if pair_key in pairs_done:
            continue
        pairs_done.add(pair_key)
        s = cosine(embeddings[aid1], embeddings[aid2])
        across_sims.append(s)
        print(f"    {g1[:20]} vs {g2[:20]}: {s:.4f}")

    print(f"\n  Across-group: mean={np.mean(across_sims):.4f}, min={min(across_sims):.4f}, max={max(across_sims):.4f}")

    # ── Gap summary ────────────────────────────────────────────────────
    all_intra = []
    for name, aids in GROUPS.items():
        for i in range(len(aids)):
            for j in range(i+1, len(aids)):
                all_intra.append(cosine(embeddings[aids[i]], embeddings[aids[j]]))

    print(f"\n--- GAP SUMMARY ---")
    print(f"  Intra-group mean: {np.mean(all_intra):.4f}")
    print(f"  Across-group mean: {np.mean(across_sims):.4f}")
    print(f"  Gap: {np.mean(all_intra) - np.mean(across_sims):.4f}")


async def main():
    # Z1: Nomic
    await analyze_model("nomic-ai/nomic-embed-text-v1.5", "NOMIC")

    # Z2: BGE
    await analyze_model("BAAI/bge-base-en-v1.5", "BGE")


asyncio.run(main())
