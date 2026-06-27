#!/usr/bin/env python3
"""Survey script — measures article body extraction yield across the panel.

For each native-RSS source, scrapes the first N articles and attempts body
extraction via newspaper4k. Reports per-source success rate, body length
distribution, and extraction timing. Google News sources are skipped (already
known BODY_UNAVAILABLE). FeedBurner sources are included (they redirect to
native content).

Answers: what % of articles produce usable body text? Which sources are
paywalled? How long does extraction take? Is the pipeline viable?

Usage:
    python scripts/survey-extraction.py --polls 1 --sample 5
    python scripts/survey-extraction.py --polls 3 --sample 10 --output extraction.json
    python scripts/survey-extraction.py --polls 1 --sample 5 --output - | jq .per_source

Follows the same CLI + JSON convention as survey-sources.py (PoC 1).
"""
import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Ensure project root is on sys.path for pipeline imports
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from pipeline.scraper import RSSPoller, FEED_CONFIG
from pipeline.extractor import ArticleExtractor


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Survey article body extraction yield across the source panel.",
    )
    parser.add_argument(
        "--polls",
        type=int,
        default=1,
        help="Number of RSS polls to run before extracting (default: 1)",
    )
    parser.add_argument(
        "--sample",
        type=int,
        default=5,
        help="Articles to extract per source per poll (default: 5)",
    )
    parser.add_argument(
        "--output",
        default="extraction.json",
        help="Output file path, or '-' for stdout (default: extraction.json)",
    )
    return parser.parse_args(argv)


def should_extract(cfg: dict) -> bool:
    """Only extract from sources where body text is possible.

    Google News sources are metadata-only (BODY_UNAVAILABLE by definition).
    Native and FeedBurner sources may yield body text.
    """
    return cfg["type"] in ("native", "feedburner")


def extract_sample(
    poller: RSSPoller,
    extractor: ArticleExtractor,
    sample_size: int,
) -> dict:
    """Poll all sources once, sample N articles from each extractable source,
    and attempt body extraction.

    Returns per-source extraction stats. Google News sources are included
    in the output for completeness but marked as skipped.
    """
    per_source: dict[str, dict] = {}
    total_attempted = 0
    total_extracted = 0
    total_body_chars = 0

    for name, cfg in FEED_CONFIG.items():
        source_start = time.monotonic()

        if not should_extract(cfg):
            # Google News — metadata only, skip extraction
            entries = list(poller.fetch(name))
            per_source[name] = {
                "type": cfg["type"],
                "tier": cfg["tier"],
                "domain": cfg["domain"],
                "articles_in_feed": len(entries),
                "skipped": True,
                "reason": "google_news_metadata_only",
            }
            continue

        # Fetch articles for this source, sample the first N
        entries = list(poller.fetch(name))
        sample = entries[:sample_size]
        source_attempted = 0
        source_extracted = 0
        source_body_chars = 0
        source_extract_ms = 0
        articles: list[dict] = []

        for entry in sample:
            url = entry.get("url", "")
            if not url:
                continue

            source_attempted += 1
            extract_start = time.monotonic()
            body, status = extractor.extract(url)
            extract_elapsed = round((time.monotonic() - extract_start) * 1000)
            source_extract_ms += extract_elapsed

            body_len = len(body)
            extracted = status == "AVAILABLE" and body_len > 0

            articles.append({
                "title": entry.get("title", "")[:80],
                "url": url[:120],
                "body_chars": body_len,
                "extracted": extracted,
                "extract_ms": extract_elapsed,
            })

            if extracted:
                source_extracted += 1
                source_body_chars += body_len

        per_source[name] = {
            "type": cfg["type"],
            "tier": cfg["tier"],
            "domain": cfg["domain"],
            "articles_in_feed": len(entries),
            "sampled": source_attempted,
            "extracted": source_extracted,
            "rate_pct": round(source_extracted / source_attempted * 100, 1)
            if source_attempted > 0
            else None,
            "avg_body_chars": round(source_body_chars / source_extracted)
            if source_extracted > 0
            else None,
            "avg_extract_ms": round(source_extract_ms / source_attempted)
            if source_attempted > 0
            else None,
            "total_extract_ms": source_extract_ms,
            "articles": articles,
        }

        total_attempted += source_attempted
        total_extracted += source_extracted
        total_body_chars += source_body_chars

    return {
        "attempted": total_attempted,
        "extracted": total_extracted,
        "rate_pct": round(total_extracted / total_attempted * 100, 1)
        if total_attempted > 0
        else None,
        "avg_body_chars": round(total_body_chars / total_extracted)
        if total_extracted > 0
        else None,
        "per_source": per_source,
    }


