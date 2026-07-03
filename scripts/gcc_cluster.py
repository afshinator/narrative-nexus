#!/usr/bin/env python3
"""Z3: Graph connected-components clustering — alternative to DBSCAN.

Builds a graph: nodes = articles, edges = pair with similarity >= tau.
Clusters = connected components. No density chaining except through edges.
"""

import asyncio, os, sqlite3, sys, time
import numpy as np
from collections import Counter, defaultdict
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except ImportError:
    pass

import openai

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from pipeline.cleaner import get_embedding_input

# ── Revised 13 labeled groups ────────────────────────────────────────────
LABELED_GROUPS = [
    ("US-Iran peace deal", {451, 1745, 1522, 1492, 345, 133, 2175, 789, 1255, 1842, 2199, 169, 189, 153, 2198}),
    ("Venezuela earthquakes", {1491, 1695, 106, 332, 2216, 2048, 2201, 1687, 2200, 1678, 772, 692, 567, 249, 1688}),
    ("World Cup 2026 (+Messi)", {1748, 1720, 1933, 1650, 1641, 838, 1263, 1328, 1275, 1276, 1230, 1340, 1723, 1719, 1708, 1752, 1746, 1737, 1732, 1727, 1726, 1703, 1698}),
    ("Japan M7.2 earthquake", {1498, 134, 1525, 1863}),
    ("Trump birthright citizenship", {711, 2729, 2707, 2725, 3152, 2837, 2834, 312, 118}),
    ("SNAP benefits cuts", {2078, 145, 2473}),
    ("Western Europe heat wave", {186, 244, 174, 1564, 135, 1483, 187, 193, 180}),
    ("Israel-Hezbollah conflict", {168, 2184, 2173, 453, 1861, 1239, 2148, 2123, 1885, 2910}),
    ("China-EU trade dispute", {1630, 1562, 1555, 1608, 1598, 1556, 1551, 1548, 764, 540}),
    ("Anthropic AI export ban", {157, 175, 486, 1493, 830}),
    ("Strait of Hormuz closure", {1518, 147, 131, 307, 306}),
    ("North Korea missile/navy", {336, 155, 1430, 2559, 3485}),
    ("Ukraine drone attack", {164, 277, 327, 1838}),
]


def connected_components(nodes, edges):
    """Find connected components via union-find."""
    parent = {n: n for n in nodes}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    for a, b in edges:
        union(a, b)

    comps = defaultdict(list)
    for n in nodes:
        comps[find(n)].append(n)
    return list(comps.values())


def evaluate(components, article_to_aid):
    """Evaluate clustering against labeled groups."""
    # Map aid → component index
    aid_to_comp = {}
    for ci, comp in enumerate(components):
        for aid in comp:
            aid_to_comp[aid] = ci

    groups_correct = 0
    groups_total = 0
    false_merges = []

    for name, group_aids in LABELED_GROUPS:
        present = group_aids & set(aid_to_comp.keys())
        if len(present) < 2:
            continue
        groups_total += 1
        comps_for_group = {aid_to_comp[aid] for aid in present}
        if len(comps_for_group) == 1:
            groups_correct += 1

    # False merges: two different labeled groups in same component
    comp_to_groups = defaultdict(set)
    for name, group_aids in LABELED_GROUPS:
        for aid in group_aids:
            if aid in aid_to_comp:
                comp_to_groups[aid_to_comp[aid]].add(name)

    for ci, gnames in comp_to_groups.items():
        if len(gnames) > 1:
            false_merges.append((ci, sorted(gnames)))

    return groups_correct, groups_total, false_merges


async def main():
    db_path = "/tmp/phase2.db"
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    rows = conn.execute("""
        SELECT a.id, a.title, a.body, a.source_id
        FROM articles a
        WHERE a.body_status = 'AVAILABLE'
          AND a.body IS NOT NULL AND a.body != ''
        ORDER BY a.id
    """).fetchall()

    article_ids = [r["id"] for r in rows]
    inputs = [get_embedding_input(r["title"], r["body"] or "", max_body_chars=1000) for r in rows]

    print(f"Articles: {len(article_ids)}")
    conn.close()

    key = os.environ.get("FIREWORKS_API_KEY", "")
    client = openai.AsyncOpenAI(base_url="https://api.fireworks.ai/inference/v1", api_key=key, timeout=120)

    # Determine which model from Z2 to use — default to BGE
    model_id = "BAAI/bge-base-en-v1.5"

    # Embed all
    print(f"\nEmbedding {len(inputs)} articles via {model_id}...")
    t0 = time.time()
    vectors = []
    BATCH = 200
    for start in range(0, len(inputs), BATCH):
        batch = inputs[start:start + BATCH]
        resp = await client.embeddings.create(model=model_id, input=batch)
        for d in resp.data:
            vectors.append(np.array(d.embedding, dtype=np.float64))
        print(f"  Batch {start//BATCH + 1}: {len(batch)} texts")
    print(f"  Embedded in {time.time()-t0:.1f}s")

    # Normalize
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms[norms == 0] = 1
    vecs_norm = vectors / norms

    # Compute full similarity matrix (all-pairs)
    print(f"\nComputing {len(article_ids)}x{len(article_ids)} similarity matrix...")
    t0 = time.time()
    sim_matrix = vecs_norm @ vecs_norm.T
    print(f"  Computed in {time.time()-t0:.1f}s")

    # ── GCC at different tau values ─────────────────────────────────────
    for tau in [0.65, 0.70, 0.75, 0.80]:
        print(f"\n{'='*60}")
        print(f"tau={tau}")
        print(f"{'='*60}")

        # Build edges
        edges = []
        n = len(article_ids)
        for i in range(n):
            for j in range(i+1, n):
                if sim_matrix[i][j] >= tau:
                    edges.append((article_ids[i], article_ids[j]))

        print(f"  Edges: {len(edges)}")

        # Connected components
        components = connected_components(article_ids, edges)
        sizes = [len(c) for c in components]
        size_hist = Counter(sizes)

        print(f"  Components: {len(components)}")
        print(f"  Largest: {max(sizes)}")
        print(f"  Size histogram: {dict(sorted(size_hist.items())[:10])}")

        # Evaluate against labeled groups
        correct, total, false_merges = evaluate(components, {})
        print(f"  Groups merged: {correct}/{total}")
        print(f"  False-merges: {len(false_merges)}")
        for ci, names in false_merges[:5]:
            print(f"    Component {ci}: {' + '.join(names)}")


asyncio.run(main())
