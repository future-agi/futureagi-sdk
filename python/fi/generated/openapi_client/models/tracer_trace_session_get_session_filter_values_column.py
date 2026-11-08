from enum import Enum


class TracerTraceSessionGetSessionFilterValuesColumn(str, Enum):
    FIRST_MESSAGE = "first_message"
    LAST_MESSAGE = "last_message"
    SESSION_ID = "session_id"
    USER_ID = "user_id"

    def __str__(self) -> str:
        return str(self.value)
