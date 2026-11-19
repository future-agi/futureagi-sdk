from enum import Enum


class OutputDiffComparisonStatus(str, Enum):
    CHANGED = "changed"
    NOT_COMPARABLE = "not_comparable"
    UNCHANGED = "unchanged"

    def __str__(self) -> str:
        return str(self.value)
