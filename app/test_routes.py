"""Tests for FastAPI application — route responses."""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from db.sources import insert_source


@pytest.fixture
def client():
    """FastAPI test client that uses the application directly."""
    return TestClient(app)


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
