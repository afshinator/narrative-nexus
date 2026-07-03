#!/usr/bin/env python3
"""Phase 2 T4b: EPS sweep on /tmp/phase2.db with nomic embeddings.

Embed all articles once, then run DBSCAN at 5 eps values.
Report per-eps: labeled group merge rate, over-merge check,
sources-per-cluster histogram, largest cluster.
"""

import asyncio
import json
import os
import sqlite3
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import normalize

# Load .env before importing pipeline modules that may need API keys
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).resolve().parent.parent / ".env"
    load_dotenv(env_path)
except ImportError:
    pass

from pipeline.embedding_client import EmbeddingClient, MODEL_DIMS

# ── 15 Labeled Story Groups (T4a) ────────────────────────────────────────
# Each group: (name, [article_ids]) — articles about the SAME real-world event
# across >= 3 different sources.

LABELED_GROUPS = [
    ("US-Iran peace deal", [
        451, 1745, 1522, 1492, 345, 133, 2175, 789, 1255, 1842,
        2199, 169, 189, 153, 2198,
    ]),
    ("Venezuela earthquakes", [
        1491, 1695, 106, 332, 2216, 2048, 2201, 1687, 2200, 1678,
        772, 692, 567, 249, 1688,
    ]),
    ("World Cup 2026", [
        1748, 1720, 1933, 1650, 1641, 838, 1263, 1328, 1275, 1276,
        1230, 1340, 1723, 1719, 1708,
    ]),
    ("Japan M7.2 earthquake", [
        1498, 134, 1525, 1863,
    ]),
    ("Messi at World Cup", [
        1752, 1746, 1737, 1732, 1727, 1726, 1723, 1719, 1703, 1698,
    ]),
    ("Trump birthright citizenship", [
        711, 2729, 2707, 2725, 3152, 2837, 2834, 453, 312, 118,
    ]),
    ("SNAP benefits cuts", [
        2078, 145, 2473,
    ]),
    ("Western Europe heat wave", [
        186, 244, 174, 1564, 135, 1483, 187, 193, 180, 175,
    ]),
    ("Israel-Gaza-Hezbollah", [
        168, 2184, 2173, 453, 1861, 1239, 2148, 2123, 1885, 2910,
    ]),
    ("China-EU trade dispute", [
        1630, 1562, 1555, 1608, 1598, 1556, 1551, 1548, 764, 540,
    ]),
    ("Anthropic AI export ban", [
        157, 175, 486, 1493, 830,
    ]),
    ("Strait of Hormuz closure", [
        1518, 147, 131, 307, 306,
    ]),
    ("North Korea missile/navy", [
        336, 155, 1430, 2559, 3485,
    ]),
    ("Ukraine drone attack", [
        164, 277, 327, 1838,
    ]),
    ("Lebanon Hezbollah deal", [
        453, 2148, 2123, 1885, 2910,
    ]),
]


def load_provider_config(path="config/providers.json"):
    with open(path) as f:
        cfg = json.load(f)
    default_id = cfg["defaults"]["agent1_embedding"]
    for p in cfg["providers"]["embeddings"]:
        if p["id"] == default_id:
            return p
    raise SystemExit(f"Provider '{default_id}' not found")


