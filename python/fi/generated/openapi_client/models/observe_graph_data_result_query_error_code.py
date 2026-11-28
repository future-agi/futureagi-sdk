from enum import Enum


class ObserveGraphDataResultQueryErrorCode(str, Enum):
    QUERY_FAILED = "query_failed"
    READ_BUDGET_EXCEEDED = "read_budget_exceeded"
    SAMPLE_LIMIT = "sample_limit"

    def __str__(self) -> str:
        return str(self.value)
