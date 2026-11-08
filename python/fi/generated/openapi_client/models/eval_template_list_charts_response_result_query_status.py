from enum import Enum


class EvalTemplateListChartsResponseResultQueryStatus(str, Enum):
    COMPLETE = "complete"
    DEGRADED = "degraded"
    STALE = "stale"

    def __str__(self) -> str:
        return str(self.value)
