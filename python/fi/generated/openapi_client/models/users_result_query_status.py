from enum import Enum


class UsersResultQueryStatus(str, Enum):
    COMPLETE = "complete"
    DEGRADED = "degraded"

    def __str__(self) -> str:
        return str(self.value)
