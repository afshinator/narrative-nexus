"""Intake & Clustering Agent — embeddings + DBSCAN + DB insert.

Reads articles from the database, generates sentence-transformer embeddings
(local CPU, configurable), clusters by cosine-similarity DBSCAN, inserts
clusters into the database, and returns an article→cluster mapping for
downstream agents.

ponytail: DBSCAN with eps=0.30, min_samples=2, metric='cosine'.
ponytail: Vertical classification via embedding proximity to prototypes.
ponytail: Articles with body_status='BODY_UNAVAILABLE' are skipped.
Phase 1 T5a: Embeddings persisted to DB for reuse across runs.
Phase 1 T5b: Time-windowing — articles bucketed into 14-day windows.
Phase 2 P4: Recursive blob-split guard — clusters >60 articles
  re-clustered at eps-0.05 down to floor 0.25.
"""

import sqlite3
from datetime import datetime, timezone, timedelta
from typing import Any

import numpy as np
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import normalize

from pipeline.base_agent import BasePipelineAgent
from pipeline.cleaner import get_embedding_input
from pipeline.embedding_client import EmbeddingClient, MODEL_DIMS
from pipeline.vertical_classifier import classify_cluster, classify_text, get_vertical_list
from db.connection import get_db
from db.clusters import create_cluster

# Phase 2 P4: recursive over-merge guard — maximum articles per cluster
MAX_CLUSTER_SIZE = 60
# Phase 2 P4: floor for recursive eps reduction
EPS_FLOOR = 0.25


class IntakeClusteringAgent(BasePipelineAgent):
    """Generates embeddings, clusters articles by semantic similarity."""

    def __init__(self, *, db_path: str, embedding_provider: dict[str, Any],
                 eps: float = 0.35, min_samples: int = 2):
        self.db_path = db_path
        self._embedding_provider = embedding_provider
        self._eps = eps
        self._min_samples = min_samples

    async def run(self) -> dict[str, Any]:
        """Execute intake + clustering with persisted embeddings and time-windowing."""
        conn = get_db(self.db_path)
        try:
            rows = conn.execute(
                """SELECT a.id, a.title, a.body, a.published_at, a.created_at
                   FROM articles a
                   WHERE a.body_status = 'AVAILABLE'
                     AND a.body IS NOT NULL
                     AND a.body != ''
                     AND a.id NOT IN (
                       SELECT DISTINCT c.article_id
                       FROM claims c
                     )
                   ORDER BY a.id"""
            ).fetchall()
        finally:
            conn.close()

        if not rows:
            return {"clusters": 0, "articles_clustered": 0, "article_map": {}}

        article_ids = [r["id"] for r in rows]
        texts = [
            get_embedding_input(r["title"], r["body"] or "", max_body_chars=1000)
            for r in rows
        ]

        # ── Check embedding cache (dim-filtered) ──────────────────────
        conn = get_db(self.db_path)
        try:
            model = self._embedding_provider["model"]
            expected_dim = MODEL_DIMS.get(model)

            raw_cache = conn.execute(
                "SELECT article_id, vector, dim FROM embeddings WHERE model = ? AND article_id IN ({})".format(
                    ",".join("?" * len(article_ids))
                ),
                [model] + article_ids,
            ).fetchall()

            cached: dict[int, np.ndarray] = {}
            skipped_dim = 0
            for row in raw_cache:
                if expected_dim is not None and row["dim"] != expected_dim:
                    skipped_dim += 1
                    continue
                cached[row["article_id"]] = np.frombuffer(row["vector"], dtype=np.float64)

            if skipped_dim:
                import logging
                logger = logging.getLogger("narrative_nexus.agent1")
                logger.warning(
                    "skipped %d cached embeddings with dim != expected %d for model %s",
                    skipped_dim, expected_dim, model,
                )
        finally:
            conn.close()

        # Determine which articles need new embeddings
        uncached_indices = [i for i, aid in enumerate(article_ids) if aid not in cached]
        need_embedding = [texts[i] for i in uncached_indices]

        # ── Generate embeddings for uncached articles ───────────────────
        if need_embedding:
            embed_client = EmbeddingClient(self._embedding_provider)
            new_embeddings = await embed_client.embed(need_embedding)
            if not new_embeddings or len(new_embeddings) != len(need_embedding):
                return {"clusters": 0, "articles_clustered": 0, "article_map": {}}

            conn = get_db(self.db_path)
            try:
                for j, vec in enumerate(new_embeddings):
                    aid = article_ids[uncached_indices[j]]
                    blob = np.array(vec, dtype=np.float64).tobytes()
                    conn.execute(
                        "INSERT OR REPLACE INTO embeddings (article_id, model, dim, vector) VALUES (?, ?, ?, ?)",
                        (aid, model, len(vec), blob),
                    )
                    cached[aid] = np.array(vec, dtype=np.float64)
                conn.commit()
            finally:
                conn.close()

        # Build full embedding matrix in article_ids order
        all_embeddings = [cached[aid] for aid in article_ids]
        matrix = np.array(all_embeddings, dtype=np.float64)

        # ── Time-windowing — 14-day buckets ─────────────────────────────
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

        # ── Cluster per window ──────────────────────────────────────────
        conn = get_db(self.db_path)
        try:
            article_map: dict[int, int] = {}

            for window_key, indices in sorted(buckets.items()):
                if len(indices) < self._min_samples:
                    for idx in indices:
                        aid = article_ids[idx]
                        vertical = classify_text(texts[idx])
                        cid = create_cluster(conn, vertical=vertical, title=f"Article {aid}")
                        article_map[aid] = cid
                    continue

                window_matrix = np.array([all_embeddings[i] for i in indices], dtype=np.float64)
                window_norm = normalize(window_matrix)

                clustering = DBSCAN(
                    eps=self._eps, min_samples=self._min_samples, metric="cosine",
                ).fit(window_norm)
                labels = clustering.labels_

                # ── P4: Recursive blob-split guard ──────────────────────
                labels = _split_oversized(
                    window_norm, labels, indices, texts,
                    eps=self._eps, min_samples=self._min_samples,
                )

                # Classify verticals for non-noise clusters
                window_label_to_vertical: dict[int, str] = {}
                for label in set(labels):
                    if label == -1:
                        continue
                    cluster_texts = [texts[indices[j]] for j, l in enumerate(labels) if l == label]
                    window_label_to_vertical[label] = classify_cluster(cluster_texts)

                # Create clusters
                window_label_to_cid: dict[int, int] = {}
                for label in set(labels):
                    if label == -1:
                        continue
                    vertical = window_label_to_vertical.get(label, "geopolitics")
                    cid = create_cluster(conn, vertical=vertical, title=f"Cluster W{window_key} L{label}")
                    window_label_to_cid[label] = cid

                # Map articles to clusters
                for j, label in enumerate(labels):
                    aid = article_ids[indices[j]]
                    if label == -1:
                        vertical = classify_text(texts[indices[j]])
                        cid = create_cluster(conn, vertical=vertical, title=f"Article {aid}")
                    else:
                        cid = window_label_to_cid[label]
                    article_map[aid] = cid

            n_clusters = len(set(article_map.values()))
            return {
                "clusters": n_clusters,
                "articles_clustered": len(article_ids),
                "article_map": article_map,
            }
        finally:
            conn.close()


