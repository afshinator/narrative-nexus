#!/usr/bin/env python3
"""W1+W2: Test BGE+DBSCAN combo with full metrics. Embed once, sweep both modes."""
import asyncio, os, sqlite3, sys, time
import numpy as np
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except ImportError:
    pass

import openai
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import normalize

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from pipeline.cleaner import get_embedding_input
from pipeline.vertical_classifier import classify_text, get_vertical_list

# ── 13 revised labeled groups (D2b) ─────────────────────────────────────
LABELED = [
    ("US-Iran", {451,1745,1522,1492,345,133,2175,789,1255,1842,2199,169,189,153,2198}),
    ("Venezuela", {1491,1695,106,332,2216,2048,2201,1687,2200,1678,772,692,567,249,1688}),
    ("WorldCup", {1748,1720,1933,1650,1641,838,1263,1328,1275,1276,1230,1340,1723,1719,1708,1752,1746,1737,1732,1727,1726,1703,1698}),
    ("JapanQuake", {1498,134,1525,1863}),
    ("Birthright", {711,2729,2707,2725,3152,2837,2834,312,118}),
    ("SNAP", {2078,145,2473}),
    ("HeatWave", {186,244,174,1564,135,1483,187,193,180}),
    ("Israel-Hez", {168,2184,2173,453,1861,1239,2148,2123,1885,2910}),
    ("China-EU", {1630,1562,1555,1608,1598,1556,1551,1548,764,540}),
    ("Anthropic", {157,175,486,1493,830}),
    ("Hormuz", {1518,147,131,307,306}),
    ("NKorea", {336,155,1430,2559,3485}),
    ("UkraineDrone", {164,277,327,1838}),
]


def bucket_key(ts_str, window_days=14):
    try:
        ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        ts = datetime(2020, 1, 1, tzinfo=timezone.utc)
    epoch = datetime(2020, 1, 1, tzinfo=timezone.utc)
    return int((ts - epoch).total_seconds() / (86400 * window_days))


async def embed_all(articles, model_id, client):
    """Embed all articles via API, return {aid: np.array}."""
    all_aids = list(articles.keys())
    inputs = [articles[aid]["input"] for aid in all_aids]
    vectors = {}
    BATCH = 200
    for start in range(0, len(inputs), BATCH):
        batch = inputs[start:start + BATCH]
        batch_aids = all_aids[start:start + BATCH]
        resp = await client.embeddings.create(model=model_id, input=batch)
        for aid, d in zip(batch_aids, resp.data):
            vectors[aid] = np.array(d.embedding, dtype=np.float64)
    return vectors


def run_dbscan(bucket_indices, all_vectors, eps):
    """Run DBSCAN on a bucket of indices. Returns dict: aid -> cluster_label."""
    if len(bucket_indices) < 2:
        return {idx: idx for idx in bucket_indices}  # each is own cluster

    mat = np.array([all_vectors[i] for i in bucket_indices], dtype=np.float64)
    mat_norm = normalize(mat)
    clustering = DBSCAN(eps=eps, min_samples=2, metric="cosine").fit(mat_norm)
    labels = clustering.labels_

    result = {}
    for j, idx in enumerate(bucket_indices):
        result[idx] = bucket_indices[0] + int(labels[j]) if labels[j] != -1 else idx
    return result


