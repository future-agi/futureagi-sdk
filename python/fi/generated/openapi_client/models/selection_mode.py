from enum import Enum


class SelectionMode(str, Enum):
    FILTER = "filter"

    def __str__(self) -> str:
        return str(self.value)
