"""P4: Unit tests for recursive blob-split guard in agent1_intake.py."""
import numpy as np
from pipeline.agent1_intake import _split_oversized, MAX_CLUSTER_SIZE, EPS_FLOOR


class TestBlobSplitGuard:
    """Synthetic chained embeddings — neighboring stories slightly related."""

    def _make_chain(self, n_stories: int = 5, articles_per_story: int = 60,
                    noise: float = 0.005) -> tuple[np.ndarray, list[int], list[str]]:
        """Create chained embeddings where adjacent stories overlap slightly.

        Story 0: articles cluster tightly around vec[0]
        Story 1: articles cluster tightly around vec[1], slightly overlapping story 0
        Story 2: articles cluster tightly around vec[2], slightly overlapping story 1
        ...

        At eps=0.35, all stories merge into one mega-cluster. At eps=0.25,
        each story becomes a separate cluster.
        """
        np.random.seed(42)
        # Cosine distance = 1 - cos(angle). Angle step 0.82:
        # MERGE at eps=0.35 (400→1), SPLIT(2) at eps=0.30, then at
        # eps=0.25 each of the 2 splits further → all ≤ MAX_CLUSTER_SIZE.
        dim = 2  # pure 2D
        total = n_stories * articles_per_story
        centroids = np.zeros((n_stories, dim))
        for i in range(n_stories):
            angle = i * 0.82
            centroids[i, 0] = np.cos(angle)
            centroids[i, 1] = np.sin(angle)

        vectors = np.zeros((total, dim))
        indices = list(range(total))
        texts = []

        for i in range(n_stories):
            for j in range(articles_per_story):
                idx = i * articles_per_story + j
                vectors[idx] = centroids[i] + np.random.normal(0, noise, dim)
                texts.append(f"Story {i} article {j}")

        # Normalize
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        norms[norms == 0] = 1
        vectors = vectors / norms

        # At eps=0.35, DBSCAN should merge all stories into one cluster.
        # The split guard at MAX_CLUSTER_SIZE=60 should then recursively
        # re-cluster at eps-0.05 until stories separate.
        return vectors, indices, texts

    def test_synthetic_chain_merges_then_splits(self):
        """Synthetic chain of 5×60=300 articles merges at eps=0.35,
        then split guard at MAX_CLUSTER_SIZE=60 breaks it: every sub-cluster
        is <= 60 articles, and the total is > 1 cluster (splitting happened)."""
        matrix, indices, texts = self._make_chain(n_stories=5, articles_per_story=60)

        # Simulate DBSCAN at eps=0.35 — all merge into label 0
        labels = np.zeros(len(indices), dtype=int)

        # Run split guard
        result = _split_oversized(
            matrix, labels, indices, texts,
            eps=0.35, min_samples=2,
        )

        unique_labels = set(int(l) for l in result if l != -1)
        # Chain was split — more than 1 sub-cluster
        assert len(unique_labels) > 1, f"Expected >1 sub-clusters, got {len(unique_labels)}"

        # Every sub-cluster respects MAX_CLUSTER_SIZE
        for label in unique_labels:
            size = int((result == label).sum())
            assert size <= MAX_CLUSTER_SIZE, f"Cluster {label} has {size} articles, max {MAX_CLUSTER_SIZE}"

    def test_small_cluster_not_split(self):
        """Cluster under MAX_CLUSTER_SIZE is left alone."""
        matrix, indices, texts = self._make_chain(n_stories=1, articles_per_story=40)
        labels = np.zeros(len(indices), dtype=int)

        result = _split_oversized(
            matrix, labels, indices, texts,
            eps=0.35, min_samples=2,
        )

        unique_labels = set(int(l) for l in result if l != -1)
        assert len(unique_labels) == 1, "Small cluster should not be split"

    def test_at_floor_stops_splitting(self):
        """At eps=EPS_FLOOR, oversized clusters are NOT split further."""
        matrix, indices, texts = self._make_chain(n_stories=2, articles_per_story=80)  # >60 to trigger split attempt

        # Simulate DBSCAN at EPS_FLOOR — all merge
        labels = np.zeros(len(indices), dtype=int)

        result = _split_oversized(
            matrix, labels, indices, texts,
            eps=EPS_FLOOR, min_samples=2,
        )

        unique_labels = set(int(l) for l in result if l != -1)
        # At floor, new_eps = max(0.25-0.05, 0.25) = 0.25 = eps — no split
        assert len(unique_labels) == 1, f"At floor, should not split: got {len(unique_labels)}"

    def test_noise_points_preserved(self):
        """Noise points (-1 labels) pass through unchanged."""
        matrix, indices, texts = self._make_chain(n_stories=3, articles_per_story=30)
        labels = np.zeros(len(indices), dtype=int)
        # Mark first 5 as noise
        labels[:5] = -1

        result = _split_oversized(
            matrix, labels, indices, texts,
            eps=0.35, min_samples=2,
        )

        # Noise points should still be -1
        noise_count = int((result == -1).sum())
        assert noise_count == 5, f"Expected 5 noise points, got {noise_count}"
