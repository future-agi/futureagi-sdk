from enum import Enum


class OutputDiffComparisonMissingSide(str, Enum):
    BASELINE = "baseline"
    BOTH = "both"
    CANDIDATE = "candidate"

    def __str__(self) -> str:
        return str(self.value)
