from enum import Enum


class TraceGraphDataRequestObserveType(str, Enum):
    TRACE = "trace"
    VOICE = "voice"

    def __str__(self) -> str:
        return str(self.value)
