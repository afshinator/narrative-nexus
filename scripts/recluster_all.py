#!/usr/bin/env python3
"""Phase 2 T3: Re-cluster all articles from scratch using nomic embeddings.

1. Embeds (or loads cached) ALL articles with body_status='AVAILABLE' using nomic.
2. Deletes all rows from clusters.
3. Runs time-windowed DBSCAN over all articles, creating fresh clusters.
4. Reassigns claims.cluster_id = the new cluster of the claim's article.
5. Re-runs vertical classification per cluster.
6. Prints: cluster count, sources-per-cluster histogram, articles-per-cluster
   histogram, largest cluster size.

Claims/claim_sources/claim_variants are NOT modified.
"""

import argparse
import asyncio
import json
import os
import sqlite3
import sys
from collections import Counter
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Load .env for API keys
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except ImportError:
    pass

import numpy as np
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import normalize

from pipeline.embedding_client import EmbeddingClient, MODEL_DIMS
from pipeline.vertical_classifier import classify_cluster, classify_text
from pipeline.agent1_intake import _split_oversized, MAX_CLUSTER_SIZE


def load_provider_config(path: str = "config/providers.json") -> dict:
    with open(path) as f:
        cfg = json.load(f)
    default_id = cfg["defaults"]["agent1_embedding"]
    for p in cfg["providers"]["embeddings"]:
        if p["id"] == default_id:
            return p
    raise SystemExit(f"Embedding provider '{default_id}' not found in {path}")


def build_embeddings(
    conn: sqlite3.Connection,
    provider: dict,
    rows: list,
    article_ids: list[int],
    texts: list[str],
) -> dict[int, np.ndarray]:
    """Load cached + embed uncached articles. Returns {article_id: vector}."""
    model = provider["model"]
    expected_dim = MODEL_DIMS.get(model)

    # ── Load cache ──────────────────────────────────────────────────────
    placeholders = ",".join("?" * len(article_ids))
    raw = conn.execute(
        f"SELECT article_id, vector, dim FROM embeddings WHERE model = ? AND article_id IN ({placeholders})",
        [model] + article_ids,
    ).fetchall()

    cached: dict[int, np.ndarray] = {}
    skipped_dim = 0
    for row in raw:
        if expected_dim is not None and row["dim"] != expected_dim:
            skipped_dim += 1
            continue
        cached[row["article_id"]] = np.frombuffer(row["vector"], dtype=np.float64)

    if skipped_dim:
        print(f"  Skipped {skipped_dim} cached vectors with wrong dim (expected {expected_dim})", file=sys.stderr)

    # ── Embed uncached ──────────────────────────────────────────────────
    uncached_pairs = [(i, aid) for i, aid in enumerate(article_ids) if aid not in cached]
    uncached_texts = [texts[i] for i, _ in uncached_pairs]

    if uncached_pairs:
        print(f"  Embedding {len(uncached_pairs)} uncached articles via {provider['name']} ({model})...", file=sys.stderr)
        client = EmbeddingClient(provider)
        loop = asyncio.get_event_loop()

        # Batch to respect 256-row limit
        BATCH = 200
        new_vecs = []
        for start in range(0, len(uncached_texts), BATCH):
            batch = uncached_texts[start:start + BATCH]
            batch_vecs = loop.run_until_complete(client.embed(batch))
            new_vecs.extend(batch_vecs)

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

    # ── Hygiene guard ──────────────────────────────────────────────────
    total_vectors = len(cached)
    cached_nomic = len(cached) - len(uncached_pairs)
    re_embedded = len(uncached_pairs)
    # Verify no non-nomic vectors were loaded
    non_nomic = conn.execute(
        "SELECT COUNT(*) FROM embeddings WHERE model != ? AND article_id IN ({})".format(
            ",".join("?" * len(article_ids))
        ),
        [model] + article_ids,
    ).fetchone()[0]
    print(f"\n  HYGIENE GUARD:", file=sys.stderr)
    print(f"    Cached nomic hits: {cached_nomic}", file=sys.stderr)
    print(f"    Re-embedded (new): {re_embedded}", file=sys.stderr)
    print(f"    Non-nomic vectors in DB for these articles: {non_nomic}", file=sys.stderr)
    print(f"    Total vectors used: {total_vectors}", file=sys.stderr)
    assert non_nomic == 0, f"HYGIENE GUARD FAILED: {non_nomic} non-nomic vectors found"
    print(f"    PASS: zero non-nomic vectors used", file=sys.stderr)

    # Build in article_ids order
    return {aid: cached[aid] for aid in article_ids}


