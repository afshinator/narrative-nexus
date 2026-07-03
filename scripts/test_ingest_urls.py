"""F4: Unit tests for scripts/ingest_urls.py."""
import pytest
import sqlite3
import tempfile
import os
import csv
from unittest.mock import patch, MagicMock

# Add project root
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.connection import init_db


@pytest.fixture
def tmp_db():
    path = tempfile.mktemp(suffix=".db")
    init_db(path)
    # Insert sources needed for FK constraints
    conn = sqlite3.connect(path)
    conn.executescript("""
        INSERT INTO sources (id, name, domain, tier) VALUES (1, 'reuters', 'reuters.com', 1);
        INSERT INTO sources (id, name, domain, tier) VALUES (2, 'apnews', 'apnews.com', 1);
    """)
    conn.commit()
    conn.close()
    yield path
    os.unlink(path)


@pytest.fixture
def tmp_csv():
    path = tempfile.mktemp(suffix=".csv")
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["story","source","source_id","tier","url","exact_chars","title","published_date"])
        w.writerow(["Test","Reuters","1","1","https://www.reuters.com/test-article-1","5000","Test Article 1","2026-06-24"])
        w.writerow(["Test","AP News","2","1","https://apnews.com/test-article-2","3000","Test Article 2","2026-06-25"])
    yield path
    os.unlink(path)


# ═══════════════════════════════════════════════════════════════════════
# Test 1: ingests new URLs
# ═══════════════════════════════════════════════════════════════════════

def test_ingests_new_urls(tmp_db, tmp_csv):
    """Two new URLs are ingested, one each."""
    from scripts.ingest_urls import ingest_csv

    with patch("scripts.ingest_urls.fetch_body") as mock_fetch:
        mock_fetch.side_effect = [
            ("Test body from Reuters about earthquakes.", "Test Article 1", "2026-06-24T00:00:00+00:00"),
            ("AP News body about earthquake aftermath.", "Test Article 2", "2026-06-25T00:00:00+00:00"),
        ]

        result = ingest_csv(tmp_db, tmp_csv)

    assert result["total"] == 2
    assert result["added"] == 2
    assert result["skipped"] == 0
    assert result["errors"] == 0

    # Verify articles table
    conn = sqlite3.connect(tmp_db)
    rows = conn.execute("SELECT source_id, url, title, body, body_status FROM articles ORDER BY id").fetchall()
    assert len(rows) == 2
    assert rows[0][0] == 1  # source_id for reuters
    assert rows[0][1] == "https://www.reuters.com/test-article-1"
    assert rows[0][2] == "Test Article 1"
    assert rows[0][3] == "Test body from Reuters about earthquakes."
    assert rows[0][4] == "AVAILABLE"
    assert rows[1][0] == 2  # source_id for apnews
    assert rows[1][4] == "AVAILABLE"
    conn.close()


# ═══════════════════════════════════════════════════════════════════════
# Test 2: idempotent — skips existing URLs
# ═══════════════════════════════════════════════════════════════════════

def test_skips_existing_urls(tmp_db, tmp_csv):
    """Running twice only adds once. Second run is all skips."""
    from scripts.ingest_urls import ingest_csv

    # First run
    with patch("scripts.ingest_urls.fetch_body") as mock_fetch:
        mock_fetch.side_effect = [
            ("Body A", "Title A", "2026-06-24"),
            ("Body B", "Title B", "2026-06-25"),
        ]
        r1 = ingest_csv(tmp_db, tmp_csv)

    # Second run — no fetch_body calls should happen
    r2 = ingest_csv(tmp_db, tmp_csv)

    assert r1["added"] == 2
    assert r1["skipped"] == 0
    assert r2["added"] == 0
    assert r2["skipped"] == 2
    assert r2["errors"] == 0

    # Only 2 articles in DB
    conn = sqlite3.connect(tmp_db)
    count = conn.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
    assert count == 2
    conn.close()


# ═══════════════════════════════════════════════════════════════════════
# Test 3: handles domain_to_source_id for known domains
# ═══════════════════════════════════════════════════════════════════════

def test_domain_to_source_id():
    from scripts.ingest_urls import domain_to_source_id
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE sources (id INTEGER, domain TEXT)")
    conn.execute("INSERT INTO sources VALUES (1, 'reuters.com')")
    conn.execute("INSERT INTO sources VALUES (2, 'apnews.com')")

    assert domain_to_source_id(conn, "www.reuters.com") == 1
    assert domain_to_source_id(conn, "apnews.com") == 2
    assert domain_to_source_id(conn, "unknown.com") is None
    conn.close()
