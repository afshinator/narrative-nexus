"""Tests for pipeline.snapshots — batch snapshot writer."""
import pytest
from db.sources import insert_source
from db.clusters import create_cluster
from db.claims import insert_claim
from db.claim_sources import add_claim_source
from pipeline.snapshots import write_daily_snapshots


class TestWriteDailySnapshots:
    def test_writes_nothing_when_no_sources(self, db):
        count = write_daily_snapshots(db, "2026-06-26")
        assert count == 0

    def test_writes_one_row_per_source_per_vertical(self, db):
        insert_source(db, "Reuters", "reuters.com", 1)
        insert_source(db, "AP", "apnews.com", 1)
        count = write_daily_snapshots(db, "2026-06-26")
        assert count == 6

    def test_idempotent(self, db):
        insert_source(db, "BBC", "bbc.com", 1)
        first = write_daily_snapshots(db, "2026-06-26")
        second = write_daily_snapshots(db, "2026-06-26")
        assert second == 0

    def test_stores_nulls_for_uncomputable_dims(self, db):
        insert_source(db, "Test", "test.com", 1)
        write_daily_snapshots(db, "2026-06-26")
        from db.snapshots import list_snapshots
        snaps = list_snapshots(db)
        s = snaps[0]
        assert s["r_orig"] is not None
        assert s["r_val"] is not None
        assert s["r_speed"] is not None
        assert s["r_frame"] is None
        assert s["r_edit"] is None
        assert s["r_correct"] is None

    def test_per_vertical_scoring(self, db):
        sid = insert_source(db, "Reuters", "reuters.com", 1)
        c1 = create_cluster(db, "geopolitics", "Geo Cluster")
        c2 = create_cluster(db, "technology", "Tech Cluster")
        from db.articles import insert_article
        a1 = insert_article(db, sid, "https://reuters.com/1", "Article 1")
        a2 = insert_article(db, sid, "https://reuters.com/2", "Article 2")
        a3 = insert_article(db, sid, "https://reuters.com/3", "Article 3")
        # Geopolitics: 1 claim, 1 originated — r_orig=100.0, r_val=0.0
        claim1 = insert_claim(db, a1, c1, "Geo claim")
        add_claim_source(db, claim1, sid)
        # Technology: 2 claims, 1 originated, 1 absorbed — r_orig=50.0, r_val=100.0
        claim2 = insert_claim(db, a2, c2, "Tech claim 1")
        claim3 = insert_claim(db, a3, c2, "Tech claim 2")
        add_claim_source(db, claim2, sid)
        add_claim_source(db, claim3, sid)
        # Mark claim2 as absorbed
        from db.claims import update_claim_state
        update_claim_state(db, claim2, "CONSENSUS_ABSORBED")

        write_daily_snapshots(db, "2026-06-26")
        from db.snapshots import list_snapshots
        snaps = list_snapshots(db)
        geopolitics = [s for s in snaps if s["vertical"] == "geopolitics"]
        technology = [s for s in snaps if s["vertical"] == "technology"]
        assert len(geopolitics) == 1
        assert len(technology) == 1
        geo_score = (geopolitics[0]["r_orig"], geopolitics[0]["r_val"])
        tech_score = (technology[0]["r_orig"], technology[0]["r_val"])
        assert geo_score != tech_score, f"Scores should differ across verticals: {geo_score} vs {tech_score}"