def _insert_cluster(conn: sqlite3.Connection, vertical: str, title: str) -> int:
    """Insert a cluster row and return its id."""
    cur = conn.execute(
        "INSERT INTO clusters (vertical, title) VALUES (?, ?)",
        (vertical, title),
    )
    conn.commit()
    cid = cur.lastrowid
    assert cid is not None, "INSERT INTO clusters returned no lastrowid"
    return cid


def cluster_all(
    conn: sqlite3.Connection,
    provider: dict,
    eps: float = 0.5,
) -> tuple[int, dict[int, int]]:
    """Embed all articles, delete clusters, re-cluster, reassign claims.

    Returns (n_clusters, {article_id: cluster_id}).
    """
    # ── 1. Fetch all articles with body ─────────────────────────────────
    rows = conn.execute("""
        SELECT a.id, a.title, a.body, a.published_at, a.created_at
        FROM articles a
        WHERE a.body_status = 'AVAILABLE'
          AND a.body IS NOT NULL
          AND a.body != ''
        ORDER BY a.id
    """).fetchall()

    if not rows:
        print("No articles with bodies found.", file=sys.stderr)
        return 0, {}

    article_ids = [r["id"] for r in rows]
    texts = [
        f"{r['title'] or ''} {r['body'][:200] if r['body'] else ''}"
        for r in rows
    ]

    # ── 2. Embed all ────────────────────────────────────────────────────
    print(f"\nStep 1: Embedding {len(article_ids)} articles...", file=sys.stderr)
    embeddings_map = build_embeddings(conn, provider, rows, article_ids, texts)
    all_vectors = [embeddings_map[aid] for aid in article_ids]
    matrix = np.array(all_vectors, dtype=np.float64)
    print(f"  Matrix shape: {matrix.shape}", file=sys.stderr)

    # ── 3. Delete clusters ──────────────────────────────────────────────
    print(f"\nStep 2: Deleting all clusters...", file=sys.stderr)
    old_count = conn.execute("SELECT COUNT(*) FROM clusters").fetchone()[0]
    conn.execute("DELETE FROM clusters")
    conn.commit()
    print(f"  Deleted {old_count} clusters.", file=sys.stderr)

    # ── 4. Time-windowed DBSCAN ─────────────────────────────────────────
    print(f"\nStep 3: Time-windowed DBSCAN (eps={eps}, min_samples=2, window=14d)...", file=sys.stderr)

    window_days = 14
    buckets: dict[int, list[int]] = {}

    for i, row in enumerate(rows):
        ts_str = row["published_at"] or row["created_at"]
        try:
            ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            ts = datetime(2020, 1, 1, tzinfo=timezone.utc)
        epoch = datetime(2020, 1, 1, tzinfo=timezone.utc)
        window_key = int((ts - epoch).total_seconds() / (86400 * window_days))
        buckets.setdefault(window_key, []).append(i)

    article_map: dict[int, int] = {}  # article_id -> cluster_id

    for window_key in sorted(buckets):
        indices = buckets[window_key]
        if len(indices) < 2:
            for idx in indices:
                aid = article_ids[idx]
                vertical = classify_text(texts[idx])
                cid = _insert_cluster(conn, vertical, f"Article {aid}")
                article_map[aid] = cid
            continue

        # Extract embeddings for this window
        win_matrix = np.array([all_vectors[i] for i in indices], dtype=np.float64)
        win_norm = normalize(win_matrix)

        clustering = DBSCAN(
            eps=eps, min_samples=2, metric="cosine",
        ).fit(win_norm)
        labels = clustering.labels_

        # ── P4: Recursive blob-split guard ──────────────────────────
        labels = _split_oversized(
            win_norm, labels, indices, texts,
            eps=eps, min_samples=2,
        )

        # Group indices by label
        label_to_indices: dict[int, list[int]] = {}
        for j, label in enumerate(labels):
            label_to_indices.setdefault(int(label), []).append(indices[j])

        for label, idxs in label_to_indices.items():
            if label == -1:
                for idx in idxs:
                    aid = article_ids[idx]
                    vertical = classify_text(texts[idx])
                    cid = _insert_cluster(conn, vertical, f"Article {aid}")
                    article_map[aid] = cid
                continue

            # Classify vertical by majority vote
            cluster_texts = [texts[idx] for idx in idxs]
            vertical = classify_cluster(cluster_texts)
            cid = _insert_cluster(conn, vertical, f"Cluster W{window_key} L{label}")
            for idx in idxs:
                article_map[article_ids[idx]] = cid

    conn.commit()
    print(f"  Created {len(set(article_map.values()))} clusters.", file=sys.stderr)

    # ── 5. Reassign claims.cluster_id ───────────────────────────────────
    print(f"\nStep 4: Reassigning claims.cluster_id...", file=sys.stderr)
    updated = 0
    for aid, cid in article_map.items():
        result = conn.execute(
            "UPDATE claims SET cluster_id = ? WHERE article_id = ?",
            (cid, aid),
        )
        updated += result.rowcount
    conn.commit()
    print(f"  Updated {updated} claims with new cluster_id.", file=sys.stderr)

    # ── 5b. Re-classify cluster verticals ───────────────────────────────
    print(f"\nStep 5: Re-classifying cluster verticals...", file=sys.stderr)
    unique_cids = set(article_map.values())
    vert_updated = 0
    for cid in unique_cids:
        # Collect article texts in this cluster
        c_article_ids = [aid for aid, c in article_map.items() if c == cid]
        c_texts = [texts[article_ids.index(aid)] for aid in c_article_ids if aid in article_ids]
        if c_texts:
            vertical = classify_cluster(c_texts)
        else:
            vertical = "geopolitics"
        conn.execute("UPDATE clusters SET vertical = ? WHERE id = ?", (vertical, cid))
        vert_updated += 1
    conn.commit()
    print(f"  Classified {vert_updated} clusters.", file=sys.stderr)

    return len(unique_cids), article_map


