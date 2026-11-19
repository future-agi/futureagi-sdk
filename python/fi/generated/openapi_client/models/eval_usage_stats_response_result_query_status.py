from enum import Enum


class EvalUsageStatsResponseResultQueryStatus(str, Enum):
    COMPLETE = "complete"
    DEGRADED = "degraded"
    PENDING = "pending"

    def __str__(self) -> str:
        return str(self.value)
