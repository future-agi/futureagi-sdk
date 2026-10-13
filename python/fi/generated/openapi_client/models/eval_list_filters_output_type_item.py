from enum import Enum


class EvalListFiltersOutputTypeItem(str, Enum):
    DETERMINISTIC = "deterministic"
    PASS_FAIL = "pass_fail"
    PERCENTAGE = "percentage"

    def __str__(self) -> str:
        return str(self.value)
