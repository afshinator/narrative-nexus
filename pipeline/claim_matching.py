"""Claim matching — greedy semantic deduplication across articles in a cluster.

Phase 1: Root Cause 1 fix.  Identifies semantically identical claims reported
by different sources and merges them into canonical claims, preserving each
source's wording in claim_variants.

Algorithm (greedy, deterministic):
 1. Fetch claims in cluster ordered by articles.published_at ASC.
 2. Embed all claim texts in one batched call.
 3. Iterate claims in order.  For each: compute cosine similarity vs all
    current canonicals.  If best sim >= threshold → merge into canonical;
    else → new canonical.
 4. Merge: insert/update claim_sources row for canonical; insert claim_variants
    for the duplicate; delete duplicate from claims + its claim_sources.
 5. Same-source duplicates merge by the same rule — one claim_sources per
    (claim, source), earliest first_seen_at kept.
 6. Idempotent: running twice on same cluster is a no-op.
"""

import logging
import sqlite3
import time
from typing import Any

import numpy as np

from db.claim_sources import add_claim_source

logger = logging.getLogger("narrative_nexus.claim_matching")


# ── Cosine similarity ────────────────────────────────────────────────────

def _cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
    """Cosine similarity between two normalized vectors. Returns float."""
    # ponytail: vectors are already normalized by the embedding model
    return float(np.dot(a, b))


# ── Single-cluster matching ──────────────────────────────────────────────

async def match_claims_in_cluster(
    conn: sqlite3.Connection,
    cluster_id: int,
    embed_client: Any,
    *,
    sim_threshold: float = 0.85,
) -> dict:
    """Run greedy claim matching on a single cluster.

    Idempotent: if all claims in the cluster already have claim_variants rows
    pointing to a canonical, returns immediately with zero merges.

    Returns dict with keys: cluster_id, claims_before, canonicals_after,
    merges, sources_linked.
    """
    # ── Fetch claims for this cluster ───────────────────────────────────
    rows = conn.execute("""
        SELECT c.id, c.text, c.article_id, a.published_at, a.source_id
        FROM claims c
        JOIN articles a ON a.id = c.article_id
        WHERE c.cluster_id = ?
        ORDER BY a.published_at ASC, c.id ASC
    """, (cluster_id,)).fetchall()

    if len(rows) < 2:
        return {
            "cluster_id": cluster_id, "claims_before": len(rows),
            "canonicals_after": len(rows), "merges": 0, "sources_linked": 0,
        }

    # ── Idempotency check ───────────────────────────────────────────────
    # If any claim in this cluster has already been matched (has a
    # claim_variants row), assume this cluster was already processed.
    claim_ids = [r["id"] for r in rows]
    placeholders = ",".join("?" * len(claim_ids))
    already_processed = conn.execute(
        f"SELECT COUNT(*) FROM claim_variants WHERE canonical_claim_id IN ({placeholders})",
        claim_ids,
    ).fetchone()[0]
    if already_processed > 0:
        logger.debug("cluster %d already processed (%d variants found), skipping", cluster_id, already_processed)
        return {
            "cluster_id": cluster_id, "claims_before": len(rows),
            "canonicals_after": len(rows), "merges": 0, "sources_linked": 0,
        }

    # ── Embed all claim texts (batched, Fireworks limit: 256 rows) ──────
    t0 = time.time()
    texts = [r["text"] for r in rows]
    embeddings = []
    BATCH = 256
    for start in range(0, len(texts), BATCH):
        batch = texts[start:start + BATCH]
        batch_embs = await embed_client.embed(batch)
        embeddings.extend(batch_embs)
    vectors = [np.array(v, dtype=np.float64) for v in embeddings]
    logger.debug("cluster %d: embedded %d claims in %.2fs", cluster_id, len(texts), time.time() - t0)

    # ── Greedy matching ─────────────────────────────────────────────────
    # Maintain: canonical_ids list, canonical_vectors list, canonical_sources dict
    canonical_indices: list[int] = []  # indices into `rows`
    canonical_source_timestamps: dict[int, dict[int, str]] = {}  # canonical_idx -> {source_id: first_seen_at}

    merges = 0
    sources_linked = 0

    for i, row in enumerate(rows):
        vec = vectors[i]
        best_sim = 0.0
        best_canonical = -1

        for j, c_idx in enumerate(canonical_indices):
            sim = _cosine_sim(vec, vectors[c_idx])
            if sim > best_sim:
                best_sim = sim
                best_canonical = j

        if best_sim >= sim_threshold and best_canonical >= 0:
            # ── Merge into canonical ────────────────────────────────────
            c_idx = canonical_indices[best_canonical]
            canonical_id = rows[c_idx]["id"]
            source_id = row["source_id"]
            first_seen = row["published_at"] or row["created_at"] if hasattr(row, "created_at") else ""

            logger.debug(
                "merge: claim %d → canonical %d (sim=%.4f) [%s]",
                row["id"], canonical_id, best_sim,
                row["text"][:80],
            )

            # Start transaction for this merge
            try:
                # Add/update claim_sources for canonical (keep earliest timestamp)
                existing_ts = canonical_source_timestamps.get(best_canonical, {}).get(source_id)
                if existing_ts is None:
                    add_claim_source(conn, canonical_id, source_id, first_seen_at=first_seen)
                    sources_linked += 1
                elif first_seen < existing_ts:
                    conn.execute(
                        "UPDATE claim_sources SET first_seen_at = ? WHERE claim_id = ? AND source_id = ?",
                        (first_seen, canonical_id, source_id),
                    )

                # Insert claim_variants for the duplicate
                conn.execute(
                    "INSERT INTO claim_variants (canonical_claim_id, source_id, article_id, text, first_seen_at) VALUES (?, ?, ?, ?, ?)",
                    (canonical_id, source_id, row["article_id"], row["text"], first_seen),
                )

                # Delete duplicate claim and its claim_sources
                conn.execute("DELETE FROM claim_sources WHERE claim_id = ?", (row["id"],))
                conn.execute("DELETE FROM claims WHERE id = ?", (row["id"],))

                conn.commit()
                merges += 1
            except Exception:
                conn.rollback()
                raise
        else:
            # ── Become a new canonical ───────────────────────────────────
            canonical_indices.append(i)
            canonical_source_timestamps[len(canonical_indices) - 1] = {
                row["source_id"]: row["published_at"] or "",
            }

            if best_sim > 0:
                logger.debug(
                    "near-miss: claim %d vs best sim=%.4f (threshold=%.2f) [%s]",
                    row["id"], best_sim, sim_threshold, row["text"][:80],
                )

    return {
        "cluster_id": cluster_id,
        "claims_before": len(rows),
        "canonicals_after": len(rows) - merges,
        "merges": merges,
        "sources_linked": sources_linked,
    }


