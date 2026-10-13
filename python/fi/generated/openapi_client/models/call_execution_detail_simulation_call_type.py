from enum import Enum


class CallExecutionDetailSimulationCallType(str, Enum):
    TEXT = "text"
    VOICE = "voice"

    def __str__(self) -> str:
        return str(self.value)
