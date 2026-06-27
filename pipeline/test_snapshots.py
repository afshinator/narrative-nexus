"""Tests for pipeline.snapshots — reputation dimension computation."""
import pytest
import sqlite3
from datetime import datetime, timezone

from db.connection import get_db, load_schema
from db.sources import insert_source
from db.clusters import create_cluster
from db.articles import insert_article
from db.claims import insert_claim, update_claim_state
from db.claim_sources import add_claim_source


@pytest.fixture
def db():
    """In-memory DB with schema and test data: 3 sources, 2 clusters, multiple claims."""
    conn = get_db()
    load_schema(conn)

    # 3 sources: tier 1, 2, 3
    s1 = insert_source(conn, name="Reuters", domain="reuters.com", tier=1)
    s2 = insert_source(conn, name="BBC", domain="bbc.com", tier=2)
    s3 = insert_source(conn, name="Fox", domain="foxnews.com", tier=3)

    # 2 clusters in geopolitics vertical
    c1 = create_cluster(conn, vertical="geopolitics", title="Cluster A")
    c2 = create_cluster(conn, vertical="geopolitics", title="Cluster B")

    # Articles
    a1 = insert_article(conn, source_id=s1, url="http://r.com/1", title="R1")
    a2 = insert_article(conn, source_id=s1, url="http://r.com/2", title="R2")
    a3 = insert_article(conn, source_id=s2, url="http://b.com/1", title="B1")
    a4 = insert_article(conn, source_id=s3, url="http://f.com/1", title="F1")

    # Claims in cluster 1:
    # - claim1: originated by s1, also reported by s2, ABSORBED
    # - claim2: originated by s1, not absorbed (PENDING)
    # - claim3: originated by s2, ABSORBED
    cl1 = insert_claim(conn, article_id=a1, cluster_id=c1, text="Claim 1")
    cl2 = insert_claim(conn, article_id=a2, cluster_id=c1, text="Claim 2")
    cl3 = insert_claim(conn, article_id=a3, cluster_id=c1, text="Claim 3")

    # s1 originated claim1 first, s2 reported it later
    t0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
    t1 = datetime(2026, 1, 2, tzinfo=timezone.utc)
    add_claim_source(conn, claim_id=cl1, source_id=s1)
    add_claim_source(conn, claim_id=cl1, source_id=s2)
    # Override first_seen_at to establish ordering
    conn.execute(
        "UPDATE claim_sources SET first_seen_at = ? WHERE claim_id = ? AND source_id = ?",
        (t0.isoformat(), cl1, s1),
    )
    conn.execute(
        "UPDATE claim_sources SET first_seen_at = ? WHERE claim_id = ? AND source_id = ?",
        (t1.isoformat(), cl1, s2),
    )

    # claim2: only s1, PENDING
    add_claim_source(conn, claim_id=cl2, source_id=s1)
    conn.execute(
        "UPDATE claim_sources SET first_seen_at = ? WHERE claim_id = ? AND source_id = ?",
        (t0.isoformat(), cl2, s1),
    )

    # claim3: originated by s2, ABSORBED
    add_claim_source(conn, claim_id=cl3, source_id=s2)
    conn.execute(
        "UPDATE claim_sources SET first_seen_at = ? WHERE claim_id = ? AND source_id = ?",
        (t0.isoformat(), cl3, s2),
    )

    # Absorb claim1 and claim3
    update_claim_state(conn, cl1, "CONSENSUS_ABSORBED", absorbed_at=t1.isoformat())
    update_claim_state(conn, cl3, "CONSENSUS_ABSORBED", absorbed_at=t0.isoformat())

    # Override created_at to past dates so julianday subtraction works
    # (insert_claim uses datetime('now') as default)
    conn.execute("UPDATE claims SET created_at = ? WHERE id = ?", (t0.isoformat(), cl1))
    conn.execute("UPDATE claims SET created_at = ? WHERE id = ?", (t0.isoformat(), cl2))
    conn.execute("UPDATE claims SET created_at = ? WHERE id = ?", (t0.isoformat(), cl3))

    conn.commit()

    yield conn
    conn.close()


def test_r_orig_counts_originations(db):
    """R_orig raw count = number of claims where this source was first reporter."""
    from pipeline.snapshots import compute_r_orig_raw

    result = compute_r_orig_raw(db)

    # s1 originated claim1 and claim2 = 2
    assert result[1] == 2  # Reuters
    # s2 originated claim3 = 1
    assert result[2] == 1  # BBC
    # s3 originated 0
    assert 3 not in result or result[3] == 0


