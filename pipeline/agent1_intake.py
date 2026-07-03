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


class IntakeClusteringAgent(BasePipelineAgent):
    """Generates embeddings, clusters articles by semantic similarity."""

    def __init__(self, *, db_path: str, embedding_provider: dict[str, Any]):
        self.db_path = db_path
        self._embedding_provider = embedding_provider

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
        # Phase 2 Y2: use cleaner + 1000-char body window (was 200 chars, un-cleaned)
        texts = [
            get_embedding_input(r["title"], r["body"] or "", max_body_chars=1000)
            for r in rows
        ]

        # ── T5a: Check embedding cache (Phase 2 T2: dim-filtered) ──────
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
                    # Phase 2 T2c: cached vector has wrong dimension — skip
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

            # T5a: persist new embeddings
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

        # ── T5b: Time-windowing — 14-day buckets ─────────────────────────
        window_days = 14
        buckets: dict[int, list[int]] = {}  # window_key -> [indices]

        for i, row in enumerate(rows):
            ts_str = row["published_at"] or row["created_at"]
            try:
                ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
            except (ValueError, TypeError):
                ts = datetime(2020, 1, 1, tzinfo=timezone.utc)
            # Floor to 14-day window
            epoch = datetime(2020, 1, 1, tzinfo=timezone.utc)
            window_key = int((ts - epoch).total_seconds() / (86400 * window_days))
            buckets.setdefault(window_key, []).append(i)

        # ── Cluster per window ──────────────────────────────────────────
        conn = get_db(self.db_path)
        try:
            label_to_cluster_id: dict[int, int] = {}
            article_map: dict[int, int] = {}

            for window_key, indices in sorted(buckets.items()):
                if len(indices) < 2:
                    # Single-article windows → each gets a singleton cluster
                    for idx in indices:
                        aid = article_ids[idx]
                        vertical = classify_text(texts[idx])
                        cid = create_cluster(conn, vertical=vertical, title=f"Article {aid}")
                        article_map[aid] = cid
                    continue

                # Extract embeddings for this window
                window_matrix = np.array([all_embeddings[i] for i in indices], dtype=np.float64)
                window_norm = normalize(window_matrix)

                clustering = DBSCAN(
                    eps=0.30, min_samples=2, metric="cosine",
                ).fit(window_norm)
                labels = clustering.labels_

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
