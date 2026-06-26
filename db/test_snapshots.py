"""Tests for db.snapshots CRUD operations."""

import pytest
from db.sources import insert_source
from db.snapshots import (
    insert_snapshot,
    get_snapshot,
    list_snapshots,
    get_source_vertical_snapshot,
    delete_snapshot,
)


@pytest.fixture
def src1(db):
    return insert_source(db, "Src1", "s1.com", 1)


@pytest.fixture
def src2(db):
    return insert_source(db, "Src2", "s2.com", 2)


class TestInsertSnapshot:
    def test_inserts_and_returns_id(self, db, src1):
        sid = insert_snapshot(db, src1, "GEOPOLITICS", "2026-06-01", r_orig=50.0, r_val=60.0)
        assert isinstance(sid, int)
        assert sid > 0

    def test_enforces_foreign_key(self, db):
        with pytest.raises(Exception):
            insert_snapshot(db, 999, "GEOPOLITICS", "2026-06-01")

    def test_enforces_unique_source_vertical_date(self, db, src1):
        insert_snapshot(db, src1, "GEOPOLITICS", "2026-06-01")
        with pytest.raises(Exception):
            insert_snapshot(db, src1, "GEOPOLITICS", "2026-06-01")

    def test_allows_different_vertical_same_date(self, db, src1):
        insert_snapshot(db, src1, "GEOPOLITICS", "2026-06-01")
        insert_snapshot(db, src1, "ECONOMICS", "2026-06-01")  # should not raise


class TestGetSnapshot:
    def test_returns_snapshot(self, db, src1):
        sid = insert_snapshot(db, src1, "TECHNOLOGY", "2026-06-01", r_orig=75.0)
        snap = get_snapshot(db, sid)
        assert snap is not None
        assert snap["r_orig"] == 75.0

    def test_returns_none_for_missing(self, db):
        assert get_snapshot(db, 999) is None


class TestListSnapshots:
    def test_filters_by_source(self, db, src1, src2):
        insert_snapshot(db, src1, "GEOPOLITICS", "2026-06-01")
        insert_snapshot(db, src2, "GEOPOLITICS", "2026-06-01")
        s1_snaps = list_snapshots(db, source_id=src1)
        assert len(s1_snaps) == 1

    def test_filters_by_vertical(self, db, src1):
        insert_snapshot(db, src1, "GEOPOLITICS", "2026-06-01")
        insert_snapshot(db, src1, "ECONOMICS", "2026-06-01")
        geo = list_snapshots(db, vertical="GEOPOLITICS")
        assert len(geo) == 1

    def test_filters_by_both(self, db, src1):
        insert_snapshot(db, src1, "GEOPOLITICS", "2026-06-01")
        insert_snapshot(db, src1, "ECONOMICS", "2026-06-01")
        result = list_snapshots(db, source_id=src1, vertical="ECONOMICS")
        assert len(result) == 1


class TestGetSourceVerticalSnapshot:
    def test_returns_exact_match(self, db, src1):
        insert_snapshot(db, src1, "GEOPOLITICS", "2026-06-01", r_val=80.0)
        snap = get_source_vertical_snapshot(db, src1, "GEOPOLITICS", "2026-06-01")
        assert snap is not None
        assert snap["r_val"] == 80.0

    def test_returns_none_for_no_match(self, db, src1):
        assert get_source_vertical_snapshot(db, src1, "GEOPOLITICS", "2099-01-01") is None


class TestDeleteSnapshot:
    def test_deletes(self, db, src1):
        sid = insert_snapshot(db, src1, "GEOPOLITICS", "2026-06-01")
        assert delete_snapshot(db, sid) is True
        assert get_snapshot(db, sid) is None

    def test_returns_false_for_missing(self, db):
        assert delete_snapshot(db, 999) is False