# ── All-cluster matching ─────────────────────────────────────────────────

async def match_all_clusters(
    conn: sqlite3.Connection,
    embed_client: Any,
    *,
    sim_threshold: float = 0.85,
) -> dict:
    """Run claim matching on all populated clusters.

    Resumable: skips clusters where any claim already has a claim_variants row
    (inferring prior processing).  Returns summary dict.
    """
    clusters = conn.execute("""
        SELECT DISTINCT c.id
        FROM clusters c
        JOIN claims cl ON cl.cluster_id = c.id
        GROUP BY c.id
        HAVING COUNT(cl.id) >= 2
        ORDER BY c.id
    """).fetchall()

    total_merges = 0
    total_sources_linked = 0
    clusters_processed = 0
    t_start = time.time()

    for i, row in enumerate(clusters):
        cid = row["id"]
        try:
            result = await match_claims_in_cluster(
                conn, cid, embed_client, sim_threshold=sim_threshold,
            )
            if result["merges"] > 0:
                total_merges += result["merges"]
                total_sources_linked += result["sources_linked"]
                clusters_processed += 1
                logger.info(
                    "cluster %d: %d claims → %d canonicals (%d merges, %d sources linked)",
                    cid, result["claims_before"], result["canonicals_after"],
                    result["merges"], result["sources_linked"],
                )
        except Exception:
            logger.exception("cluster %d failed, rolling back", cid)
            conn.rollback()

        if (i + 1) % 100 == 0:
            elapsed = time.time() - t_start
            logger.info(
                "progress: %d/%d clusters, %d merges, %.1f clusters/s",
                i + 1, len(clusters), total_merges,
                (i + 1) / elapsed if elapsed > 0 else 0,
            )

    elapsed = time.time() - t_start
    return {
        "clusters_with_claims": len(clusters),
        "clusters_processed": clusters_processed,
        "total_merges": total_merges,
        "total_sources_linked": total_sources_linked,
        "elapsed_seconds": round(elapsed, 1),
    }
