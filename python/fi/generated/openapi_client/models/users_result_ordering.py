from enum import Enum


class UsersResultOrdering(str, Enum):
    LATEST_MATCHING_ACTIVITY = "latest_matching_activity"

    def __str__(self) -> str:
        return str(self.value)