def evaluate(article_map, aid_to_cluster):
    """Evaluate clustering against labeled groups."""
    # Build cluster -> set of aids
    cluster_to_aids = defaultdict(set)
    for aid, cid in aid_to_cluster.items():
        cluster_to_aids[cid].add(aid)

    clusters_list = list(cluster_to_aids.values())

    # Evaluate labeled groups
    groups_correct = 0
    groups_total = 0
    group_results = []

    for name, group_aids in LABELED:
        present = group_aids & set(aid_to_cluster.keys())
        if len(present) < 2:
            continue
        groups_total += 1
        comps = {aid_to_cluster[aid] for aid in present}
        merged = len(comps) == 1
        if merged:
            groups_correct += 1
        group_results.append((name, merged, len(comps)))

    # False merges (D2-revised: only flag if clusters contain >= 2 labeled groups)
    # We consider it a false merge if any cluster has articles from >= 2 labeled groups
    cluster_to_groups = defaultdict(set)
    for name, group_aids in LABELED:
        for aid in group_aids:
            if aid in aid_to_cluster:
                cluster_to_groups[aid_to_cluster[aid]].add(name)

    false_merges = [(cid, sorted(gnames)) for cid, gnames in cluster_to_groups.items() if len(gnames) > 1]

    # Multi-source cluster counts
    conn3 = sqlite3.connect("file:data/nn.db?mode=ro", uri=True)
    aid_to_src = dict(conn3.execute("SELECT a.id, a.source_id FROM articles a WHERE a.id IN ({})".format(
        ",".join("?" * len(aid_to_cluster))
    ), list(aid_to_cluster.keys())).fetchall())
    conn3.close()

    multi_src = {1: 0, 2: 0, 3: 0, 5: 0}
    for cid, aids in cluster_to_aids.items():
        n_src = len({aid_to_src.get(a, -1) for a in aids})
        for thresh in [5, 3, 2, 1]:
            if n_src >= thresh:
                multi_src[thresh] += 1
                break

    # Sources-per-cluster histogram
    src_hist = Counter()
    for cid, aids in cluster_to_aids.items():
        n_src = len({aid_to_src.get(a, -1) for a in aids})
        if n_src <= 1:
            bucket = 1
        elif n_src <= 2:
            bucket = 2
        elif n_src <= 5:
            bucket = "3-5"
        elif n_src <= 10:
            bucket = "6-10"
        else:
            bucket = "11+"
        src_hist[bucket] += 1

    # Largest cluster
    largest = max(len(aids) for aids in cluster_to_aids.values()) if cluster_to_aids else 0
    n_clusters = len(cluster_to_aids)
    n_singletons = sum(1 for aids in cluster_to_aids.values() if len(aids) == 1)

    return {
        "n_clusters": n_clusters,
        "n_non_singleton": n_clusters - n_singletons,
        "largest": largest,
        "groups_merged": groups_correct,
        "groups_total": groups_total,
        "false_merges": len(false_merges),
        "false_merge_detail": false_merges[:5],
        "multi_src_2": multi_src.get(2, 0),
        "multi_src_3": multi_src.get(3, 0),
        "multi_src_5": multi_src.get(5, 0),
        "src_histogram": dict(src_hist),
    }


