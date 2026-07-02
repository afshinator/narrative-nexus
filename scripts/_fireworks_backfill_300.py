#!/usr/bin/env python3
"""Fireworks AI LLM backfill — 300 articles, no pause (credit-backed)."""
import os, asyncio, json, sqlite3, sys, time
from pathlib import Path
_PROJ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJ))
from dotenv import load_dotenv
load_dotenv(_PROJ / ".env")
import openai
from pipeline.framing import score_llm_prompt

API_KEY = os.environ.get("FIREWORKS_API_KEY", "")
if not API_KEY:
    print("FATAL: FIREWORKS_API_KEY not set in environment/.env")
    sys.exit(1)

DB = str(_PROJ / "data" / "nn.db")
BATCH = 300
DELAY = 3  # seconds between calls to stay under Fireworks rate limit
MODEL = "accounts/fireworks/models/deepseek-v4-flash"
BASE_URL = "https://api.fireworks.ai/inference/v1"

async def main():
    client = openai.AsyncOpenAI(
        base_url=BASE_URL,
        api_key=API_KEY,
        timeout=30.0,
    )

    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT a.id, a.title, a.body FROM article_framing af "
        "JOIN articles a ON a.id = af.article_id "
        "WHERE af.llm_score IS NULL ORDER BY a.id LIMIT ?",
        (BATCH,),
    ).fetchall()
    conn.close()

    print(f"Fireworks backfill: {len(rows)} articles, model={MODEL}")
    start_time = time.time()
    scored = 0
    failed = 0
    total_tokens = 0

    for i, row in enumerate(rows):
        if i > 0:
            await asyncio.sleep(DELAY)

        body = (row["body"] or "")[:2000]
        prompt = score_llm_prompt(body)

        for attempt in range(3):
            try:
                resp = await client.chat.completions.create(
                    model=MODEL,
                    messages=[{"role": "user", "content": prompt}],
                    response_format={"type": "json_object"},
                    temperature=0.0,
                    max_tokens=2000,
                )
                content = resp.choices[0].message.content or "{}"
                score_val = int(json.loads(content)["score"])
                tokens = resp.usage.total_tokens if resp.usage else 0
                total_tokens += tokens

                conn = sqlite3.connect(DB)
                conn.execute(
                    "UPDATE article_framing SET llm_score = ? WHERE article_id = ?",
                    (score_val, row["id"]),
                )
                conn.commit()
                conn.close()
                scored += 1

                if (scored) % 10 == 0 or scored == 1:
                    elapsed = time.time() - start_time
                    remaining = len(rows) - scored
                    rate = scored / elapsed if elapsed > 0 else 0
                    eta = remaining / rate if rate > 0 else 0
                    print(f"[{scored}/{len(rows)}] id={row['id']} score={score_val} "
                          f"elapsed={elapsed:.0f}s rate={rate:.1f}/s eta={eta:.0f}s tokens={total_tokens}")
                break  # success

            except Exception as e:
                err = str(e)
                if "429" in err and attempt < 2:
                    wait = (attempt + 1) * 10
                    print(f"  rate-limited, retrying in {wait}s (attempt {attempt+2}/3)...")
                    await asyncio.sleep(wait)
                    continue
                failed += 1
                print(f"[{scored}/{len(rows)}] FAIL id={row['id']}: {err[:100]}")
                break

    elapsed = time.time() - start_time
    print(f"\nDONE. {scored} scored, {failed} failed in {elapsed:.0f}s ({total_tokens} tokens)")

asyncio.run(main())
