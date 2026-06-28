"""Tests for pipeline.runner_scheduler — start_pipeline_scheduler."""
import os
import time
import tempfile
from datetime import datetime, timezone

import pytest

from db.connection import get_db, init_db
from db.sources import insert_source
from db.clusters import create_cluster
from db.articles import insert_article
from db.claims import insert_claim, update_claim_state
from db.claim_sources import add_claim_source
from db.snapshots import list_snapshots


@pytest.fixture
def seeded_db_path():
    """Temp file DB with sources, clusters, and claims — pipeline-ready."""
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


def test_pipeline_scheduler_writes_snapshots_on_first_fire(seeded_db_path):
    """Pipeline scheduler fires immediately and writes snapshots to the DB."""
    from pipeline.runner_scheduler import start_pipeline_scheduler

    # No snapshots before scheduler starts
    conn = get_db(seeded_db_path)
    before = list_snapshots(conn, vertical="geopolitics")
    conn.close()
    assert len(before) == 0, "Expected empty snapshot table before scheduler fires"

    scheduler = start_pipeline_scheduler(seeded_db_path)

    # Wait for the immediate fire (next_run_time=now)
    deadline = time.monotonic() + 5.0
    while time.monotonic() < deadline:
        conn = get_db(seeded_db_path)
        after = list_snapshots(conn, vertical="geopolitics")
        conn.close()
        if len(after) >= 2:
            break
        time.sleep(0.2)
    else:
        scheduler.shutdown(wait=False)
        raise AssertionError("Scheduler did not write snapshots within 5 seconds")

    scheduler.shutdown(wait=False)
    assert len(after) >= 2, f"Expected >=2 snapshots, got {len(after)}"
