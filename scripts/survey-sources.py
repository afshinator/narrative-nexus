#!/usr/bin/env python3
"""Survey script — measures article distribution across the 20-source panel.

Runs N consecutive RSS polls and reports per-source article counts, timing,
and feed types. No database writes. No pipeline execution. Pure data collection.

Usage:
    python scripts/survey-sources.py --polls 3
    python scripts/survey-sources.py --polls 5 --output survey.json
    python scripts/survey-sources.py --polls 1 --output - | jq .aggregates

Output is JSON — designed as the first in a family of PoC survey scripts
following the same CLI + JSON convention. Future scripts can pipe into this
format for analysis or comparison.

ADR-0002 compliance: one-shot CLI, shares code paths with live pipeline
(imports RSSPoller and FEED_CONFIG directly — no duplicate feed definitions).
"""
import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Ensure project root is on sys.path so we can import pipeline modules
# (needed when running as a standalone script, not via pytest)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from pipeline.scraper import RSSPoller, FEED_CONFIG


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Survey article distribution across the Narrative Nexus source panel.",
    )
    parser.add_argument(
        "--polls",
        type=int,
        default=3,
        help="Number of consecutive RSS polls to run (default: 3)",
    )
    parser.add_argument(
        "--output",
        default="survey.json",
        help="Output file path, or '-' for stdout (default: survey.json)",
    )
    return parser.parse_args(argv)


def poll_all(poller: RSSPoller) -> dict:
    """Run one poll across all 20 sources.

    Returns a dict with per-source article counts, per-source timing,
    and poll-level totals. Each source is polled sequentially to avoid
    rate-limiting and to capture per-feed performance data.
    """
    per_source: dict[str, dict] = {}
    total_articles = 0
    poll_start = time.monotonic()

    for name, cfg in FEED_CONFIG.items():
        source_start = time.monotonic()

        try:
            # feedparser.parse() is forgiving — returns empty entries on
            # network failure rather than raising. We count what we get.
            entries = list(poller.fetch(name))

        except Exception as exc:
            # Feedparser almost never raises, but network stack can
            # (DNS failure, TLS error). Log and move on.
            per_source[name] = {
                "count": 0,
                "elapsed_ms": round((time.monotonic() - source_start) * 1000),
                "type": cfg["type"],
                "tier": cfg["tier"],
                "domain": cfg["domain"],
                "error": str(exc),
            }
            continue

        elapsed = round((time.monotonic() - source_start) * 1000)
        per_source[name] = {
            "count": len(entries),
            "elapsed_ms": elapsed,
            "type": cfg["type"],
            "tier": cfg["tier"],
            "domain": cfg["domain"],
        }
        total_articles += len(entries)

    return {
        "total": total_articles,
        "elapsed_ms": round((time.monotonic() - poll_start) * 1000),
        "sources": per_source,
    }


def compute_aggregates(polls: list[dict]) -> dict:
    """Compute per-source aggregate stats across all polls.

    For each source: total articles, mean per poll, stddev, min, max.
    Only computed for sources that appeared at least once — sources
    with zero articles across all polls are still included (count=0).
    """
    # Collect all source names from the first poll's sources dict
    all_sources: set[str] = set()
    for poll in polls:
        all_sources.update(poll["sources"].keys())

    aggregates: dict[str, dict] = {}
    for name in sorted(all_sources):
        counts = []
        type_ = None
        tier = None
        domain = None
        errors = 0

        for poll in polls:
            src = poll["sources"].get(name, {})
            counts.append(src.get("count", 0))
            type_ = type_ or src.get("type")
            tier = tier or src.get("tier")
            domain = domain or src.get("domain")
            if "error" in src:
                errors += 1

        n = len(counts)
        mean = sum(counts) / n
        variance = sum((c - mean) ** 2 for c in counts) / n

        aggregates[name] = {
            "total": sum(counts),
            "mean_per_poll": round(mean, 1),
            "stddev": round(variance ** 0.5, 1),
            "min": min(counts),
            "max": max(counts),
            "type": type_,
            "tier": tier,
            "domain": domain,
        }
        if errors > 0:
            aggregates[name]["polls_with_errors"] = errors

    return aggregates


def main() -> int:
    args = parse_args()

    # ── Header ──────────────────────────────────────────────────────────
    # Print a human-readable header to stderr so it doesn't pollute JSON
    # output when using --output - (stdout).
    started = datetime.now(timezone.utc).isoformat()
    print(f"Survey: {args.polls} poll(s) across {len(FEED_CONFIG)} sources", file=sys.stderr)
    print(f"Started: {started}", file=sys.stderr)
    print(file=sys.stderr)

    # ── Polling ──────────────────────────────────────────────────────────
    poller = RSSPoller()
    polls: list[dict] = []

    for i in range(args.polls):
        print(f"  Poll {i + 1}/{args.polls} ...", end=" ", flush=True, file=sys.stderr)
        result = poll_all(poller)
        polls.append(result)
        print(
            f"{result['total']} articles in {result['elapsed_ms']}ms",
            file=sys.stderr,
        )

    # ── Report ──────────────────────────────────────────────────────────
    report = {
        "polls": args.polls,
        "started": started,
        "finished": datetime.now(timezone.utc).isoformat(),
        "total_articles": sum(p["total"] for p in polls),
        "per_poll": [
            {
                "index": i,
                "elapsed_ms": p["elapsed_ms"],
                "total": p["total"],
                "sources": p["sources"],
            }
            for i, p in enumerate(polls)
        ],
        "aggregates": compute_aggregates(polls),
    }

    if args.output == "-":
        json.dump(report, sys.stdout, indent=2)
        sys.stdout.write("\n")
    else:
        with open(args.output, "w") as f:
            json.dump(report, f, indent=2)
        print(f"\nWrote {args.output}", file=sys.stderr)

    # ── Summary to stderr ───────────────────────────────────────────────
    aggs = report["aggregates"]
    by_tier: dict[int, int] = {}
    by_type: dict[str, int] = {}
    for src in aggs.values():
        t = src.get("tier", 0)
        by_tier[t] = by_tier.get(t, 0) + src["total"]
        ft = src.get("type", "unknown")
        by_type[ft] = by_type.get(ft, 0) + src["total"]

    print(f"\nTotal: {report['total_articles']} articles", file=sys.stderr)
    print("By tier:", file=sys.stderr)
    for t in sorted(by_tier):
        print(f"  Tier {t}: {by_tier[t]}", file=sys.stderr)
    print("By feed type:", file=sys.stderr)
    for ft in sorted(by_type):
        print(f"  {ft}: {by_type[ft]}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
