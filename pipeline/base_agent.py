"""Base class for all pipeline agents."""

from abc import ABC, abstractmethod


class BasePipelineAgent(ABC):
    """Abstract base for all four Narrative Nexus pipeline agents.

    Every agent implements `run()` with agent-specific input/output types.
    Subclasses must override `run()`. For stub subclasses, `run()` returns
    empty results matching the expected output type.
    """

    @abstractmethod
    async def run(self, *args, **kwargs):
        """Execute the agent's pipeline stage.

        All agents accept keyword arguments specific to their stage and
        return structured results.
        """
        ...
