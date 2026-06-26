"""Tests for db.claims CRUD operations."""

import pytest
from db.sources import insert_source
from db.articles import insert_article
from db.clusters import create_cluster
from db.claims import (
    insert_claim,
    get_claim,
    list_claims,
    update_claim_state,
    delete_claim,
)


@pytest.fixture
def src(db):
    return insert_source(db, "Src", "src.com", 1)


@pytest.fixture
def art(db, src):
    return insert_article(db, src, "https://src.com/a", "Article")


@pytest.fixture
def clus(db):
    return create_cluster(db, "GEOPOLITICS", "Story")


class TestInsertClaim:
    def test_inserts_and_returns_id(self, db, art, clus):
        cid = insert_claim(db, art, clus, "claim text")
        assert isinstance(cid, int)
        assert cid > 0

    def test_defaults_to_pending(self, db, art, clus):
        cid = insert_claim(db, art, clus, "text")
        claim = get_claim(db, cid)
        assert claim["state"] == "PENDING"

    def test_rejects_invalid_state(self, db, art, clus):
        with pytest.raises(Exception):
            insert_claim(db, art, clus, "text", state="INVALID")

    def test_rejects_invalid_convergence_type(self, db, art, clus):
        with pytest.raises(Exception):
            insert_claim(db, art, clus, "text", state="CONSENSUS_ABSORBED", convergence_type="INVALID")

    def test_accepts_valid_convergence_values(self, db, art, clus):
        c1 = insert_claim(db, art, clus, "a", state="CONSENSUS_ABSORBED", convergence_type="CROSS_SOURCE_CONVERGENT")
        c2 = insert_claim(db, art, clus, "b", state="CONSENSUS_ABSORBED", convergence_type="SELF_CONSISTENT")
        assert get_claim(db, c1)["convergence_type"] == "CROSS_SOURCE_CONVERGENT"
        assert get_claim(db, c2)["convergence_type"] == "SELF_CONSISTENT"

    def test_enforces_foreign_key_article(self, db, clus):
        with pytest.raises(Exception):
            insert_claim(db, 999, clus, "text")

    def test_enforces_foreign_key_cluster(self, db, art):
        with pytest.raises(Exception):
            insert_claim(db, art, 999, "text")


class TestGetClaim:
    def test_returns_claim(self, db, art, clus):
        cid = insert_claim(db, art, clus, "hello")
        claim = get_claim(db, cid)
        assert claim["text"] == "hello"

    def test_returns_none_for_missing(self, db):
        assert get_claim(db, 999) is None


class TestListClaims:
    def test_filters_by_cluster(self, db, art, clus):
        c1 = create_cluster(db, "ECONOMICS", "Other")
        insert_claim(db, art, clus, "in geo")
        insert_claim(db, art, c1, "in econ")
        geo_claims = list_claims(db, cluster_id=clus)
        assert len(geo_claims) == 1
        assert geo_claims[0]["text"] == "in geo"

    def test_filters_by_state(self, db, art, clus):
        insert_claim(db, art, clus, "pending")
        c2 = insert_claim(db, art, clus, "absorbed", state="CONSENSUS_ABSORBED")
        pending = list_claims(db, state="CONSENSUS_ABSORBED")
        assert len(pending) == 1
        assert pending[0]["id"] == c2


class TestUpdateClaimState:
    def test_transitions_to_absorbed(self, db, art, clus):
        cid = insert_claim(db, art, clus, "text")
        assert update_claim_state(db, cid, "CONSENSUS_ABSORBED", convergence_type="CROSS_SOURCE_CONVERGENT") is True
        claim = get_claim(db, cid)
        assert claim["state"] == "CONSENSUS_ABSORBED"
        assert claim["convergence_type"] == "CROSS_SOURCE_CONVERGENT"

    def test_transitions_to_unresolved(self, db, art, clus):
        cid = insert_claim(db, art, clus, "text")
        assert update_claim_state(db, cid, "UNRESOLVED") is True
        claim = get_claim(db, cid)
        assert claim["state"] == "UNRESOLVED"

    def test_returns_false_for_missing(self, db):
        assert update_claim_state(db, 999, "CONSENSUS_ABSORBED") is False


class TestDeleteClaim:
    def test_deletes(self, db, art, clus):
        cid = insert_claim(db, art, clus, "text")
        assert delete_claim(db, cid) is True
        assert get_claim(db, cid) is None

    def test_returns_false_for_missing(self, db):
        assert delete_claim(db, 999) is False
