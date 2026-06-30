"""Intake & Clustering Agent — embeddings + DBSCAN + DB insert.

Reads articles from the database, generates sentence-transformer embeddings
(local CPU, configurable), clusters by cosine-similarity DBSCAN, inserts
clusters into the database, and returns an article→cluster mapping for
downstream agents.

ponytail: DBSCAN with eps=0.5, min_samples=2, metric='cosine'.
ponytail: Vertical classification via embedding proximity to prototypes.
ponytail: Articles with body_status='BODY_UNAVAILABLE' are skipped.
"""

import sqlite3
from typing import Any

import numpy as np
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import normalize

from pipeline.base_agent import BasePipelineAgent
from pipeline.embedding_client import EmbeddingClient
from pipeline.vertical_classifier import classify_cluster, classify_text, get_vertical_list
from db.connection import get_db
from db.clusters import create_cluster


class IntakeClusteringAgent(BasePipelineAgent):
    """Generates embeddings, clusters articles by semantic similarity.

    Wire to embedding_client for provider-agnostic embedding generation.
    Uses DBSCAN for clustering — no hyperparameter tuning needed at
    hackathon scale (~50-100 articles per run).
    """

    def __init__(self, *, db_path: str, embedding_provider: dict[str, Any]):
        """Create the intake agent.

        Args:
          db_path: Path to the SQLite database.
          embedding_provider: Dict with id, name, model, amd fields
                              (from config/providers.json, resolved via
                              provider_config.get_provider_for_agent).
        """
        self.db_path = db_path
        self._embedding_provider = embedding_provider

    async def run(self) -> dict[str, Any]:
        """Execute intake + clustering.

        Steps:
          1. Read articles with body_status='AVAILABLE' and no existing claims
          2. Generate embeddings via EmbeddingClient
          3. Cluster with DBSCAN (cosine distance, normalized vectors)
          4. Insert clusters into the database (geopolitics vertical)
          5. Return {article_id: cluster_id} mapping

        Returns:
          dict with keys: clusters (count), articles_clustered (count),
          article_map (dict[int, int] of article_id → cluster_id).
        """
        # 1. Read articles needing clustering
        conn = get_db(self.db_path)
        try:
            rows = conn.execute(
                """SELECT a.id, a.title, a.body
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
        # ponytail: embed title + first 200 chars of body to save tokens
        texts = [
            f"{r['title'] or ''} {r['body'][:200] if r['body'] else ''}"
            for r in rows
        ]

        # 2. Generate embeddings
        embed_client = EmbeddingClient(self._embedding_provider)
        embeddings = await embed_client.embed(texts)
        if not embeddings or len(embeddings) != len(rows):
            return {"clusters": 0, "articles_clustered": 0, "article_map": {}}

        # 3. Cluster with DBSCAN
        matrix = np.array(embeddings, dtype=np.float64)
        matrix_norm = normalize(matrix)  # unit vectors for cosine distance

        clustering = DBSCAN(
            eps=0.5,
            min_samples=2,
            metric="cosine",
        ).fit(matrix_norm)

        labels = clustering.labels_

        # 4. Classify each cluster's vertical via majority vote.
        # Classify non-noise clusters by their article texts.
        # ponytail: classify before creating DB records so vertical is known.
        label_to_vertical: dict[int, str] = {}
        for label in set(labels):
            if label == -1:
                continue
            cluster_texts = [
                texts[idx] for idx, l in enumerate(labels) if l == label
            ]
            label_to_vertical[label] = classify_cluster(cluster_texts)

        # 5. Insert clusters into DB.
        # Each unique label (except -1 = noise) gets a cluster.
        # Noise articles (-1) get their own singleton clusters classified
        # individually so Agent 2 has a cluster_id to reference.
        conn = get_db(self.db_path)
        try:
            label_to_cluster_id: dict[int, int] = {}
            for label in set(labels):
                if label == -1:
                    continue  # noise handled below
                vertical = label_to_vertical.get(label, "geopolitics")
                cid = create_cluster(conn, vertical=vertical,
                                     title=f"Cluster {label}")
                label_to_cluster_id[label] = cid

            article_map: dict[int, int] = {}
            for idx, label in enumerate(labels):
                aid = article_ids[idx]
                if label == -1:
                    vertical = classify_text(texts[idx])
                    cid = create_cluster(conn, vertical=vertical,
                                         title=f"Article {aid}")
                else:
                    cid = label_to_cluster_id[label]
                article_map[aid] = cid
        finally:
            conn.close()

        n_clusters = len(label_to_cluster_id) + list(labels).count(-1)
        return {
            "clusters": n_clusters,
            "articles_clustered": len(article_ids),
            "article_map": article_map,
        }