# ── P4: Recursive blob-split guard ────────────────────────────────────────

def _split_oversized(
    matrix: np.ndarray,
    labels: np.ndarray,
    indices: list[int],
    texts: list[str],
    *,
    eps: float,
    min_samples: int,
    depth: int = 0,
) -> np.ndarray:
    """Recursively split clusters larger than MAX_CLUSTER_SIZE.

    For each non-noise cluster with > MAX_CLUSTER_SIZE articles:
      1. Extract the subset embedding matrix.
      2. Re-run DBSCAN at eps - 0.05 (floor EPS_FLOOR).
      3. Replace the original label with sub-labels (negative offset to
         avoid collision with existing labels).
      4. Recurse if any sub-cluster is still oversized.

    Returns modified labels array.
    """
    if depth > 10:
        return labels

    unique_labels = sorted(set(int(l) for l in labels))
    new_labels = labels.copy()
    next_sub_label = -1000 - (depth * 1000)

    for label in unique_labels:
        if label == -1:
            continue
        member_mask = labels == label
        n_members = int(member_mask.sum())

        if n_members <= MAX_CLUSTER_SIZE:
            continue

        member_positions = [j for j, m in enumerate(member_mask) if m]
        subset_matrix = matrix[member_positions]
        subset_norm = normalize(subset_matrix)

        new_eps = max(eps - 0.05, EPS_FLOOR)
        if new_eps >= eps:
            continue

        sub_clustering = DBSCAN(
            eps=new_eps, min_samples=min_samples, metric="cosine",
        ).fit(subset_norm)
        sub_labels = sub_clustering.labels_

        # Recurse
        sub_labels = _split_oversized(
            subset_matrix, sub_labels,
            [indices[j] for j in member_positions],
            [texts[j] for j in member_positions],
            eps=new_eps, min_samples=min_samples, depth=depth + 1,
        )

        for pos, sub_lbl in enumerate(sub_labels):
            global_pos = member_positions[pos]
            if sub_lbl == -1:
                new_labels[global_pos] = -1
            else:
                new_labels[global_pos] = next_sub_label + int(sub_lbl)

        next_sub_label -= 1000

    return new_labels
