"""Tests for db.silent_edits CRUD operations."""
import pytest
from db.sources import insert_source
from db.articles import insert_article
from db.silent_edits import insert_silent_edit, list_silent_edits


@pytest.fixture
def art(db):
    src = insert_source(db, "Test", "test.com", 1)
    return insert_article(db, src, "https://test.com/1", "Title", body="text")


class TestInsertSilentEdit:
    def test_inserts_and_returns_id(self, db, art):
        eid = insert_silent_edit(db, art, 0.35, 100, 85)
        assert isinstance(eid, int)
        assert eid > 0

    def test_stores_all_fields(self, db, art):
        eid = insert_silent_edit(db, art, 0.15, 200, 170)
        rows = db.execute(
            "SELECT * FROM silent_edits WHERE id = ?", (eid,)
        ).fetchall()
        assert len(rows) == 1
        r = rows[0]
        assert r["article_id"] == art
        assert r["change_ratio"] == 0.15
        assert r["stored_body_length"] == 200
        assert r["fetched_body_length"] == 170
        assert r["detected_at"] is not None

    def test_enforces_foreign_key(self, db):
        with pytest.raises(Exception):
            insert_silent_edit(db, 999, 0.5, 100, 50)


class TestListSilentEdits:
    def test_returns_empty_when_none(self, db, art):
        assert list_silent_edits(db, art) == []

    def test_returns_edits_for_article(self, db, art):
        insert_silent_edit(db, art, 0.2, 100, 80)
        insert_silent_edit(db, art, 0.3, 100, 70)
        edits = list_silent_edits(db, art)
        assert len(edits) == 2
        assert edits[0]["article_id"] == art
        assert edits[1]["article_id"] == art

    def test_filters_by_article_id(self, db):
        src2 = insert_source(db, "Other", "other.com", 2)
        art2 = insert_article(db, src2, "https://other.com/1", "T2", body="x")
        insert_silent_edit(db, art2, 0.1, 50, 45)
        eid = insert_silent_edit(db, art2, 0.2, 50, 40)
        assert len(list_silent_edits(db, art2)) == 2
        assert len(list_silent_edits(db, eid)) == 0  # wrong article_id
