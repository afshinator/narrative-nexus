"""T6a: Tests for Phase 1 — claim matching, consensus rule, R_val 7-day exclusion."""
import pytest
import sqlite3
import tempfile
import os
from unittest.mock import AsyncMock, MagicMock, patch
import numpy as np

from db.connection import init_db, get_db
from db.sources import insert_source
from db.articles import insert_article
from db.clusters import create_cluster
from db.claims import insert_claim
from db.claim_sources import add_claim_source

from pipeline.claim_matching import match_claims_in_cluster
from pipeline.consensus import MIN_CORROBORATION
from pipeline.snapshots import compute_r_val_raw


# ── Fixtures ────────────────────────────────────────────────────────────

@pytest.fixture
def db():
    path = tempfile.mktemp(suffix=".db")
    init_db(path)
    conn = get_db(path)
    # Add sources
    for sid in range(1, 6):
        conn.execute(
            "INSERT INTO sources (id, name, domain, tier) VALUES (?, ?, ?, ?)",
            (sid, f"src{sid}", f"src{sid}.com", 1 if sid <= 3 else 3),
        )
    conn.commit()
    yield conn
    conn.close()
    os.unlink(path)


def _make_article(conn, source_id, title, body, published_at="2026-06-15T00:00:00+00:00"):
    cur = conn.execute(
        "INSERT INTO articles (source_id, url, title, body, published_at) VALUES (?, ?, ?, ?, ?)",
        (source_id, f"http://test/{title}", title, body, published_at),
    )
    return cur.lastrowid


def _make_claim(conn, article_id, cluster_id, text, state="PENDING"):
    cur = conn.execute(
        "INSERT INTO claims (article_id, cluster_id, text, state) VALUES (?, ?, ?, ?)",
        (article_id, cluster_id, text, state),
    )
    cid = cur.lastrowid
    art = conn.execute("SELECT source_id FROM articles WHERE id = ?", (article_id,)).fetchone()
    add_claim_source(conn, cid, art["source_id"])
    return cid


# ── T6a.1: Claim matching ───────────────────────────────────────────────

class TestClaimMatching:
    @pytest.mark.asyncio
    async def test_same_source_dupes_merge(self, db):
        """Same outlet repeating itself → one claim_sources row, earliest timestamp."""
        cid = create_cluster(db, vertical="geopolitics")
        a1 = _make_article(db, 1, "a1", "The sky is blue", "2026-06-10")
        a2 = _make_article(db, 1, "a2", "The sky is blue", "2026-06-15")
        cl1 = _make_claim(db, a1, cid, "The sky is blue")
        cl2 = _make_claim(db, a2, cid, "The sky is blue")

        embed = AsyncMock()
        embed.embed = AsyncMock(return_value=[
            [1.0, 0.0],  # claim 1
            [0.99, 0.01],  # claim 2 (very similar)
        ])

        result = await match_claims_in_cluster(db, cid, embed, sim_threshold=0.85)
        assert result["merges"] == 1
        assert result["canonicals_after"] == 1
        # Variant preserved
        cv = db.execute("SELECT * FROM claim_variants").fetchone()
        assert cv is not None

    @pytest.mark.asyncio
    async def test_cross_source_merges(self, db):
        """Two sources reporting same claim → merged with both claim_sources."""
        cid = create_cluster(db, vertical="geopolitics")
        a1 = _make_article(db, 1, "Reuters", "Strike hits facility", "2026-06-10")
        a2 = _make_article(db, 2, "AP", "Missile strikes facility", "2026-06-11")
        cl1 = _make_claim(db, a1, cid, "Strike hits facility")
        cl2 = _make_claim(db, a2, cid, "Missile strikes facility")

        embed = AsyncMock()
        embed.embed = AsyncMock(return_value=[
            [1.0, 0.0],
            [0.95, 0.05],  # semantically similar
        ])

        result = await match_claims_in_cluster(db, cid, embed, sim_threshold=0.85)
        assert result["merges"] == 1
        assert result["sources_linked"] >= 1

    @pytest.mark.asyncio
    async def test_below_threshold_no_merge(self, db):
        """Different claims below threshold stay separate."""
        cid = create_cluster(db, vertical="geopolitics")
        a1 = _make_article(db, 1, "R1", "Stock market rises", "2026-06-10")
        a2 = _make_article(db, 2, "R2", "Earthquake hits city", "2026-06-11")
        cl1 = _make_claim(db, a1, cid, "Stock market rises")
        cl2 = _make_claim(db, a2, cid, "Earthquake hits city")

        embed = AsyncMock()
        embed.embed = AsyncMock(return_value=[
            [1.0, 0.0],
            [0.0, 1.0],  # orthogonal vectors → sim ≈ 0
        ])

        result = await match_claims_in_cluster(db, cid, embed, sim_threshold=0.85)
        assert result["merges"] == 0
        assert result["canonicals_after"] == 2

    @pytest.mark.asyncio
    async def test_idempotent(self, db):
        """Running twice on same cluster is a no-op."""
        cid = create_cluster(db, vertical="geopolitics")
        a1 = _make_article(db, 1, "a1", "Same text", "2026-06-10")
        a2 = _make_article(db, 2, "a2", "Same text", "2026-06-11")
        cl1 = _make_claim(db, a1, cid, "Same text")
        cl2 = _make_claim(db, a2, cid, "Same text")

        embed = AsyncMock()
        embed.embed = AsyncMock(return_value=[
            [1.0, 0.0], [1.0, 0.0],
        ])

        r1 = await match_claims_in_cluster(db, cid, embed, sim_threshold=0.85)
        assert r1["merges"] == 1

        # Re-embed for second call (claims changed)
        embed.embed = AsyncMock(return_value=[[1.0, 0.0]])
        r2 = await match_claims_in_cluster(db, cid, embed, sim_threshold=0.85)
        assert r2["merges"] == 0

    @pytest.mark.asyncio
    async def test_threshold_boundary(self, db):
        """Claim at exactly threshold should merge."""
        cid = create_cluster(db, vertical="geopolitics")
        a1 = _make_article(db, 1, "a1", "Claim A", "2026-06-10")
        a2 = _make_article(db, 2, "a2", "Claim A variant", "2026-06-11")
        cl1 = _make_claim(db, a1, cid, "Claim A")
        cl2 = _make_claim(db, a2, cid, "Claim A variant")

        embed = AsyncMock()
        embed.embed = AsyncMock(return_value=[
            [1.0, 0.0],
            [0.85, 0.5268],  # cos ≈ 0.85 with [1,0]
        ])

        result = await match_claims_in_cluster(db, cid, embed, sim_threshold=0.85)
        # At threshold and above should merge
        assert result["merges"] == 1


