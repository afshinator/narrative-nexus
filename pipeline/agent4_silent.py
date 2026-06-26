"""Silent Auditor Agent — stub.

Compares historical article snapshots to detect unreported edits.
Runs as a background job."""

from pipeline.base_agent import BasePipelineAgent


class SilentAuditorAgent(BasePipelineAgent):
    """Stub — returns empty diff list until article snapshots exist."""

    async def run(self, article_ids: list[int] | None = None) -> list[dict]:
        """Stub: returns empty diff list.

        In production:
        1. Re-fetch article bodies via scraper
        2. Diff against stored bodies
        3. Flag significant changes without correction notices
        """
        return []
