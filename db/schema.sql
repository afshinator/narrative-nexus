-- Narrative Nexus — SQLite Schema
-- WAL mode for concurrent reads (REQ-112)
PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

-- Source panel registry (REQ-048–053)
CREATE TABLE sources (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL,
    domain      TEXT NOT NULL UNIQUE,
    tier        INTEGER NOT NULL CHECK (tier BETWEEN 1 AND 5),
    active      INTEGER NOT NULL DEFAULT 1,
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Scraped article storage
CREATE TABLE articles (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id     INTEGER NOT NULL REFERENCES sources(id),
    url           TEXT NOT NULL,
    title         TEXT,
    body          TEXT,
    published_at  TEXT,
    body_status   TEXT NOT NULL DEFAULT 'AVAILABLE'
                  CHECK (body_status IN ('AVAILABLE', 'BODY_UNAVAILABLE')),
    created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX idx_articles_source ON articles(source_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_articles_url ON articles(url);

-- Story clusters (grouped by semantic similarity)
CREATE TABLE clusters (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    vertical    TEXT NOT NULL,
    title       TEXT,
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Extracted factual claims
CREATE TABLE claims (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    article_id        INTEGER NOT NULL REFERENCES articles(id),
    cluster_id        INTEGER NOT NULL REFERENCES clusters(id),
    text              TEXT NOT NULL,
    state             TEXT NOT NULL DEFAULT 'PENDING'
                      CHECK (state IN ('PENDING', 'CONSENSUS_ABSORBED', 'UNRESOLVED')),
    convergence_type  TEXT CHECK (convergence_type IN ('CROSS_SOURCE_CONVERGENT', 'SELF_CONSISTENT')),
    absorbed_at       TEXT,
    created_at        TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX idx_claims_article ON claims(article_id);
CREATE INDEX idx_claims_cluster ON claims(cluster_id);
CREATE INDEX idx_claims_state ON claims(state);

-- Which sources published each claim
CREATE TABLE claim_sources (
    claim_id      INTEGER NOT NULL REFERENCES claims(id),
    source_id     INTEGER NOT NULL REFERENCES sources(id),
    first_seen_at TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (claim_id, source_id)
);

-- Daily reputation snapshots (one row per source per vertical per day)
CREATE TABLE snapshots (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id   INTEGER NOT NULL REFERENCES sources(id),
    vertical    TEXT NOT NULL,
    date        TEXT NOT NULL,
    r_orig      REAL,
    r_val       REAL,
    r_speed     REAL,
    r_frame     REAL,
    r_edit      REAL,
    r_correct   REAL,
    archetype   TEXT,
    created_at  TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(source_id, vertical, date)
);

CREATE INDEX idx_snapshots_source ON snapshots(source_id, vertical, date);
