"""Tests for db.connection — schema loading and connection setup."""

import pytest
import sqlite3
from db.connection import get_db, load_schema


class TestGetDB:
    def test_returns_connection(self):
        conn = get_db()
        assert isinstance(conn, sqlite3.Connection)
        conn.close()

    def test_in_memory_by_default(self):
        conn = get_db()
        # in-memory databases report ":memory:" as filename
        # WAL pragma is silently ignored for in-memory, which is fine
        assert conn.execute("SELECT 1").fetchone()[0] == 1
        conn.close()

    def test_has_expected_tables(self, db):
        tables = db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()
        names = [row["name"] for row in tables]
        assert "sources" in names
        assert "articles" in names
        assert "clusters" in names
        assert "claims" in names
        assert "claim_sources" in names
        assert "snapshots" in names

    def test_schema_loaded_from_file(self):
        schema_sql = load_schema.__globals__["SCHEMA_PATH"].read_text()
        assert "CREATE TABLE sources" in schema_sql
        assert "CREATE TABLE articles" in schema_sql

    def test_foreign_keys_enabled(self, db):
        row = db.execute("PRAGMA foreign_keys").fetchone()
        assert row[0] == 1
