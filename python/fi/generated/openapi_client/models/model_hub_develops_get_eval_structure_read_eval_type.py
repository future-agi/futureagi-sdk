from enum import Enum


class ModelHubDevelopsGetEvalStructureReadEvalType(str, Enum):
    PRESET = "preset"
    PREVIOUSLY_CONFIGURED = "previously_configured"
    USER = "user"

    def __str__(self) -> str:
        return str(self.value)
