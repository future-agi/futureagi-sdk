from enum import Enum


class AgentDefinitionResponseAgentType(str, Enum):
    TEXT = "text"
    VOICE = "voice"

    def __str__(self) -> str:
        return str(self.value)
