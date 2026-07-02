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
from db.silent_edits import insert_silent_edit


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

    # Silent edits: a1 (s1) has 1 edit, a2 (s1) has 0, a3 (s2) has 0, a4 (s3) has 0
    insert_silent_edit(conn, article_id=a1, change_ratio=0.5,
                       stored_body_length=1000, fetched_body_length=1500)

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


def test_redit_raw_counts_edits_per_source(db):
    """R_edit raw = edit_count / article_count per source.
    s1: 1 edit / 2 articles = 0.5
    s2: 0 edits / 1 article = 0.0
    s3: 0 edits / 1 article = 0.0
    """
    from pipeline.snapshots import compute_r_edit_raw

    result = compute_r_edit_raw(db)

    assert result[1] == pytest.approx(0.5)
    assert result[2] == pytest.approx(0.0)
    assert result[3] == pytest.approx(0.0)


def test_write_daily_snapshots(db):
    """write_daily_snapshots inserts one row per source per vertical."""
    from pipeline.snapshots import write_daily_snapshots

    r_orig = {1: 50.0, 2: 30.0, 3: 10.0}
    r_val = {1: 60.0, 2: 40.0, 3: 20.0}
    r_speed = {1: 25.0, 2: None, 3: None}
    archetypes = {1: "EARLY_BREAKER", 2: "CONSENSUS_FOLLOWER", 3: "CONSENSUS_FOLLOWER"}
    r_edit = {1: 50.0, 2: 20.0, 3: None}

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
        r_edit=r_edit,
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
    assert rows[0]["r_edit"] == 50.0
    assert rows[0]["r_correct"] is None

    assert rows[1]["source_id"] == 2
    assert rows[1]["r_edit"] == 20.0

    assert rows[2]["source_id"] == 3
    assert rows[2]["r_speed"] is None
    assert rows[2]["r_edit"] is None


def test_redit_raw_zero_articles_source():
    """Source with zero articles gets None edit rate."""
    from pipeline.snapshots import compute_r_edit_raw
    from db.sources import insert_source
    from db.connection import get_db, load_schema

    conn = get_db()
    load_schema(conn)
    try:
        s1 = insert_source(conn, name="Has Articles", domain="has.com", tier=1)
        s2 = insert_source(conn, name="No Articles", domain="no.com", tier=2)
        # Give s1 one article and one edit, s2 gets nothing
        from db.articles import insert_article
        a1 = insert_article(conn, source_id=s1, url="http://has.com/1", title="A1")
        from db.silent_edits import insert_silent_edit
        insert_silent_edit(conn, article_id=a1, change_ratio=0.3,
                           stored_body_length=100, fetched_body_length=130)

        result = compute_r_edit_raw(conn)

        assert result[s1] == pytest.approx(1.0)  # 1 edit / 1 article
        assert result[s2] is None  # 0 articles → None
    finally:
        conn.close()


def test_redit_raw_as_of_filter():
    """as_of filters silent_edits by detected_at."""
    from pipeline.snapshots import compute_r_edit_raw
    from db.sources import insert_source
    from db.connection import get_db, load_schema
    from db.articles import insert_article
    from db.silent_edits import insert_silent_edit

    conn = get_db()
    load_schema(conn)
    try:
        s1 = insert_source(conn, name="TestSrc", domain="test.com", tier=1)
        a1 = insert_article(conn, source_id=s1, url="http://test.com/1", title="A1")
        a2 = insert_article(conn, source_id=s1, url="http://test.com/2", title="A2")

        # Two edits: one old, one recent
        e1 = insert_silent_edit(conn, article_id=a1, change_ratio=0.1,
                                stored_body_length=100, fetched_body_length=110)
        e2 = insert_silent_edit(conn, article_id=a2, change_ratio=0.2,
                                stored_body_length=200, fetched_body_length=240)

        conn.execute(
            "UPDATE silent_edits SET detected_at = ? WHERE id = ?",
            ("2026-01-15 12:00:00", e1),
        )
        conn.execute(
            "UPDATE silent_edits SET detected_at = ? WHERE id = ?",
            ("2026-06-15 12:00:00", e2),
        )
        conn.commit()

        # as_of mid-point: only the January edit should count
        result = compute_r_edit_raw(conn, as_of="2026-03-01T00:00:00")
        # 1 edit / 2 articles = 0.5
        assert result[s1] == pytest.approx(0.5)

        # as_of after both edits: both count
        result2 = compute_r_edit_raw(conn, as_of="2026-07-01T00:00:00")
        # 2 edits / 2 articles = 1.0
        assert result2[s1] == pytest.approx(1.0)

        # as_of before both edits: none count
        result3 = compute_r_edit_raw(conn, as_of="2025-12-01T00:00:00")
        # 0 edits / 2 articles = 0.0
        assert result3[s1] == pytest.approx(0.0)
    finally:
        conn.close()