def test_r_val_ratio_absorbed_to_originated(db):
    """R_val = absorbed / originated ratio (0-1, later percentile-ranked to 0-100)."""
    from pipeline.snapshots import compute_r_val_raw

    result = compute_r_val_raw(db)

    # s1: 2 originated, 1 absorbed → 0.5
    assert result[1] == pytest.approx(0.5)
    # s2: 1 originated, 1 absorbed → 1.0
    assert result[2] == pytest.approx(1.0)
    # s3: 0 originated → NULL (no division)
    assert result.get(3) is None


def test_r_speed_median_days(db):
    """R_speed = median days between origination and absorption for absorbed claims."""
    from pipeline.snapshots import compute_r_speed_raw

    result = compute_r_speed_raw(db)

    # s1: claim1 absorbed 1 day after origination → median = 1.0
    assert result[1] == pytest.approx(1.0, abs=0.1)
    # s2: claim3 absorbed same day → 0
    assert result[2] == pytest.approx(0.0, abs=0.1)
    # s3: no absorbed claims → None
    assert result.get(3) is None


def test_percentile_rank(db):
    """Percentile rank converts raw values to 0-100 scale."""
    from pipeline.snapshots import percentile_rank

    # 3 sources: values 0.5, 1.0, 0.0
    raw = {1: 0.5, 2: 1.0, 3: 0.0}
    result = percentile_rank(raw)

    assert result[2] == pytest.approx(100.0)  # highest
    assert result[1] == pytest.approx(50.0)  # middle
    assert result[3] == pytest.approx(0.0)  # lowest


def test_percentile_rank_single_source(db):
    """Single source gets 100 (it's the entire panel)."""
    from pipeline.snapshots import percentile_rank

    result = percentile_rank({1: 0.5})
    assert result[1] == 100.0


def test_percentile_rank_empty(db):
    """Empty input returns empty dict."""
    from pipeline.snapshots import percentile_rank

    result = percentile_rank({})
    assert result == {}


def test_archetype_assignment(db):
    """Archetype from R_orig and R_val vs panel median."""
    from pipeline.archetype import get_archetype

    median_orig = 50
    median_val = 50

    assert get_archetype(80, 80, median_orig, median_val) == "EARLY_BREAKER"
    assert get_archetype(80, 30, median_orig, median_val) == "NOISE_GENERATOR"
    assert get_archetype(30, 80, median_orig, median_val) == "SELECTIVE_ACCURATE"
    assert get_archetype(30, 30, median_orig, median_val) == "CONSENSUS_FOLLOWER"


def test_write_daily_snapshots(db):
    """write_daily_snapshots inserts one row per source per vertical."""
    from pipeline.snapshots import write_daily_snapshots

    r_orig = {1: 50.0, 2: 30.0, 3: 10.0}
    r_val = {1: 60.0, 2: 40.0, 3: 20.0}
    r_speed = {1: 25.0, 2: None, 3: None}
    archetypes = {1: "EARLY_BREAKER", 2: "CONSENSUS_FOLLOWER", 3: "CONSENSUS_FOLLOWER"}

    date_str = "2026-06-26"
    write_daily_snapshots(
        db,
        date_str=date_str,
        vertical="geopolitics",
        r_orig=r_orig,
        r_val=r_val,
        r_speed=r_speed,
        archetypes=archetypes,
        r_frame={},
        r_edit={},
        r_correct={},
    )

    rows = db.execute(
        "SELECT * FROM snapshots WHERE vertical = ? AND date = ? ORDER BY source_id",
        ("geopolitics", date_str),
    ).fetchall()

    assert len(rows) == 3
    assert rows[0]["source_id"] == 1
    assert rows[0]["r_orig"] == 50.0
    assert rows[0]["r_val"] == 60.0
    assert rows[0]["r_speed"] == 25.0
    assert rows[0]["archetype"] == "EARLY_BREAKER"
    assert rows[0]["r_frame"] is None
    assert rows[0]["r_edit"] is None
    assert rows[0]["r_correct"] is None

    assert rows[1]["source_id"] == 2
    assert rows[1]["r_speed"] is None  # NULL when no absorbed claims
    assert rows[2]["source_id"] == 3