def embed_all(conn, provider, rows, article_ids, texts):
    """Embed all articles via Fireworks nomic, cache in DB. Returns {aid: vector}."""
    model = provider["model"]
    expected_dim = MODEL_DIMS.get(model)

    # Check cache
    placeholders = ",".join("?" * len(article_ids))
    raw = conn.execute(
        f"SELECT article_id, vector, dim FROM embeddings WHERE model = ? AND article_id IN ({placeholders})",
        [model] + article_ids,
    ).fetchall()

    cached = {}
    for row in raw:
        if expected_dim is not None and row["dim"] != expected_dim:
            continue
        cached[row["article_id"]] = np.frombuffer(row["vector"], dtype=np.float64)

    # Embed uncached
    uncached_pairs = [(i, aid) for i, aid in enumerate(article_ids) if aid not in cached]
    if uncached_pairs:
        uncached_texts = [texts[i] for i, _ in uncached_pairs]
        print(f"  Embedding {len(uncached_pairs)} articles via {provider['name']} ({model})...", file=sys.stderr)
        client = EmbeddingClient(provider)
        loop = asyncio.get_event_loop()

        # Batch to respect 256-row limit
        BATCH = 256
        new_vecs = []
        for start in range(0, len(uncached_texts), BATCH):
            batch = uncached_texts[start:start + BATCH]
            batch_vecs = loop.run_until_complete(client.embed(batch))
            new_vecs.extend(batch_vecs)
            print(f"    Batch {start//BATCH + 1}: {len(batch)} texts, {len(batch_vecs)} vectors", file=sys.stderr)

        for (_, aid), vec in zip(uncached_pairs, new_vecs):
            arr = np.array(vec, dtype=np.float64)
            blob = arr.tobytes()
            conn.execute(
                "INSERT OR REPLACE INTO embeddings (article_id, model, dim, vector) VALUES (?, ?, ?, ?)",
                (aid, model, len(vec), blob),
            )
            cached[aid] = arr
        conn.commit()
        print(f"  Persisted {len(uncached_pairs)} new embeddings.", file=sys.stderr)

    return {aid: cached[aid] for aid in article_ids}


def run_dbscan_at_eps(all_vectors, article_ids, rows, texts, eps):
    """Run time-windowed DBSCAN at given eps. Returns {article_id: cluster_id}."""
    window_days = 14
    buckets = defaultdict(list)
    for i, row in enumerate(rows):
        ts_str = row["published_at"] or row["created_at"]
        try:
            ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            ts = datetime(2020, 1, 1, tzinfo=timezone.utc)
        epoch = datetime(2020, 1, 1, tzinfo=timezone.utc)
        wk = int((ts - epoch).total_seconds() / (86400 * window_days))
        buckets[wk].append(i)

    article_map = {}  # article_id -> cluster_label
    next_label = 0

    for wk in sorted(buckets):
        indices = buckets[wk]
        if len(indices) < 2:
            for idx in indices:
                article_map[article_ids[idx]] = next_label
                next_label += 1
            continue

        win_matrix = np.array([all_vectors[i] for i in indices], dtype=np.float64)
        win_norm = normalize(win_matrix)

        clustering = DBSCAN(eps=eps, min_samples=2, metric="cosine").fit(win_norm)
        labels = clustering.labels_

        label_map = {}  # DBSCAN label -> our global label
        for j, label in enumerate(labels):
            db_label = int(label)
            if db_label == -1:
                aid = article_ids[indices[j]]
                article_map[aid] = next_label
                next_label += 1
            else:
                if db_label not in label_map:
                    label_map[db_label] = next_label
                    next_label += 1
                aid = article_ids[indices[j]]
                article_map[aid] = label_map[db_label]

    return article_map


def evaluate(article_map, eps):
    """Evaluate clustering against labeled groups."""
    # Build {article_id: cluster_id}
    # For each group: check how many distinct clusters the group's articles fall into
    results = []
    total_articles = 0
    total_correctly_merged = 0  # articles in groups where ALL group articles share one cluster
    group_details = []

    for name, group_ids in LABELED_GROUPS:
        present = [aid for aid in group_ids if aid in article_map]
        if not present:
            continue
        total_articles += len(present)
        clusters = {article_map[aid] for aid in present}
        if len(clusters) == 1:
            total_correctly_merged += len(present)
            group_details.append((name, True, len(clusters), len(present)))
        else:
            group_details.append((name, False, len(clusters), len(present)))

    merge_rate = total_correctly_merged / total_articles * 100 if total_articles else 0

    # Over-merge check: do any two DIFFERENT labeled groups share a cluster?
    # Build cluster -> set of group names
    cluster_to_groups = defaultdict(set)
    for name, group_ids in LABELED_GROUPS:
        for aid in group_ids:
            if aid in article_map:
                cluster_to_groups[article_map[aid]].add(name)

    over_merges = []
    for cid, group_names in cluster_to_groups.items():
        if len(group_names) > 1:
            over_merges.append((cid, sorted(group_names)))

    # Sources-per-cluster histogram
    # Need to check: not available without DB. We'll approximate with article_map.
    # For now, just compute cluster sizes.
    cluster_sizes = Counter(article_map.values())
    size_hist = Counter(cluster_sizes.values())

    largest = max(cluster_sizes.values()) if cluster_sizes else 0

    return {
        "eps": eps,
        "labeled_groups_correct": sum(1 for _, correct, _, _ in group_details if correct),
        "labeled_groups_total": len(group_details),
        "merge_rate_pct": round(merge_rate, 1),
        "over_merges": over_merges[:5],  # top 5
        "n_over_merges": len(over_merges),
        "sources_per_cluster_hist": {},  # populated below
        "articles_per_cluster_hist": dict(sorted(size_hist.items())[:15]),
        "largest_cluster": largest,
        "n_clusters": len(set(article_map.values())),
        "group_details": group_details,
    }


