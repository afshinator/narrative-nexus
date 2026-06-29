"""Tests for db.articles CRUD operations."""

import pytest
from db.sources import insert_source
from db.articles import (
    insert_article,
    get_article,
    list_articles,
    update_article_body,
    delete_article,
)


@pytest.fixture
def src(db):
    return insert_source(db, "Source", "src.com", 1)


class TestInsertArticle:
    def test_inserts_and_returns_id(self, db, src):
        aid = insert_article(db, src, "https://src.com/article1", "Title")
        assert isinstance(aid, int)
        assert aid > 0

    def test_defaults_to_available(self, db, src):
        aid = insert_article(db, src, "https://src.com/a", "T")
        art = get_article(db, aid)
        assert art["body_status"] == "AVAILABLE"

    def test_body_unavailable(self, db, src):
        aid = insert_article(db, src, "https://src.com/b", "T", body_status="BODY_UNAVAILABLE")
        art = get_article(db, aid)
        assert art["body_status"] == "BODY_UNAVAILABLE"

    def test_rejects_invalid_body_status(self, db, src):
        with pytest.raises(Exception):
            insert_article(db, src, "https://src.com/c", "T", body_status="INVALID")

    def test_enforces_foreign_key(self, db):
        with pytest.raises(Exception):
            insert_article(db, 999, "https://x.com/a", "T")


class TestGetArticle:
    def test_returns_article(self, db, src):
        aid = insert_article(db, src, "https://src.com/x", "Title X")
        art = get_article(db, aid)
        assert art is not None
        assert art["url"] == "https://src.com/x"

    def test_returns_none_for_missing(self, db):
        assert get_article(db, 999) is None


class TestListArticles:
    def test_returns_empty_when_none(self, db):
        assert list_articles(db) == []

    def test_returns_all(self, db, src):
        insert_article(db, src, "https://src.com/a", "A")
        insert_article(db, src, "https://src.com/b", "B")
        arts = list_articles(db)
        assert len(arts) == 2

    def test_filters_by_source(self, db, src):
        src2 = insert_source(db, "Other", "other.com", 2)
        insert_article(db, src, "https://src.com/a", "A")
        insert_article(db, src2, "https://other.com/b", "B")
        arts = list_articles(db, source_id=src)
        assert len(arts) == 1
        assert arts[0]["url"] == "https://src.com/a"


class TestUpdateArticleBody:
    def test_updates_body(self, db, src):
        aid = insert_article(db, src, "https://src.com/x", "T")
        assert update_article_body(db, aid, "new body") is True
        art = get_article(db, aid)
        assert art["body"] == "new body"

    def test_updates_status(self, db, src):
        aid = insert_article(db, src, "https://src.com/x", "T")
        assert update_article_body(db, aid, "", "BODY_UNAVAILABLE") is True
        art = get_article(db, aid)
        assert art["body_status"] == "BODY_UNAVAILABLE"

    def test_returns_false_for_missing(self, db):
        assert update_article_body(db, 999, "body") is False


class TestDeleteArticle:
    def test_deletes(self, db, src):
        aid = insert_article(db, src, "https://src.com/x", "T")
        assert delete_article(db, aid) is True
        assert get_article(db, aid) is None

    def test_returns_false_for_missing(self, db):
        assert delete_article(db, 999) is False


class TestUrlUniqueness:
    def test_duplicate_url_raises(self, db, src):
        insert_article(db, src, "https://src.com/dup", "First")
        with pytest.raises(Exception):
            insert_article(db, src, "https://src.com/dup", "Second")


class TestListPendingArticles:
    def test_returns_empty_when_none_pending(self, db, src):
        from db.articles import list_pending_articles
        # All articles have bodies — nothing pending
        insert_article(db, src, "https://src.com/a", "A", body="text")
        insert_article(db, src, "https://src.com/b", "B",
                       body="", body_status="BODY_UNAVAILABLE")
        assert list_pending_articles(db) == []

    def test_returns_articles_with_empty_body_and_available_status(self, db, src):
        from db.articles import list_pending_articles
        # These should be pending: AVAILABLE status + empty body
        insert_article(db, src, "https://src.com/p1", "P1",
                       body="", body_status="AVAILABLE")
        insert_article(db, src, "https://src.com/p2", "P2",
                       body=None, body_status="AVAILABLE")
        # These should NOT be pending
        insert_article(db, src, "https://src.com/n1", "N1",
                       body="text", body_status="AVAILABLE")
        insert_article(db, src, "https://src.com/n2", "N2",
                       body="", body_status="BODY_UNAVAILABLE")
        pending = list_pending_articles(db)
        assert len(pending) == 2
        urls = {a["url"] for a in pending}
        assert urls == {"https://src.com/p1", "https://src.com/p2"}

    def test_respects_limit(self, db, src):
        from db.articles import list_pending_articles
        for i in range(5):
            insert_article(db, src, f"https://src.com/{i}", f"T{i}",
                           body="", body_status="AVAILABLE")
        pending = list_pending_articles(db, limit=3)
        assert len(pending) == 3