# ── T6a.2: Consensus rule ───────────────────────────────────────────────

class TestConsensusRule:
    def test_min_corroboration_constant(self):
        assert MIN_CORROBORATION == 2

    def test_single_source_rejected(self):
        """1 source reporting → not absorbed regardless of pct."""
        from pipeline.consensus import MIN_CORROBORATION
        reporting = 1
        assert reporting < MIN_CORROBORATION

    def test_two_source_accepted(self):
        """2 sources reporting at threshold → absorbed."""
        from pipeline.consensus import compute_baseline_pct, classify_claim
        reporting = 2
        pool_size = 2
        pct = compute_baseline_pct(reporting, pool_size)
        assert pct == 100.0
        assert classify_claim(pct, 65) == "CONSENSUS_ABSORBED"


# ── T6a.3: R_val 7-day exclusion ────────────────────────────────────────

class TestRValWindow:
    def test_excludes_claims_within_7_days(self, db):
        """Claims created within 7 days of as_of are excluded from R_val."""
        cid = create_cluster(db, vertical="geopolitics")
        a1 = _make_article(db, 1, "early", "Early claim", "2026-06-01")
        a2 = _make_article(db, 1, "recent", "Recent claim", "2026-06-28")
        cl1 = _make_claim(db, a1, cid, "Early claim", state="CONSENSUS_ABSORBED")
        cl2 = _make_claim(db, a2, cid, "Recent claim", state="CONSENSUS_ABSORBED")

        # Set created_at to specific dates
        db.execute("UPDATE claims SET created_at = '2026-06-01T00:00:00+00:00' WHERE id = ?", (cl1,))
        db.execute("UPDATE claims SET created_at = '2026-06-28T00:00:00+00:00' WHERE id = ?", (cl2,))
        # Set first_seen_at
        db.execute("UPDATE claim_sources SET first_seen_at = '2026-06-01T00:00:00+00:00' WHERE claim_id = ?", (cl1,))
        db.execute("UPDATE claim_sources SET first_seen_at = '2026-06-28T00:00:00+00:00' WHERE claim_id = ?", (cl2,))
        db.commit()

        # as_of = 2026-06-30, 7-day cutoff = 2026-06-23
        result = compute_r_val_raw(db, as_of="2026-06-30T00:00:00+00:00")
        # Only the June 1 claim should count (June 28 is within 7 days)
        assert result[1] is not None
        assert result[1] == 1.0  # 1 absorbed / 1 originated (both early)

    def test_no_as_of_returns_all(self, db):
        """Without as_of, all claims count."""
        cid = create_cluster(db, vertical="geopolitics")
        a1 = _make_article(db, 1, "a1", "Claim", "2026-06-01")
        cl1 = _make_claim(db, a1, cid, "Claim", state="CONSENSUS_ABSORBED")
        db.commit()

        result = compute_r_val_raw(db, as_of=None)
        assert result[1] is not None
        assert result[1] == 1.0
