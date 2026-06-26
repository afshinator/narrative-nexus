"""Tests for db.claim_sources CRUD operations."""

import pytest
from db.sources import insert_source
from db.articles import insert_article
from db.clusters import create_cluster
from db.claims import insert_claim
from db.claim_sources import (
    add_claim_source,
    list_claim_sources,
    list_source_claims,
    remove_claim_source,
)


@pytest.fixture
def src1(db):
    return insert_source(db, "Src1", "s1.com", 1)


@pytest.fixture
def src2(db):
    return insert_source(db, "Src2", "s2.com", 2)


@pytest.fixture
def art(db, src1):
    return insert_article(db, src1, "https://s1.com/a", "A")


@pytest.fixture
def clus(db):
    return create_cluster(db, "GEOPOLITICS")


@pytest.fixture
def claim(db, art, clus):
    return insert_claim(db, art, clus, "claim text")


class TestAddClaimSource:
    def test_adds_link(self, db, claim, src1):
        assert add_claim_source(db, claim, src1) is True

    def test_prevents_duplicate(self, db, claim, src1):
        add_claim_source(db, claim, src1)
        assert add_claim_source(db, claim, src1) is False


class TestListClaimSources:
    def test_lists_sources_for_claim(self, db, claim, src1, src2):
        add_claim_source(db, claim, src1)
        add_claim_source(db, claim, src2)
        links = list_claim_sources(db, claim)
        assert len(links) == 2
        source_ids = {l["source_id"] for l in links}
        assert source_ids == {src1, src2}

    def test_returns_empty_when_none(self, db, claim):
        assert list_claim_sources(db, claim) == []


class TestListSourceClaims:
    def test_lists_claims_for_source(self, db, claim, src1, src2, art, clus):
        add_claim_source(db, claim, src1)
        c2 = insert_claim(db, art, clus, "second")
        add_claim_source(db, c2, src1)
        add_claim_source(db, claim, src2)

        src1_claims = list_source_claims(db, src1)
        assert len(src1_claims) == 2

        src2_claims = list_source_claims(db, src2)
        assert len(src2_claims) == 1


class TestRemoveClaimSource:
    def test_removes_link(self, db, claim, src1):
        add_claim_source(db, claim, src1)
        assert remove_claim_source(db, claim, src1) is True
        assert list_claim_sources(db, claim) == []

    def test_returns_false_for_nonexistent(self, db, claim, src1):
        assert remove_claim_source(db, claim, src1) is False
