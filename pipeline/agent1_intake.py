"""Intake & Clustering Agent — stub.

Ingests article text, generates embeddings, clusters articles by semantic similarity.
Runs on AMD GPU pod (embedding workload)."""

from pipeline.base_agent import BasePipelineAgent


class IntakeClusteringAgent(BasePipelineAgent):
    """Stub — returns empty cluster list until worker/pipeline is wired."""

    async def run(self, article_texts: list[str] | None = None) -> list[dict]:
        """Stub: returns empty cluster list.

        In production:
        1. Generate embeddings via WorkerClient.embed()
        2. Cluster by semantic similarity (BERTopic or DBSCAN)
        3. Insert clusters into the database
        """
        return []
