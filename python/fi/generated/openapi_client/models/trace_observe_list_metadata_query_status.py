from enum import Enum


class TraceObserveListMetadataQueryStatus(str, Enum):
    COMPLETE = "complete"
    DEGRADED = "degraded"

    def __str__(self) -> str:
        return str(self.value)
