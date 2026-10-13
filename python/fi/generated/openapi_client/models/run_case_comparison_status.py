from enum import Enum


class RunCaseComparisonStatus(str, Enum):
    DUPLICATE = "duplicate"
    ERROR = "error"
    IMPROVED = "improved"
    INVALID = "invalid"
    MISSING = "missing"
    NOT_ASSESSED = "not_assessed"
    REGRESSED = "regressed"
    TIE = "tie"
    UNKNOWN = "unknown"
    UNSUPPORTED = "unsupported"

    def __str__(self) -> str:
        return str(self.value)
