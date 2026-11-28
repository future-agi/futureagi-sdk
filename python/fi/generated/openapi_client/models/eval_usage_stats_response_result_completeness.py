from enum import Enum


class EvalUsageStatsResponseResultCompleteness(str, Enum):
    COMPLETE = "complete"
    DEGRADED = "degraded"
    PENDING = "pending"

    def __str__(self) -> str:
        return str(self.value)
