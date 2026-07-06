#!/usr/bin/env python3
"""R2.9c — Run Agent 2 on articles 940-945 only."""
import asyncio
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.connection import get_db
from pipeline.provider_config import load_provider_config, get_provider_for_agent
from pipeline.agent2_forensic import ForensicExtractionAgent

DB = "data/demo/demo.db"
ARTICLE_IDS = [940, 941, 942, 943, 944, 945]

async def main():
    cfg_path = os.path.join(os.path.dirname(__file__), "..", "config", "providers.json")
    cfg = load_provider_config(cfg_path)
    a2_provider = get_provider_for_agent(cfg, "agent2_llm")
    a2_key = os.environ.get(f"{a2_provider['id'].upper()}_API_KEY", "")

    print(f"Agent 2 provider: {a2_provider['name']} ({a2_provider['model']})")
    print(f"API key present: {bool(a2_key)}")
    print(f"Target articles: {ARTICLE_IDS}")

    # Verify articles exist with bodies
    conn = get_db(DB)
    rows = conn.execute(
        f"SELECT id, title, length(body) as blen FROM articles WHERE id IN ({','.join('?'*len(ARTICLE_IDS))})",
        ARTICLE_IDS,
    ).fetchall()
    conn.close()
    print(f"\nArticles found: {len(rows)}")
    for r in rows:
        print(f"  id={r['id']}: {r['title'][:80]}... ({r['blen']} chars)")

    # Create a temporary cluster for these articles
    conn = get_db(DB)
    cursor = conn.execute("INSERT INTO clusters (vertical, title) VALUES (?, ?)",
                          ("geopolitics", "R2.9c temporary — articles 940-945"))
    temp_cluster_id = cursor.lastrowid
    conn.commit()
    conn.close()
    print(f"\nTemporary cluster created: id={temp_cluster_id}")

    article_map = {aid: temp_cluster_id for aid in ARTICLE_IDS}

    # Run Agent 2
    agent2 = ForensicExtractionAgent(
        db_path=DB,
        llm_provider=a2_provider,
        api_key=a2_key,
    )
    result = await agent2.run(article_map=article_map)
    print(f"\nAgent 2 result: {result}")

    # Verify claims extracted
    conn = get_db(DB)
    for aid in ARTICLE_IDS:
        claims = conn.execute(
            "SELECT id, text FROM claims WHERE article_id = ?", (aid,)
        ).fetchall()
        print(f"\nArticle {aid}: {len(claims)} claims")
        for i, c in enumerate(claims[:2]):
            print(f"  [{c['id']}] {c['text'][:120]}")
    conn.close()

    return 0

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
