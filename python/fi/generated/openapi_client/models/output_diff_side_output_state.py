from enum import Enum


class OutputDiffSideOutputState(str, Enum):
    AVAILABLE = "available"
    INVALID = "invalid"
    MISSING = "missing"
    OVER_LIMIT = "over_limit"
    UNAVAILABLE = "unavailable"

    def __str__(self) -> str:
        return str(self.value)
