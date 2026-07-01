"""Forensic Extraction Agent — LLM-powered claim extraction.

Reads articles from the database, sends each to an LLM with a structured
extraction prompt, parses the JSON response, and inserts atomic factual
claims into the database.

Uses response_format={"type": "json_object"} for guaranteed valid JSON.
Temperature 0.0 for deterministic extraction.

ponytail: Single-pass extraction (bias rating + neutralization + claims in one call).
ponytail: Lexical and sentiment scores computed locally (no API) per article.
ponytail: Claims from malformed JSON are silently skipped.
"""

import json
import sqlite3
from typing import Any

from pipeline.llm_client import LLMClient
from pipeline.base_agent import BasePipelineAgent
from pipeline.framing import score_lexical, score_sentiment
from db.connection import get_db
from db.claims import insert_claim
from db.claim_sources import add_claim_source
from db.framing import insert_framing_scores

# ── Extraction prompt ────────────────────────────────────────────────────
# One system message defining the task, then the article body as user message.

EXTRACTION_SYSTEM_PROMPT = """You are a forensic claim extractor. For each article you receive:

STEP 1 — Rate editorial framing bias on a scale of 1-10:
  1 = Pure wire-service style. Just the facts, no adjectives, no opinion.
      Example: "The president signed the bill into law Tuesday afternoon."
  3 = Mostly neutral with occasional loaded language.
      Example: "The controversial legislation, debated for months, was signed Tuesday."
  5 = Moderate editorial framing. Clear word choices that steer interpretation.
      Example: "The embattled president reluctantly signed the deeply divisive bill into law."
  7 = Heavy editorializing. Strong adjectives, clear author opinion, dramatic framing.
      Example: "In a stunning capitulation, the president caved to pressure and signed the disastrous bill."
  10 = Pure opinion piece. Every sentence carries judgment.
      Example: "The corrupt administration rammed through yet another catastrophic policy Tuesday, proving once again that they answer only to their billionaire donors."

STEP 2 — Strip editorial framing (remove adjectives, hedges, passive-voice attribution).

STEP 3 — Extract every atomic, verifiable factual claim from the neutralized text.

Rules for claims:
1. Each claim must be a single self-contained statement that CAN be verified or falsified
2. Claims must be atomic — one fact per claim, not compound statements
3. Do NOT summarize, paraphrase, or add commentary
4. Do NOT include opinions, predictions, or value judgments
5. Include named entities (people, organizations, locations) in each claim

Return JSON with a "results" array — one object per article:
  - "article_id": the integer ID provided with the article
  - "framing_score": integer 1-10 from STEP 1
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
            body_map: dict[int, str] = {}  # article_id → full body for lexical/sentiment
            for row in batch:
                articles_text += (
                    f"\n--- ARTICLE {row['id']} ---\n"
                    f"{row['title'] or ''}\n"
                    f"{row['body'][:400] or ''}\n"
                )
                body_map[row["id"]] = (row["body"] or "")[:2000]

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

                    # Store LLM framing score if present
                    framing_raw = result.get("framing_score")
                    llm_score = None
                    if framing_raw is not None:
                        try:
                            llm_score = float(framing_raw)
                        except (ValueError, TypeError):
                            pass

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
                    # Compute + store lexical and sentiment scores (no API)
                    body = body_map.get(article_id, "")
                    insert_framing_scores(
                        conn,
                        article_id=article_id,
                        llm_score=llm_score,
                        lexical_score=score_lexical(body),
                        sentiment_score=score_sentiment(body),
                    )
            finally:
                conn.close()

        return {
            "claims_extracted": claims_extracted,
            "articles_processed": articles_processed,
        }
