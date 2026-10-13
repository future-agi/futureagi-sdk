from enum import Enum


class ExternalRunScoreStatus(str, Enum):
    ASSESSED = "assessed"
    ERROR = "error"
    NOT_ASSESSED = "not_assessed"
    UNKNOWN = "unknown"
    UNSUPPORTED = "unsupported"

    def __str__(self) -> str:
        return str(self.value)
