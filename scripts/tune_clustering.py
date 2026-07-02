"""T5d: Eps tuning harness — sweep DBSCAN eps on hand-picked story groups.

Tests whether different eps values correctly merge articles covering the
same real-world event from different sources.

Usage: python3 scripts/tune_clustering.py
"""

import sys, os
sys.path.insert(0, ".")
import sqlite3
import numpy as np
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import normalize
from pipeline.embedding_client import EmbeddingClient
from dotenv import load_dotenv
load_dotenv(".env")


# ── Hand-picked story groups (June 2026, same event, 3+ sources each) ──

STORY_GROUPS = [
    {
        "label": "Iran-US strikes",
        "article_ids": [1851, 1852, 1853, 1904, 1905],
        "description": "US strikes on Iran targets; Iran attacks Bahrain/Kuwait",
    },
    {
        "label": "Venezuela earthquake",
        "article_ids": [1763, 1764, 1765, 1771, 1772, 1873],
        "description": "Venezuela earthquakes, rescue efforts, death toll",
    },
    {
        "label": "Andy Burnham UK politics",
        "article_ids": [2850, 2851, 2852, 3110, 3111],
        "description": "Andy Burnham as potential UK PM, devolution plan",
    },
    {
        "label": "Pakistan-Afghanistan strikes",
        "article_ids": [3120, 3121, 3122, 3123, 3124, 3125],
        "description": "Pakistan ground operations and strikes along Afghan border",
    },
    {
        "label": "Europe heatwave",
        "article_ids": [1760, 1761, 1950, 1951],
        "description": "Heat records in Central Europe, climate denial",
    },
    {
        "label": "US Supreme Court rulings",
        "article_ids": [3140, 3141, 3142, 3143],
        "description": "Supreme Court decisions on Trump, Lisa Cook, federal workers",
    },
    {
        "label": "South Africa migration",
        "article_ids": [3160, 3161, 3162, 3163, 3164],
        "description": "Anti-migrant sentiment, undocumented migrants, deadline",
    },
    {
        "label": "Social media bans",
        "article_ids": [3170, 3171, 3172, 3173, 3174],
        "description": "Australia/Japan social media regulation for youth",
    },
    {
        "label": "Israel-Lebanon deal",
        "article_ids": [1740, 1741, 1742, 1743],
        "description": "Lebanon-Israel ceasefire, war crimes, ICJ rulings",
    },
    {
        "label": "Cape Verde World Cup",
        "article_ids": [1720, 1721, 1722, 1860, 1861],
        "description": "Cape Verde soccer success, African soccer rise",
    },
    {
        "label": "Venezuela rescue (sub-story)",
        "article_ids": [1864, 1865, 1866, 1870, 1871],
        "description": "Venezuela rescue efforts, volunteer rush, aftershock",
    },
    {
        "label": "Skydiving plane crash",
        "article_ids": [3180, 3181, 3182],
        "description": "Plane crash in France, China restricts aircraft",
    },
    {
        "label": "Trump legal cases",
        "article_ids": [3200, 3201, 3202],
        "description": "Trump appeal, Supreme Court ruling, E Jean Carroll",
    },
    {
        "label": "Economic policy varied",
        "article_ids": [3300, 3301, 3302, 3303],
        "description": "Apple prices, Fed policy, trade tariffs — UNRELATED (should NOT merge)",
    },
    {
        "label": "Sports varied",
        "article_ids": [3400, 3401, 3402, 3403],
        "description": "Messi, Serena Williams, Japan-Brazil — UNRELATED (should NOT merge)",
    },
]


async def tune():
    db = sqlite3.connect("data/nn.db")
    db.row_factory = sqlite3.Row

    provider = {
        "id": "fireworks", "name": "Fireworks AI",
        "model": "nomic-ai/nomic-embed-text-v1.5", "amd": True,
    }
    api_key = os.environ.get("FIREWORKS_API_KEY", "")
    client = EmbeddingClient(provider, api_key=api_key)

    eps_values = [0.30, 0.35, 0.40, 0.45, 0.50]

    for group in STORY_GROUPS:
        label = group["label"]
        aids = group["article_ids"]

        # Get article texts
        placeholders = ",".join("?" * len(aids))
        rows = db.execute(
            f"SELECT id, title, body, source_id FROM articles WHERE id IN ({placeholders})",
            aids,
        ).fetchall()

        if len(rows) < 2:
            print(f"\n{label}: SKIPPED — only {len(rows)} articles found in DB")
            continue

        texts = [
            f"{r['title'] or ''} {r['body'][:200] if r['body'] else ''}"
            for r in rows
        ]
        source_ids = [r["source_id"] for r in rows]

        # Generate embeddings
        vectors = await client.embed(texts)
        matrix = np.array(vectors, dtype=np.float64)
        matrix_norm = normalize(matrix)

        unique_sources = len(set(source_ids))
        print(f"\n{'='*60}")
        print(f"Group: {label} ({len(rows)} articles, {unique_sources} sources)")
        print(f"  {group['description']}")
        print(f"  Article IDs: {aids[:8]}{'...' if len(aids) > 8 else ''}")
        print(f"  Source IDs: {source_ids}")
        print()

        header = f"{'eps':>8} {'clusters':>8} {'max_cluster':>12} {'noise':>8} {'merge?':>8}"
        print(header)
        print("-" * len(header))

        for eps in eps_values:
            clustering = DBSCAN(eps=eps, min_samples=2, metric="cosine").fit(matrix_norm)
            labels = clustering.labels_

            n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
            n_noise = list(labels).count(-1)

            # Cluster size distribution
            cluster_sizes = {}
            for l in labels:
                if l != -1:
                    cluster_sizes[l] = cluster_sizes.get(l, 0) + 1
            max_size = max(cluster_sizes.values()) if cluster_sizes else 0

            # Check: do articles from different sources end up in same cluster?
            source_clusters = {}
            for i, l in enumerate(labels):
                if l != -1:
                    source_clusters.setdefault(l, set()).add(source_ids[i])

            # "Good merge" = cluster contains articles from 2+ sources
            good_merges = sum(1 for srcs in source_clusters.values() if len(srcs) >= 2)

            merge_note = "MERGE" if good_merges > 0 else "no"

            print(f"{eps:>8.2f} {n_clusters:>8} {max_size:>12} {n_noise:>8} {merge_note:>8}")

            if good_merges > 0:
                for cl, srcs in source_clusters.items():
                    if len(srcs) >= 2:
                        print(f"         cluster {cl}: sources {srcs} ({len(srcs)} sources)")

    db.close()


if __name__ == "__main__":
    import asyncio
    asyncio.run(tune())
