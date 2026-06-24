import { describe, it, expect, beforeAll } from "vitest";
import Database from "better-sqlite3";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const SCHEMA_PATH = resolve(import.meta.dirname, "../schema.sql");

let db: Database.Database;

function loadSchema(): string {
  return readFileSync(SCHEMA_PATH, "utf8");
}

function columns(table: string) {
  return db.prepare(`PRAGMA table_info('${table}')`).all() as Array<{
    cid: number; name: string; type: string; notnull: number; dflt_value: string | null; pk: number;
  }>;
}

function columnNames(table: string): string[] {
  return columns(table).map((c) => c.name);
}

beforeAll(() => {
  db = new Database(":memory:");
  db.pragma("foreign_keys = ON");
  db.pragma("journal_mode = WAL");
  db.exec(loadSchema());
});

describe("SQLite schema", () => {
  it("includes WAL journal mode pragma", () => {
    const sql = loadSchema();
    // in-memory databases always report "memory" — can't test WAL at runtime.
    // Verify the schema source contains the pragma instead.
    expect(sql).toMatch(/PRAGMA\s+journal_mode\s*=\s*WAL/i);
  });

  describe("sources table", () => {
    it("exists with expected columns", () => {
      const names = columnNames("sources");
      expect(names).toContain("id");
      expect(names).toContain("name");
      expect(names).toContain("domain");
      expect(names).toContain("tier");
      expect(names).toContain("active");
      expect(names).toContain("created_at");
    });

    it("rejects invalid tier values", () => {
      expect(() =>
        db.exec("INSERT INTO sources (name, domain, tier) VALUES ('Test', 'test.com', 0)"),
      ).toThrow();
      expect(() =>
        db.exec("INSERT INTO sources (name, domain, tier) VALUES ('Test', 'test.com', 6)"),
      ).toThrow();
    });

    it("accepts valid tier values 1-5", () => {
      db.exec("INSERT INTO sources (name, domain, tier) VALUES ('T1', 't1.com', 1)");
      db.exec("INSERT INTO sources (name, domain, tier) VALUES ('T5', 't5.com', 5)");
      const rows = db.prepare("SELECT * FROM sources").all();
      expect(rows).toHaveLength(2);
    });
  });

  describe("articles table", () => {
    it("exists with expected columns", () => {
      const names = columnNames("articles");
      expect(names).toContain("id");
      expect(names).toContain("source_id");
      expect(names).toContain("url");
      expect(names).toContain("title");
      expect(names).toContain("body");
      expect(names).toContain("published_at");
      expect(names).toContain("body_status");
    });

    it("rejects invalid body_status values", () => {
      db.exec("INSERT INTO sources (name, domain, tier) VALUES ('S', 's.com', 1)");
      expect(() =>
        db.exec(
          "INSERT INTO articles (source_id, url, title, body_status) VALUES (1, '/a', 'T', 'INVALID')",
        ),
      ).toThrow();
    });

    it("accepts valid body_status values", () => {
      db.exec(
        "INSERT INTO articles (source_id, url, title, body_status) VALUES (1, '/a', 'T', 'AVAILABLE')",
      );
      db.exec(
        "INSERT INTO articles (source_id, url, title, body_status) VALUES (1, '/b', 'T', 'BODY_UNAVAILABLE')",
      );
      const rows = db.prepare("SELECT body_status FROM articles").all() as Array<{ body_status: string }>;
      expect(rows.map((r) => r.body_status).sort()).toEqual(["AVAILABLE", "BODY_UNAVAILABLE"]);
    });

    it("enforces foreign key to sources", () => {
      expect(() =>
        db.exec("INSERT INTO articles (source_id, url, title) VALUES (999, '/x', 'T')"),
      ).toThrow();
    });
  });

  describe("clusters table", () => {
    it("exists with expected columns", () => {
      const names = columnNames("clusters");
      expect(names).toContain("id");
      expect(names).toContain("vertical");
      expect(names).toContain("title");
      expect(names).toContain("created_at");
    });
  });

  describe("claims table", () => {
    it("exists with expected columns", () => {
      const names = columnNames("claims");
      expect(names).toContain("id");
      expect(names).toContain("article_id");
      expect(names).toContain("cluster_id");
      expect(names).toContain("text");
      expect(names).toContain("state");
      expect(names).toContain("convergence_type");
      expect(names).toContain("absorbed_at");
    });

    it("rejects invalid state values", () => {
      db.exec("INSERT INTO sources (name, domain, tier) VALUES ('S2', 's2.com', 1)");
      db.exec("INSERT INTO articles (source_id, url, title) VALUES (2, '/c', 'T')");
      db.exec("INSERT INTO clusters (vertical, title) VALUES ('GEOPOLITICS', 'Test')");
      expect(() =>
        db.exec(
          "INSERT INTO claims (article_id, cluster_id, text, state) VALUES (1, 1, 'text', 'INVALID')",
        ),
      ).toThrow();
    });

    it("accepts valid state values", () => {
      db.exec(
        "INSERT INTO claims (article_id, cluster_id, text, state, convergence_type) VALUES (1, 1, 'text', 'PENDING', NULL)",
      );
      db.exec(
        "INSERT INTO claims (article_id, cluster_id, text, state, convergence_type) VALUES (1, 1, 'text2', 'CONSENSUS_ABSORBED', 'CROSS_SOURCE_CONVERGENT')",
      );
      const rows = db.prepare("SELECT state FROM claims").all() as Array<{ state: string }>;
      expect(rows.map((r) => r.state).sort()).toEqual(["CONSENSUS_ABSORBED", "PENDING"]);
    });

    it("rejects invalid convergence_type values", () => {
      expect(() =>
        db.exec(
          "INSERT INTO claims (article_id, cluster_id, text, state, convergence_type) VALUES (1, 1, 'text3', 'CONSENSUS_ABSORBED', 'INVALID')",
        ),
      ).toThrow();
    });

    it("enforces foreign key to articles", () => {
      expect(() =>
        db.exec("INSERT INTO claims (article_id, cluster_id, text, state) VALUES (999, 1, 'x', 'PENDING')"),
      ).toThrow();
    });

    it("enforces foreign key to clusters", () => {
      expect(() =>
        db.exec("INSERT INTO claims (article_id, cluster_id, text, state) VALUES (1, 999, 'x', 'PENDING')"),
      ).toThrow();
    });
  });

  describe("claim_sources table", () => {
    it("exists with expected columns", () => {
      const names = columnNames("claim_sources");
      expect(names).toContain("claim_id");
      expect(names).toContain("source_id");
      expect(names).toContain("first_seen_at");
    });

    it("enforces composite primary key", () => {
      db.exec("INSERT INTO claim_sources (claim_id, source_id) VALUES (1, 1)");
      expect(() =>
        db.exec("INSERT INTO claim_sources (claim_id, source_id) VALUES (1, 1)"),
      ).toThrow();
    });
  });

  describe("snapshots table", () => {
    it("exists with expected columns", () => {
      const names = columnNames("snapshots");
      expect(names).toContain("id");
      expect(names).toContain("source_id");
      expect(names).toContain("vertical");
      expect(names).toContain("date");
      expect(names).toContain("r_orig");
      expect(names).toContain("r_val");
      expect(names).toContain("r_speed");
      expect(names).toContain("r_frame");
      expect(names).toContain("r_edit");
      expect(names).toContain("r_correct");
      expect(names).toContain("archetype");
    });

    it("enforces foreign key to sources", () => {
      expect(() =>
        db.exec("INSERT INTO snapshots (source_id, vertical, date) VALUES (999, 'GEOPOLITICS', '2026-01-01')"),
      ).toThrow();
    });
  });
});
