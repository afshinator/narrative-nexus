"""Forensic Extraction Agent — stub.

Strips editorial framing, extracts atomic factual claims as structured JSON.
Runs via Fireworks AI API."""

from pipeline.base_agent import BasePipelineAgent


class ForensicExtractionAgent(BasePipelineAgent):
    """Stub — returns empty claim list until Fireworks API is wired."""

    async def run(self, article_texts: list[str] | None = None) -> list[dict]:
        """Stub: returns empty claim list.

        In production:
        1. For each article, call Fireworks LLM with extraction prompt
        2. Parse JSON output into atomic claims
        3. Insert claims into the database
        """
        return []
