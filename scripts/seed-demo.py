#!/usr/bin/env python3
"""Seed script — populates the database with 90 days of historical data.

Usage:
    python scripts/seed-demo.py --articles articles.json --db /data/narrative-nexus.db

Per ADR-0002, this script shares code paths with the live pipeline.
It fetches article URLs via newspaper4k, runs them through the pipeline
agents, and writes 90 days of data to the database.

This is a scaffold stub — real pipeline agent calls will be wired in
when the pipeline is implemented.
"""

import argparse
import sys


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Seed the Narrative Nexus database with 90 days of historical data.",
    )
    parser.add_argument(
        "--articles",
        required=True,
        help="Path to JSON file containing article URLs organized by story",
    )
    parser.add_argument(
        "--db",
        default="/data/narrative-nexus.db",
        help="Path to SQLite database file (default: /data/narrative-nexus.db)",
    )
    return parser.parse_args(argv)


def main() -> int:
    args = parse_args()
    print(f"Seed script scaffold ready.")
    print(f"  Articles: {args.articles}")
    print(f"  Database: {args.db}")
    print()
    print("Pipeline calls will be wired when agents are implemented.")
    print("Placeholder — no data written.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
