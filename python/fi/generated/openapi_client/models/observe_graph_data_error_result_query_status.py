from enum import Enum


class ObserveGraphDataErrorResultQueryStatus(str, Enum):
    COMPLETE = "complete"
    DEGRADED = "degraded"
    PENDING = "pending"
    SAMPLED = "sampled"

    def __str__(self) -> str:
        return str(self.value)
