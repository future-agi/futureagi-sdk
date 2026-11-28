from enum import Enum


class TraceSessionListMetadataQueryStatus(str, Enum):
    COMPLETE = "complete"
    DEGRADED = "degraded"

    def __str__(self) -> str:
        return str(self.value)
