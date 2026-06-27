"""Tests for pipeline.runner — run_daily_pipeline."""
import pytest
import tempfile
import os
from datetime import datetime, timezone

from db.connection import init_db, get_db
from db.sources import insert_source
from db.clusters import create_cluster
from db.articles import insert_article
from db.claims import insert_claim, update_claim_state
from db.claim_sources import add_claim_source
from db.snapshots import list_snapshots


@pytest.fixture
def db_path():
    """Temp file DB with sources, clusters, and claims ready for pipeline."""
    path = tempfile.mktemp(suffix=".db")
    init_db(path)

    conn = get_db(path)
    try:
        s1 = insert_source(conn, name="Reuters", domain="reuters.com", tier=1)
        s2 = insert_source(conn, name="BBC", domain="bbc.com", tier=2)

        c1 = create_cluster(conn, vertical="geopolitics", title="Test Cluster")

        a1 = insert_article(conn, source_id=s1, url="http://r.com/1", title="R1")
        a2 = insert_article(conn, source_id=s2, url="http://b.com/1", title="B1")

        t0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
        t1 = datetime(2026, 1, 3, tzinfo=timezone.utc)

        cl1 = insert_claim(conn, article_id=a1, cluster_id=c1, text="Claim 1")
        cl2 = insert_claim(conn, article_id=a2, cluster_id=c1, text="Claim 2")

        add_claim_source(conn, claim_id=cl1, source_id=s1)
        add_claim_source(conn, claim_id=cl1, source_id=s2)
        add_claim_source(conn, claim_id=cl2, source_id=s2)

        conn.execute(
            "UPDATE claim_sources SET first_seen_at = ? WHERE claim_id = ? AND source_id = ?",
            (t0.isoformat(), cl1, s1),
        )
        conn.execute(
            "UPDATE claim_sources SET first_seen_at = ? WHERE claim_id = ? AND source_id = ?",
            (t1.isoformat(), cl1, s2),
        )
        conn.execute(
            "UPDATE claim_sources SET first_seen_at = ? WHERE claim_id = ? AND source_id = ?",
            (t0.isoformat(), cl2, s2),
        )

        update_claim_state(conn, cl1, "CONSENSUS_ABSORBED", absorbed_at=t1.isoformat())
        conn.execute("UPDATE claims SET created_at = ? WHERE id = ?", (t0.isoformat(), cl1))
        conn.execute("UPDATE claims SET created_at = ? WHERE id = ?", (t0.isoformat(), cl2))
        conn.commit()
    finally:
        conn.close()

    yield path
    os.unlink(path)


def test_run_daily_pipeline_processes_all_clusters(db_path):
    """run_daily_pipeline runs agent 3 on all clusters and writes snapshots."""
    from pipeline.runner import run_daily_pipeline

    result = run_daily_pipeline(db_path)

    assert result["clusters_processed"] == 1
    assert "claims_classified" in result
    assert result["snapshots_written"] >= 2


def test_run_daily_pipeline_writes_snapshots(db_path):
    """Snapshots are actually written to the DB."""
    from pipeline.runner import run_daily_pipeline

    run_daily_pipeline(db_path)

    conn = get_db(db_path)
    try:
        snapshots = list_snapshots(conn, vertical="geopolitics")
        assert len(snapshots) >= 2
        assert all(s["date"] is not None for s in snapshots)
    finally:
        conn.close()


def test_run_daily_pipeline_empty_db():
    """Pipeline handles empty database gracefully."""
    path = tempfile.mktemp(suffix=".db")
    init_db(path)
    try:
        from pipeline.runner import run_daily_pipeline

        result = run_daily_pipeline(path)
        assert result["clusters_processed"] == 0
        assert result["snapshots_written"] == 0
    finally:
        os.unlink(path)
