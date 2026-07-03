#!/usr/bin/env python3
"""Y3: 8-article pairwise cosine similarity with CLEANED input + 1000-char window + nomic."""
import asyncio, os, sqlite3, sys
import numpy as np
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except ImportError:
    pass

import openai
from pipeline.cleaner import get_embedding_input

ARTICLES = [
    (118, "US politics"),
    (453, "Middle East"),
    (186, "European weather"),
    (157, "Tech/AI"),
    (1748, "Sports"),
    (1630, "Economics"),
    (106, "Natural disaster"),
    (486, "Science/Tech"),
]

conn = sqlite3.connect("file:data/nn.db?mode=ro", uri=True)
conn.row_factory = sqlite3.Row

texts = []
labels = []
for aid, label in ARTICLES:
    r = conn.execute("SELECT title, body FROM articles WHERE id=?", (aid,)).fetchone()
    if r:
        texts.append(get_embedding_input(r["title"], r["body"] or "", max_body_chars=1000))
        labels.append(label)
conn.close()

# Show what changed for the worst case (article 157)
print("=== Input comparison: Article 157 (Anthropic) ===")
conn3 = sqlite3.connect("file:data/nn.db?mode=ro", uri=True)
conn3.row_factory = sqlite3.Row
r2 = conn3.execute("SELECT title, body FROM articles WHERE id=157").fetchone()
conn3.close()
old_input = f"{r2['title'] or ''} {(r2['body'] or '')[:200]}"
new_input = get_embedding_input(r2["title"], r2["body"] or "", max_body_chars=1000)
print(f"  OLD (200 chars, no cleaning): {len(old_input)} chars")
print(f"    {old_input[:200]}")
print(f"  NEW (1000 chars, cleaned): {len(new_input)} chars")
print(f"    {new_input[:200]}")
print()

key = os.environ.get("FIREWORKS_API_KEY", "")
client = openai.AsyncOpenAI(base_url="https://api.fireworks.ai/inference/v1", api_key=key, timeout=30)


async def embed_nomic(inputs):
    resp = await client.embeddings.create(
        model="nomic-ai/nomic-embed-text-v1.5", input=inputs,
    )
    return np.array([d.embedding for d in resp.data], dtype=np.float64)


def cosine_matrix(vectors):
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms[norms == 0] = 1
    return (vectors / norms) @ (vectors / norms).T


async def main():
    print("=" * 70)
    print("Y3: NOMIC with CLEANED input (1000-char window, boilerplate stripped)")
    print("=" * 70)

    vecs = await embed_nomic(texts)
    sim = cosine_matrix(vecs)

    short = [l[:8] for l in labels]
    print(f"{'':>20s}", end="")
    for s in short:
        print(f"{s:>9s}", end="")
    print()
    for i, label in enumerate(labels):
        print(f"{label:20s}", end="")
        for j in range(len(labels)):
            if i == j:
                print(f"{'--':>9s}", end="")
            else:
                print(f"{sim[i][j]:9.4f}", end="")
        print()

    off = [sim[i][j] for i in range(len(labels)) for j in range(len(labels)) if i != j]
    print(f"\n  Off-diagonal: mean={np.mean(off):.4f}, min={np.min(off):.4f}, max={np.max(off):.4f}")

    # Comparison
    print("\n" + "=" * 70)
    print("COMPARISON: X2 (old, 200 chars) vs Y3 (new, 1000 chars + cleaned)")
    print("=" * 70)
    print(f"{'Metric':20s} {'X2 (old)':>10s} {'Y3 (new)':>10s} {'Delta':>10s}")
    print(f"{'Mean off-diag':20s} {'0.5415':>10s} {np.mean(off):10.4f} {np.mean(off)-0.5415:+10.4f}")
    print(f"{'Max off-diag':20s} {'0.8222':>10s} {np.max(off):10.4f} {np.max(off)-0.8222:+10.4f}")
    print(f"{'Min off-diag':20s} {'0.4624':>10s} {np.min(off):10.4f} {np.min(off)-0.4624:+10.4f}")

    # Check specific topic-different pairs
    pairs = [
        ("Venezuela vs Anthropic", 6, 3),
        ("Sports vs Middle East", 4, 1),
        ("Weather vs Economics", 2, 5),
    ]
    print("\nTopic-different pair similarities:")
    for name, i, j in pairs:
        print(f"  {name}: {sim[i][j]:.4f}")

    # Same-topic pair
    print(f"\nSame-topic (Anthropic vs Anthropic): {sim[3][7]:.4f}")

    if np.mean(off) <= 0.44:
        print("\n✓ MEAN DROP >= 0.10 — SUCCESS")
    elif np.mean(off) <= 0.49:
        print(f"\n⚠ MEAN DROP = {0.5415 - np.mean(off):.4f} — MODERATE improvement")
    else:
        print("\n✗ DROP < 0.05 — STOP AND REPORT")


asyncio.run(main())
