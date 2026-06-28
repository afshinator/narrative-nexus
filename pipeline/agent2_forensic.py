"""Forensic Extraction Agent — LLM-powered claim extraction.

Reads articles from the database, sends each to an LLM with a structured
extraction prompt, parses the JSON response, and inserts atomic factual
claims into the database.

Uses response_format={"type": "json_object"} for guaranteed valid JSON.
Temperature 0.0 for deterministic extraction.

ponytail: Single-pass extraction (neutralization + claims in one call).
ponytail: Claims from malformed JSON are silently skipped.
"""

import json
import sqlite3
from typing import Any

from pipeline.llm_client import LLMClient
from pipeline.base_agent import BasePipelineAgent
from db.connection import get_db
from db.claims import insert_claim
from db.claim_sources import add_claim_source

# ── Extraction prompt ────────────────────────────────────────────────────
# One system message defining the task, then the article body as user message.

EXTRACTION_SYSTEM_PROMPT = """You are a forensic claim extractor. Your job is to read news articles and extract every atomic, verifiable factual claim they make.

Rules:
1. Strip editorial framing — remove adjectives, hedges, and passive-voice attribution
2. Each claim must be a single self-contained statement that CAN be verified or falsified
3. Claims must be atomic — one fact per claim, not compound statements
4. Do NOT summarize, paraphrase, or add commentary
5. Do NOT include opinions, predictions, or value judgments
6. Include named entities (people, organizations, locations) in each claim

You will receive multiple articles. Return JSON with a "results" array — one object per article. Each object has:
  - "article_id": the integer ID provided with the article
  - "claims": array of claim objects, each with "text" (string) and "entities" (array of strings)"""

# ponytail: batch size tuned for free-tier rate limits. 5 articles per call
# keeps response under 8000 tokens and finishes in ~13s on deepseek-v4-flash-free.
_BATCH_SIZE = 5


class ForensicExtractionAgent(BasePipelineAgent):
    """Extracts atomic claims from articles using a configurable LLM.

    Takes an article_map (from Agent 1) mapping article_id → cluster_id.
    For each article, calls the LLM, parses the JSON, and inserts claims.
    """

    def __init__(self, *, db_path: str, llm_provider: dict[str, Any],
                 api_key: str = ""):
        """Create the extraction agent.

        Args:
          db_path: Path to the SQLite database.
          llm_provider: Dict with id, name, model fields (resolved via
                        provider_config.get_provider_for_agent).
          api_key: API key for the LLM provider.
        """
        self.db_path = db_path
        self._llm_provider = llm_provider
        self._api_key = api_key

    async def run(self, *, article_map: dict[int, int] | None = None) -> dict[str, Any]:
        """Extract claims from articles assigned to clusters.

        Args:
          article_map: dict of article_id → cluster_id (from Agent 1).
                       If None or empty, the agent processes nothing.

        Returns:
          dict with keys: claims_extracted (count), articles_processed (count).
        """
        if not article_map:
            return {"claims_extracted": 0, "articles_processed": 0}

        # Fetch articles from DB with source_id for claim_sources linking
        conn = get_db(self.db_path)
        try:
            placeholders = ",".join("?" * len(article_map))
            rows = conn.execute(
                f"""SELECT id, title, body, source_id
                    FROM articles
                    WHERE id IN ({placeholders})
                      AND body IS NOT NULL
                      AND body != ''""",
                list(article_map.keys()),
            ).fetchall()
        finally:
            conn.close()

        if not rows:
            return {"claims_extracted": 0, "articles_processed": 0}

        # Create LLM client (one per run — provider may change between runs)
        client = LLMClient(self._llm_provider, api_key=self._api_key)

        claims_extracted = 0
        articles_processed = 0

        # ponytail: process articles in batches of _BATCH_SIZE per LLM call.
        # This reduces API calls from N to N/_BATCH_SIZE and avoids rate limits.
        for batch_start in range(0, len(rows), _BATCH_SIZE):
            batch = rows[batch_start:batch_start + _BATCH_SIZE]

            # Build batched prompt: list each article with its ID
            articles_text = ""
            for row in batch:
                articles_text += (
                    f"\n--- ARTICLE {row['id']} ---\n"
                    f"{row['title'] or ''}\n"
                    f"{row['body'][:400] or ''}\n"
                )

            try:
                raw = await client.chat(
                    messages=[
                        {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
                        {"role": "user", "content": f"Articles:{articles_text}"},
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.0,
                    max_tokens=8000,
                )
                parsed = json.loads(raw)
                results = parsed.get("results", [])
            except (json.JSONDecodeError, Exception):
                continue

            if not isinstance(results, list):
                continue

            # Insert claims from each article in the batch
            conn = get_db(self.db_path)
            try:
                # Build a lookup for article_id → source_id
                source_map = {row["id"]: row["source_id"] for row in rows}
                # Also need published_at for first_seen_at backdating
                date_map = {}
                pub_rows = conn.execute(
                    f"SELECT id, published_at FROM articles WHERE id IN ({placeholders})",
                    list(article_map.keys()),
                ).fetchall()
                for pr in pub_rows:
                    if pr["published_at"]:
                        date_map[pr["id"]] = pr["published_at"]

                for result in results:
                    if not isinstance(result, dict):
                        continue
                    article_id = result.get("article_id")
                    claims = result.get("claims", [])
                    if article_id is None or not isinstance(claims, list):
                        continue

                    cluster_id = article_map.get(article_id)
                    if cluster_id is None:
                        continue

                    source_id = source_map.get(article_id)
                    first_seen = date_map.get(article_id)

                    for claim_obj in claims:
                        if not isinstance(claim_obj, dict):
                            continue
                        claim_text = claim_obj.get("text", "")
                        if not claim_text:
                            continue
                        cid = insert_claim(
                            conn,
                            article_id=article_id,
                            cluster_id=cluster_id,
                            text=claim_text,
                            created_at=first_seen,  # backdate to article pub date
                        )
                        claims_extracted += 1
                        # Link claim to the source that published it
                        if source_id is not None:
                            add_claim_source(
                                conn,
                                claim_id=cid,
                                source_id=source_id,
                                first_seen_at=first_seen,
                            )
                    articles_processed += 1
            finally:
                conn.close()

        return {
            "claims_extracted": claims_extracted,
            "articles_processed": articles_processed,
        }
