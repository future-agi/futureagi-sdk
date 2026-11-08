from enum import Enum


class TraceGraphDataRequestReqDataConfigSource(str, Enum):
    SESSIONS = "sessions"
    TRACES = "traces"

    def __str__(self) -> str:
        return str(self.value)
