from enum import Enum


class AgentDefinitionCreateRequestAgentType(str, Enum):
    TEXT = "text"
    VOICE = "voice"

    def __str__(self) -> str:
        return str(self.value)
