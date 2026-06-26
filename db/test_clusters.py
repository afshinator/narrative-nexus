"""Tests for db.clusters CRUD operations."""

from db.clusters import create_cluster, get_cluster, list_clusters, delete_cluster


class TestCreateCluster:
    def test_creates_and_returns_id(self, db):
        cid = create_cluster(db, "GEOPOLITICS", "Election Story")
        assert isinstance(cid, int)
        assert cid > 0

    def test_creates_without_title(self, db):
        cid = create_cluster(db, "ECONOMICS")
        cluster = get_cluster(db, cid)
        assert cluster is not None
        assert cluster["title"] is None


class TestGetCluster:
    def test_returns_cluster(self, db):
        cid = create_cluster(db, "TECHNOLOGY", "Chip Ban")
        cluster = get_cluster(db, cid)
        assert cluster is not None
        assert cluster["vertical"] == "TECHNOLOGY"

    def test_returns_none_for_missing(self, db):
        assert get_cluster(db, 999) is None


class TestListClusters:
    def test_returns_empty_when_none(self, db):
        assert list_clusters(db) == []

    def test_returns_all(self, db):
        create_cluster(db, "GEOPOLITICS", "A")
        create_cluster(db, "ECONOMICS", "B")
        assert len(list_clusters(db)) == 2

    def test_filters_by_vertical(self, db):
        create_cluster(db, "GEOPOLITICS", "A")
        create_cluster(db, "ECONOMICS", "B")
        geo = list_clusters(db, vertical="GEOPOLITICS")
        assert len(geo) == 1
        assert geo[0]["title"] == "A"


class TestDeleteCluster:
    def test_deletes(self, db):
        cid = create_cluster(db, "GEOPOLITICS")
        assert delete_cluster(db, cid) is True
        assert get_cluster(db, cid) is None

    def test_returns_false_for_missing(self, db):
        assert delete_cluster(db, 999) is False
