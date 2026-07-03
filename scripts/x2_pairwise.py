#!/usr/bin/env python3
"""X2/X3: 8-article pairwise cosine similarity matrix — nomic vs BGE."""
import asyncio, os, sqlite3, sys
import numpy as np
from pathlib import Path

# Load .env
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except ImportError:
    pass

import openai

# 8 articles from clearly different topics
# US politics, Middle East conflict, European weather, tech/AI, sports,
# economics/markets, natural disaster, science
ARTICLES = [
    (118, "US politics — Trump election order blocked"),
    (453, "Middle East — Lebanon Israel Hezbollah deal"),
    (186, "European weather — Heat dome Europe"),
    (157, "Tech/AI — Anthropic AI export controls"),
    (1748, "Sports — World Cup 2026 first round"),
    (1630, "Economics — China WTO EU trade concerns"),
    (106, "Natural disaster — Venezuela earthquakes"),
    (486, "Science/Tech — Anthropic Mythos export ban lifted"),
]

conn = sqlite3.connect("file:data/nn.db?mode=ro", uri=True)
conn.row_factory = sqlite3.Row

texts = []
labels = []
for aid, label in ARTICLES:
    r = conn.execute("SELECT title, body FROM articles WHERE id=?", (aid,)).fetchone()
    if r:
        # Use the EXACT same input as Agent 1
        input_str = f"{r['title'] or ''} {r['body'][:200] if r['body'] else ''}"
        texts.append(input_str)
        labels.append(label)
conn.close()

print(f"Loaded {len(texts)} articles\n")

key = os.environ.get("FIREWORKS_API_KEY", "")
client = openai.AsyncOpenAI(
    base_url="https://api.fireworks.ai/inference/v1",
    api_key=key, timeout=30,
)


async def embed_with(model_id, prefix=""):
    """Embed texts with a given model."""
    if prefix:
        inputs = [f"{prefix}{t}" for t in texts]
    else:
        inputs = texts
    resp = await client.embeddings.create(model=model_id, input=inputs)
    return np.array([d.embedding for d in resp.data], dtype=np.float64)


def cosine_matrix(vectors):
    """Compute pairwise cosine similarity matrix."""
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms[norms == 0] = 1
    normalized = vectors / norms
    return normalized @ normalized.T


async def main():
    # X2: Nomic, no prefix
    print("=" * 70)
    print("X2: NOMIC (nomic-ai/nomic-embed-text-v1.5, no prefix)")
    print("=" * 70)
    nomic_vecs = await embed_with("nomic-ai/nomic-embed-text-v1.5")
    nomic_sim = cosine_matrix(nomic_vecs)

    # Print header
    short = [l.split(" — ")[0] for l in labels]
    print(f"{'':>25s}", end="")
    for s in short:
        print(f"{s[:8]:>9s}", end="")
    print()
    for i, (label, vec) in enumerate(zip(labels, nomic_vecs)):
        print(f"{label[:25]:25s}", end="")
        for j in range(len(labels)):
            if i == j:
                print(f"{'--':>9s}", end="")
            else:
                print(f"{nomic_sim[i][j]:9.4f}", end="")
        print()

    off_diag = [nomic_sim[i][j] for i in range(len(labels)) for j in range(len(labels)) if i != j]
    print(f"\n  Off-diagonal: mean={np.mean(off_diag):.4f}, min={np.min(off_diag):.4f}, max={np.max(off_diag):.4f}")

    # X3: BGE, no prefix
    print("\n" + "=" * 70)
    print("X3: BGE (BAAI/bge-base-en-v1.5, no prefix)")
    print("=" * 70)
    bge_vecs = await embed_with("BAAI/bge-base-en-v1.5")
    bge_sim = cosine_matrix(bge_vecs)

    print(f"{'':>25s}", end="")
    for s in short:
        print(f"{s[:8]:>9s}", end="")
    print()
    for i, (label, vec) in enumerate(zip(labels, bge_vecs)):
        print(f"{label[:25]:25s}", end="")
        for j in range(len(labels)):
            if i == j:
                print(f"{'--':>9s}", end="")
            else:
                print(f"{bge_sim[i][j]:9.4f}", end="")
        print()

    off_diag2 = [bge_sim[i][j] for i in range(len(labels)) for j in range(len(labels)) if i != j]
    print(f"\n  Off-diagonal: mean={np.mean(off_diag2):.4f}, min={np.min(off_diag2):.4f}, max={np.max(off_diag2):.4f}")

    # Comparison
    print("\n" + "=" * 70)
    print("COMPARISON")
    print("=" * 70)
    print(f"{'Metric':20s} {'Nomic':>10s} {'BGE':>10s}")
    print(f"{'Mean off-diag':20s} {np.mean(off_diag):10.4f} {np.mean(off_diag2):10.4f}")
    print(f"{'Max off-diag':20s} {np.max(off_diag):10.4f} {np.max(off_diag2):10.4f}")
    print(f"{'Min off-diag':20s} {np.min(off_diag):10.4f} {np.min(off_diag2):10.4f}")


asyncio.run(main())
