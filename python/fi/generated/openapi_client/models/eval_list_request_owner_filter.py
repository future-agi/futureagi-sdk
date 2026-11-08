from enum import Enum


class EvalListRequestOwnerFilter(str, Enum):
    ALL = "all"
    SYSTEM = "system"
    USER = "user"

    def __str__(self) -> str:
        return str(self.value)
