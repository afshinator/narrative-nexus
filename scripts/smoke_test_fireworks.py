"""T1: Fireworks smoke tests — T1b through T1e."""
import os, sys, json, time
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

FW_KEY = os.environ.get("FIREWORKS_API_KEY", "")
if not FW_KEY:
    print("BLOCKED: FIREWORKS_API_KEY not set")
    sys.exit(1)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from pipeline.llm_client import LLMClient
from pipeline.embedding_client import EmbeddingClient

# ── T1b: List available models ──────────────────────────────────────────
print("=== T1b: Available Fireworks models ===")
import urllib.request, json as jmod
req = urllib.request.Request(
    "https://api.fireworks.ai/inference/v1/models",
    headers={"Authorization": f"Bearer {FW_KEY}"}
)
resp = jmod.loads(urllib.request.urlopen(req, timeout=15).read())
models = resp.get("data", [])

gemma_models = [m["id"] for m in models if "gemma" in m["id"].lower()]
deepseek_models = [m["id"] for m in models if "deepseek" in m["id"].lower()]
nomic_models = [m["id"] for m in models if "nomic" in m["id"].lower()]

print(f"Total models: {len(models)}")
print(f"Gemma chat models: {gemma_models}")
print(f"DeepSeek models: {deepseek_models}")
print(f"Nomic embedding models: {nomic_models}")

# ── T1c: Chat smoke test (current default model) ────────────────────────
print("\n=== T1c: Chat smoke test (deepseek-v4-pro) ===")
import asyncio

async def chat_test(model_id):
    provider = {"id": "fireworks", "name": "Fireworks AI", "model": model_id, "amd": True}
    client = LLMClient(provider, api_key=FW_KEY)
    t0 = time.time()
    try:
        resp = await client.chat(
            messages=[{"role": "user", "content": "Return JSON: {\"status\": \"ok\", \"number\": 42}"}],
            response_format={"type": "json_object"},
            max_tokens=100,
        )
        elapsed = time.time() - t0
        print(f"  Model: {model_id}")
        print(f"  Latency: {elapsed:.2f}s")
        print(f"  Response: {resp[:200]}")
    except Exception as e:
        elapsed = time.time() - t0
        print(f"  Model: {model_id}")
        print(f"  Latency: {elapsed:.2f}s")
        print(f"  ERROR: {e}")

asyncio.run(chat_test("accounts/fireworks/models/deepseek-v4-pro"))

# ── T1d: Gemma chat test ───────────────────────────────────────────────
print("\n=== T1d: Gemma chat smoke test ===")
gemma_chat = [m for m in gemma_models if "chat" in m.lower() or "instruct" in m.lower()]
if not gemma_chat:
    gemma_chat = gemma_models[:1] if gemma_models else []
if gemma_chat:
    asyncio.run(chat_test(gemma_chat[0]))
else:
    print("  No Gemma models found in catalog")

# ── T1e: Embeddings smoke test ─────────────────────────────────────────
print("\n=== T1e: Embeddings smoke test (nomic) ===")
async def embed_test():
    provider = {"id": "fireworks", "name": "Fireworks AI", "model": "nomic-ai/nomic-embed-text-v1.5", "amd": True}
    client = EmbeddingClient(provider, api_key=FW_KEY)
    t0 = time.time()
    try:
        vecs = await client.embed(["hello world", "goodbye world", "test embedding"])
        elapsed = time.time() - t0
        print(f"  Latency: {elapsed:.2f}s")
        print(f"  Vectors returned: {len(vecs)}")
        print(f"  Dimensionality: {len(vecs[0])}")
    except Exception as e:
        elapsed = time.time() - t0
        print(f"  Latency: {elapsed:.2f}s")
        print(f"  ERROR: {e}")

asyncio.run(embed_test())
print("\nDone.")
