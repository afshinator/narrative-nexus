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
