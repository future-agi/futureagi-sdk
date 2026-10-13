from enum import Enum


class CallExecutionSimulationCallType(str, Enum):
    TEXT = "text"
    VOICE = "voice"

    def __str__(self) -> str:
        return str(self.value)