def main() -> int:
    args = parse_args()

    # ── Header ──────────────────────────────────────────────────────────
    started = datetime.now(timezone.utc).isoformat()
    extractable = sum(1 for cfg in FEED_CONFIG.values() if should_extract(cfg))
    print(
        f"Extraction survey: {args.polls} poll(s), "
        f"{args.sample} articles per source, "
        f"{extractable} extractable sources",
        file=sys.stderr,
    )
    print(f"Started: {started}", file=sys.stderr)
    print(file=sys.stderr)

    # ── Poll + Extract ──────────────────────────────────────────────────
    poller = RSSPoller()
    extractor = ArticleExtractor()
    polls: list[dict] = []

    for i in range(args.polls):
        print(
            f"  Poll {i + 1}/{args.polls} — scraping + extracting ...",
            end=" ",
            flush=True,
            file=sys.stderr,
        )
        result = extract_sample(poller, extractor, args.sample)
        polls.append(result)
        print(
            f"{result['extracted']}/{result['attempted']} extracted "
            f"({result['rate_pct']}%)",
            file=sys.stderr,
        )

    # ── Aggregate across polls ──────────────────────────────────────────
    # Collect all source names
    all_sources: set[str] = set()
    for poll in polls:
        all_sources.update(poll["per_source"].keys())

    per_source_agg: dict[str, dict] = {}
    for name in sorted(all_sources):
        attempted = 0
        extracted = 0
        body_chars = 0
        extract_ms = 0

        for poll in polls:
            src = poll["per_source"].get(name, {})
            attempted += src.get("sampled", 0)
            extracted += src.get("extracted", 0)
            if src.get("avg_body_chars"):
                body_chars += src["avg_body_chars"] * src.get("extracted", 0)
            extract_ms += src.get("total_extract_ms", 0)

        per_source_agg[name] = {
            "type": polls[0]["per_source"].get(name, {}).get("type"),
            "tier": polls[0]["per_source"].get(name, {}).get("tier"),
            "domain": polls[0]["per_source"].get(name, {}).get("domain"),
            "skipped": polls[0]["per_source"].get(name, {}).get("skipped", False),
            "attempted": attempted,
            "extracted": extracted,
            "rate_pct": round(extracted / attempted * 100, 1) if attempted > 0 else None,
            "avg_body_chars": round(body_chars / extracted) if extracted > 0 else None,
            "avg_extract_ms": round(extract_ms / attempted) if attempted > 0 else None,
        }

    total_att = sum(s["attempted"] for s in per_source_agg.values())
    total_ext = sum(s["extracted"] for s in per_source_agg.values())

    # ── Report ──────────────────────────────────────────────────────────
    report = {
        "polls": args.polls,
        "sample_per_source": args.sample,
        "started": started,
        "finished": datetime.now(timezone.utc).isoformat(),
        "total_attempted": total_att,
        "total_extracted": total_ext,
        "extraction_rate_pct": round(total_ext / total_att * 100, 1)
        if total_att > 0
        else None,
        "per_poll": [
            {
                "index": i,
                "attempted": p["attempted"],
                "extracted": p["extracted"],
                "rate_pct": p["rate_pct"],
            }
            for i, p in enumerate(polls)
        ],
        "per_source": per_source_agg,
    }

    if args.output == "-":
        json.dump(report, sys.stdout, indent=2)
        sys.stdout.write("\n")
    else:
        with open(args.output, "w") as f:
            json.dump(report, f, indent=2)
        print(f"\nWrote {args.output}", file=sys.stderr)

    # ── Summary to stderr ───────────────────────────────────────────────
    print(f"\nTotal: {total_ext}/{total_att} extracted ({report['extraction_rate_pct']}%)", file=sys.stderr)
    print("By tier:", file=sys.stderr)
    by_tier: dict[int, dict] = {}
    for name, s in per_source_agg.items():
        t = s.get("tier", 0)
        if t not in by_tier:
            by_tier[t] = {"att": 0, "ext": 0}
        by_tier[t]["att"] += s["attempted"]
        by_tier[t]["ext"] += s["extracted"]
    for t in sorted(by_tier):
        d = by_tier[t]
        rate = round(d["ext"] / d["att"] * 100, 1) if d["att"] > 0 else 0
        print(f"  Tier {t}: {d['ext']}/{d['att']} ({rate}%)", file=sys.stderr)

    # Zero-extraction sources are noteworthy
    zeros = [n for n, s in per_source_agg.items() if not s.get("skipped") and s["attempted"] > 0 and s["extracted"] == 0]
    if zeros:
        print(f"\nZero extraction: {', '.join(zeros)}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
