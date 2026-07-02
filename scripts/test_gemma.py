"""T0a: Test Gemma model IDs directly via llm_client.py"""
import os, sys, time, asyncio
from pathlib import Path
_PROJ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJ))
from dotenv import load_dotenv
load_dotenv(_PROJ / ".env")
from pipeline.llm_client import LLMClient

FW_KEY = os.environ.get("FIREWORKS_API_KEY", "")
if not FW_KEY:
    print("BLOCKED: FIREWORKS_API_KEY not set")
    sys.exit(1)

GAMMA_IDS = [
    "accounts/fireworks/models/gemma-4-31b-it",
    "accounts/fireworks/models/gemma-4-26b-a4b-it",
    "accounts/fireworks/models/gemma2-9b-it",
]

async def test_gemma(model_id):
    provider = {"id": "fireworks", "name": "Fireworks AI", "model": model_id, "amd": True}
    client = LLMClient(provider, api_key=FW_KEY)
    t0 = time.time()
    try:
        resp = await client.chat(
            messages=[{"role": "user", "content": 'Return JSON: {"status": "ok", "test": "gemma"}'}],
            response_format={"type": "json_object"},
            max_tokens=100,
        )
        elapsed = time.time() - t0
        print(f"  SUCCESS ({elapsed:.2f}s): {resp[:200]}")
        return True
    except Exception as e:
        elapsed = time.time() - t0
        msg = str(e)[:300]
        print(f"  FAILED ({elapsed:.2f}s): {msg}")
        return False

async def main():
    for mid in GAMMA_IDS:
        print(f"Testing: {mid}")
        ok = await test_gemma(mid)
        if ok:
            print(f"  => First working Gemma model: {mid}")
            break
        print()

asyncio.run(main())
print("\nDone.")
