"""Tests for FastAPI application — route responses."""

import os
import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture(autouse=True)
def _disable_pipeline():
    """Prevent the pipeline scheduler from firing during route tests.

    Without this, the TestClient triggers the app lifespan which starts
    a BackgroundScheduler that writes snapshots to the default DB path.
    Override per-test by setting os.environ["NN_NO_PIPELINE"] = "0".
    """
    os.environ["NN_NO_PIPELINE"] = "1"
    yield
    del os.environ["NN_NO_PIPELINE"]


@pytest.fixture
def client():
    """FastAPI test client with lifespan (scheduler attached to app.state)."""
    with TestClient(app) as c:
        yield c


class TestHealth:
    def test_returns_ok(self, client):
        resp = client.get("/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["version"] == "0.1.0"


class TestSourcesRoute:
    def test_returns_sources(self, client):
        # Sources table is empty by default (in-memory per request)
        resp = client.get("/api/sources")
        assert resp.status_code == 200
        data = resp.json()
        assert "sources" in data

    def test_active_only_filter(self, client):
        resp = client.get("/api/sources?active_only=true")
        assert resp.status_code == 200

    def test_source_by_id_returns_null_when_empty(self, client):
        resp = client.get("/api/sources/1")
        assert resp.status_code == 200
        data = resp.json()
        assert "source" in data
        assert data["source"] is None


class TestArticlesRoute:
    def test_returns_empty(self, client):
        resp = client.get("/api/articles")
        assert resp.status_code == 200
        data = resp.json()
        assert "articles" in data

    def test_supports_pagination(self, client):
        resp = client.get("/api/articles?limit=10&offset=0")
        assert resp.status_code == 200


class TestClustersRoute:
    def test_returns_empty(self, client):
        resp = client.get("/api/clusters")
        assert resp.status_code == 200
        data = resp.json()
        assert "clusters" in data

    def test_filters_by_vertical(self, client):
        resp = client.get("/api/clusters?vertical=GEOPOLITICS")
        assert resp.status_code == 200


class TestClaimsRoute:
    def test_returns_empty(self, client):
        resp = client.get("/api/claims")
        assert resp.status_code == 200
        data = resp.json()
        assert "claims" in data

    def test_filters_by_cluster_and_state(self, client):
        resp = client.get("/api/claims?cluster_id=1&state=PENDING")
        assert resp.status_code == 200


class TestSnapshotsRoute:
    def test_returns_empty(self, client):
        resp = client.get("/api/snapshots")
        assert resp.status_code == 200
        data = resp.json()
        assert "snapshots" in data

    def test_filters(self, client):
        resp = client.get("/api/snapshots?source_id=1&vertical=GEOPOLITICS")
        assert resp.status_code == 200


class TestRouteErrors:
    def test_not_found_returns_404(self, client):
        resp = client.get("/api/nonexistent")
        assert resp.status_code == 404


class TestScraperRoutes:
    def test_status_returns_paused_by_default(self, client):
        resp = client.get("/api/scraper/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["running"] is False

    def test_start_stop(self, client):
        resp = client.post("/api/scraper/start")
        assert resp.status_code == 200
        assert client.get("/api/scraper/status").json()["running"] is True
        resp = client.post("/api/scraper/stop")
        assert resp.status_code == 200
        assert client.get("/api/scraper/status").json()["running"] is False


class TestSourceProfileRoute:
    def test_returns_404_for_missing_source(self, client):
        resp = client.get("/api/sources/9999/profile")
        assert resp.status_code == 404

    def test_returns_profile_with_snapshots(self, tmp_path):
        """Seed a DB with snapshots, test the profile endpoint."""
        import sqlite3
        from db.connection import init_db
        from db.sources import insert_source
        from db.snapshots import insert_snapshot

        db_path = str(tmp_path / "profile_test.db")
        init_db(db_path)
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        src_id = insert_source(conn, "TestSource", "test.com", 1)
        insert_snapshot(conn, src_id, "geopolitics", "2026-01-01", r_orig=50, r_val=60)
        insert_snapshot(conn, src_id, "geopolitics", "2026-01-02", r_orig=55, r_val=65)
        conn.close()

        os.environ["NN_DB_PATH"] = db_path
        try:
            with TestClient(app) as c:
                resp = c.get(f"/api/sources/{src_id}/profile?vertical=geopolitics")
                assert resp.status_code == 200
                data = resp.json()
                assert "snapshots" in data
                assert len(data["snapshots"]) == 2
                assert data["snapshots"][0]["day"] == 0
                assert data["snapshots"][0]["R_val"] == 60
                assert data["snapshots"][1]["day"] == 1
                assert data["snapshots"][1]["R_val"] == 65
                assert "tierAvg" in data
                assert "panelMedian" in data
        finally:
            os.environ.pop("NN_DB_PATH", None)

    def test_profile_respects_vertical_filter(self, tmp_path):
        """Only snapshots for the requested vertical are returned."""
        import sqlite3
        from db.connection import init_db
        from db.sources import insert_source
        from db.snapshots import insert_snapshot

        db_path = str(tmp_path / "profile_vf.db")
        init_db(db_path)
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        src_id = insert_source(conn, "TS", "ts.com", 1)
        insert_snapshot(conn, src_id, "geopolitics", "2026-01-01", r_val=10)
        insert_snapshot(conn, src_id, "economics", "2026-01-01", r_val=90)
        conn.close()

        os.environ["NN_DB_PATH"] = db_path
        try:
            with TestClient(app) as c:
                resp = c.get(f"/api/sources/{src_id}/profile?vertical=economics")
                assert resp.status_code == 200
                data = resp.json()
                assert len(data["snapshots"]) == 1
                assert data["snapshots"][0]["R_val"] == 90
        finally:
            os.environ.pop("NN_DB_PATH", None)

    def test_profile_empty_snapshots_returns_empty_array(self, tmp_path):
        """Source with no snapshots returns empty array, not error."""
        import sqlite3
        from db.connection import init_db
        from db.sources import insert_source

        db_path = str(tmp_path / "profile_empty.db")
        init_db(db_path)
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        src_id = insert_source(conn, "Empty", "empty.com", 2)
        conn.close()

        os.environ["NN_DB_PATH"] = db_path
        try:
            with TestClient(app) as c:
                resp = c.get(f"/api/sources/{src_id}/profile?vertical=geopolitics")
                assert resp.status_code == 200
                data = resp.json()
                assert data["snapshots"] == []
                assert data["tierAvg"] is None  # no tier data for this source
                assert data["panelMedian"] is not None
        finally:
            os.environ.pop("NN_DB_PATH", None)

    def test_returns_events_edits_and_claim_summary(self, tmp_path):
        """Profile endpoint includes events, edits, and claimSummary fields."""
        import sqlite3
        from db.connection import init_db
        from db.sources import insert_source
        from db.snapshots import insert_snapshot
        from db.articles import insert_article
        from db.claims import insert_claim
        from db.clusters import create_cluster
        from db.claim_sources import add_claim_source

        db_path = str(tmp_path / "profile_full.db")
        init_db(db_path)
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        src_id = insert_source(conn, "TS", "ts.com", 1)
        insert_snapshot(conn, src_id, "geopolitics", "2026-01-01", r_orig=50, r_val=60)
        art_id = insert_article(conn, src_id, "http://ts.com/1", "Test Article")
        # Add a silent edit
        conn.execute(
            "INSERT INTO silent_edits (article_id, change_ratio, stored_body_length, fetched_body_length) VALUES (?, 0.33, 1000, 670)",
            [art_id],
        )
        # Add a cluster + claim
        cid = create_cluster(conn, "geopolitics", "Test Cluster")
        claim_id = insert_claim(conn, art_id, cid, "Test claim",
                                state="CONSENSUS_ABSORBED",
                                absorbed_at="2026-06-30T00:00:00")
        add_claim_source(conn, claim_id, src_id, first_seen_at="2026-06-27T00:00:00")
        conn.commit()
        conn.close()

        os.environ["NN_DB_PATH"] = db_path
        try:
            with TestClient(app) as c:
                resp = c.get(f"/api/sources/{src_id}/profile?vertical=geopolitics")
                assert resp.status_code == 200
                data = resp.json()
                # New fields
                assert "events" in data
                assert len(data["events"]) == 2  # ABSORBED + SILENT_EDIT
                types = {e["type"] for e in data["events"]}
                assert types == {"CLAIM_ABSORBED", "SILENT_EDIT"}

                assert "edits" in data
                assert len(data["edits"]) == 1
                assert data["edits"][0]["change_ratio"] == 0.33
                assert data["edits"][0]["article_title"] == "Test Article"

                assert "claimSummary" in data
                assert data["claimSummary"]["total"] == 1
                assert data["claimSummary"]["absorbed"] == 1
                assert data["claimSummary"]["pending"] == 0

                # Existing fields still present
                assert "snapshots" in data
                assert "tierAvg" in data
                assert "panelMedian" in data
        finally:
            os.environ.pop("NN_DB_PATH", None)


class TestScoresRoute:
    def test_returns_scores(self, tmp_path):
        """Seed two sources with snapshots, verify scores endpoint."""
        import sqlite3
        from db.connection import init_db
        from db.sources import insert_source
        from db.snapshots import insert_snapshot

        db_path = str(tmp_path / "scores_test.db")
        init_db(db_path)
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        src1 = insert_source(conn, "SrcA", "srca.com", 1)
        src2 = insert_source(conn, "SrcB", "srcb.com", 2)
        insert_snapshot(conn, src1, "geopolitics", "2026-01-01", r_orig=50, r_val=60, r_speed=30)
        insert_snapshot(conn, src2, "geopolitics", "2026-01-01", r_orig=80, r_val=90, r_speed=70)
        conn.close()

        os.environ["NN_DB_PATH"] = db_path
        try:
            with TestClient(app) as c:
                resp = c.get("/api/scores?vertical=geopolitics")
                assert resp.status_code == 200
                data = resp.json()
                assert "scores" in data
                assert len(data["scores"]) == 2
                by_domain = {s["sourceId"]: s for s in data["scores"]}
                assert by_domain["srca.com"]["R_orig"] == 50.0
                assert by_domain["srca.com"]["R_val"] == 60.0
                assert by_domain["srcb.com"]["R_orig"] == 80.0
                assert all(s["vertical"] == "geopolitics" for s in data["scores"])
        finally:
            os.environ.pop("NN_DB_PATH", None)

    def test_returns_empty_when_no_snapshots(self, tmp_path):
        """No snapshots means empty scores array, not error."""
        import sqlite3
        from db.connection import init_db
        from db.sources import insert_source

        db_path = str(tmp_path / "scores_empty.db")
        init_db(db_path)
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        insert_source(conn, "Empty", "empty.com", 1)
        conn.close()

        os.environ["NN_DB_PATH"] = db_path
        try:
            with TestClient(app) as c:
                resp = c.get("/api/scores?vertical=geopolitics")
                assert resp.status_code == 200
                data = resp.json()
                assert data["scores"] == []
        finally:
            os.environ.pop("NN_DB_PATH", None)

    def test_vertical_filter(self, tmp_path):
        """Only snapshots for the requested vertical are returned."""
        import sqlite3
        from db.connection import init_db
        from db.sources import insert_source
        from db.snapshots import insert_snapshot

        db_path = str(tmp_path / "scores_vf.db")
        init_db(db_path)
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        src_id = insert_source(conn, "TS", "ts.com", 1)
        insert_snapshot(conn, src_id, "geopolitics", "2026-01-01", r_val=10)
        insert_snapshot(conn, src_id, "economics", "2026-01-01", r_val=90)
        conn.close()

        os.environ["NN_DB_PATH"] = db_path
        try:
            with TestClient(app) as c:
                resp = c.get("/api/scores?vertical=economics")
                assert resp.status_code == 200
                data = resp.json()
                assert len(data["scores"]) == 1
                assert data["scores"][0]["R_val"] == 90.0
        finally:
            os.environ.pop("NN_DB_PATH", None)


class TestTimelineRoute:
    def test_returns_grouped_claims(self, tmp_path):
        """Seed a cluster with claims from multiple sources, verify grouping."""
        import sqlite3
        import datetime
        from db.connection import init_db
        from db.sources import insert_source
        from db.articles import insert_article
        from db.clusters import create_cluster
        from db.claims import insert_claim
        from db.claim_sources import add_claim_source

        db_path = str(tmp_path / "timeline_test.db")
        init_db(db_path)
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        src1 = insert_source(conn, "SrcA", "srca.com", 1)
        src2 = insert_source(conn, "SrcB", "srcb.com", 2)
        art1 = insert_article(conn, src1, "http://a.com/1")
        art2 = insert_article(conn, src2, "http://b.com/1")
        cid = create_cluster(conn, "geopolitics", "Test Cluster")
        claim1 = insert_claim(conn, art1, cid, "Claim from A first",
                              state="CONSENSUS_ABSORBED",
                              absorbed_at="2026-06-30T00:00:00")
        claim2 = insert_claim(conn, art2, cid, "Claim from B second",
                              state="PENDING")
        add_claim_source(conn, claim1, src1, first_seen_at="2026-06-27T15:00:00")
        add_claim_source(conn, claim2, src2, first_seen_at="2026-06-28T10:00:00")
        conn.close()

        os.environ["NN_DB_PATH"] = db_path
        try:
            with TestClient(app) as c:
                resp = c.get(f"/api/timeline/{cid}")
                assert resp.status_code == 200
                data = resp.json()
                assert data["cluster"]["id"] == cid
                assert data["cluster"]["title"] == "Test Cluster"
                assert len(data["sources"]) == 2
                # Source groups should be in first_seen_at order
                assert data["sources"][0]["domain"] == "srca.com"
                assert len(data["sources"][0]["claims"]) == 1
                assert data["sources"][0]["claims"][0]["state"] == "CONSENSUS_ABSORBED"
                assert data["sources"][1]["domain"] == "srcb.com"
                assert data["sources"][1]["claims"][0]["state"] == "PENDING"
        finally:
            os.environ.pop("NN_DB_PATH", None)

    def test_returns_404_for_missing_cluster(self, client):
        """Nonexistent cluster returns 404."""
        resp = client.get("/api/timeline/99999")
        assert resp.status_code == 404


class TestClusterReportRoute:
    def test_returns_report(self, tmp_path):
        """Seed a cluster with claims, verify report endpoint."""
        import sqlite3
        from db.connection import init_db
        from db.sources import insert_source
        from db.articles import insert_article
        from db.clusters import create_cluster
        from db.claims import insert_claim
        from db.claim_sources import add_claim_source

        db_path = str(tmp_path / "report_test.db")
        init_db(db_path)
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        src = insert_source(conn, "Src", "src.com", 1)
        art = insert_article(conn, src, "http://s.com/1")
        cid = create_cluster(conn, "geopolitics", "Test")
        c1 = insert_claim(conn, art, cid, "Claim A", state="CONSENSUS_ABSORBED",
                          absorbed_at="2026-06-30T00:00:00")
        c2 = insert_claim(conn, art, cid, "Claim B", state="PENDING")
        add_claim_source(conn, c1, src, first_seen_at="2026-06-27T00:00:00")
        add_claim_source(conn, c2, src, first_seen_at="2026-06-27T00:00:00")
        conn.close()

        os.environ["NN_DB_PATH"] = db_path
        try:
            with TestClient(app) as c:
                resp = c.get(f"/api/clusters/{cid}/report")
                assert resp.status_code == 200
                data = resp.json()
                assert data["cluster"]["id"] == cid
                assert data["cluster"]["title"] == "Test"

                assert data["summary"]["totalClaims"] == 2
                assert data["summary"]["absorbed"] == 1
                assert data["summary"]["pending"] == 1
                assert data["summary"]["sourceCount"] == 1

                assert len(data["sources"]) == 1
                assert data["sources"][0]["domain"] == "src.com"
                assert data["sources"][0]["claims"] == 2
                assert data["sources"][0]["absorbed"] == 1
                assert data["sources"][0]["pending"] == 1

                assert len(data["claims"]) == 2
                assert data["claims"][0]["domain"] == "src.com"
        finally:
            os.environ.pop("NN_DB_PATH", None)

    def test_returns_404_for_missing_cluster(self, client):
        resp = client.get("/api/clusters/99999/report")
        assert resp.status_code == 404


class TestCoverageLandscapeRoute:
    """T1b: /api/coverage-landscape endpoint tests."""

    def test_returns_all_sources(self, client):
        """37 sources returned, each with required fields."""
        resp = client.get("/api/coverage-landscape")
        assert resp.status_code == 200
        data = resp.json()
        assert data["totalSources"] == 37
        assert len(data["sources"]) == 37
        for src in data["sources"]:
            assert "source_id" in src
            assert "name" in src
            assert "tier" in src
            assert "total_claims" in src
            assert "solo_claims" in src
            assert "solo_share_pct" in src
            assert "has_absorbed_claims" in src

    def test_solo_share_is_number(self, client):
        """solo_share_pct is a number."""
        resp = client.get("/api/coverage-landscape")
        data = resp.json()
        for src in data["sources"]:
            assert isinstance(src["solo_share_pct"], (int, float))

    def test_has_absorbed_flag_is_int(self, client):
        """has_absorbed_claims is 0 or 1."""
        resp = client.get("/api/coverage-landscape")
        data = resp.json()
        for src in data["sources"]:
            assert src["has_absorbed_claims"] in (0, 1)

    def test_sources_sorted_by_solo_share(self, client):
        """Results sorted by solo_share_pct DESC, then total_claims DESC."""
        resp = client.get("/api/coverage-landscape")
        data = resp.json()
        sources = data["sources"]
        for i in range(len(sources) - 1):
            a, b = sources[i], sources[i + 1]
            if a["solo_share_pct"] == b["solo_share_pct"]:
                assert a["total_claims"] >= b["total_claims"]
            else:
                assert a["solo_share_pct"] >= b["solo_share_pct"]
