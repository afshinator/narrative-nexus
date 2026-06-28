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

# ── Extraction prompt ────────────────────────────────────────────────────
# One system message defining the task, then the article body as user message.

EXTRACTION_SYSTEM_PROMPT = """You are a forensic claim extractor. Your job is to read a news article and extract every atomic, verifiable factual claim it makes.

Rules:
1. Strip editorial framing — remove adjectives, hedges, and passive-voice attribution
2. Each claim must be a single self-contained statement that CAN be verified or falsified
3. Claims must be atomic — one fact per claim, not compound statements
4. Do NOT summarize, paraphrase, or add commentary
5. Do NOT include opinions, predictions, or value judgments
6. Include named entities (people, organizations, locations) in each claim

Output format: valid JSON with a "claims" array. Each claim object has:
  - "text": the atomic factual claim (string)
  - "entities": array of named entity strings mentioned in the claim

Example:
{"claims": [
  {"text": "The president signed Executive Order 14123", "entities": ["president"]},
  {"text": "The order allocates 2.3 billion dollars to climate programs", "entities": ["climate programs"]}
]}"""


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

        # Fetch articles from DB
        conn = get_db(self.db_path)
        try:
            placeholders = ",".join("?" * len(article_map))
            rows = conn.execute(
                f"""SELECT id, title, body
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

        for row in rows:
            article_id = row["id"]
            cluster_id = article_map.get(article_id)
            if cluster_id is None:
                continue  # safety: article not in map (shouldn't happen)

            text = f"{row['title'] or ''}\n\n{row['body'] or ''}"

            try:
                raw = await client.chat(
                    messages=[
                        {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
                        {"role": "user", "content": text},
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.0,
                    max_tokens=2000,
                )
                parsed = json.loads(raw)
            except (json.JSONDecodeError, Exception):
                # ponytail: skip malformed responses silently
                continue

            claims = parsed.get("claims", [])
            if not isinstance(claims, list):
                continue

            # Insert claims into DB
            conn = get_db(self.db_path)
            try:
                for claim_obj in claims:
                    if not isinstance(claim_obj, dict):
                        continue
                    claim_text = claim_obj.get("text", "")
                    if not claim_text:
                        continue
                    insert_claim(
                        conn,
                        article_id=article_id,
                        cluster_id=cluster_id,
                        text=claim_text,
                    )
                    claims_extracted += 1
            finally:
                conn.close()

            articles_processed += 1

        return {
            "claims_extracted": claims_extracted,
            "articles_processed": articles_processed,
        }
