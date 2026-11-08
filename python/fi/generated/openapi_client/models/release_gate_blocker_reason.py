from enum import Enum


class ReleaseGateBlockerReason(str, Enum):
    CRITICAL_REGRESSION = "critical_regression"
    CRITICAL_THRESHOLD = "critical_threshold"
    DUPLICATE = "duplicate"
    EMPTY_PLAN = "empty_plan"
    ERROR = "error"
    INVALID = "invalid"
    MISSING = "missing"
    NOT_ASSESSED = "not_assessed"
    REGRESSION_LIMIT_EXCEEDED = "regression_limit_exceeded"
    UNKNOWN = "unknown"
    UNSUPPORTED = "unsupported"

    def __str__(self) -> str:
        return str(self.value)
