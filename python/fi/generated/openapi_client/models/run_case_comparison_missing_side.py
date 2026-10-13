from enum import Enum


class RunCaseComparisonMissingSide(str, Enum):
    BASELINE = "baseline"
    CANDIDATE = "candidate"

    def __str__(self) -> str:
        return str(self.value)
