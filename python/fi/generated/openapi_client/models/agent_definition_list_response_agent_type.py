from enum import Enum


class AgentDefinitionListResponseAgentType(str, Enum):
    TEXT = "text"
    VOICE = "voice"

    def __str__(self) -> str:
        return str(self.value)
