from enum import Enum


class TraceSessionGraphDataRequestReqDataConfigSource(str, Enum):
    SESSIONS = "sessions"
    TRACES = "traces"

    def __str__(self) -> str:
        return str(self.value)
