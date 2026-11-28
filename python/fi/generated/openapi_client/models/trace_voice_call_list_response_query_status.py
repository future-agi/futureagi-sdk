from enum import Enum


class TraceVoiceCallListResponseQueryStatus(str, Enum):
    COMPLETE = "complete"
    DEGRADED = "degraded"

    def __str__(self) -> str:
        return str(self.value)
