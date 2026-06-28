#!/usr/bin/env python3
"""Seed script — runs the pipeline against existing scraped articles.

Usage:
    python scripts/seed-demo.py [--db data/nn.db]

Per ADR-0002, this shares code paths with the live pipeline. No demo mode,
no mock data, no separate database. It imports the same agent classes and
snapshot functions the live scheduler uses.

What it does:
  1. Runs Agent 1 (Intake & Clustering) on articles with bodies
  2. Runs Agent 2 (Forensic Extraction) on clustered articles
  3. Runs Agent 3 (Consensus Alignment) on all clusters
  4. Runs Agent 4 (Silent Auditor) to detect edits
  5. Generates date-filtered daily snapshots across the full article date range

After seeding, the database contains clusters, claims, consensus states,
and reputation time-series — all produced by the real pipeline.
"""

import argparse
import os
import sys
from datetime import datetime, timedelta, timezone

# Ensure the project root is on sys.path so we can import db/ and pipeline/
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.connection import get_db
from pipeline.provider_config import load_provider_config, get_provider_for_agent
from pipeline.agent1_intake import IntakeClusteringAgent
from pipeline.agent2_forensic import ForensicExtractionAgent
from pipeline.agent3_consensus import ConsensusAlignmentAgent
from pipeline.agent4_silent import SilentAuditorAgent
from pipeline.runner import _compute_and_write_snapshots


# ── CLI ──────────────────────────────────────────────────────────────────


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Seed the Narrative Nexus database with pipeline output.",
    )
    parser.add_argument(
        "--db",
        default="data/nn.db",
        help="Path to SQLite database (default: data/nn.db)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Load config and report what would happen, but don't write data",
    )
    return parser.parse_args(argv)


# ── Main ─────────────────────────────────────────────────────────────────


def main() -> int:
    args = parse_args()

    # ── 0. Load provider config ───────────────────────────────────────
    cfg_path = os.environ.get(
        "NN_PROVIDERS_CONFIG",
        os.path.join(os.path.dirname(__file__), "..", "config", "providers.json"),
    )
    try:
        cfg = load_provider_config(cfg_path)
    except (FileNotFoundError, ValueError) as exc:
        print(f"Error loading provider config: {exc}", file=sys.stderr)
        return 1

    a1_embed = get_provider_for_agent(cfg, "agent1_embedding")
    a1_llm = get_provider_for_agent(cfg, "agent1_llm")
    a2_llm = get_provider_for_agent(cfg, "agent2_llm")

    print(f"Providers:")
    print(f"  Agent 1 embedding: {a1_embed['name']} ({a1_embed['model']})")
    print(f"  Agent 1 LLM:       {a1_llm['name']} ({a1_llm['model']})")
    print(f"  Agent 2 LLM:       {a2_llm['name']} ({a2_llm['model']})")
    print(f"  Agent 3:           CPU (pure Python)")
    print(f"  Agent 4:           CPU (text diff)")
    print(f"  Database:           {args.db}")

    if args.dry_run:
        print("\nDry run — no data written.")
        return 0

    # ── 1. Agent 1 — Intake & Clustering ──────────────────────────────
    print("\n── Agent 1: Intake & Clustering ──")
    import asyncio

    agent1 = IntakeClusteringAgent(
        db_path=args.db,
        embedding_provider=a1_embed,
    )
    a1_result = asyncio.run(agent1.run())
    print(f"  Clusters:          {a1_result['clusters']}")
    print(f"  Articles clustered: {a1_result['articles_clustered']}")
    article_map = a1_result.get("article_map", {})

    if not article_map:
        print("  No articles with bodies found. Nothing to seed.")
        return 0

    # ── 2. Agent 2 — Forensic Extraction ──────────────────────────────
    print("\n── Agent 2: Forensic Extraction ──")
    a2_key = os.environ.get(f"{a2_llm['id'].upper()}_API_KEY", "")
    agent2 = ForensicExtractionAgent(
        db_path=args.db,
        llm_provider=a2_llm,
        api_key=a2_key,
    )
    a2_result = asyncio.run(agent2.run(article_map=article_map))
    print(f"  Claims extracted:  {a2_result['claims_extracted']}")
    print(f"  Articles processed: {a2_result['articles_processed']}")

    # ── 3. Agent 3 — Consensus Alignment ──────────────────────────────
    print("\n── Agent 3: Consensus Alignment ──")
    conn = get_db(args.db)
    try:
        agent3 = ConsensusAlignmentAgent(db_path=args.db)
        a3_result = agent3.run_all(conn)
        print(f"  Clusters:          {a3_result.get('clusters', 0)}")
        print(f"  Claims classified: {a3_result.get('classified', 0)}")
    finally:
        conn.close()

    # ── 4. Agent 4 — Silent Auditor ───────────────────────────────────
    print("\n── Agent 4: Silent Auditor ──")
    agent4 = SilentAuditorAgent(db_path=args.db)
    a4_result = asyncio.run(agent4.run())
    print(f"  Articles checked:  {a4_result['articles_checked']}")
    print(f"  Edits detected:    {a4_result['edits_detected']}")

    # ── 5. Date-filtered daily snapshots ──────────────────────────────
    print("\n── Daily Snapshots ──")
    conn2 = get_db(args.db)
    try:
        # Find the date range of articles in the DB
        date_rows = conn2.execute(
            "SELECT MIN(published_at), MAX(published_at) FROM articles "
            "WHERE published_at IS NOT NULL"
        ).fetchone()
        if not date_rows or not date_rows[0]:
            print("  No article dates found. Skipping snapshots.")
            return 0

        min_date_str = date_rows[0][:10]  # YYYY-MM-DD
        max_date_str = date_rows[1][:10]

        min_date = datetime.fromisoformat(min_date_str)
        max_date = datetime.fromisoformat(max_date_str)

        print(f"  Date range: {min_date_str} → {max_date_str}")

        # Generate one snapshot per day
        current = min_date
        total = 0
        while current <= max_date:
            date_str = current.strftime("%Y-%m-%d")
            # as_of: use end-of-day so all articles published on this day
            # are included in the snapshot for this day.
            as_of = (current + timedelta(days=1)).isoformat()
            snap_count = _compute_and_write_snapshots(
                conn2,
                date_str=date_str,
                as_of=as_of,
            )
            total += snap_count
            current += timedelta(days=1)

        print(f"  Snapshots written: {total} ({total // 37} sources × "
              f"{(max_date - min_date).days + 1} days)")
    finally:
        conn2.close()

    print("\n── Done ──")
    print(f"  Clusters:   {a1_result['clusters']}")
    print(f"  Claims:     {a2_result['claims_extracted']}")
    print(f"  Snapshots:  total snapshots written")
    print(f"\nOpen the app to verify: http://localhost:5173")
    return 0


if __name__ == "__main__":
    sys.exit(main())
