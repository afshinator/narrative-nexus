"""Tests for db.sources CRUD operations."""

import pytest
from db.sources import (
    insert_source,
    get_source,
    get_source_by_domain,
    list_sources,
    update_source_active,
    delete_source,
)


class TestInsertSource:
    def test_inserts_and_returns_id(self, db):
        sid = insert_source(db, "Test Source", "test.com", 3)
        assert isinstance(sid, int)
        assert sid > 0

    def test_rejects_invalid_tier(self, db):
        with pytest.raises(Exception):
            insert_source(db, "Bad", "bad.com", 0)

    def test_enforces_unique_domain(self, db):
        insert_source(db, "A", "a.com", 1)
        with pytest.raises(Exception):
            insert_source(db, "B", "a.com", 2)


class TestGetSource:
    def test_returns_source(self, db):
        sid = insert_source(db, "Reuters", "reuters.com", 1)
        source = get_source(db, sid)
        assert source is not None
        assert source["name"] == "Reuters"
        assert source["domain"] == "reuters.com"
        assert source["tier"] == 1

    def test_returns_none_for_missing(self, db):
        assert get_source(db, 999) is None


class TestGetSourceByDomain:
    def test_finds_by_domain(self, db):
        insert_source(db, "AP", "ap.org", 1)
        source = get_source_by_domain(db, "ap.org")
        assert source is not None
        assert source["name"] == "AP"

    def test_returns_none_for_missing_domain(self, db):
        assert get_source_by_domain(db, "nonexistent.com") is None


class TestListSources:
    def test_returns_empty_when_no_sources(self, db):
        assert list_sources(db) == []

    def test_returns_all_sources(self, db):
        insert_source(db, "A", "a.com", 1)
        insert_source(db, "B", "b.com", 2)
        sources = list_sources(db)
        assert len(sources) == 2

    def test_filters_active_only(self, db):
        s1 = insert_source(db, "Active", "active.com", 1, active=1)
        insert_source(db, "Inactive", "inactive.com", 2, active=0)
        active = list_sources(db, active_only=True)
        assert len(active) == 1
        assert active[0]["id"] == s1

    def test_orders_by_tier_then_name(self, db):
        insert_source(db, "Z", "z.com", 2)
        insert_source(db, "A", "a.com", 1)
        sources = list_sources(db)
        assert sources[0]["domain"] == "a.com"  # tier 1, name A
        assert sources[1]["domain"] == "z.com"  # tier 2, name Z


class TestUpdateSourceActive:
    def test_activates_source(self, db):
        sid = insert_source(db, "T", "t.com", 1, active=0)
        assert update_source_active(db, sid, 1) is True
        source = get_source(db, sid)
        assert source["active"] == 1

    def test_deactivates_source(self, db):
        sid = insert_source(db, "T", "t.com", 1, active=1)
        assert update_source_active(db, sid, 0) is True
        source = get_source(db, sid)
        assert source["active"] == 0

    def test_returns_false_for_missing_id(self, db):
        assert update_source_active(db, 999, 1) is False


class TestDeleteSource:
    def test_deletes_source(self, db):
        sid = insert_source(db, "T", "t.com", 1)
        assert delete_source(db, sid) is True
        assert get_source(db, sid) is None

    def test_returns_false_for_missing(self, db):
        assert delete_source(db, 999) is False
