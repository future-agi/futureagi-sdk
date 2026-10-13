from enum import Enum


class ApiSelectionTooLargeErrorType(str, Enum):
    SELECTION_TOO_LARGE = "selection_too_large"

    def __str__(self) -> str:
        return str(self.value)