def print_histograms(conn: sqlite3.Connection, article_map: dict[int, int]):
    """Print cluster statistics."""
    cluster_ids = set(article_map.values())

    # Sources per cluster
    sources_per = []
    for cid in cluster_ids:
        count = conn.execute("""
            SELECT COUNT(DISTINCT a.source_id)
            FROM articles a
            WHERE a.id IN (
                SELECT article_id FROM claims WHERE cluster_id = ?
            )
        """, (cid,)).fetchone()[0]
        sources_per.append(count)

    src_hist = Counter(sources_per)

    # Articles per cluster
    art_per = Counter()
    for cid in article_map.values():
        art_per[cid] = art_per.get(cid, 0) + 1

    art_hist = Counter(art_per.values())

    print("\n" + "=" * 60)
    print(f"Cluster count: {len(cluster_ids)}")
    print(f"\nSources per cluster histogram:")
    for k in sorted(src_hist):
        print(f"  {k:3d} source(s): {src_hist[k]:5d} clusters")

    print(f"\nArticles per cluster histogram:")
    for k in sorted(art_hist):
        print(f"  {k:3d} article(s): {art_hist[k]:5d} clusters")

    print(f"\nLargest cluster: {max(art_per.values())} articles")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="Re-cluster all articles from scratch")
    parser.add_argument("--db", default="data/nn.db", help="Database path")
    parser.add_argument("--eps", type=float, default=0.5, help="DBSCAN epsilon (cosine distance)")
    parser.add_argument("--providers", default="config/providers.json", help="Provider config path")
    args = parser.parse_args()

    provider = load_provider_config(args.providers)
    print(f"Embedding provider: {provider['name']} ({provider['model']})", file=sys.stderr)

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    try:
        n_clusters, article_map = cluster_all(conn, provider, eps=args.eps)
        if n_clusters > 0:
            print_histograms(conn, article_map)
        else:
            print("No clusters created.", file=sys.stderr)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
