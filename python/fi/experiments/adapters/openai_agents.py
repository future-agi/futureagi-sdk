"""OpenAI Agents SDK: ``await Runner.run(agent, row.input, context=ctx)`` → ``.final_output``."""

from __future__ import annotations

from typing import Any

from fi.experiments.adapters._base import TaskRunner


class OpenAIAgentsRunner(TaskRunner):
    framework = "openai_agents"
    is_async = True
    needs_single_input = True

    def __init__(self, agent: Any) -> None:
        self.agent = agent

    def describe(self) -> str:
        name = getattr(self.agent, "name", None) or "agent"
        return f"OpenAI Agents → await Runner.run({name}, row.input, context=ctx) → .final_output"

    async def acall(self, row: Any, ctx: Any) -> Any:
        from agents import Runner

        result = await Runner.run(self.agent, row.input, context=ctx)
        return result.final_output
