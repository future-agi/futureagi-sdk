from enum import Enum


class UsersResultApproximateFieldsItem(str, Enum):
    NUM_SESSIONS = "num_sessions"

    def __str__(self) -> str:
        return str(self.value)
