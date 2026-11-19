from enum import Enum


class TraceAgentGraphResultQueryStatus(str, Enum):
    COMPLETE = "complete"
    PENDING = "pending"

    def __str__(self) -> str:
        return str(self.value)
