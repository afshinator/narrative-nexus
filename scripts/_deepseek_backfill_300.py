#!/usr/bin/env python3
"""Quick DeepSeek LLM backfill — 300 articles with 10s pause."""
import os, asyncio, json, sqlite3, sys, time
from pathlib import Path
_PROJ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJ))
from dotenv import load_dotenv
load_dotenv(_PROJ / ".env")
import openai
from pipeline.framing import score_llm_prompt

API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
if not API_KEY:
    print("FATAL: DEEPSEEK_API_KEY not set in environment")
    sys.exit(1)

DB = str(_PROJ / "data" / "nn.db")
BATCH = 300
DELAY = 2  # seconds between calls (was 10 — DeepSeek has no rate limit issue)
MODEL = "deepseek-chat"

async def main():
    client = openai.AsyncOpenAI(
        base_url="https://api.deepseek.com/v1",
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

    print(f"Backfilling {len(rows)} articles with {DELAY}s pause...")
    start_time = time.time()
    scored = 0
    failed = 0
    total_tokens = 0

    for i, row in enumerate(rows):
        if i > 0:
            await asyncio.sleep(DELAY)

        body = (row["body"] or "")[:2000]
        prompt = score_llm_prompt(body)

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
                eta = (elapsed / scored) * remaining if scored > 0 else 0
                print(f"[{scored}/{len(rows)}] id={row['id']} score={score_val} "
                      f"elapsed={elapsed:.0f}s eta={eta:.0f}s tokens={total_tokens}")

        except Exception as e:
            failed += 1
            err = str(e)[:100]
            print(f"[{scored}/{len(rows)}] FAIL id={row['id']}: {err}")

    elapsed = time.time() - start_time
    print(f"\nDONE. {scored} scored, {failed} failed in {elapsed:.0f}s ({total_tokens} tokens)")

asyncio.run(main())
