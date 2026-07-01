#!/usr/bin/env python3
"""Backfill framing scores for articles that already have bodies.

Existing articles already went through Agent 2 (claim extraction) before
the framing scorer was added. This script scores them retroactively.

Usage:
  python scripts/backfill_framing.py [--delay 0.5] [--limit 100] [--db data/nn.db]
"""
import argparse
import asyncio
import json
import os
import sys
import time

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.connection import get_db
from db.framing import count_unscored, get_unscored_articles, insert_framing_scores
from db.framing import count_unllmed, get_unllmed_articles
from pipeline.framing import score_lexical, score_sentiment, score_llm_prompt
from pipeline.llm_client import LLMClient
from pipeline.provider_config import load_provider_config, get_provider_for_agent


def main():
    parser = argparse.ArgumentParser(description="Backfill framing scores")
    parser.add_argument("--delay", type=float, default=0.5,
                        help="Seconds between LLM calls (default: 0.5)")
    parser.add_argument("--limit", type=int, default=0,
                        help="Max articles to score (0 = all)")
    parser.add_argument("--db", default="data/nn.db",
                        help="Database path (default: data/nn.db)")
    parser.add_argument("--skip-llm", action="store_true",
                        help="Skip LLM scoring, only compute lexical + sentiment")
    parser.add_argument("--llm-only", action="store_true",
                        help="Only compute LLM scores for articles missing them")
    args = parser.parse_args()

    db_path = os.path.abspath(args.db)
    if not os.path.exists(db_path):
        print(f"Database not found: {db_path}")
        sys.exit(1)

    llm_only = args.llm_only

    conn = get_db(db_path)
    try:
        if llm_only:
            total = count_unllmed(conn)
        else:
            total = count_unscored(conn)
    finally:
        conn.close()

    if total == 0:
        if llm_only:
            print("All articles already have LLM scores. Nothing to do.")
        else:
            print("All articles already scored. Nothing to do.")
        return

    limit = args.limit if args.limit > 0 else total
    print(f"Articles to score: {min(total, limit)} of {total} unscored")

    # LLM client for framing-only prompts
    llm_client = None
    if not args.skip_llm:
        cfg = load_provider_config(os.path.join(os.path.dirname(__file__), "..", "config", "providers.json"))
        llm_provider = get_provider_for_agent(cfg, "agent2_llm")
        api_key = os.environ.get(f"{llm_provider['id'].upper()}_API_KEY", "")
        llm_client = LLMClient(llm_provider, api_key=api_key)
        print(f"Using LLM: {llm_provider['name']} ({llm_provider['model']})")

    scored = 0
    batch = []
    batch_size = 50

    while scored < limit:
        conn = get_db(db_path)
        try:
            if llm_only:
                articles = get_unllmed_articles(conn, limit=min(batch_size, limit - scored))
            else:
                articles = get_unscored_articles(conn, limit=min(batch_size, limit - scored))
        finally:
            conn.close()

        if not articles:
            break

        for art in articles:
            body = (art["body"] or "")[:2000]
            llm_score = None

            if llm_client is not None and body.strip():
                prompt = score_llm_prompt(body)
                try:
                    raw = asyncio.run(
                        llm_client.chat(
                            messages=[
                                {"role": "user", "content": prompt},
                            ],
                            response_format={"type": "json_object"},
                            temperature=0.0,
                            max_tokens=2000,
                        )
                    )
                    parsed = json.loads(raw)
                    score_val = parsed.get("score")
                    if score_val is not None:
                        llm_score = float(score_val)
                except Exception as e:
                    print(f"  LLM error for article {art['id']}: {e}")

            batch.append({
                "article_id": art["id"],
                "llm_score": llm_score,
                "lexical_score": 0.0 if llm_only else score_lexical(body),
                "sentiment_score": 0.0 if llm_only else score_sentiment(body),
            })
            scored += 1

            if llm_client is not None:
                time.sleep(args.delay)

        # Batch insert
        conn = get_db(db_path)
        try:
            for b in batch:
                if llm_only:
                    conn.execute(
                        "UPDATE article_framing SET llm_score = ? WHERE article_id = ?",
                        (b["llm_score"], b["article_id"]),
                    )
                    conn.commit()
                else:
                    insert_framing_scores(
                        conn,
                        article_id=b["article_id"],
                        llm_score=b["llm_score"],
                        lexical_score=b["lexical_score"],
                        sentiment_score=b["sentiment_score"],
                    )
        finally:
            conn.close()
        print(f"  Scored {scored}/{min(total, limit)} articles ({batch[-1]['article_id']})")
        batch = []

    print(f"\nDone. Scored {scored} articles.")
    if not args.skip_llm:
        print("LLM scores: check article_framing.llm_score for non-NULL values.")


if __name__ == "__main__":
    main()
