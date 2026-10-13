from enum import Enum


class ScenarioCreateRequestSourceType(str, Enum):
    AGENT_DEFINITION = "agent_definition"
    PROMPT = "prompt"

    def __str__(self) -> str:
        return str(self.value)