def test_redit_end_to_end(db):
    """Full pipeline: raw → percentile → write → query yields correct r_edit values."""
    from pipeline.snapshots import (
        compute_r_edit_raw,
        percentile_rank,
        write_daily_snapshots,
    )

    # Compute raw edit rates from fixture
    r_edit_raw = compute_r_edit_raw(db)
    # s1: 1 edit / 2 articles = 0.5
    # s2: 0 edits / 1 article = 0.0
    # s3: 0 edits / 1 article = 0.0
    assert r_edit_raw[1] == pytest.approx(0.5)
    assert r_edit_raw[2] == pytest.approx(0.0)
    assert r_edit_raw[3] == pytest.approx(0.0)

    # Percentile rank (lower edit rate = better, so 0.0 ranks 0, 0.5 ranks 100)
    r_edit = percentile_rank(
        {k: v for k, v in r_edit_raw.items() if v is not None}
    )
    assert r_edit[1] == pytest.approx(100.0)  # highest = worst (most edits)
    assert r_edit[2] == pytest.approx(0.0)    # tied lowest = best
    assert r_edit[3] == pytest.approx(0.0)    # tied lowest = best

    # Write to snapshots and verify stored values
    date_str = "2026-06-30"
    write_daily_snapshots(
        db,
        date_str=date_str,
        vertical="geopolitics",
        r_orig={1: 50.0, 2: 30.0, 3: 10.0},
        r_val={1: 60.0, 2: 40.0, 3: 20.0},
        r_speed={1: 25.0, 2: None, 3: None},
        archetypes={1: "EARLY_BREAKER", 2: "CONSENSUS_FOLLOWER", 3: "CONSENSUS_FOLLOWER"},
        r_edit=r_edit,
    )

    rows = db.execute(
        "SELECT source_id, r_edit FROM snapshots WHERE vertical = ? AND date = ? ORDER BY source_id",
        ("geopolitics", date_str),
    ).fetchall()

    assert len(rows) == 3
    assert rows[0]["r_edit"] == pytest.approx(100.0)  # s1: 0.5 → 100th percentile
    assert rows[1]["r_edit"] == pytest.approx(0.0)    # s2: 0.0 → 0th percentile
    assert rows[2]["r_edit"] == pytest.approx(0.0)    # s3: 0.0 → 0th percentile


def test_r_frame_raw_stddev(db):
    """Stddev of LLM scores per source. s1: [2,8] → 3.0, s3: 1 article → None."""
    from pipeline.snapshots import compute_r_frame_raw

    # Add framing scores: s1 articles get 2 and 8, s3 gets single score
    db.execute(
        "INSERT INTO article_framing (article_id, llm_score) VALUES (?, ?)",
        (1, 2.0),
    )
    db.execute(
        "INSERT INTO article_framing (article_id, llm_score) VALUES (?, ?)",
        (2, 8.0),
    )
    db.execute(
        "INSERT INTO article_framing (article_id, llm_score) VALUES (?, ?)",
        (4, 5.0),  # s3: only 1 article → not enough for stddev
    )
    db.commit()

    result = compute_r_frame_raw(db)

    # s1: scores [2, 8] → mean=5, variance=(9+9)/2=9, stddev=3.0
    assert result[1] == pytest.approx(3.0)
    # s2: no framing scores → None
    assert result[2] is None
    # s3: 1 article → None (< 2 minimum)
    assert result[3] is None