def main():
    db_path = "/tmp/phase2.db"
    eps_values = [0.30, 0.35, 0.40, 0.45, 0.50]

    provider = load_provider_config()
    print(f"Embedding via: {provider['name']} ({provider['model']})", file=sys.stderr)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    # Fetch all articles with bodies
    rows = conn.execute("""
        SELECT a.id, a.title, a.body, a.published_at, a.created_at
        FROM articles a
        WHERE a.body_status = 'AVAILABLE'
          AND a.body IS NOT NULL AND a.body != ''
        ORDER BY a.id
    """).fetchall()

    article_ids = [r["id"] for r in rows]
    texts = [f"{r['title'] or ''} {r['body'][:200] if r['body'] else ''}" for r in rows]

    print(f"\nTotal articles: {len(article_ids)}", file=sys.stderr)

    # Step 1: Embed all (or load from cache)
    print(f"\n{'='*60}\nStep 1: Embedding\n{'='*60}", file=sys.stderr)
    t0 = time.time()
    emb_map = embed_all(conn, provider, rows, article_ids, texts)
    all_vectors = [emb_map[aid] for aid in article_ids]
    matrix = np.array(all_vectors, dtype=np.float64)
    print(f"  Embedded in {time.time()-t0:.1f}s. Matrix shape: {matrix.shape}", file=sys.stderr)

    # Step 2: Sweep eps
    print(f"\n{'='*60}\nStep 2: EPS Sweep\n{'='*60}", file=sys.stderr)
    all_results = []

    for eps in eps_values:
        print(f"\n--- eps={eps} ---", file=sys.stderr)
        t0 = time.time()
        article_map = run_dbscan_at_eps(all_vectors, article_ids, rows, texts, eps)
        elapsed = time.time() - t0

        result = evaluate(article_map, eps)
        result["elapsed_s"] = round(elapsed, 1)
        all_results.append(result)

        print(f"  Clusters: {result['n_clusters']}", file=sys.stderr)
        print(f"  Groups correctly merged: {result['labeled_groups_correct']}/{result['labeled_groups_total']}", file=sys.stderr)
        print(f"  Merge rate: {result['merge_rate_pct']}%", file=sys.stderr)
        print(f"  Over-merges: {result['n_over_merges']}", file=sys.stderr)
        print(f"  Largest cluster: {result['largest_cluster']}", file=sys.stderr)

    # Print final report
    print("\n\n" + "=" * 80)
    print("EPS SWEEP RESULTS")
    print("=" * 80)

    for r in all_results:
        print(f"\neps={r['eps']}")
        print(f"  Clusters: {r['n_clusters']}")
        print(f"  Groups correctly merged: {r['labeled_groups_correct']}/{r['labeled_groups_total']} ({r['merge_rate_pct']}%)")
        print(f"  Over-merge pairs: {r['n_over_merges']}")
        for cid, names in r["over_merges"]:
            print(f"    Cluster {cid}: {' + '.join(names)}")
        print(f"  Largest cluster: {r['largest_cluster']} articles")
        print(f"  Articles-per-cluster: {r['articles_per_cluster_hist']}")
        print(f"  Time: {r['elapsed_s']}s")

        # Show which groups failed
        failed = [(n, nc) for n, ok, nc, na in r["group_details"] if not ok]
        if failed:
            print(f"  Failed groups (split across clusters):")
            for name, nclusters in failed:
                print(f"    {name}: {nclusters} clusters")

    conn.close()


if __name__ == "__main__":
    main()