async def main():
    db_path = "/tmp/phase2.db"
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    rows = conn.execute("""
        SELECT a.id, a.title, a.body, a.published_at, a.created_at
        FROM articles a
        WHERE a.body_status = 'AVAILABLE'
          AND a.body IS NOT NULL AND a.body != ''
        ORDER BY a.id
    """).fetchall()

    articles = {}
    for r in rows:
        articles[r["id"]] = {
            "input": get_embedding_input(r["title"], r["body"] or "", max_body_chars=1000),
            "ts": r["published_at"] or r["created_at"] or "2020-01-01",
            "aid": r["id"],
        }

    print(f"Articles: {len(articles)}")
    conn.close()

    key = os.environ.get("FIREWORKS_API_KEY", "")
    client = openai.AsyncOpenAI(base_url="https://api.fireworks.ai/inference/v1", api_key=key, timeout=180)

    # ── Embed all with BGE ──────────────────────────────────────────────
    model_id = "BAAI/bge-base-en-v1.5"
    print(f"\nEmbedding {len(articles)} articles via {model_id}...")
    t0 = time.time()
    vectors = await embed_all(articles, model_id, client)
    print(f"  Done in {time.time()-t0:.1f}s")

    # Build ordered arrays for DBSCAN
    aid_list = list(articles.keys())
    all_vectors_arr = [vectors[aid] for aid in aid_list]
    aid_to_idx = {aid: i for i, aid in enumerate(aid_list)}

    # ── W1: Sweep DBSCAN (time-windowed only) ───────────────────────────
    print(f"\n{'='*70}")
    print("W1: BGE + DBSCAN (14-day windows, no vertical bucketing)")
    print(f"{'='*70}")

    eps_values = [0.25, 0.30, 0.35, 0.40]
    w1_results = []

    for eps in eps_values:
        # Time-window bucketing
        windows = defaultdict(list)
        for aid in aid_list:
            wk = bucket_key(articles[aid]["ts"])
            windows[wk].append(aid_to_idx[aid])

        # Cluster per window
        aid_to_cluster = {}
        for wk in sorted(windows):
            indices = windows[wk]
            cluster_map = run_dbscan(indices, all_vectors_arr, eps)
            for idx, cid in cluster_map.items():
                aid_to_cluster[aid_list[idx]] = cid

        metrics = evaluate({}, aid_to_cluster)
        metrics["eps"] = eps
        w1_results.append(metrics)

        print(f"\neps={eps}:")
        print(f"  Clusters: {metrics['n_clusters']} ({metrics['n_non_singleton']} non-singleton)")
        print(f"  Largest: {metrics['largest']}")
        print(f"  Groups merged: {metrics['groups_merged']}/{metrics['groups_total']}")
        print(f"  False-merges: {metrics['false_merges']}")
        print(f"  Multi-source: >=2: {metrics['multi_src_2']}, >=3: {metrics['multi_src_3']}, >=5: {metrics['multi_src_5']}")
        print(f"  Src-histogram: {metrics['src_histogram']}")

    # ── W2: Vertical pre-bucketing ──────────────────────────────────────
    # Pick best eps from W1 (later)
    print(f"\n{'='*70}")
    print("W2: BGE + DBSCAN (14-day windows × vertical)")
    print(f"{'='*70}")

    # Classify each article
    print("Classifying verticals...")
    aid_to_vertical = {}
    for aid in aid_list:
        aid_to_vertical[aid] = classify_text(articles[aid]["input"][:2000])
    vert_dist = Counter(aid_to_vertical.values())
    print(f"  Vertical distribution: {dict(vert_dist)}")

    w2_results = []
    for eps in eps_values:
        # Bucket by (window_key, vertical)
        buckets = defaultdict(list)
        for aid in aid_list:
            wk = bucket_key(articles[aid]["ts"])
            vert = aid_to_vertical[aid]
            buckets[(wk, vert)].append(aid_to_idx[aid])

        aid_to_cluster = {}
        for (wk, vert), indices in sorted(buckets.items()):
            cluster_map = run_dbscan(indices, all_vectors_arr, eps)
            for idx, cid in cluster_map.items():
                aid_to_cluster[aid_list[idx]] = cid

        metrics = evaluate({}, aid_to_cluster)
        metrics["eps"] = eps
        w2_results.append(metrics)

        print(f"\neps={eps}:")
        print(f"  Clusters: {metrics['n_clusters']} ({metrics['n_non_singleton']} non-singleton)")
        print(f"  Largest: {metrics['largest']}")
        print(f"  Groups merged: {metrics['groups_merged']}/{metrics['groups_total']}")
        print(f"  False-merges: {metrics['false_merges']}")
        print(f"  Multi-source: >=2: {metrics['multi_src_2']}, >=3: {metrics['multi_src_3']}, >=5: {metrics['multi_src_5']}")
        print(f"  Src-histogram: {metrics['src_histogram']}")

    # ── Summary comparison ──────────────────────────────────────────────
    print(f"\n{'='*70}")
    print("SUMMARY TABLE")
    print(f"{'='*70}")
    print(f"{'Config':40s} {'Clust':>6s} {'Largest':>7s} {'Merged':>7s} {'False':>6s} {'>=2src':>6s} {'>=3src':>6s}")
    print("-" * 80)

    for metrics, label in [(w1_results, "W1"), (w2_results, "W2")]:
        for m in metrics:
            cfg = f"{label} BGE+DBSCAN eps={m['eps']}"
            print(f"{cfg:40s} {m['n_clusters']:6d} {m['largest']:7d} {m['groups_merged']:4d}/{m['groups_total']:<2d} {m['false_merges']:6d} {m['multi_src_2']:6d} {m['multi_src_3']:6d}")

    # ── Success criteria check ──────────────────────────────────────────
    print(f"\n{'='*70}")
    print("SUCCESS CRITERIA (must all pass)")
    print(f"{'='*70}")
    criteria = {
        ">=50 multi-source (>=2)": lambda m: m["multi_src_2"] >= 50,
        "Largest < 500": lambda m: m["largest"] < 500,
        ">=5/13 groups merged": lambda m: m["groups_merged"] >= 5,
        "False <= merged": lambda m: m["false_merges"] <= m["groups_merged"],
    }

    for metrics, label in [(w1_results, "W1"), (w2_results, "W2")]:
        for m in metrics:
            cfg = f"{label} eps={m['eps']}"
            results = []
            for name, fn in criteria.items():
                results.append("PASS" if fn(m) else "FAIL")
            print(f"  {cfg:25s}  {', '.join(results)}")


asyncio.run(main())
