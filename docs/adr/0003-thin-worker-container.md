# ADR-0003: Thin Worker Container Architecture

**Status:** Accepted

## Context

Docker Compose must define three services: app, worker, db (REQ-102-104). The worker container requires AMD GPU via ROCm for sentence-transformer embeddings. The app container handles everything else: scraping, Fireworks API calls, consensus math, reputation scoring, SQLite, static file serving.

The spec requires all Fireworks API calls to originate from the app container (REQ-106) and no GPU access in the app container (REQ-108). Consensus math and reputation scoring run on CPU (REQ-019).

## Decision

The worker container has a **single responsibility**: sentence-transformer embeddings on AMD GPU via ROCm. The app sends raw article text to the worker over HTTP and receives embeddings back. Everything else runs in the app container.

The worker is deliberately thin — a GPU-accelerated embedding service and nothing else. On the Pipeline Flow page, the worker renders as a distinct node labeled "AMD GPU Pod (sentence-transformers)".

## Consequences

**Positive:**
- Cleanly satisfies AMD GPU requirement (worker on ROCm) while keeping app GPU-free
- Worker is easy to test in isolation (HTTP API with well-defined input/output)
- Worker image is small (sentence-transformers + ROCm runtime, no web framework beyond a lightweight HTTP server)
- Pipeline visualization naturally shows the split, making the AMD integration visible to judges

**Negative:**
- Adds a network hop for embedding requests (latency, but negligible at hackathon scale)
- Requires a health-check / retry mechanism if the worker is unavailable
- Worker cannot run on systems without AMD GPU (local dev requires CPU fallback)

## Alternatives Considered

1. **Embeddings in the app container** — simpler architecture but loses the AMD GPU narrative for judges. Also violates REQ-108 implicitly since the app container doesn't need a GPU.
2. **BERTopic clustering also on the worker** — clustering is CPU-bound and doesn't benefit from GPU. Adds unnecessary complexity to the worker.
3. **All four agents as separate containers** — over-engineered for hackathon scale. Three services is the right level of granularity.