def test_r_frame_raw_as_of_filter(db):
    """as_of filters by articles.published_at."""
    from pipeline.snapshots import compute_r_frame_raw

    # Add framing for all articles
    for aid in (1, 2, 3, 4):
        db.execute(
            "INSERT OR IGNORE INTO article_framing (article_id, llm_score) VALUES (?, 3.0)",
            (aid,),
        )
    # Set different published_at dates
    db.execute(
        "UPDATE articles SET published_at = ? WHERE id = ?",
        ("2025-01-01T00:00:00", 1),
    )
    db.execute(
        "UPDATE articles SET published_at = ? WHERE id = ?",
        ("2026-01-01T00:00:00", 2),
    )
    db.commit()

    # as_of mid-2025: only article 1 counts (s1: 1 article → None since <2)
    result = compute_r_frame_raw(db, as_of="2025-06-01T00:00:00")
    assert result[1] is None  # only 1 article before cutoff

    # as_of after both: both articles count (s1: 2 articles → stddev)
    result2 = compute_r_frame_raw(db, as_of="2026-06-01T00:00:00")
    assert result2[1] == pytest.approx(0.0)  # both score 3.0 → stddev=0


def test_r_frame_end_to_end(db):
    """Full pipeline: raw → percentile → write → query yields correct r_frame."""
    from pipeline.snapshots import (
        compute_r_frame_raw,
        percentile_rank,
        write_daily_snapshots,
    )

    # Add framing scores so all 3 sources get stddev values
    # s1: [1, 5] → stddev=2.0, s2: [10] → None (<2), s3: [3, 3] → stddev=0.0
    db.execute("INSERT INTO article_framing (article_id, llm_score) VALUES (1, 1.0)")
    db.execute("INSERT INTO article_framing (article_id, llm_score) VALUES (2, 5.0)")
    db.execute("INSERT INTO article_framing (article_id, llm_score) VALUES (3, 10.0)")  # s2 single
    db.execute("INSERT INTO article_framing (article_id, llm_score) VALUES (4, 3.0)")   # s3 single
    # Add second article for s3 so it gets a stddev
    from db.articles import insert_article
    a5 = insert_article(db, source_id=3, url="http://f.com/2", title="F2")
    db.execute("INSERT INTO article_framing (article_id, llm_score) VALUES (?, 3.0)", (a5,))
    db.commit()

    # Compute raw stddev
    r_frame_raw = compute_r_frame_raw(db)
    assert r_frame_raw[1] == pytest.approx(2.0)  # s1: [1,5] → stddev=2.0
    assert r_frame_raw[2] is None                 # s2: 1 article
    assert r_frame_raw[3] == pytest.approx(0.0)   # s3: [3,3] → stddev=0.0

    # Percentile rank (higher stddev = higher percentile = worse)
    r_frame = percentile_rank(
        {k: v for k, v in r_frame_raw.items() if v is not None}
    )
    assert r_frame[1] == pytest.approx(100.0)  # s1: highest stddev
    assert r_frame[3] == pytest.approx(0.0)    # s3: lowest stddev
    # s2 not in r_frame (excluded by None filter)

    # Write to snapshots and verify stored values
    date_str = "2026-07-01"
    write_daily_snapshots(
        db, date_str=date_str, vertical="geopolitics",
        r_orig={1: 50.0, 2: 30.0, 3: 10.0},
        r_val={1: 60.0, 2: 40.0, 3: 20.0},
        r_speed={1: 25.0, 2: None, 3: None},
        archetypes={1: "EARLY_BREAKER", 2: "CONSENSUS_FOLLOWER", 3: "CONSENSUS_FOLLOWER"},
        r_frame=r_frame,
    )

    rows = db.execute(
        "SELECT source_id, r_frame FROM snapshots WHERE vertical=? AND date=? ORDER BY source_id",
        ("geopolitics", date_str),
    ).fetchall()

    assert len(rows) == 3
    assert rows[0]["r_frame"] == pytest.approx(100.0)  # s1: high stddev
    assert rows[1]["r_frame"] is None                   # s2: no data
    assert rows[2]["r_frame"] == pytest.approx(0.0)     # s3: low stddev
